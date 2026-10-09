# Costruisce "IG STORIA LINK" partendo dal warm-up (instagram_warmup/IG_WARMUP_IMPORT.json):
# warm-up prima -> storia (foto del task, sticker del link, musica da For you) -> warm-up dopo.
# Si rigenera con:  python3 instagram_storia_link/genera_storia_link.py
import json, os, re, uuid

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(QUI, '..', 'instagram_warmup', 'IG_WARMUP_IMPORT.json')
OUT = os.path.join(QUI, 'IG_STORIA_LINK_IMPORT.json')
MAX_BYTE, MAX_PASSI = 240000, 520

d = json.load(open(BASE, encoding='utf-8'))
top = d['content']['contents']


def nid():
    return str(uuid.uuid4())


def P(x=0):
    return {'x': x, 'y': 285}


def figli(n):
    c = n['config']
    out = list(c.get('children', []) or [])
    if isinstance(c.get('other'), list):
        out += c['other']
    return out


def tutti(lista):
    for n in lista:
        yield n
        yield from tutti(figli(n))


def trova(lista, nome):
    r = [n for n in tutti(lista) if n.get('name') == nome]
    assert r, nome
    return r[0]


def js(nome, vars_in, corpo, outs):
    args = '{ ' + ', '.join(vars_in) + ' }' if vars_in else ''
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'script',
            'config': {'injectVariables': list(vars_in),
                       'script': 'async function main(%s) { %s }' % (args, corpo),
                       'type': 'js', 'variableMap': [{'value': o, 'variable': o} for o in outs]}}


def azzera(nome, valori):
    corpo = 'return { ' + ', '.join('%s: %s' % (k, json.dumps(v)) for k, v in valori.items()) + ' };'
    return js(nome, [], corpo, list(valori))


OK = "const ok=v=>!(v==null||v===false||/^(|0|false|undefined|null)$/i.test(String(v).trim()));"


def esito(nome, var_in, var_out):
    return js(nome, [var_in], OK + " return { %s: ok(%s) ? '1' : '0' };" % (var_out, var_in), [var_out])


def adb(nome, cmd, var='adbOut'):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'executeADB',
            'config': {'content': cmd, 'timeout': 120000, 'variable': var, 'error': False}}


def attendi(a, b, nome='wait'):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'waitTime',
            'config': {'timeoutMax': b, 'timeoutMin': a, 'timeoutType': 'randomInterval'}}


def filtri(lista):
    # lista di (tipo, contenuto, 'equal'|'contain')
    return [[{'content': c, 'filterType': f, 'type': t}] for t, c, f in lista]


def tocca(nome, lista, var, cerca=2500):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'click',
            'config': {'filterCollection': filtri(lista), 'hiddenChildren': False, 'randomDistance': 0,
                       'searchTime': cerca, 'useOffset': False, 'serialType': 'fixedValue', 'serial': 1,
                       'excuteError': 'noProcessing', 'variable': var}}


def leggi(nome, lista, var, cerca=2500):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'getEle',
            'config': {'filterCollection': filtri(lista), 'serialType': 'fixedValue', 'serial': 1,
                       'hiddenChildren': False, 'searchTime': cerca, 'type': 'centerY',
                       'variable': var, 'error': False}}


def toccaXY(nome, x, y):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'clickXY',
            'config': {'excuteError': 'noProcessing', 'randomDistance': 0, 'x': x, 'y': y}}


def scrivi(nome, testo, serial, var):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'inputContent',
            'config': {'content': [testo], 'filterType': 'contain',
                       'filters': [{'content': 'EditText', 'type': 'class'}], 'hiddenChildren': True,
                       'inputType': 'taskOrder', 'searchTime': 3000, 'serial': serial,
                       'serialType': 'fixedValue', 'variable': var}}


def foto(nome):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'screenshotPage',
            'config': {'error': False, 'isBase64': False, 'isScope': False}}


