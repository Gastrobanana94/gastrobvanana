# Genera IG_REEL_VIRALE_IMPORT.json (il flusso vero) partendo dalla prova v4.
# Uso: python3 genera_flusso.py   (dalla cartella instagram_reel_virale)
# Prende dei pezzi gia' provati da:
#   - IG_REEL_VIRALE_PROVA_IMPORT.json (canzone, Use audio, galleria, editor, pagina finale, liste caption)
#   - ../instagram_trial/IG_TRIAL_REEL_IMPORT.json (SoloProva, scorri fino a 'Share to', Share)
#   - ../instagram_warmup/IG_WARMUP_IMPORT.json (repost, salva, like nella home)
import copy, json, os, sys, uuid

QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, 'IG_REEL_VIRALE_IMPORT.json')
TITOLO = 'IG REEL VIRALE v1'
MAX_BYTE = 240000   # v10.4 (243.090 byte, 532 passi) parte; v10.2 (250.245, 550) no
MAX_PASSI = 520


def carica(p):
    with open(os.path.join(QUI, p), encoding='utf-8') as f:
        return json.load(f)


PROVA = carica('IG_REEL_VIRALE_PROVA_IMPORT.json')
TRIAL = carica('../instagram_trial/IG_TRIAL_REEL_IMPORT.json')
WARM = carica('../instagram_warmup/IG_WARMUP_IMPORT.json')


def sotto(n):
    """liste di figli di un nodo (children, other)"""
    return [(k, v) for k, v in n.get('config', {}).items()
            if isinstance(v, list) and v and isinstance(v[0], dict) and 'config' in v[0]]


def trova(flusso, nome, dentro=None):
    nodi = dentro if dentro is not None else flusso['content']['contents']
    for n in nodi:
        if n.get('name') == nome:
            return copy.deepcopy(n)
        for _, v in sotto(n):
            r = trova(flusso, nome, v)
            if r is not None:
                return r
    if dentro is None:
        sys.exit('nodo non trovato: ' + nome)
    return None


def figli(n, chiave='children'):
    return n['config'][chiave]


# ---------- costruttori ----------
OK = "const ok=v=>!(v==null||v===false||/^(|0|false|undefined|null)$/i.test(String(v).trim()));"
R = "const r=(a,b)=>a+Math.floor(Math.random()*(b-a+1));"


def nodo(nome, tipo, config):
    return {'position': {'x': 0, 'y': 285}, 'id': '', 'name': nome, 'type': tipo, 'config': config}


def js(nome, inp, corpo, out):
    """corpo: codice JS che finisce con return {...}"""
    arg = '{ ' + ', '.join(inp) + ' }' if inp else ''
    return nodo(nome, 'script', {
        'injectVariables': list(inp),
        'script': 'async function main(%s) { %s }' % (arg, corpo),
        'type': 'js',
        'variableMap': [{'value': o, 'variable': o} for o in out]})


def azzera(nome, valori):
    corpo = 'return { ' + ', '.join('%s: %s' % (k, json.dumps(v)) for k, v in valori.items()) + ' };'
    return js(nome, [], corpo, list(valori))


def adb(nome, cmd, var='tapOut'):
    return nodo(nome, 'executeADB', {'content': cmd, 'timeout': 120000, 'variable': var, 'error': False})


def attendi(a, b, nome='wait'):
    return nodo(nome, 'waitTime', {'timeoutMax': b, 'timeoutMin': a, 'timeoutType': 'randomInterval'})


def cond(var, val=None, rel='equal'):
    c = {'probability': 50, 'relation': rel, 'useVariable': var}
    if val is not None:
        c['result'] = val
    return c


def se(nome, conds, figli_, altri=None):
    return nodo(nome, 'ifElse', {'apposition': 'and', 'children': figli_,
                                 'conditionList': conds, 'other': altri or []})


def ciclo(nome, volte, figli_, indice=None):
    c = {'serialType': 'randomInterval', 'minTimes': volte, 'maxTimes': volte,
         'hiddenChildren': False, 'children': figli_}
    if indice:
        c['variableIndex'] = indice
    return nodo(nome, 'forTimes', c)


def filtri(*gruppi):
    """gruppi: liste di (tipo, contenuto, 'equal'|'contain')"""
    return [[{'content': c, 'filterType': f, 'type': t} for (t, c, f) in g] for g in gruppi]


def tocca(nome, fc, cerca, var=None):
    c = {'filterCollection': fc, 'hiddenChildren': False, 'randomDistance': 0, 'searchTime': cerca,
         'useOffset': False, 'serialType': 'fixedValue', 'serial': 1, 'excuteError': 'noProcessing'}
    if var:
        c['variable'] = var
    return nodo(nome, 'click', c)


def leggi(nome, fc, cerca, var, tipo='centerY', serial=1):
    return nodo(nome, 'getEle', {'filterCollection': fc, 'serialType': 'fixedValue', 'serial': serial,
                                 'hiddenChildren': False, 'searchTime': cerca, 'type': tipo,
                                 'variable': var, 'error': False})


def foto(nome, fine=False):
    return nodo(nome, 'screenshotPage', {'endPicture': True} if fine else
                {'error': False, 'isBase64': False, 'isScope': False})


