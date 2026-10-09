# Genera IG_REEL_VIRALE_IMPORT.json (il flusso vero) partendo dalla prova v4.
# Uso: python3 genera_flusso.py   (dalla cartella instagram_reel_virale)
# Prende dei pezzi gia' provati da:
#   - IG_REEL_VIRALE_PROVA_IMPORT.json (canzone, Use audio, galleria, editor, pagina finale, liste caption)
#   - ../instagram_trial/IG_TRIAL_REEL_IMPORT.json (SoloProva, scorri fino a 'Share to', Share)
#   - ../instagram_warmup/IG_WARMUP_IMPORT.json (repost, salva, like nella home)
import copy, json, os, re, sys, uuid

QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, 'IG_REEL_VIRALE_IMPORT.json')
TITOLO = 'IG REEL VIRALE v2'
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
    'salviChiusi': '0', 'pubOk': '0', 'esito': '',
    'likeDopo': '0', 'nReel': '0', 'nDopo': '0', 'videoOk': '0'}.items()) + ' };',
    ['ciechi', 'fermo', 'diario', 'scelto', 'reelScelto', 'perche', 'likeNum', 'quantiReel', 'usaOk',
     'galOk', 'comeGal', 'primo', 'videoScelto', 'editorOk', 'finaleOk', 'capOk', 'capFinale', 'daDove',
     'usaPos', 'comeUsa', 'comeVideo', 'galVista', 'editsChiusi', 'playStore', 'trending', 'inPlay',
     'likeFatti', 'likeHome', 'repostFatti', 'salvaFatti', 'cercaN', 'salviChiusi',
     'pubOk', 'esito', 'likeDopo', 'nReel', 'nDopo', 'videoOk']))

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

# piano del warm-up: 13-15 minuti (SoloProva 2,5-3) in pezzi in ordine a caso (storie di altri, home, reels);
# le storie sempre prima della home (servono la home in cima); l'ultimo pezzo e' sempre nei Reels e alla fine
# cerca la canzone
inizio += [nodo('larghezza dello schermo', 'mathOperation',
                {'operationStr': '${_SCREEN_WIDTH_} * 1', 'variable': 'larghezza'}),
           trova(WARM, 'misure dello schermo'), trova(WARM, 'posizioni sullo schermo')]
inizio.append(js('piano del warm-up (13-15 minuti, pezzi in ordine a caso)', ['prova'],
                 R + "const now=Date.now(); const tOk=(isFinite(now) && now>1.6e12)?'1':'0'; "
                 "const pr=String(prova)==='1'; const wu=pr ? r(150,180)*1000 : r(780,900)*1000; "
                 "const mischia=a=>{ for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); "
                 "const t=a[i]; a[i]=a[j]; a[j]=t; } return a; }; "
                 "let L=['home','reels']; if(Math.random()<0.8) L.push('storie'); if(!pr && Math.random()<0.4) L.push('reels'); "
                 "L=mischia(L); if(L.indexOf('storie')>=0 && L.indexOf('home')<L.indexOf('storie')){ "
                 "L=L.filter(x=>x!=='home'); L.splice(L.indexOf('storie')+1,0,'home'); } "
                 "L=L.filter((x,i)=>i===0||x!==L[i-1]); if(L[L.length-1]!=='reels') L.push('reels'); "
                 "const k=pr?0.25:1; const dur={storie:r(60,150)*1000*k, home:r(90,180)*1000*k}; "
                 "return { tOk, tInizio: String(now), fineWU: String(now+wu), minutiWU: (wu/60000).toFixed(1), "
                 "ordine: L.join(','), durStorie: String(dur.storie), durHome: String(dur.home), "
                 "nextLike: String(r(7,8)), nTot: '0', repostTot: '1', salvaTot: String(r(1,2)), "
                 "likeHomeTot: String(r(0,2)), tentativi: '0', fuori: '0', dove: '' };",
                 ['tOk', 'tInizio', 'fineWU', 'minutiWU', 'ordine', 'durStorie', 'durHome', 'nextLike', 'nTot',
                  'repostTot', 'salvaTot', 'likeHomeTot', 'tentativi', 'fuori', 'dove']))