def se(nome, conds, figli_, altrimenti=None, modo='and'):
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'ifElse',
            'config': {'apposition': modo, 'children': figli_,
                       'conditionList': [{'probability': 50, 'relation': 'equal', 'useVariable': v, 'result': r}
                                         for v, r in conds],
                       'other': altrimenti or []}}


def ciclo(nome, n, figli_, indice=None):
    c = {'serialType': 'randomInterval', 'minTimes': n, 'maxTimes': n, 'hiddenChildren': False, 'children': figli_}
    if indice:
        c['variableIndex'] = indice
    return {'position': P(), 'id': nid(), 'name': nome, 'type': 'forTimes', 'config': c}


def errore(msg):
    # niente throwException: nel test del 09/10 GeeLark restava "in esecuzione" dopo l'eccezione
    return [js('errore: ' + msg[:60], [], 'return { errore: %s };' % json.dumps(msg, ensure_ascii=False), ['errore']),
            {'position': P(), 'id': nid(), 'name': 'End task (dopo l\'errore)', 'type': 'endTask', 'config': {}}]


def togli(lista, nome, primo=True):
    for i, n in enumerate(lista):
        if n.get('name') == nome:
            del lista[i]
            return True
        for k in ('children', 'other'):
            if isinstance(n['config'].get(k), list) and togli(n['config'][k], nome, False):
                return True
    assert not primo, nome
    return False


def indice(nome):
    for i, n in enumerate(top):
        if n.get('name') == nome:
            return i
    raise AssertionError(nome)


# ---------------------------------------------------------------- titolo e parametri
d['title'] = 'IG STORIA LINK v2'
d['desc'] = ("Storia con il link. Warm-up prima (MinutiPrima, vuoto = 8-12 minuti: storie, home, notifiche, "
             "reels a 140-190 ms con like/salvati/repost, ordine a caso), poi la storia: foto del task (Storia), "
             "sticker -> LINK -> URL = Link del task -> 'Customize sticker text' = Testo del task o una caption "
             "della lista (mai ripetuta) -> Done -> trascina il link in basso -> musica a caso da For you -> "
             "'Your stories'. Poi warm-up dopo (MinutiDopo, vuoto = 3-5 minuti). Senza link o se lo sticker "
             "del link non riesce, la storia non viene pubblicata e il task finisce con l'errore e lo screenshot.")
vecchi = {p['key']: p for p in d['content']['startParamMap']}
storia = dict(vecchi['Storia'], isNotRequired=False)
d['content']['startParamMap'] = [
    {'contentable': True, 'createFrom': '', 'id': nid(), 'isNotRequired': False, 'key': 'Link', 'length': 500,
     'type': 'string', 'value': ''},
    storia,
    {'contentable': True, 'createFrom': '', 'id': nid(), 'isNotRequired': True, 'key': 'Testo', 'length': 100,
     'type': 'string', 'value': ''},
    {'contentable': True, 'createFrom': '', 'id': nid(), 'isNotRequired': True, 'key': 'MinutiPrima', 'length': 3,
     'type': 'string', 'value': ''},
    {'contentable': True, 'createFrom': '', 'id': nid(), 'isNotRequired': True, 'key': 'MinutiDopo', 'length': 3,
     'type': 'string', 'value': ''},
    vecchi['Lingua'],
]

# ---------------------------------------------------------------- niente nota, niente DM
togli(top, "quando e' stata fatta l'ultima nota?")
togli(top, 'tocca fare la nota?')
togli(top, 'IF nota dovuta -> nota')
togli(top, 'IF modulo = DM (solo guardati)')
i = indice('azzera: inizio')
top.insert(i + 1, js("c'e' il link? (nota mai)", ['Link'],
                     "const s=String(Link===undefined||Link===null?'':Link).trim(); "
                     "return { notaDovuta: '0', linkPronto: (s && !/\\s/.test(s)) ? '1' : '0' };",
                     ['notaDovuta', 'linkPronto']))
top.insert(i + 2, se('IF manca il link -> errore (non faccio niente)', [('linkPronto', '0')],
                     errore("[Link] Nel task manca il link (campo Link vuoto o con spazi): non faccio niente.")))