def errore(testo):
    """screenshot, chiude Instagram, errore, fine task"""
    return [foto('screenshot dell\'errore', True),
            adb('chiudi Instagram (errore, non pubblico niente)', 'am force-stop com.instagram.android', 'stopIg'),
            nodo('errore: ' + testo[:60], 'throwException', {'content': testo}),
            nodo('End task (dopo l\'errore)', 'endTask', {})]


CHIUDI_IG = 'am force-stop com.instagram.android'
NOT_NOW = trova(PROVA, "pop-up 'Not now'")
REELS_POS = 'input tap 216 1326'


def tocca_reels():
    return [azzera('azzera: Reels', {'cReels': ''}),
            trova(PROVA, 'tocca Reels (in basso)'),
            trova(PROVA, "IF GeeLark non l'ha trovato -> tocca Reels per posizione"),
            attendi(2500, 3500),
            copy.deepcopy(NOT_NOW)]


def apri_instagram():
    return [trova(PROVA, 'apri Instagram'), trova(PROVA, "apri Instagram (come l'icona)"),
            trova(PROVA, "aspetta che Instagram si apra"), copy.deepcopy(NOT_NOW)]


SCORRI = ("const x=r(330,390); const sx1=String(x), sy1=String(r(1000,1100)), sx2=String(x+r(-25,25)), "
          "sy2=String(r(250,350)), sd=String(r(140,190));")


# ---------- 1. inizio: SoloProva, video, lingua e caption ----------
inizio = []
inizio.append(js('azzera: riepilogo', [], 'return { ' + ', '.join('%s: %s' % (k, json.dumps(v)) for k, v in {
    'ciechi': '0', 'fermo': '0', 'diario': '', 'scelto': '0', 'reelScelto': '', 'perche': '', 'likeNum': '',
    'quantiReel': '', 'usaOk': '0', 'galOk': '0', 'comeGal': '', 'primo': '0', 'videoScelto': '0',
    'editorOk': '0', 'finaleOk': '0', 'capOk': '0', 'capFinale': '', 'daDove': '', 'usaPos': '0',
    'comeUsa': '', 'comeVideo': '', 'galVista': '', 'editsChiusi': '0', 'playStore': '0', 'trending': '',
    'inPlay': '0', 'likeFatti': '0', 'likeHome': '0', 'repostFatti': '0', 'salvaFatti': '0', 'cercaN': '0',
    'fbStato': '', 'trialStato': '', 'fbTocchi': '0', 'trialTocchi': '0', 'pubOk': '0', 'esito': '',
    'likeDopo': '0', 'nReel': '0', 'nDopo': '0', 'videoOk': '0'}.items()) + ' };',
    ['ciechi', 'fermo', 'diario', 'scelto', 'reelScelto', 'perche', 'likeNum', 'quantiReel', 'usaOk',
     'galOk', 'comeGal', 'primo', 'videoScelto', 'editorOk', 'finaleOk', 'capOk', 'capFinale', 'daDove',
     'usaPos', 'comeUsa', 'comeVideo', 'galVista', 'editsChiusi', 'playStore', 'trending', 'inPlay',
     'likeFatti', 'likeHome', 'repostFatti', 'salvaFatti', 'cercaN', 'fbStato', 'trialStato', 'fbTocchi',
     'trialTocchi', 'pubOk', 'esito', 'likeDopo', 'nReel', 'nDopo', 'videoOk']))

prova_js = js('SoloProva acceso?', ['SoloProva'],
              "const p=String(SoloProva===undefined||SoloProva===null?'':SoloProva).trim().toLowerCase(); "
              "const prova=(p==='true'||p==='1'||p==='yes'||p==='on')?'1':'0'; "
              "const provaBoh=(p===''||p==='undefined'||p==='null')?'1':'0'; return { prova, provaBoh };",
              ['prova', 'provaBoh'])
inizio += [prova_js, trova(TRIAL, 'IF lo script non ha letto SoloProva -> decide GeeLark')]

for nome in ['tastiera GeeLark', 'permessi a Instagram (foto, video, fotocamera)', 'chiudi Instagram',
             'svuota la cartella Download', 'segnaposto: da qui in poi arriva solo il video del task',
             'carica il video del task sul telefono', 'azzera: video arrivato?',
             'aspetta il video del task (fino a 1 minuto)']:
    inizio.append(trova(PROVA, nome))
inizio.append(se('IF il video non e\' arrivato -> errore', [cond('videoOk', '0')],
                 errore("[Video] Il video del task non e' arrivato sul telefono (cartella Download). "
                        "Non pubblico niente.")))
for nome in ['la galleria vede il video nuovo', 'da che paese esce il telefono? (proxy)',
             'note e caption: italiane o tedesche? (dal proxy)',
             "questo telefono: quante caption reel ha gia' usato? (e schermo)",
             "caption dalla lista (ogni telefono in un ordine suo)",
             "caption: quella del task o quella della lista? (e grandezza dello schermo)"]:
    inizio.append(trova(PROVA, nome))

# ---------- 2. apre Instagram e aspetta che GeeLark ci veda ----------
inizio += apri_instagram()
inizio += [trova(PROVA, "azzera: GeeLark vede? (la barra in basso)"),
           trova(PROVA, "GeeLark ci vede? (la barra in basso; se e' cieco aspetta)")]