# ---------- 3. home (scorre solo in giu', 0-2 like in tutto) ----------
like_home = trova(WARM, "metti like al post (cuore 'Like')")
home = ciclo('home: scorri (solo verso il basso)', 40, [
    se('IF home non finita', [cond('ancoraH', '1')], [
        copy.deepcopy(NOT_NOW),
        attendi(2000, 7000, 'guarda il post'),
        js('home: like a questo post? e come scorro', ['likeHome', 'likeHomeTot'],
           R + "const l=(parseInt(likeHome,10)||0)<(parseInt(likeHomeTot,10)||0) && Math.random()<0.15; "
           "const x=r(320,400); return { hLike: l?'1':'0', hx1: String(x), hy1: String(r(950,1050)), "
           "hx2: String(x+r(-20,20)), hy2: String(r(380,480)), hd: String(r(250,450)) };",
           ['hLike', 'hx1', 'hy1', 'hx2', 'hy2', 'hd']),
        se('IF like a questo post', [cond('hLike', '1')], [
            azzera('azzera: like', {'cLike': ''}),
            like_home,
            js('like messo?', ['cLike', 'likeHome'],
               OK + "return { likeHome: String((parseInt(likeHome,10)||0)+(ok(cLike)?1:0)) };", ['likeHome']),
            attendi(800, 1500)]),
        adb('scorri la home', 'input swipe ${hx1} ${hy1} ${hx2} ${hy2} ${hd}', 'swOut'),
        js('home: ancora?', ['fineModulo', 'tOk', 'kh', 'maxK'],
           "const n=parseInt(kh,10)||0; const t=String(tOk)==='1' ? Date.now()<Number(fineModulo) : "
           "n<(parseInt(maxK,10)||20); return { ancoraH: t?'1':'0' };", ['ancoraH'])])], 'kh')

# ---------- 4. reels: warm-up (like ogni 7-8, 1 repost, 1-2 salvati) e, nell'ultimo pezzo, la canzone ----------
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
    ['iReel', 'nTot', 'suReels', 'nextLike', 'fineModulo', 'fineWU', 'ultimo', 'tOk', 'maxK', 'repostFatti',
     'repostTot', 'salvaFatti', 'salvaTot', 'cercaN'],
    R + "const i=parseInt(iReel,10)||1; const n=(parseInt(nTot,10)||0)+1; const su=String(suReels)==='1'; "
    "const now=Date.now(); const ok=String(tOk)==='1'; const fm=Number(fineModulo); "
    "const tempoSu = ok ? now>=fm : i>(parseInt(maxK,10)||40); const ult=String(ultimo)==='1'; "
    "const cn=parseInt(cercaN,10)||0; const cerca = ult && tempoSu && cn<50; "
    "const finito = tempoSu && (!ult || cn>=50); const metti = su && n>=(parseInt(nextLike,10)||8); "
    "let est = ok ? (Number(fineWU)-now)/9000 : 30; est=Math.max(1,est); "
    "const p=(t,f)=>{ const x=(parseInt(t,10)||0)-(parseInt(f,10)||0); return x<=0?0:Math.min(1,x/est); }; "
    "const rep = su && !tempoSu && i>=3 && Math.random()<p(repostTot,repostFatti); "
    "const sal = su && !tempoSu && i>=2 && !rep && Math.random()<p(salvaTot,salvaFatti); "
    "return { metti: metti?'1':'0', fRep: rep?'1':'0', fSal: sal?'1':'0', cerca: cerca?'1':'0', "
    "cercaN: String(cn+(cerca?1:0)), finito: finito?'1':'0', nTot: String(n), nReel: String(n), "
    "dtX: String(r(300,420)), dtY: String(r(520,760)) };",
    ['metti', 'fRep', 'fSal', 'cerca', 'cercaN', 'finito', 'nTot', 'nReel', 'dtX', 'dtY']))

like_blocco = trova(PROVA, 'IF like -> cuore o doppio tocco')
for n in figli(like_blocco):
    if n['name'] == 'like fatti +1':
        n.update(js('like fatti +1 (il prossimo tra 7-8 reel)', ['likeFatti', 'nTot'],
                    R + "return { likeFatti: String((parseInt(likeFatti,10)||0)+1), "
                    "nextLike: String((parseInt(nTot,10)||1)+r(7,8)) };", ['likeFatti', 'nextLike']))