# ---------------------------------------------------------------- posizioni (sticker)
pos = trova(top, 'posizioni sullo schermo')['config']
pos['script'] = pos['script'].replace("frY: R(h*0.899) };",
                                      "frY: R(h*0.899), stkX: R(w*0.921), stkY: R(w*0.194), "
                                      "cenX: R(w*0.5), cenY: R(h*0.468) };")
assert 'stkX' in pos['script']
pos['variableMap'] += [{'value': v, 'variable': v} for v in ('stkX', 'stkY', 'cenX', 'cenY')]

# ---------------------------------------------------------------- piano per fase
piano = trova(top, 'piano del giro (ordine a caso, durata, numeri)')
pc = piano['config']
vecchio = pc['script']
inizio = vecchio.index('const r=(a,b)')
pc['injectVariables'] = ['MinutiPrima', 'MinutiDopo', 'fase']
pc['script'] = (
    "async function main({ MinutiPrima, MinutiDopo, fase }) { const now=Date.now(); "
    "const tok=typeof now==='number' && isFinite(now) && now>0; "
    "const r=(a,b)=>a+Math.floor(Math.random()*(b-a+1)); const dopo=String(fase)==='2'; "
    "const M=dopo ? MinutiDopo : MinutiPrima; "
    "let m=parseInt(String(M===undefined||M===null?'':M).replace(/[^0-9]/g,''),10); "
    "const T = (m>=1 && m<=90) ? m*60000 : (dopo ? r(180,300) : r(480,720))*1000; m=Math.round(T/60000); "
    "const mischia=a=>{ for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); "
    "const t=a[i]; a[i]=a[j]; a[j]=t; } return a; }; "
    "let L = dopo ? mischia(['home','reels']) : mischia(['storie','home','notifiche','reels','reels']); "
    "if(L.indexOf('storie')>=0 && L.indexOf('home') < L.indexOf('storie')){ L=L.filter(x => x!=='home'); "
    "L.splice(L.indexOf('storie')+1, 0, 'home'); } "
    "return { tOk: tok?'1':'0', tFine: String(now+T), durataMin: String(m), ordine: L.join(','), "
    "durStorie: String(r(60,150)*1000), durHome: String((dopo ? r(50,90) : r(90,180))*1000), "
    "likeTot: String(dopo ? r(0,2) : r(1,6)), commTot: String(dopo ? 0 : r(0,4)), profTot: String(dopo ? 0 : r(0,3)), "
    "salvaTot: String(dopo ? r(0,1) : r(1,2)), repostTot: String(dopo ? 0 : r(0,1)), likeHomeTot: String(r(0,1)), "
    "likeFatti:'0', commFatti:'0', profFatti:'0', salvaFatti:'0', repostFatti:'0', likeHomeFatti:'0', reelFeedFatti:'0' }; }")
assert 'r(1,6)' in pc['script'] and inizio > 0

# ---------------------------------------------------------------- sticker del link (prima della musica)
blocco = trova(top, "IF c'e' il file della storia -> storia")
bc = blocco['config']['children']
j = [k for k, n in enumerate(bc) if n.get('name') == 'scegli la caption (lista, mai ripetuta)'][0]
bc.insert(j + 1, js('testo dello sticker (Testo del task o caption della lista)', ['Testo', 'captionStoria'],
                    "const t=String(Testo===undefined||Testo===null?'':Testo).trim(); "
                    "return { testoSticker: t || String(captionStoria||''), testoDaTask: t ? '1' : '0' };",
                    ['testoSticker', 'testoDaTask']))

# ---------------------------------------------------------------- galleria della storia: terza via (fotocamera)
# Test 09/10: dopo il '+' su 'Your story' non si apriva 'Add to story' (si apriva altro a tutto schermo,
# forse la fotocamera o la storia gia' pubblicata). Terza via: home -> swipe dal bordo sinistro verso destra -> fotocamera ->
# quadratino della galleria in basso a sinistra. La spia scrive nel log cosa c'e' sullo schermo.
GAL = [('text', 'Add to story', 'equal'), ('text', 'Recents', 'equal'), ('text', 'Recent', 'equal'),
       ('text', 'Gallery', 'equal')]
