# IG STORIA LINK v3: copia IDENTICA di IG WARMUP v10.4 (base_IG_WARMUP_v10_4.json, il file del 10/10 dell'utente)
# con due sole modifiche: niente nota, e lo sticker del link nella storia (prima della musica).
# Si rigenera con:  python3 instagram_storia_link/genera_storia_link.py
import json, os, re, uuid

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(QUI, 'base_IG_WARMUP_v10_4.json')
OUT = os.path.join(QUI, 'IG_STORIA_LINK_IMPORT.json')
MAX_BYTE, MAX_PASSI = 243500, 532

d = json.load(open(BASE, encoding='utf-8'))
top = d['content']['contents']
assert d['title'] == 'IG WARMUP v10.4'


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
d['title'] = 'IG STORIA LINK v3'
d['desc'] = d['desc'].replace(', nota ogni 24 ore dalla lista', '').replace('Note e caption', 'Caption') + (
    " + Link: nella storia, prima della musica, sticker -> LINK -> URL = Link del task -> 'Customize sticker text' "
    "= Testo del task (vuoto = la caption della lista) -> Done -> trascina il link in basso. Niente nota.")
d['content']['startParamMap'] += [
    {'contentable': True, 'createFrom': '', 'id': nid(), 'isNotRequired': False, 'key': 'Link', 'length': 500,
     'type': 'string', 'value': ''},
    {'contentable': True, 'createFrom': '', 'id': nid(), 'isNotRequired': True, 'key': 'Testo', 'length': 100,
     'type': 'string', 'value': ''},
]

# ---------------------------------------------------------------- 1) niente nota
i = indice("quando e' stata fatta l'ultima nota?")
top[i] = js('niente nota (mai)', [], "return { notaDovuta: '0' };", ['notaDovuta'])
togli(top, 'tocca fare la nota?')
togli(top, 'IF nota dovuta -> nota')

# ---------------------------------------------------------------- 2) sticker del link
pos = trova(top, 'posizioni sullo schermo')['config']
assert "frY: R(h*0.899) };" in pos['script']
pos['script'] = pos['script'].replace("frY: R(h*0.899) };",
                                      "frY: R(h*0.899), stkX: R(w*0.921), stkY: R(w*0.194), "
                                      "cenX: R(w*0.5), cenY: R(h*0.468) };")
pos['variableMap'] += [{'value': v, 'variable': v} for v in ('stkX', 'stkY', 'cenX', 'cenY')]

bc = trova(top, "IF c'e' il file della storia -> storia")['config']['children']
j = [k for k, n in enumerate(bc) if n.get('name') == 'scegli la caption (lista, mai ripetuta)'][0]
bc.insert(j + 1, js('testo dello sticker (Testo del task o caption della lista)', ['Testo', 'captionStoria'],
                    "const t=String(Testo===undefined||Testo===null?'':Testo).trim(); "
                    "return { testoSticker: t || String(captionStoria||''), testoDaTask: t ? '1' : '0' };",
                    ['testoSticker', 'testoDaTask']))

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

err = trova(top, "c'e' un errore da segnalare?")['config']
for a, b in (('\\"storiaErr:condividi\\"', '\\"storiaErr:link\\": \\"[Link] Non riesco a mettere lo sticker del link: storia non pubblicata. Guarda gli screenshot.\\", \\"storiaErr:condividi\\"'),
             ('"storiaErr:condividi"', '"storiaErr:link": "[Link] Non riesco a mettere lo sticker del link: storia non pubblicata. Guarda gli screenshot.", "storiaErr:condividi"')):
    if 'storiaErr:link' not in err['script']:
        err['script'] = err['script'].replace(a, b, 1)
assert 'storiaErr:link' in err['script']

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