reels_figli.append(like_blocco)
reels_figli.append(trova(WARM, 'IF repost'))

# salva; poi chiude il pannello 'Saved / Collect the posts you love' (esce le prime volte):
# tocca sopra il pannello (la parte scura in alto), se c'e' ancora 'indietro'
SALVATI = filtri([('text', 'Collect the posts you love', 'contain')], [('text', 'Start a collection', 'equal')],
                 [('text', 'Save posts in collections', 'contain')], [('text', 'Saved', 'equal')])
FOGLIO = ("sh -c 'dumpsys activity top 2>/dev/null | grep -E \"[{][0-9a-f]+ V\" | "
          "grep -cE \"app:id/(bottom_sheet_compose_view|bottom_sheet_container|layout_container_bottom_sheet)\"'")


def chiudi_salvati(quando):
    return [azzera('azzera: pannello Saved? (%s)' % quando, {'salY': '', 'foglioOut': ''}),
            leggi("c'e' il pannello 'Saved / Start a collection'? (%s)" % quando, SALVATI, 1200, 'salY'),
            adb("Android: c'e' un pannello aperto? (%s)" % quando, FOGLIO, 'foglioOut'),
            js('chiudo il pannello Saved? (%s)' % quando, ['salY', 'foglioOut', 'salviChiusi'],
               OK + "const si=ok(salY) || (parseInt(String(foglioOut||'').trim(),10)||0)>0; "
               "return { chiudiSal: si?'1':'0', vistoSal: ok(salY)?'1':'0', "
               "salviChiusi: String((parseInt(salviChiusi,10)||0)+(si?1:0)) };",
               ['chiudiSal', 'vistoSal', 'salviChiusi'])]


salva = trova(WARM, 'IF salva')
salva['config']['children'] += [attendi(1200, 1800)] + chiudi_salvati('dopo il salva') + [
    se('IF pannello Saved -> tocca sopra il pannello', [cond('chiudiSal', '1')], [
        adb('tocca sopra il pannello (in alto, si abbassa)', 'sh -c \'input tap $(( 300 + RANDOM % 120 )) $(( 170 + RANDOM % 90 ))\''),
        attendi(1200, 1800)] + chiudi_salvati('dopo il tocco') + [
        se("IF GeeLark lo vede ancora -> indietro", [cond('vistoSal', '1')], [
            adb('indietro (chiudi il pannello Saved)', 'input keyevent 4', 'backOut'),
            attendi(1200, 1800)])])]
reels_figli.append(salva)

# la parte della canzone (solo nell'ultimo pezzo, quando il tempo del warm-up e' finito)
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
            s = s.replace("const i=parseInt(iReel,10)||1;", "const i=parseInt(nTot,10)||1;")
            s = s.replace("likeNum, iReel, diario", "likeNum, nTot, diario")
            n['config']['script'] = s
            n['config']['injectVariables'] = [('nTot' if v == 'iReel' else v)
                                              for v in n['config']['injectVariables'] if v != 'facile']
            assert 'facile' not in s and 'parseInt(iReel' not in s, s
        elif n['type'] == 'script' and 'iReel' in n['config'].get('injectVariables', []):
            n['config']['script'] = re.sub(r'\biReel\b', 'nTot', n['config']['script'])
            n['config']['injectVariables'] = [('nTot' if v == 'iReel' else v)
                                              for v in n['config']['injectVariables']]
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

reels = ciclo('reels: guarda e scorri (nell\'ultimo pezzo poi cerca la canzone)', 250, [
    se('IF canzone non ancora scelta (e pezzo non finito)', [cond('scelto', '0'), cond('finito', '0')],
       reels_figli)], 'iReel')