for n in tutti(bc):
    if n.get('name') == "si e' aperta 'Add to story'?":
        n['config']['filterCollection'] = filtri(GAL)
spia_cmd = trova(top, 'spia: bottoni sullo schermo (storia non pubblicata)')['config']['content']
SPIA_TESTI = ("sh -c 'uiautomator dump /sdcard/spia.xml >/dev/null 2>&1; "
              "grep -oE \"(text|content-desc|resource-id)=.[^\\\"]+\" /sdcard/spia.xml | "
              "sed -E \"s/com.instagram.android:id.//\" | tr \"\\n\" \" \" | cut -c1-2500; echo; echo fine'")
prima = trova(bc, "IF non si e' aperta -> indietro e tocca 'Your story'")['config']['children']
prima[0:0] = [
    adb("spia: testi sullo schermo dopo il '+'", SPIA_TESTI, 'testiPiu'),
    adb("spia: bottoni sullo schermo dopo il '+'", trova(top, 'spia: bottoni sullo schermo (storia non pubblicata)')['config']['content'], 'bottoniPiu'),
    js("spia dopo il '+' (cosa c'e' sullo schermo)", ['testiPiu', 'bottoniPiu'], "return { spiaPiu: '1' };", ['spiaPiu']),
]
ancora = trova(bc, 'IF ancora no -> niente storia')
fine_gal = ancora['config']['children']
ancora['config']['children'] = [
    adb("spia: cosa c'e' sullo schermo (galleria non aperta)", spia_cmd, 'spiaGal'),
    adb("spia: testi sullo schermo (galleria non aperta)", SPIA_TESTI, 'testiGal'),
    js("spia (galleria non aperta)", ['spiaGal', 'testiGal'], "return { spiaGalVista: '1' };", ['spiaGalVista']),
    foto("screenshot: dopo 'Your story' niente galleria"),
    adb('indietro', 'input keyevent 4', 'backOut'),
    attendi(1500, 2000),
    tocca('vai sulla home', [('id', 'com.instagram.android:id/feed_tab', 'equal')], 'cHome', 2000),
    attendi(1500, 2500),
    js('swipe verso la fotocamera (posizioni)', ['larghezza', 'alto'],
       "const w=Number(larghezza)||720, h=Number(alto)||w*2; const R=x=>String(Math.round(x)); "
       "return { sx1: R(w*(0.03+Math.random()*0.03)), sx2: R(w*(0.80+Math.random()*0.12)), "
       "sy: R(h*(0.45+Math.random()*0.10)), durSw: String(250+Math.floor(Math.random()*150)), "
       "galX: R(w*0.10), galY: R(h*0.885) };",
       ['sx1', 'sx2', 'sy', 'durSw', 'galX', 'galY']),
    adb('swipe da sinistra a destra dalla home -> fotocamera', 'input swipe ${sx1} ${sy} ${sx2} ${sy} ${durSw}', 'swOut'),
    attendi(2500, 3500),
    azzera('azzera: galleria', {'inGal': ''}),
    leggi("si e' aperta 'Add to story'?", GAL, 'inGal', 2000),
    esito('galleria aperta?', 'inGal', 'galOk'),
    se('IF fotocamera -> tocca la galleria (in basso a sinistra)', [('galOk', '0')], [
        tocca('tocca il quadratino della galleria', [('id', 'gallery', 'contain'), ('desc', 'allery', 'contain')],
              'cGalB', 2500),
        esito('galleria toccata?', 'cGalB', 'galTocco'),
        se('IF non trovato -> galleria (posizione)', [('galTocco', '0')],
           [toccaXY('tocca la galleria (posizione)', '${galX}', '${galY}')]),
        attendi(2500, 3500),
        leggi("si e' aperta 'Add to story'?", GAL, 'inGal', 3000),
        esito('galleria aperta?', 'inGal', 'galOk'),
    ]),
    se('IF ancora niente galleria -> niente storia', [('galOk', '0')], fine_gal),
]