# tempi: warm-up 13-15 minuti prima di cercare la canzone (SoloProva: 2,5-3 minuti)
inizio.append(js('tempi del warm-up (13-15 minuti; SoloProva 2,5-3)', ['prova'],
                 R + "const now=Date.now(); const tOk=(isFinite(now) && now>1.6e12)?'1':'0'; "
                 "const pr=String(prova)==='1'; const wu=pr ? r(150,180)*1000 : r(780,900)*1000; "
                 "const home=pr ? r(30,45)*1000 : r(100,160)*1000; "
                 "return { tOk, tInizio: String(now), fineWU: String(now+wu), fineHome: String(now+home), "
                 "minutiWU: (wu/60000).toFixed(1), maxWU: String(Math.round(wu/9000)), "
                 "maxHome: String(Math.round(home/6000)), nextLike: String(r(7,8)), "
                 "repostTot: '1', salvaTot: String(r(1,2)), likeHomeTot: '1', ancoraH: '1', tentativi: '0', "
                 "fuori: '0', finito: '0' };",
                 ['tOk', 'tInizio', 'fineWU', 'fineHome', 'minutiWU', 'maxWU', 'maxHome', 'nextLike',
                  'repostTot', 'salvaTot', 'likeHomeTot', 'ancoraH', 'tentativi', 'fuori', 'finito']))

# ---------- 3. warm-up: home (scorre solo in giu', al massimo 1 like) ----------
like_home = trova(WARM, "metti like al post (cuore 'Like')")
home = ciclo('warm-up: scorri la home (solo verso il basso)', 40, [
    se('IF home non finita', [cond('ancoraH', '1')], [
        copy.deepcopy(NOT_NOW),
        attendi(2000, 6500, 'guarda il post'),
        js('home: like a questo post? e come scorro', ['likeHome', 'likeHomeTot'],
           R + "const l=(parseInt(likeHome,10)||0)<(parseInt(likeHomeTot,10)||0) && Math.random()<0.15; "
           "const x=r(320,400); return { hLike: l?'1':'0', hx1: String(x), hy1: String(r(950,1050)), "
           "hx2: String(x+r(-20,20)), hy2: String(r(380,480)), hd: String(r(280,420)) };",
           ['hLike', 'hx1', 'hy1', 'hx2', 'hy2', 'hd']),
        se('IF like a questo post', [cond('hLike', '1')], [
            azzera('azzera: like', {'cLike': ''}),
            like_home,
            js('like messo?', ['cLike', 'likeHome'],
               OK + "return { likeHome: String((parseInt(likeHome,10)||0)+(ok(cLike)?1:0)) };", ['likeHome']),
            attendi(800, 1500)]),
        adb('scorri la home', 'input swipe ${hx1} ${hy1} ${hx2} ${hy2} ${hd}', 'swOut'),
        js('home: ancora?', ['fineHome', 'tOk', 'kh', 'maxHome'],
           "const n=parseInt(kh,10)||0; const t=String(tOk)==='1' ? Date.now()<Number(fineHome) : "
           "n<(parseInt(maxHome,10)||20); return { ancoraH: t?'1':'0' };", ['ancoraH'])])], 'kh')

# ---------- 4. warm-up nei Reels + ricerca della canzone virale ----------
# un solo giro di reels: prima il warm-up (like ogni 7-8 reel, 1 repost, 1-2 salvati),
# finito il tempo cerca la canzone come nella prova (dal reel dopo, al massimo 50 reel)
reels_figli = []
watch = trova(PROVA, 'IF 25%: guarda poco')
reels_figli += [watch,
                trova(PROVA, 'Android: dove sono cuore e quadratino della canzone?'),
                trova(PROVA, 'mappa del reel'),
                trova(PROVA, 'IF non sono sui reels (2 volte) -> tocca Reels'),
                trova(PROVA, 'primo reel?'),
                trova(PROVA, 'IF primo reel -> screenshot')]

reels_figli.append(js(
    'cosa faccio su questo reel? (like ogni 7-8, repost, salva, cerco la canzone?)',
    ['iReel', 'suReels', 'nextLike', 'fineWU', 'tOk', 'maxWU', 'repostFatti', 'repostTot', 'salvaFatti',
     'salvaTot', 'cercaN'],
    R + "const i=parseInt(iReel,10)||1; const su=String(suReels)==='1'; const now=Date.now(); "
    "const fine=Number(fineWU); const tempoSu = String(tOk)==='1' ? now>=fine : i>(parseInt(maxWU,10)||90); "
    "const cn=parseInt(cercaN,10)||0; const cerca = tempoSu && cn<50; const finito = tempoSu && cn>=50; "
    "const metti = su && i>=(parseInt(nextLike,10)||8); "
    "let est = String(tOk)==='1' ? (fine-now)/9000 : (parseInt(maxWU,10)||90)-i; est=Math.max(1,est); "
    "const p=(t,f)=>{ const x=(parseInt(t,10)||0)-(parseInt(f,10)||0); return x<=0?0:Math.min(1,x/est); }; "
    "let rep = su && !tempoSu && i>=3 && Math.random()<p(repostTot,repostFatti); "
    "let sal = su && !tempoSu && i>=3 && !rep && Math.random()<p(salvaTot,salvaFatti); "
    "return { metti: metti?'1':'0', fRep: rep?'1':'0', fSal: sal?'1':'0', cerca: cerca?'1':'0', "
    "cercaN: String(cn+(cerca?1:0)), finito: finito?'1':'0', nReel: String(i), "
    "dtX: String(r(300,420)), dtY: String(r(520,760)) };",
    ['metti', 'fRep', 'fSal', 'cerca', 'cercaN', 'finito', 'nReel', 'dtX', 'dtY']))