# ---------- il giro: pezzi in ordine a caso ----------
prossimo = js('prossimo pezzo del giro', ['ordine', 'im', 'fineWU', 'durStorie', 'durHome', 'tOk'],
              "const L=String(ordine||'').split(',').filter(Boolean); const i=(parseInt(im,10)||1)-1; "
              "const now=Date.now(); const fine=Number(fineWU); const mod = i<L.length ? L[i] : ''; "
              "const ult = mod!=='' && i===L.length-1; const dopo=L.slice(i+1); "
              "const riserva = dopo.reduce((s,x)=>s+(x==='storie'?Number(durStorie):x==='home'?Number(durHome):90000),0); "
              "let fm=now, maxK=10; if(mod==='storie'){ fm=now+Number(durStorie); maxK=15; } "
              "else if(mod==='home'){ fm=now+Number(durHome); maxK=25; } "
              "else if(mod==='reels'){ fm = ult ? fine : now+Math.max(60000,(fine-now-riserva)*(0.35+Math.random()*0.3)); maxK=ult?90:40; } "
              "return { modulo: mod, ultimo: ult?'1':'0', fineModulo: String(Math.round(fm)), maxK: String(maxK), "
              "ancoraH: '1', finito: '0' };",
              ['modulo', 'ultimo', 'fineModulo', 'maxK', 'ancoraH', 'finito'])
giro = ciclo('il giro di warm-up (pezzi in ordine a caso)', 5, [
    azzera('azzera: pezzo', {'modulo': ''}),
    prossimo,
    trova(WARM, "IF c'e' un modulo -> controlla la barra e Instagram"),
    trova(WARM, 'IF storie, home o notifiche -> vai alla home'),
    trova(WARM, 'IF reels -> vai ai Reels'),
    trova(WARM, 'IF modulo = storie di altri'),
    se('IF pezzo = home', [cond('modulo', 'home')], [home]),
    se('IF pezzo = reels', [cond('modulo', 'reels')], [reels])], 'im')

giro = [giro,
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

# ---------- 7. scorre fino in fondo e Share: Facebook NON si tocca (e' gia' acceso) ----------
fondo = [trova(TRIAL, 'azzera: fondo della pagina'),
         trova(TRIAL, "scorri giu' fino a 'Share to' (al massimo 5 volte)")]
# se per sbaglio esce 'Stop sharing on Facebook?' -> 'Cancel' (mai 'Don't share' o 'Stop sharing')
controlli = [azzera('azzera: avviso Facebook', {'stopFb': ''}),
             leggi("e' uscito 'Stop sharing on Facebook?'", filtri([('text', 'Stop sharing on Facebook', 'contain')]),
                   1000, 'stopFb'),
             se("IF si' -> 'Cancel' (Facebook resta acceso)", [cond('stopFb', rel='exist')], [
                 tocca("tocca 'Cancel'", filtri([('text', 'Cancel', 'equal')]), 2000),
                 attendi(1000, 1500)])]

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
            'lingua', 'linguaPerche', 'capFinale', 'salviChiusi', 'ordine', 'pubOk',
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
           "' | pannelli Saved chiusi ' + s(salviChiusi) + ' | ordine del giro ' + s(ordine) + ' | pubblicazione partita ' + s(pubOk) + "
           "' | warm-up dopo: reel ' + s(nDopo) + ', like ' + s(likeDopo) }; ",
           ['riepilogo']),
        adb('chiudi Instagram', CHIUDI_IG, 'stopIg'),
        adb('HOME', 'input keyevent 3', 'homeOut'),
        nodo('End task', 'endTask', {})]

contenuti = inizio + giro + prepara + cap + fondo + controlli + finale + dopo + fine

# ---------- id nuovi, posizioni, parametri ----------
def togli_spie(nodi):
    # la v1 e' andata bene: tolgo le 'spie' (servivano a capire le schermate), restano gli screenshot
    for n in nodi:
        for k, v in sotto(n):
            n['config'][k] = togli_spie(v)
    return [n for n in nodi if not n['name'].startswith('spia')]


contenuti = togli_spie(contenuti)
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
    'desc': ("Reel con la canzone di un reel virale. Warm-up di 13-15 minuti a pezzi in ordine a caso (storie di "
             "altri, home, reels scorsi veloci 140-190 ms: like ogni 7-8 reel, 1 repost, 1-2 salvati, chiude il pannello "
             "'Saved'), poi nei Reels cerca una canzone Trending (o in almeno 1.000 reel) -> 'Use audio' -> il video del "
             "task -> caption -> scorre in fondo e Share (Facebook non si tocca) -> controlla che sia partita -> warm-up "
             "di 3 minuti -> chiude Instagram. Errori prima di Share: si ferma con screenshot. SoloProva: niente Share."),
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