ED = [('text', 'Your stories', 'equal'), ('text', 'Add a caption', 'contain'), ('text', 'Close Friends', 'equal')]
ADD = [('text', 'Add link', 'equal'), ('text', 'URL', 'equal')]

link_fallito = [
    foto('screenshot: lo sticker del link non riesce'),
    js('errore link', [], "return { storiaErr: 'link', esciEditor: '1', edOk: '0', linkOk: '0' };",
       ['storiaErr', 'esciEditor', 'edOk', 'linkOk']),
]

trascina = [
    js('dove trascino il link (in basso, facile da toccare)', ['cenX', 'cenY', 'larghezza', 'alto'],
       "const w=Number(larghezza)||720, h=Number(alto)||w*2; const R=x=>String(Math.round(x)); "
       "const posti=[[0.50,0.70],[0.50,0.74],[0.32,0.77],[0.62,0.72]]; "
       "const p=posti[Math.floor(Math.random()*posti.length)]; "
       "const dx=(Math.random()-0.5)*w*0.04, dy=(Math.random()-0.5)*h*0.02; "
       "return { daX: String(cenX), daY: String(cenY), aX: R(w*p[0]+dx), aY: R(h*p[1]+dy), "
       "durTr: String(900+Math.floor(Math.random()*500)) };",
       ['daX', 'daY', 'aX', 'aY', 'durTr']),
    adb('trascina il link (lento, oltre le griglie)', "input swipe ${daX} ${daY} ${aX} ${aY} ${durTr}", 'trOut'),
    attendi(1200, 2000),
    azzera('azzera: editor dopo il trascinamento', {'inEd': ''}),
    leggi("sono ancora nell'editor?", ED, 'inEd', 2500),
    esito('editor?', 'inEd', 'edDopoTr'),
    se("IF si e' aperto altro (testo o sticker) -> indietro", [('edDopoTr', '0')], [
        adb('indietro', 'input keyevent 4', 'backOut'),
        attendi(1200, 1800),
    ]),
    foto('screenshot: link messo'),
]