like_blocco = trova(PROVA, 'IF like -> cuore o doppio tocco')
for n in figli(like_blocco):
    if n['name'] == 'like fatti +1':
        n.update(js('like fatti +1 (il prossimo tra 7-8 reel)', ['likeFatti', 'iReel'],
                    R + "return { likeFatti: String((parseInt(likeFatti,10)||0)+1), "
                    "nextLike: String((parseInt(iReel,10)||1)+r(7,8)) };", ['likeFatti', 'nextLike']))
reels_figli.append(like_blocco)

reels_figli.append(trova(WARM, 'IF repost'))
reels_figli.append(trova(WARM, 'IF salva'))

# la parte della canzone (solo quando il warm-up e' finito)
canzone = []
for nome in ['azzera: like', 'orologio', 'quanti like? (numero sotto il cuore)']:
    canzone.append(trova(PROVA, nome))
canzone.append(js(
    'apro la canzone? (almeno 2K like, se si leggono)',
    ['likeT', 'haLike', 'haArt', 't0', 'tentativi', 'ciechi'],
    OK + "const num=s=>{ const m=/(\\d[\\d.,]*)\\s*([KkMm]?)/.exec(String(s==null?'':s).replace(/\\d+:\\d+/g,'')); "
    "if(!m) return null; let n; if(m[2]){ n=parseFloat(m[1].replace(',','.'))*(/k/i.test(m[2])?1e3:1e6); } "
    "else n=parseInt(m[1].replace(/[.,]/g,''),10); return isFinite(n) ? Math.round(n) : null; }; "
    "const like=num(likeT); const dt=Date.now()-Number(t0); "
    "const buio = !ok(likeT) && String(haLike)==='1' && isFinite(dt) && dt<400; const t=parseInt(tentativi,10)||0; "
    "const apri = String(haArt)==='1' && t<20 && (like===null || like>=2000); "
    "return { apri: apri?'1':'0', likeNum: like===null?'':String(like), tentativi: String(t+(apri?1:0)), "
    "primoTent: (apri && t===0)?'1':'0', ciechi: String((parseInt(ciechi,10)||0)+(buio?1:0)) };",
    ['apri', 'likeNum', 'tentativi', 'primoTent', 'ciechi']))
apri_blocco = trova(PROVA, "IF si' -> quadratino della canzone")


def ritocca_virale(nodi):
    for n in nodi:
        if n['name'] == 'canzone virale? (bollino Trending o almeno 1.000 reel)':
            s = n['config']['script']
            s = s.replace("const fac = String(facile)==='1'; ", "const fac = false; ")
            s = s.replace("+((fac && !trend && !(n>=1000))?' (dal 12° reel basta una canzone)':'')", "")
            s = s.replace(", facile, likeNum", ", likeNum")
            n['config']['script'] = s
            n['config']['injectVariables'] = [v for v in n['config']['injectVariables'] if v != 'facile']
            assert 'facile' not in s, s
        for _, v in sotto(n):
            ritocca_virale(v)


ritocca_virale([apri_blocco])
canzone.append(apri_blocco)
reels_figli.append(se('IF warm-up finito -> cerco la canzone virale', [cond('cerca', '1')], canzone))

scorri = trova(PROVA, 'IF non scelto -> reel dopo (veloce, 147-180 ms)')
scorri['name'] = 'IF non scelto -> reel dopo (veloce, 140-190 ms)'
for n in figli(scorri):
    if n['name'] == 'come scorre':
        n.update(js('come scorre (140-190 ms)', [], R + SCORRI + " return { sx1, sy1, sx2, sy2, sd };",
                    ['sx1', 'sy1', 'sx2', 'sy2', 'sd']))
reels_figli.append(scorri)

reels = ciclo('warm-up nei reels, poi cerca la canzone virale (al massimo 50 reel)', 250, [
    se('IF canzone non ancora scelta (e non ho finito)', [cond('scelto', '0'), cond('finito', '0')],
       reels_figli)], 'iReel')

giro = [home] + tocca_reels() + [reels,
        se('IF nessuna canzone virale -> errore', [cond('scelto', '0')],
           errore("[Canzone] Dopo il warm-up non ho trovato una canzone virale (bollino Trending o almeno "
                  "1.000 reel, reel con almeno 2K like) in 50 reel. Non pubblico niente."))]

# ---------- 5. Use audio, galleria, video, editor (come nella prova v4) ----------
prepara = [trova(PROVA, 'azzera: fotocamera e galleria'),
           trova(PROVA, "IF canzone scelta -> 'Use audio'"),
           se("IF il video del task non e' il primo -> errore", [cond('primo', '0')],
              errore("[Galleria] Per Android l'ultimo video aggiunto non e' quello del task (o la galleria non "
                     "si e' aperta). Non pubblico niente.")),
           se('IF editor non aperto -> errore', [cond('editorOk', '0')],
              errore("[Editor] Toccato il video ma l'editor (Next) non si apre. Non pubblico niente.")),
           trova(PROVA, 'azzera: pagina finale')]
editor = trova(PROVA, 'IF editor aperto -> Next, pagina finale')
editor['config']['children'] = [n for n in figli(editor)
                                 if n['name'] != 'IF pagina finale -> scrivi la caption (per provare la casella)']