link = [
    azzera('azzera: link', {'cStk': '', 'stkTocco': '0', 'cLink': '', 'linkTocco': '0', 'inAdd': '',
                            'addOk': '0', 'urlScritto': '', 'cCust': '', 'custOk': '0', 'testoScritto': '',
                            'cDoneL': '', 'addAncora': '', 'linkOk': '0'}),
    tocca("tocca l'icona degli sticker (la faccina)", [('desc', 'Stickers', 'equal'), ('desc', 'Sticker', 'equal'),
                                                      ('desc', 'ticker', 'contain')], 'cStk'),
    esito('sticker toccato?', 'cStk', 'stkTocco'),
    se('IF non trovata -> sticker (posizione)', [('stkTocco', '0')], [toccaXY('tocca gli sticker (posizione)', '${stkX}', '${stkY}')]),
    attendi(2000, 3000),
    tocca("tocca 'LINK'", [('text', 'LINK', 'equal'), ('text', 'Link', 'equal'), ('desc', 'Link', 'equal'),
                          ('desc', 'Link sticker', 'contain')], 'cLink', 3000),
    esito('LINK toccato?', 'cLink', 'linkTocco'),
    se("IF non trovato -> cerca 'link' nella ricerca degli sticker", [('linkTocco', '0')], [
        tocca("tocca 'Search'", [('text', 'Search', 'contain')], 'cCerca', 2000),
        attendi(800, 1200),
        scrivi("scrivi 'link'", 'link', 1, 'cercaScritto'),
        attendi(1500, 2500),
        tocca("tocca 'LINK'", [('text', 'LINK', 'equal'), ('text', 'Link', 'equal'), ('desc', 'Link', 'equal'),
                              ('desc', 'Link sticker', 'contain')], 'cLink', 3000),
    ]),
    attendi(2000, 3000),
    leggi("si e' aperta 'Add link'?", ADD, 'inAdd', 3000),
    esito("'Add link' aperta?", 'inAdd', 'addOk'),
    se("IF 'Add link' aperta -> URL, testo e Done", [('addOk', '1')], [
        scrivi("scrivi l'URL (casella URL)", '${Link}', 1, 'urlScritto'),
        attendi(1000, 1600),
        tocca("tocca 'Customize sticker text'", [('text', 'ustomize sticker text', 'contain'),
                                                ('desc', 'ustomize sticker text', 'contain')], 'cCust'),
        esito('customize toccato?', 'cCust', 'custOk'),
        se('IF si -> scrivi il testo dello sticker', [('custOk', '1')], [
            attendi(1000, 1500),
            scrivi('scrivi il testo dello sticker (seconda casella)', '${testoSticker}', 2, 'testoScritto'),
        ]),
        attendi(1200, 1800),
        foto('screenshot: link e testo scritti'),
        tocca("tocca 'Done' (in alto a destra)", [('text', 'Done', 'equal'), ('desc', 'Done', 'equal')], 'cDoneL', 3000),
        attendi(2000, 3000),
        azzera("azzera: 'Add link' ancora aperta?", {'addAncora': ''}),
        leggi("'Add link' e' ancora aperta?", ADD, 'addAncora', 1500),
        esito('ancora aperta?', 'addAncora', 'addAperta'),
        se("IF ancora aperta -> chiudi la tastiera e 'Done' di nuovo", [('addAperta', '1')], [
            adb('chiudi la tastiera', 'input keyevent 111', 'escOut'),
            attendi(1000, 1500),
            tocca("tocca 'Done' (in alto a destra)", [('text', 'Done', 'equal'), ('desc', 'Done', 'equal')], 'cDoneL', 3000),
            attendi(2000, 3000),
            azzera("azzera: 'Add link' ancora aperta?", {'addAncora': ''}),
            leggi("'Add link' e' ancora aperta?", ADD, 'addAncora', 1500),
            esito('ancora aperta?', 'addAncora', 'addAperta'),
        ]),
        azzera("azzera: editor?", {'inEd': ''}),
        leggi('sono tornato all\'editor?', ED, 'inEd', 2500),
        js('link messo?', ['inEd', 'addAperta'],
           OK + " return { linkOk: (ok(inEd) && String(addAperta)!=='1') ? '1' : '0' };", ['linkOk']),
    ]),
    se('IF link messo -> trascinalo in basso', [('linkOk', '1')], trascina, link_fallito),
]

i_mus = [k for k, n in enumerate(bc) if n.get('name') == 'IF editor aperto -> musica, emoji e pubblica'][0]
bc.insert(i_mus, se('IF editor aperto -> sticker del link', [('edOk', '1')], link))

# niente caption sulla storia: il testo va nello sticker
ned = trova(bc, "IF nell'editor -> caption e 'Your stories'")['config']['children']
for nome in ("tocca 'Add a caption...'", 'scrivi la caption', 'screenshot: caption scritta'):
    k = [k for k, n in enumerate(ned) if n.get('name') == nome][0]
    del ned[k]
while ned[0]['type'] == 'waitTime':
    del ned[0]
ned.insert(0, attendi(1000, 1600))

# niente caption scritta -> non servono la freccia blu "per nome" ne' il correttore (passi per stare nel limite)
togli(top, 'IF ancora aperta -> prova la freccia blu per nome')
togli(top, "IF si e' aperto il correttore -> indietro (lo chiude)")

# ---------------------------------------------------------------- due fasi: prima (+ storia) e dopo
i_piano = indice('piano del giro (ordine a caso, durata, numeri)')
piano = top.pop(i_piano)
i_giro = indice('il giro di warm-up (moduli in ordine a caso)')
giro = top.pop(i_giro)
riapri = top.pop(indice('IF nota o storia -> riapri Instagram pulito'))
storia_blocco = top.pop(indice("IF c'e' il file della storia -> storia"))
fasi = ciclo('fase 1: warm-up prima + storia con link / fase 2: warm-up dopo', 2, [
    js('che fase e\'?', ['faseN'], "const n=(parseInt(faseN,10)||0)+1; return { faseN: String(n), fase: String(n) };",
       ['faseN', 'fase']),
    piano,
    giro,
    se('IF fase 1 -> storia con link', [('fase', '1')], [riapri, storia_blocco]),
])
top.insert(i_giro, fasi)
top.insert(i_giro, azzera('azzera: fasi', {'faseN': '0', 'fase': '1'}))

# ---------------------------------------------------------------- riepilogo ed errori
rie = trova(top, 'riepilogo del giro (per il log)')
rie['config']['injectVariables'] = ['ordine', 'likeFatti', 'likeTot', 'salvaFatti', 'repostFatti', 'storiaFatta',
                                   'storiaErr', 'linkOk', 'Link', 'testoSticker', 'testoDaTask', 'musicaMessa',
                                   'lingua', 'haStoria']
rie['config']['script'] = (
    "async function main({ ordine, likeFatti, likeTot, salvaFatti, repostFatti, storiaFatta, storiaErr, linkOk, "
    "Link, testoSticker, testoDaTask, musicaMessa, lingua, haStoria }) { return { riepilogo: "
    "'storia ' + storiaFatta + (storiaErr ? ' (' + storiaErr + ')' : '') + ' | link messo ' + linkOk + ' ' + Link + "
    "' | testo ' + testoSticker + (String(testoDaTask)==='1' ? ' (dal task)' : ' (dalla lista, ' + lingua + ')') + "
    "' | musica ' + musicaMessa + ' | ultimo giro: ordine ' + ordine + ' like ' + likeFatti + '/' + likeTot + "
    "' salvati ' + salvaFatti + ' repost ' + repostFatti }; }")
err = trova(top, "c'e' un errore da segnalare?")['config']
err['script'] = err['script'].replace(
    '\\"storiaErr:condividi\\"',
    '\\"storiaErr:link\\": \\"[Link] Non riesco a mettere lo sticker del link (faccina degli sticker, LINK o '
    '\'Add link\'): storia non pubblicata. Guarda gli screenshot.\\", \\"storiaErr:condividi\\"', 1)
if 'storiaErr:link' not in err['script']:
    err['script'] = err['script'].replace('"storiaErr:condividi"',
                                          '"storiaErr:link": "[Link] Non riesco a mettere lo sticker del link '
                                          '(faccina degli sticker, LINK o \'Add link\'): storia non pubblicata. '
                                          'Guarda gli screenshot.", "storiaErr:condividi"', 1)
assert 'storiaErr:link' in err['script']
err['script'] = err['script'].replace("(il resto del giro e' fatto)", "(il warm-up e' fatto)")

# alla fine niente throwException (il task restava "in esecuzione"): l'errore va nel log, poi End task
fin = trova(top, "IF errore -> il task finisce con l'errore")['config']['children']
k = [k for k, n in enumerate(fin) if n['type'] == 'throwException'][0]
fin[k] = js('errore (scritto nel log)', ['errMsg'], "return { errore: String(errMsg||'') };", ['errore'])
assert not [n for n in tutti(top) if n['type'] == 'throwException']

# ---------------------------------------------------------------- posizioni nel disegno di GeeLark
x = [200]


def disponi(lista):
    # come genera_flusso.py del reel virale: prima i figli, poi il padre; id nuovi
    for n in lista:
        disponi(figli(n))
        x[0] += 200
        n['id'] = nid()
        n['position'] = {'x': x[0], 'y': 285}


disponi(top)

testo = json.dumps(d, separators=(',', ':'), ensure_ascii=False)
passi = sum(1 for _ in tutti(top))
open(OUT, 'w', encoding='utf-8').write(testo)
print('scritto', OUT, len(testo.encode('utf-8')), 'byte', passi, 'passi')
assert len(testo.encode('utf-8')) <= MAX_BYTE, 'troppo grande per GeeLark'
assert passi <= MAX_PASSI, 'troppi passi per GeeLark'