prepara += [editor,
            se('IF pagina finale non aperta -> errore', [cond('finaleOk', '0')],
               errore("[Pagina finale] Dopo Next non vedo la pagina finale (quella con Share). "
                      "Non pubblico niente."))]

# ---------- 6. caption ----------
cap = [azzera('azzera: caption', {'tCap': '', 'capOk': '0'}),
       trova(PROVA, 'scrivi la caption'), trova(PROVA, 'caption scritta?'),
       trova(PROVA, 'IF non scritta -> nella casella di testo'),
       se('IF caption non scritta -> errore', [cond('capOk', '0')],
          errore("[Caption] Non riesco a scrivere la caption. Non pubblico niente.")),
       attendi(1000, 1500),
       trova(TRIAL, "tocca OK (fine descrizione), se c'e'"),
       attendi(1200, 1800),
       foto('screenshot: caption scritta')]

# ---------- 7. in fondo alla pagina: Facebook acceso, Trial spento ----------
fondo = [trova(TRIAL, 'azzera: fondo della pagina'),
         trova(TRIAL, "scorri giu' fino a 'Share to' (al massimo 5 volte)")]

UI = ("sh -c 'f=/sdcard/.ig_ui.xml; rm -f $f; uiautomator dump $f >/dev/null 2>&1; "
      "if [ -s $f ]; then tr \">\" \"\\n\" < $f | grep -E \"checkable=.true|Facebook|[Tt]rial\" | "
      "sed -E \"s/.*text=(\\\"[^\\\"]*\\\").*content-desc=(\\\"[^\\\"]*\\\").*checkable=\\\"([a-z]*)\\\" "
      "checked=\\\"([a-z]*)\\\".*selected=\\\"([a-z]*)\\\" bounds=\\\"[[]([0-9]+),([0-9]+)[]][[]([0-9]+),([0-9]+)[]]\\\".*"
      "/N|\\1|\\2|\\3|\\4|\\5|\\6|\\7|\\8|\\9/\" | grep \"^N|\" | head -n 30; else echo nodump; fi; "
      "rm -f $f; echo fine'")

CONTROLLA = (
    "const righe=String(uiOut||'').split(/\\n/).filter(x=>/^N\\|/.test(x)).map(x=>{ const p=x.split('|'); "
    "return { t:(p[1]||'').replace(/^\"|\"$/g,''), d:(p[2]||'').replace(/^\"|\"$/g,''), sw:p[3]==='true', "
    "on:p[4]==='true'||p[5]==='true', x:(+p[6]+ +p[8])/2, y:(+p[7]+ +p[9])/2 }; }); "
    "let sw=righe.filter(n=>n.sw); const da=sw.length?'android':'geelark'; "
    "if(!sw.length){ sw=String(tglLista||'').split(';').filter(Boolean).map(s=>{ const q=s.split(':'); "
    "return { sw:true, on:q[1]==='1', x:(Number(larghezza)||720)-70, y:Number(q[0]) }; }).filter(n=>isFinite(n.y)&&n.y>0); } "
    "const etich=(re,gy)=>{ const l=righe.filter(n=>!n.sw && (re.test(n.t)||re.test(n.d))).map(n=>n.y); "
    "if(ok(gy)) l.push(Number(gy)); return l.filter(y=>isFinite(y)&&y>0); }; "
    "const vicino=(ys,re)=>{ const da=sw.find(s=>re.test(s.t)||re.test(s.d)); if(da) return da; "
    "let best=null; for(const y of ys) for(const s of sw){ const dy=Math.abs(s.y-y); "
    "if(dy<=90 && (!best||dy<best.dy)) best=Object.assign({},s,{dy}); } return best; }; "
    "const FB=etich(/Facebook/, fbRiga); const TR=etich(/^Trial/, trialRiga); "
    "const fb=vicino(FB,/Facebook/); const tr=TR.length?vicino(TR,/^Trial/):null; const banner=ok(trialBanner); "
    "const fbOn = fb ? (fb.on?'1':'0') : '?'; const trialOn = tr ? (tr.on?'1':'0') : (banner?'1':'0'); "
    "const nf=parseInt(fbTocchi,10)||0, nt=parseInt(trialTocchi,10)||0; let azione='ok'; "
    "if(trialOn==='1' && tr && nt<2) azione='trial'; else if(fbOn==='0' && nf<2) azione='fb'; "
    "else if(fbOn==='?' || (fbOn==='0') || trialOn==='1') azione='no'; "
    "return { fbOn, fbOk: fbOn==='1'?'1':'0', trialOn, azione, fatto: (azione==='ok'||azione==='no')?'1':'0', "
    "fbX: String(Math.round(fb?fb.x:0)), fbY: String(Math.round(fb?fb.y:0)), "
    "trX: String(Math.round(tr?tr.x:0)), trY: String(Math.round(tr?tr.y:0)), "
    "fbStato: (fb?(fb.on?'acceso':'spento'):'non trovato')+' ('+da+', '+FB.length+' scritte, '+sw.length+' interruttori)', "
    "trialStato: tr?(tr.on?'acceso':'spento'):(banner?'banner trial':'non c\\'e\\''), "
    "fbTocchi: String(nf+(azione==='fb'?1:0)), trialTocchi: String(nt+(azione==='trial'?1:0)) };")

FB_FILTRI = filtri([('text', 'Facebook ·', 'contain')], [('text', 'Facebook •', 'contain')],
                   [('text', 'Facebook', 'equal')], [('text', 'Facebook', 'contain')],
                   [('desc', 'Facebook', 'contain')])
TRIAL_FILTRI = filtri([('text', 'Trial', 'equal')], [('text', 'Trial', 'contain')], [('desc', 'Trial', 'equal')])

# GeeLark: interruttori della pagina (solo se Android non li vede)
tgl = ciclo('GeeLark: gli interruttori della pagina (se Android non li vede)', 5, [
    azzera('azzera: interruttore', {'tgl': '', 'tglY': '', 'tglSel': ''}),
    nodo("c'e' l'interruttore n?", 'waitEle', {
        'excuteError': 'noProcessing', 'hiddenChildren': True, 'searchTime': 800, 'serial': '${kt}',
        'serialType': 'fixedValue', 'variable': 'tgl',
        'filterCollection': filtri([('id', 'com.instagram.android:id/toggle', 'equal')],
                                   [('class', 'android.widget.Switch', 'equal')])}),
    se("IF c'e' -> dove e acceso?", [cond('tgl', rel='exist')], [
        nodo('altezza', 'getEle', {'saveItemName': 'tgl', 'type': 'centerY', 'variable': 'tglY'}),
        nodo('acceso?', 'getEle', {'saveItemName': 'tgl', 'type': 'selected', 'variable': 'tglSel'}),
        js('annota', ['tglY', 'tglSel', 'tglLista'],
           OK + "return { tglLista: String(tglLista||'')+String(tglY)+':'+(ok(tglSel)?'1':'0')+';' };",
           ['tglLista'])])], 'kt')

controllo = ciclo('controlla Facebook (acceso) e Trial (spento), al massimo 4 volte', 4, [
    se('IF non ancora finito', [cond('fatto', '0')], [
        azzera('azzera: interruttori', {'uiOut': '', 'fbRiga': '', 'trialRiga': '', 'trialBanner': '',
                                         'tglLista': ''}),
        adb('Android: interruttori della pagina (Facebook, Trial)', UI, 'uiOut'),
        leggi('riga di Facebook', FB_FILTRI, 1500, 'fbRiga'),
        leggi('riga Trial', TRIAL_FILTRI, 800, 'trialRiga'),
        leggi("c'e' 'This is a trial reel'?", filtri([('text', 'This is a trial reel', 'contain')]), 800,
              'trialBanner'),
        js('Android vede gli interruttori?', ['uiOut'],
           "return { swAndroid: /^N\\|[^|]*\\|[^|]*\\|true/m.test(String(uiOut||'')) ? '1' : '0' };",
           ['swAndroid']),
        se('IF Android non vede gli interruttori -> GeeLark', [cond('swAndroid', '0')], [tgl]),
        js('Facebook e Trial: acceso o spento?',
           ['uiOut', 'tglLista', 'fbRiga', 'trialRiga', 'trialBanner', 'fbTocchi', 'trialTocchi', 'larghezza'],
           OK + CONTROLLA,
           ['fbOn', 'fbOk', 'trialOn', 'azione', 'fatto', 'fbX', 'fbY', 'trX', 'trY', 'fbStato', 'trialStato',
            'fbTocchi', 'trialTocchi']),
        se('IF Facebook spento -> accendilo', [cond('azione', 'fb')], [
            adb("tocca l'interruttore di Facebook", 'input tap ${fbX} ${fbY}'),
            attendi(1800, 2500),
            tocca("se chiede: 'Always share reels' (Facebook sempre acceso)",
                  filtri([('text', 'Always share reels', 'contain')], [('text', 'Always share', 'contain')],
                         [('text', 'Turn on', 'equal')]), 1500),
            attendi(1200, 1800)]),
        se('IF Trial acceso -> spegnilo', [cond('azione', 'trial')], [
            adb("tocca l'interruttore Trial", 'input tap ${trX} ${trY}'),
            attendi(1800, 2500)])])], 'kc')

controlli = [nodo('larghezza dello schermo', 'mathOperation',
                  {'operationStr': '${_SCREEN_WIDTH_} * 1', 'variable': 'larghezza'}),
             azzera('azzera: controlli', {'fatto': '0', 'fbOn': '', 'fbOk': '0', 'trialOn': '', 'azione': ''}),
             controllo,
             foto('screenshot: pagina finale in fondo (Facebook e Trial)'),
             se('IF Facebook non acceso -> errore', [cond('fbOk', '0')],
                errore("[Facebook] La condivisione su Facebook non e' accesa (o non trovo l'interruttore). "
                       "Non pubblico niente.")),
             se('IF Trial acceso -> errore', [cond('trialOn', '1')],
                errore("[Trial] L'interruttore Trial e' acceso e non riesco a spegnerlo. Non pubblico niente."))]

# ---------- 8. Share (o SoloProva) ----------
FINALE = filtri([('text', 'Save draft', 'equal')], [('text', 'Tag people', 'equal')],
                [('text', 'Add location', 'equal')], [('text', 'Audience', 'equal')],
                [('text', 'Share to', 'equal')], [('text', 'More options', 'equal')])
share_tocca = trova(TRIAL, 'tocca Share')
partita = [attendi(6000, 8000, 'aspetta che parta'),
           azzera('azzera: pubblicazione partita?', {'ancoraFin': '', 'upOut': ''}),
           leggi('sono ancora sulla pagina finale?', FINALE, 2500, 'ancoraFin'),
           adb('Android: si vede il caricamento?',
               "sh -c 'dumpsys activity top 2>/dev/null | grep -E \"[{][0-9a-f]+ V\" | "
               "grep -oE \"app:id/[a-z_]*(pending|upload|progress)[a-z_]*\" | sort -u | tr \"\\n\" \" \"; "
               "dumpsys window 2>/dev/null | grep -m 1 mCurrentFocus; echo fine'", 'upOut'),
           js('pubblicazione partita?', ['ancoraFin', 'upOut'],
              OK + "const via=!ok(ancoraFin) && /com[.]instagram[.]android/.test(String(upOut||'')); "
              "return { pubOk: via?'1':'0' };", ['pubOk'])]
share = [foto('screenshot: prima di Share'),
         azzera('azzera: Share', {'cShare': '', 'shareOk': '0'}),
         share_tocca,
         trova(TRIAL, 'Share toccato?'),
         se('IF Share non toccato -> errore', [cond('shareOk', '0')],
            errore("[Share] Non riesco a toccare 'Share'. Non pubblicato.")),
         attendi(3000, 4000),
         trova(TRIAL, 'azzera: avviso dopo Share'),
         trova(TRIAL, "avviso 'About Reels' / audio originale?"),
         js('avviso?', ['avviso'], OK + "return { avvisoOk: ok(avviso)?'1':'0' };", ['avvisoOk']),
         trova(TRIAL, 'IF avviso -> Share'),
         tocca("se chiede: 'Always share reels' (Facebook)",
               filtri([('text', 'Always share reels', 'contain')], [('text', 'Always share', 'contain')]), 1500)]
share += partita
# niente secondo Share (rischio di due reel uguali): se e' ancora sulla pagina aspetta e ricontrolla
share.append(se('IF ancora sulla pagina finale -> aspetta ancora e ricontrolla', [cond('ancoraFin', rel='exist')],
                copy.deepcopy(partita)))
share += [se("IF la pubblicazione non e' partita -> errore", [cond('pubOk', '0')],
             errore("[Share] Ho premuto Share ma sono ancora sulla pagina finale: la pubblicazione non e' "
                    "partita.")),
          foto('screenshot: pubblicazione partita'),
          js('caption: passo alla prossima? (solo se pubblicato e presa dalla lista)', ['pubOk', 'daDove'],
             "return { avanza: (String(pubOk)==='1' && String(daDove)==='dalla lista')?'1':'0', "
             "esito: 'pubblicato' };", ['avanza', 'esito']),
          se('IF si -> la prossima volta la caption dopo', [cond('avanza', '1')], [
              adb('ricorda la prossima caption', "sh -c 'echo ${reelProssima} > /sdcard/.wu_reel_n; echo ok'",
                  'capOut')]),
          attendi(15000, 25000, 'lascia caricare')]

finale = [se('IF SoloProva -> non pubblico (ELSE: Share)', [cond('prova', '1')], [
    foto('SOLO PROVA: tutto pronto, non premo Share'),
    azzera('esito: prova', {'esito': 'SOLO PROVA, non pubblicato'}),
    adb('chiudi Instagram senza pubblicare', CHIUDI_IG, 'stopIg')] + apri_instagram(), share)]

# ---------- 9. warm-up dopo (3 minuti; SoloProva 1 minuto) e chiude ----------
dopo_like = trova(PROVA, 'IF like -> cuore o doppio tocco')
dopo_like['config']['conditionList'] = [cond('metti2', '1')]
for n in figli(dopo_like):
    if n['name'] == 'like fatti +1':
        n.update(js('like dopo +1 (il prossimo tra 7-8 reel)', ['likeDopo', 'jReel'],
                    R + "return { likeDopo: String((parseInt(likeDopo,10)||0)+1), "
                    "nextLike2: String((parseInt(jReel,10)||1)+r(7,8)) };", ['likeDopo', 'nextLike2']))
dopo = tocca_reels() + [
    js('warm-up dopo: 3 minuti (SoloProva 1)', ['prova'],
       R + "const d=String(prova)==='1' ? r(50,70)*1000 : r(170,200)*1000; "
       "return { fineDopo: String(Date.now()+d), maxDopo: String(Math.round(d/8000)), ancoraD: '1', "
       "nextLike2: String(r(5,8)) };", ['fineDopo', 'maxDopo', 'ancoraD', 'nextLike2']),
    ciclo('warm-up dopo nei reels', 40, [
        se('IF warm-up dopo non finito', [cond('ancoraD', '1')], [
            copy.deepcopy(NOT_NOW),
            trova(PROVA, 'IF 25%: guarda poco'),
            js('like a questo reel? e come scorro', ['jReel', 'nextLike2', 'fineDopo', 'tOk', 'maxDopo'],
               R + SCORRI + " const j=parseInt(jReel,10)||1; const t=String(tOk)==='1' ? Date.now()<Number(fineDopo) "
               ": j<(parseInt(maxDopo,10)||20); return { metti2: j>=(parseInt(nextLike2,10)||8)?'1':'0', "
               "dtX: String(r(300,420)), dtY: String(r(520,760)), sx1, sy1, sx2, sy2, sd, ancoraD: t?'1':'0', "
               "nDopo: String(j) };",
               ['metti2', 'dtX', 'dtY', 'sx1', 'sy1', 'sx2', 'sy2', 'sd', 'ancoraD', 'nDopo']),
            dopo_like,
            adb('scorri al reel dopo (140-190 ms)', 'input swipe ${sx1} ${sy1} ${sx2} ${sy2} ${sd}', 'swOut'),
            attendi(300, 700)])], 'jReel')]

RIEP_VAR = ['esito', 'prova', 'minutiWU', 'likeHome', 'nReel', 'likeFatti', 'repostFatti', 'salvaFatti',
            'cercaN', 'ciechi', 'editsChiusi', 'playStore', 'diario', 'reelScelto', 'perche', 'usaOk', 'comeUsa',
            'galOk', 'comeGal', 'primo', 'videoScelto', 'comeVideo', 'editorOk', 'finaleOk', 'capOk', 'daDove',
            'lingua', 'linguaPerche', 'capFinale', 'fbStato', 'fbTocchi', 'trialStato', 'trialTocchi', 'pubOk',
            'nDopo', 'likeDopo']
fine = [foto('screenshot: fine', True),
        js('riepilogo', RIEP_VAR,
           "const s=v => v==null ? '' : String(v); const c=v => s(v) ? ' (' + s(v) + ')' : ''; "
           "return { riepilogo: s(esito) + ' | warm-up ' + s(minutiWU) + ' min: like home ' + s(likeHome) + "
           "', reel guardati ' + s(nReel) + ', like ' + s(likeFatti) + ', repost ' + s(repostFatti) + "
           "', salvati ' + s(salvaFatti) + ' | canzone: reel guardati cercando ' + s(cercaN) + ', ' + s(diario) + "
           "'scelto il reel ' + (s(reelScelto)||'nessuno') + c(perche) + ' | GeeLark cieco ' + s(ciechi) + "
           "' volte, pannelli Edits chiusi ' + s(editsChiusi) + ', Play Store ' + s(playStore) + "
           "' | Use audio ' + s(usaOk) + c(comeUsa) + ' | galleria ' + s(galOk) + c(comeGal) + "
           "' | video del task primo ' + s(primo) + ', toccato ' + s(videoScelto) + c(comeVideo) + "
           "' | editor ' + s(editorOk) + ' | pagina finale ' + s(finaleOk) + ' | caption ' + s(capOk) + "
           "' (' + s(daDove) + ', ' + s(lingua) + ' ' + s(linguaPerche) + '): ' + s(capFinale) + "
           "' | Facebook ' + s(fbStato) + ', tocchi ' + s(fbTocchi) + ' | Trial ' + s(trialStato) + "
           "', tocchi ' + s(trialTocchi) + ' | pubblicazione partita ' + s(pubOk) + "
           "' | warm-up dopo: reel ' + s(nDopo) + ', like ' + s(likeDopo) }; ",
           ['riepilogo']),
        adb('chiudi Instagram', CHIUDI_IG, 'stopIg'),
        adb('HOME', 'input keyevent 3', 'homeOut'),
        nodo('End task', 'endTask', {})]

contenuti = inizio + giro + prepara + cap + fondo + controlli + finale + dopo + fine

# ---------- id nuovi, posizioni, parametri ----------
conta = [0]


def sistema(nodi):
    for n in nodi:
        for _, v in sotto(n):
            sistema(v)
        conta[0] += 1
        n['id'] = str(uuid.uuid4())
        n['position'] = {'x': 333 + 200 * conta[0], 'y': 285}


sistema(contenuti)

params = copy.deepcopy(PROVA['content']['startParamMap'])
solo = copy.deepcopy([p for p in TRIAL['content']['startParamMap'] if p['key'] == 'SoloProva'][0])
params.append(solo)
for p in params:
    p['id'] = str(uuid.uuid4())

flusso = {
    'title': TITOLO,
    'desc': ("Reel con la canzone di un reel virale. Warm-up di 13-15 minuti (home, poi reels scorsi veloci "
             "140-190 ms: like ogni 7-8 reel, 1 repost, 1-2 salvati), poi nei Reels cerca una canzone Trending "
             "(o in almeno 1.000 reel) su un reel con almeno 2K like -> 'Use audio' -> il video del task -> "
             "caption (del task o dalla lista di CommentBot) -> Facebook acceso, Trial spento -> Share e "
             "controlla che sia partita -> warm-up di 3 minuti -> chiude Instagram. Se qualcosa va storto prima "
             "di Share si ferma con errore e screenshot. SoloProva: fa tutto ma non preme Share."),
    'content': {
        'startParamMap': params,
        'contents': contenuti,
        'otherContents': copy.deepcopy(PROVA['content']['otherContents']),
        'contentType': 'phone',
        'errorType': 'skip'}}

testo = json.dumps(flusso, ensure_ascii=False, separators=(',', ':'))
byte = len(testo.encode('utf-8'))


def passi(nodi):
    return sum(1 + sum(passi(v) for _, v in sotto(n)) for n in nodi)


np_ = passi(contenuti)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(testo)
print('%s: %d byte, %d passi' % (os.path.basename(OUT), byte, np_))
if byte > MAX_BYTE or np_ > MAX_PASSI:
    print('ATTENZIONE: troppo grande, GeeLark potrebbe non farlo partire (limite %d byte, %d passi)'
          % (MAX_BYTE, MAX_PASSI))
    sys.exit(1)
