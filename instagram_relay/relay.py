# ==========================================================
#  RELAY INSTAGRAM - risponde ai commenti leggendo il TESTO
#  Il telefono GeeLark legge i nomi a schermo con i nodi RPA e li manda qui.
#  Il relay decide a chi rispondere (in ogni post 4 commenti nuovi su 10), chiede
#  la risposta al bot Hermes "commentbot" e dice al telefono QUALE "Reply"
#  premere. Gira sul tuo PC, ngrok lo rende raggiungibile dal cloud.
#  Ogni telefono (elisa, melina francoforte, ...) ha la sua memoria e
#  commentbot riceve il nome del telefono insieme al commento.
# ==========================================================

# ---------- 1) COMPILA QUI (solo questa parte) ----------

# Il bot Hermes "commentbot" (DeepSeek Flash), raggiunto tramite il
# multiplexer del profilo default. La chiave e' la voce API_SERVER_KEY in
# C:\Users\bstaa\AppData\Local\hermes\profiles\commentbot\.env
URL_API = "http://127.0.0.1:8643/p/commentbot/v1/chat/completions"
CHIAVE_API = "INCOLLA_QUI_API_SERVER_KEY_DI_COMMENTBOT"
MODELLO = "commentbot"

# La chiave API (token) di GeeLark: con questa il relay capisce da solo come si
# chiama ogni telefono (elisa, melina francoforte, ...). Se la lasci vuota, i
# nomi dei telefoni li scrivi tu nel file telefoni.txt.
GEELARK_TOKEN = ""

PORTA = 8787                 # la stessa porta che dai a ngrok
PERCENTUALE_RISPOSTE = 0.40  # 0.40 = in ogni post risponde a 4 commenti nuovi su 10 (il primo sempre)
GIORNI_MEMORIA = 7           # una persona gia' decisa (risposta o saltata) non viene riconsiderata
                             # per questi giorni, cosi' non risponde mai due volte allo stesso
                             # commento. Se Melina pubblica meno di un post ogni 2 giorni metti 14.
TIMEOUT_AI = 25              # secondi massimi di attesa per commentbot

# Lo stile delle risposte lo decide commentbot, che riceve "Telefono: <nome>"
# insieme a ogni commento. Se vuoi aggiungere istruzioni per un telefono crea il
# file persona_<nome telefono>.txt nella cartella del relay (per esempio
# persona_elisa.txt, oppure persona_melina_francoforte.txt) e scrivile li'.
PERSONA = ""

# ---------- 2) DA QUI IN GIU' NON TOCCARE NIENTE ----------

import json
import re
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

CARTELLA = Path(__file__).resolve().parent
CARTELLA_MEMORIA = CARTELLA / "memoria"
CARTELLA_MEMORIA.mkdir(exist_ok=True)

# fino alla v9.6 il flusso mandava sempre questo nome (acc=...). In GeeLark il telefono di
# Francoforte si chiama proprio cosi': la sua memoria resta la stessa.
ACCOUNT_VECCHIO = "Melina Berner Frankfurt"

PAROLE_REPLY = {"reply", "rispondi", "antworten", "responder", "répondre", "repondre"}
RUMORE = re.compile(
    r"^(like|mi piace|gefällt mir|reply|rispondi|antworten|see translation|"
    r"visualizza traduzione|übersetzung anzeigen|author|autore|autor|"
    r"liked by creator|view \d+ more repl(y|ies)|hide replies|hide|nascondi|ausblenden|"
    r"for you|per te|für dich|comments|commenti|kommentare|view|visualizza|ansehen|"
    r"\d+ comments from .*|add a comment.*|aggiungi un commento.*|kommentar hinzufügen.*|"
    r"\d+[.,]?\d*\s?[kKmM]?|\d+\s?(s|m|h|d|w|y|min|sec|hr|std|tag|tage|wo)\.?|\d{1,2}:\d{2})$",
    re.IGNORECASE,
)
# chi e' gia' stato servito: non si sceglie e non si risponde di nuovo
GIA_SERVITO = ("risposto", "in_corso")

lock = threading.Lock()
stato = {}  # per account: memoria, conteggio del 40%, ultima schermata, scelta in attesa


def log(*parti):
    print(time.strftime("%H:%M:%S"), *parti, flush=True)


def slug(account):
    # le lettere accentate restano (Melina Berner Zürich -> Melina_Berner_Zürich)
    return re.sub(r"[^\w.-]+", "_", account).strip("_") or "account"


def quota():
    """Quanti commenti nuovi su 100 ricevono una risposta."""
    p = PERCENTUALE_RISPOSTE
    return max(0, min(100, round(p * 100 if p <= 1 else p)))


def secondi(quando):
    try:
        return time.mktime(time.strptime(quando, "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        return 0.0


def nome_utente(testo):
    return re.sub(r"[^a-z0-9._]", "", str(testo or "").lower().lstrip("@"))


def leggi_memoria(account):
    """Una riga per decisione: @nome, esito, nome, data, testo. L'ultima riga vince.
    Dei file delle versioni vecchie si tengono solo le risposte pubblicate."""
    memoria = {}
    file = CARTELLA_MEMORIA / f"{slug(account)}.txt"
    if file.exists():
        for riga in file.read_text(encoding="utf-8").splitlines():
            parti = riga.split("\t")
            if len(parti) < 4:
                continue
            chiave, esito, utente, quando = parti[:4]
            if chiave.startswith("@"):
                utente = chiave[1:]
            elif esito != "risposto":
                continue
            utente = nome_utente(utente)
            if utente:
                memoria[utente] = (esito, secondi(quando))
    return memoria


def dati_account(account):
    if account not in stato:
        memoria = leggi_memoria(account)
        stato[account] = {
            "memoria": memoria, "credito": 100 - quota(), "ultima": None, "nomi": {},
            "attesa": None, "esito": None, "stallo": 0, "spostamento": 0, "ai_ko_fino": 0.0,
            "nuovi_post": 0, "risposte_post": 0, "ultimo_pick": 0.0, "tentativi": {},
            # sfasamento tra nomi e Reply visto sulla prima schermata dei post e dopo gli scroll
            "schermo": "inizio", "da_osservare": False, "visti": {"inizio": [], "scroll": []},
        }
        recenti = [e for e, t in memoria.values() if time.time() - t < GIORNI_MEMORIA * 86400]
        log(account, f"memoria: {len(recenti)} persone gia' decise negli ultimi {GIORNI_MEMORIA} giorni "
                     f"({sum(e in GIA_SERVITO for e in recenti)} con risposta)")
    return stato[account]


def ricorda(account, utente, esito, testo=""):
    adesso = time.time()
    dati_account(account)["memoria"][utente] = (esito, adesso)
    riga = "\t".join(["@" + utente, esito, utente, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(adesso)),
                      re.sub(r"\s+", " ", str(testo or "")).strip()])
    with open(CARTELLA_MEMORIA / f"{slug(account)}.txt", "a", encoding="utf-8") as f:
        f.write(riga + "\n")


def deciso(dati, utente):
    """Cosa si e' deciso per questa persona negli ultimi GIORNI_MEMORIA giorni (None = mai vista)."""
    voce = dati["memoria"].get(utente)
    if voce and time.time() - voce[1] < GIORNI_MEMORIA * 86400:
        return voce[0]
    return None


def azzera(account):
    """Per rifare un test sugli stessi post: dimentica i commenti saltati o scelti,
    tiene chi ha gia' ricevuto una risposta (cosi' non gli risponde due volte)."""
    with lock:
        memoria = leggi_memoria(account)
        tenuti = {u: v for u, v in memoria.items() if v[0] in GIA_SERVITO}
        file = CARTELLA_MEMORIA / f"{slug(account)}.txt"
        righe = ["\t".join(["@" + u, e, u, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)), ""])
                 for u, (e, t) in tenuti.items()]
        file.write_text("".join(r + "\n" for r in righe), encoding="utf-8")
        dimentica_stato(account)
    log(account, f"memoria azzerata: tenute {len(tenuti)} persone con risposta, "
                 f"dimenticate {len(memoria) - len(tenuti)} decisioni")
    return len(tenuti), len(memoria) - len(tenuti)


def dimentica_stato(account):
    """Lo stato in memoria si ricarica dal file (stesso file = stesso telefono)."""
    for nome in [n for n in stato if slug(n).lower() == slug(account).lower()]:
        stato.pop(nome)


def persona(account):
    file = CARTELLA / f"persona_{slug(account)}.txt"
    return file.read_text(encoding="utf-8-sig").strip() if file.exists() else PERSONA


NOME_IG = re.compile(r"[a-z0-9._]{2,30}")
COMPOSER = re.compile(r"^(add a comment|aggiungi un commento|kommentar hinzuf)", re.IGNORECASE)
META = re.compile(r"(modell|commento|risposta|hector|mandami|incolla|sono pronto|non posso|"
                  r"as an ai|language model)", re.IGNORECASE)


def e_reply(valore):
    valore = valore.lower()
    return len(valore) < 60 and any(valore == p or valore.startswith(p + " ") for p in PAROLE_REPLY)


def e_nome(valore):
    return bool(NOME_IG.fullmatch(valore)) and not valore.isdigit() and not RUMORE.match(valore)


def commenti_da_elenco(elenco):
    """Il telefono manda i testi a schermo uno per riga, dall'alto in basso.
    Di solito Instagram mostra come testo solo i nomi: il commento N e' quello
    dell'N-esimo nome, che corrisponde all'N-esimo pulsante Reply.
    Se tra i testi ci sono anche i "Reply", ogni "Reply" chiude un commento."""
    righe = []
    for riga in elenco.splitlines():
        riga = re.sub(r"\s+", " ", riga).strip()
        if COMPOSER.match(riga) or riga.startswith("@"):
            break
        if riga:
            righe.append(riga)

    commenti = []
    if any(e_reply(r) for r in righe):
        pezzi = []
        numero = 0
        for riga in righe:
            if e_reply(riga):
                numero += 1
                utente = next((p for p in pezzi if e_nome(p)), "")
                if utente:
                    corpo = " ".join(p for p in pezzi if p != utente)
                    commenti.append({"numero": numero, "utente": nome_utente(utente), "commento": corpo,
                                     "con_reply": True})
                pezzi = []
            elif not RUMORE.match(riga) and riga not in pezzi:
                pezzi.append(riga)
        return commenti

    nomi = [r for r in righe if e_nome(r)]
    return [{"numero": n, "utente": nome_utente(u), "commento": ""} for n, u in enumerate(nomi, start=1)]


def parole_del_nome(account, utente):
    """Il nome Instagram contiene le parole del nome (es. "Melina Berner" -> melinabernerr)."""
    parole = [p for p in re.findall(r"[a-z]+", account.lower()) if len(p) >= 4][:2]
    return bool(parole) and all(p in utente for p in parole)


def e_proprio(account, utente):
    """Il commento e' dell'account stesso: il nome Instagram letto in alto nel profilo del
    telefono (o scritto in telefoni.txt). Per i flussi vecchi, le parole del nome dell'account."""
    propri = io_di(account)
    return utente in propri if propri else parole_del_nome(account, utente)


# ---------- TELEFONI: come si chiama il telefono e qual e' il suo account Instagram ----------
# Il flusso legge il codice del telefono (getprop ro.serialno) e lo manda al relay.
# Il nome del telefono si trova nel file telefoni.txt oppure, con la chiave API,
# chiedendolo a GeeLark (il codice e' lo stesso che GeeLark chiama "device ID").

INTESTAZIONE_TELEFONI = """\
# TELEFONI: il relay deve sapere come si chiama ogni telefono (elisa, melina francoforte, ...)
# per dirlo a commentbot e per tenere una memoria separata per ogni telefono.
# Con la chiave API di GeeLark (GEELARK_TOKEN in relay.py) li trova da solo: qui non serve scrivere niente.
# Senza chiave scrivi una riga per telefono, in uno di questi due modi:
#   codice del telefono = nome del telefono
#   @nome instagram = nome del telefono
# Quando arriva un telefono che non conosce il relay aggiunge qui sotto il suo codice:
# scrivi il nome dopo il segno = e salva il file (non serve riavviare il relay).
"""
SEGNI_PROFILO = re.compile(r"\b(posts?|followers?|following|beitr[aä]ge?|abonnenten|abonniert|gefolgt|"
                           r"seguiti|seguaci|publicaciones|seguidores|seguidos)\b", re.IGNORECASE)

lock_telefoni = threading.Lock()
lock_geelark = threading.Lock()
cache_telefoni = {"file": None, "quando": None, "dati": ({}, {})}
cache_instagram = {"file": None, "dati": {}}
telefoni_geelark = {}  # codice del telefono -> nome in GeeLark (dall'API)
stato_geelark = {"codici": {}, "ultimo": 0.0, "pausa_fino": 0.0}


def file_telefoni():
    return CARTELLA / "telefoni.txt"


def stesso_nome(a, b):
    return re.sub(r"\s+", " ", str(a)).strip().casefold() == re.sub(r"\s+", " ", str(b)).strip().casefold()


def codici_telefono(testo):
    """I codici del telefono letti con getprop (di solito due volte lo stesso)."""
    codici = []
    for c in re.split(r"[,;\s]+", str(testo or "").strip().lower()):
        if re.fullmatch(r"[a-z0-9._-]{4,64}", c) and c not in ("unknown", "null", "none", "undefined") \
                and c not in codici:
            codici.append(c)
    return codici


def leggi_telefoni():
    """telefoni.txt -> ({codice: nome}, {nome instagram: nome}). Si rilegge quando cambia."""
    file = file_telefoni()
    try:
        quando = file.stat().st_mtime
    except OSError:
        return {}, {}
    with lock_telefoni:
        if cache_telefoni["file"] != file or cache_telefoni["quando"] != quando:
            codici, instagram = {}, {}
            for riga in file.read_text(encoding="utf-8-sig").splitlines():
                riga = riga.split("#", 1)[0]
                if "=" not in riga:
                    continue
                chiave, nome = riga.split("=", 1)
                chiave, nome = chiave.strip(), re.sub(r"\s+", " ", nome).strip()
                if not chiave or not nome:
                    continue
                if chiave.startswith("@"):
                    if nome_utente(chiave):
                        instagram[nome_utente(chiave)] = nome
                else:
                    for c in codici_telefono(chiave):
                        codici[c] = nome
            cache_telefoni.update(file=file, quando=quando, dati=(codici, instagram))
        return cache_telefoni["dati"]


def prepara_file_telefoni():
    if not file_telefoni().exists():
        file_telefoni().write_text(INTESTAZIONE_TELEFONI, encoding="utf-8")


def segna_sconosciuto(codici, io):
    """Aggiunge il telefono sconosciuto a telefoni.txt: l'utente deve solo scrivere il nome."""
    prepara_file_telefoni()
    chiave = codici[0] if codici else (f"@{io}" if io else "")
    testo = file_telefoni().read_text(encoding="utf-8-sig")
    if not chiave or chiave in testo.lower():
        return
    with open(file_telefoni(), "a", encoding="utf-8") as f:
        f.write(("" if testo.endswith("\n") else "\n")
                + f"# telefono nuovo visto il {time.strftime('%d/%m alle %H:%M')}"
                + (f" (il suo Instagram e' @{io})" if io else "")
                + ": scrivi il suo nome dopo il segno =\n" + f"{chiave} = \n")


def geelark(percorso, dati):
    """Una chiamata all'API di GeeLark (il token si prende nel programma GeeLark, pagina API)."""
    richiesta = urllib.request.Request("https://openapi.geelark.com/open/v1/" + percorso,
                                       data=json.dumps(dati).encode("utf-8"), headers={
                                           "Content-Type": "application/json",
                                           "traceId": str(uuid.uuid4()).upper(),
                                           "Authorization": f"Bearer {GEELARK_TOKEN.strip()}",
                                       })
    with urllib.request.urlopen(richiesta, timeout=20) as r:
        risposta = json.loads(r.read().decode("utf-8"))
    if risposta.get("code") != 0:
        raise RuntimeError(f"errore {risposta.get('code')}: {risposta.get('msg')}")
    return risposta.get("data") or {}


def aggiorna_da_geelark(codici=(), dopo=20):
    """Chiede a GeeLark i nomi dei telefoni e i loro codici (al massimo ogni `dopo` secondi)."""
    if not GEELARK_TOKEN.strip():
        return
    with lock_geelark:
        adesso = time.time()
        if adesso < stato_geelark["pausa_fino"] or adesso - stato_geelark["ultimo"] < dopo:
            return
        stato_geelark["ultimo"] = adesso
        try:
            elenco, pagina = [], 1
            while True:
                dati = geelark("phone/list", {"page": pagina, "pageSize": 100})
                pezzo = dati.get("items") or []
                elenco += pezzo
                if not pezzo or len(elenco) >= int(dati.get("total") or 0) or pagina >= 50:
                    break
                pagina += 1
            for giro in range(2):
                nuovi = {}
                for telefono in elenco:
                    pid, nome = str(telefono.get("id") or ""), str(telefono.get("serialName") or "").strip()
                    if not pid or not nome:
                        continue
                    if pid not in stato_geelark["codici"]:
                        stato_geelark["codici"][pid] = codici_telefono(
                            geelark("phone/serialNum/get", {"id": pid}).get("serialNum"))
                    for c in stato_geelark["codici"][pid]:
                        nuovi[c] = nome
                if giro or not codici or any(c in nuovi for c in codici):
                    break
                stato_geelark["codici"].clear()  # dopo "nuovo telefono con un clic" il codice cambia
            with lock_telefoni:
                telefoni_geelark.clear()
                telefoni_geelark.update(nuovi)
        except Exception as e:
            stato_geelark["pausa_fino"] = adesso + 600
            log("GeeLark", f"non riesco a leggere i nomi dei telefoni con l'API ({e}): riprovo tra 10 minuti")


def nome_telefono(codici, io="", aggiorna=False):
    """Il nome del telefono (come in GeeLark) dal suo codice; "" se non si sa."""
    dal_file, per_instagram = leggi_telefoni()
    for c in codici:
        if dal_file.get(c):
            return dal_file[c]
    if io and per_instagram.get(io):
        return per_instagram[io]

    def da_geelark():
        with lock_telefoni:
            return next((telefoni_geelark[c] for c in codici if c in telefoni_geelark), "")
    nome = "" if aggiorna else da_geelark()
    if not nome and codici:
        aggiorna_da_geelark(codici, dopo=20 if aggiorna else 300)
        nome = da_geelark()
    return nome


def carica_instagram():
    """I nomi Instagram letti in alto nel profilo di ogni telefono: {telefono: {nomi}}."""
    file = CARTELLA_MEMORIA / "account_instagram.txt"
    if cache_instagram["file"] != file:
        dati = {}
        if file.exists():
            for riga in file.read_text(encoding="utf-8").splitlines():
                parti = riga.split("\t")
                if len(parti) >= 2 and nome_utente(parti[1]):
                    dati.setdefault(parti[0], set()).add(nome_utente(parti[1]))
        cache_instagram.update(file=file, dati=dati)
    return cache_instagram["dati"]


def io_di(telefono):
    """I nomi Instagram dell'account del telefono (dal profilo o da telefoni.txt)."""
    _, per_instagram = leggi_telefoni()
    nomi = {u for t, insieme in list(carica_instagram().items()) if stesso_nome(t, telefono) for u in insieme}
    return nomi | {u for u, t in per_instagram.items() if stesso_nome(t, telefono)}


def impara_io(telefono, io):
    if io in io_di(telefono):
        return
    noti = carica_instagram()
    noti[telefono] = noti.get(telefono, set()) | {io}  # insieme nuovo: chi lo sta leggendo non si confonde
    with open(CARTELLA_MEMORIA / "account_instagram.txt", "a", encoding="utf-8") as f:
        f.write(f"{telefono}\t{io}\n")
    log(telefono, f"il suo account Instagram e' @{io}: ai commenti di @{io} non risponde mai")


def nome_dal_profilo(testo):
    """Il nome Instagram scritto in alto nella pagina del profilo ("" se non si legge)."""
    righe = [re.sub(r"\s+", " ", r).strip() for r in str(testo or "").splitlines()]
    alto = next((r[4:].strip().lstrip("@") for r in righe if r.startswith("top=")), "")
    if e_nome(alto):
        return alto
    altre = [r for r in righe if r and not r.startswith("top=")]
    # senza "post", "follower"... non e' la pagina del profilo: meglio non indovinare
    if not any(SEGNI_PROFILO.search(r) for r in altre):
        return ""
    return next((r for r in altre if e_nome(r) and not SEGNI_PROFILO.fullmatch(r)), "")


def eredita_memoria(telefono):
    """La memoria segue l'account Instagram: se lo stesso account aveva un altro nome
    (telefono rinominato in GeeLark) la sua memoria passa a questo telefono, cosi' non
    risponde due volte alla stessa persona."""
    propri = io_di(telefono)
    vecchi = [nome for nome, insieme in list(carica_instagram().items()) if insieme & propri]
    nuovo = CARTELLA_MEMORIA / f"{slug(telefono)}.txt"
    for nome in vecchi:
        vecchio = CARTELLA_MEMORIA / f"{slug(nome)}.txt"
        if slug(nome).lower() == slug(telefono).lower() or not vecchio.exists():
            continue
        righe = vecchio.read_text(encoding="utf-8").splitlines()
        if nuovo.exists():
            righe += nuovo.read_text(encoding="utf-8").splitlines()
        # in ordine di data: l'ultima riga (la decisione piu' recente) vince
        righe.sort(key=lambda r: (r.split("\t") + [""] * 4)[3])
        nuovo.write_text("".join(r + "\n" for r in righe if r.strip()), encoding="utf-8")
        vecchio.replace(vecchio.with_name(vecchio.stem + ".importato"))
        dimentica_stato(telefono)
        log(telefono, f"memoria di \"{nome}\" (stesso account Instagram) passata a questo telefono")


def ciao(codici, testo):
    """Inizio del task: il telefono manda il suo codice e il testo in alto nel profilo.
    Risponde OK se sa come si chiama il telefono e qual e' il suo account, se no STOP."""
    io = nome_dal_profilo(testo)
    telefono = nome_telefono(codici, io, aggiorna=True)
    descrizione = f"codice {', '.join(codici) or 'non letto'}" + (f", Instagram @{io}" if io else "")
    if not telefono:
        segna_sconosciuto(codici, io)
        log("?", f"telefono sconosciuto ({descrizione}): non so come si chiama -> STOP. "
            + ("Controlla la chiave API di GeeLark in relay.py oppure scrivi" if GEELARK_TOKEN.strip()
               else "Scrivi") + " il suo nome in telefoni.txt e riavvia il task")
        return "STOP|telefono sconosciuto"
    with lock:
        if io:
            impara_io(telefono, io)
        eredita_memoria(telefono)
        dati_account(telefono)
        propri = io_di(telefono)
    if not propri:
        log(telefono, f"non so qual e' il suo account Instagram ({descrizione}) -> STOP, cosi' non risponde "
            f"a se stessa. Scrivi in telefoni.txt una riga cosi': @nomeinstagram = {telefono}")
        return "STOP|account instagram sconosciuto"
    log(telefono, f"=== telefono {telefono} (Instagram @{', @'.join(sorted(propri))}): comincio ===")
    return f"OK|{telefono}"


def chi_e(parametri):
    """Il nome del telefono che fa la richiesta ("" = non si sa: il telefono si ferma).
    Il flusso v9.7 manda il codice del telefono (dev), quelli vecchi il nome dell'account (acc)."""
    if "dev" not in parametri:
        return (parametri.get("acc") or [ACCOUNT_VECCHIO])[0] or ACCOUNT_VECCHIO
    codici = codici_telefono(parametri["dev"][0])
    telefono = nome_telefono(codici) if codici else ""
    if not telefono:
        log("?", f"richiesta da un telefono sconosciuto (codice {', '.join(codici) or 'non letto'}) -> mi fermo")
        return ""
    if not io_di(telefono):
        log(telefono, "non so qual e' il suo account Instagram -> mi fermo (vedi telefoni.txt)")
        return ""
    return telefono


def pulisci(testo):
    return re.sub(r"\s+", " ", str(testo or "")).replace("|", "/").strip()


def pulisci_risposta(testo):
    """Tiene solo il testo da pubblicare, anche se commentbot aggiunge altro."""
    testo = str(testo or "").strip()
    trovato = re.search(r"\{.*\}", testo, re.DOTALL)
    if trovato:
        try:
            dati = json.loads(trovato.group(0))
            testo = str(dati.get("risposta") or dati.get("reply") or dati.get("text") or "")
        except ValueError:
            pass
    righe = [r.strip() for r in testo.replace("```", "").splitlines() if r.strip()]
    righe = [r for r in righe if not r.endswith(":")]
    testo = righe[0] if righe else ""
    testo = re.sub(r"^(risposta|reply|antwort)\s*:\s*", "", testo, flags=re.IGNORECASE)
    testo = re.sub(r"^(@[A-Za-z0-9._]+\s*)+", "", testo)
    testo = pulisci(testo.strip(" \"'«»“”„"))
    if len(testo) > 180:
        taglio = max(testo.rfind(s, 0, 180) for s in ".!?")
        testo = testo[:taglio + 1] if taglio > 40 else testo[:180]
    if META.search(testo):
        return ""
    return testo


def chiedi_risposta(account, c):
    extra = persona(account)
    propri = sorted(io_di(account))
    commento = c["commento"] or "(il testo non si legge: probabilmente un cuore ❤️ o un complimento)"
    messaggio = (
        f"Telefono: {account}\n"
        + (f"Account Instagram: @{', @'.join(propri)}\n" if propri else "")
        + (f"Istruzioni: {extra}\n" if extra else "")
        + f"Commento di @{c['utente']} sotto un suo post: {commento}\n\n"
        "Scrivi SOLO la risposta da pubblicare sotto questo commento, come la scriverebbe lei: "
        "breve (massimo 1-2 frasi), senza virgolette, senza @ e senza usare il nome della persona, "
        "senza altro testo."
    )
    corpo = json.dumps({
        "model": MODELLO,
        "messages": [{"role": "user", "content": messaggio}],
        "stream": False,
    }).encode("utf-8")
    richiesta = urllib.request.Request(URL_API, data=corpo, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHIAVE_API}",
    })
    with urllib.request.urlopen(richiesta, timeout=TIMEOUT_AI) as r:
        risposta = json.loads(r.read().decode("utf-8"))
    grezzo = risposta["choices"][0]["message"]["content"]
    pulito = pulisci_risposta(grezzo)
    if not pulito:
        log(account, "risposta di commentbot scartata:", repr(str(grezzo)[:200]))
    return pulito


def maggioranza(osservati, predefinito):
    """Lo sfasamento visto piu' spesso di recente (a parita' il piu' recente)."""
    recenti = osservati[-6:]
    if not recenti:
        return predefinito
    migliore = max(recenti.count(o) for o in recenti)
    return next(o for o in reversed(recenti) if recenti.count(o) == migliore)


def rimborsa(dati):
    """Il commento scelto non ha avuto risposta: il prossimo commento nuovo prende il suo posto."""
    dati["credito"] = min(dati["credito"] + 100, 200)


def scegli(account, elenco, nuovo=None):
    """Sceglie il commento e dice al telefono quale Reply premere. La risposta di
    commentbot si chiede dopo, quando la casella e' aperta e si sa a chi rispondere."""
    with lock:
        risultato, c = _prepara(account, elenco, nuovo)
        dati = dati_account(account)
        if c is not None and time.time() < dati["ai_ko_fino"]:
            log(account, "commentbot non risponde: salto per ora, riprovo tra poco")
            risultato, c = "NO_MATCH", None
        if c is None:
            dati["esito"] = risultato
            return risultato
        premuto = max(1, c["numero"] + dati["spostamento"])
        dati["attesa"] = {"utente": c["utente"], "commento": c["commento"], "premuto": premuto,
                          "quando": time.time()}
        dati["esito"] = "PICK"
    log(account, f"scelto @{c['utente']}: premo il Reply n.{premuto}")
    return f"PICK|{premuto}|0|0|{c['utente']}|ok"


def _prepara(account, elenco, nuovo=None):
    """Legge la schermata, decide i commenti nuovi e sceglie il prossimo a cui rispondere.
    nuovo: True se il telefono ha appena aperto i commenti di un post (None = non lo dice)."""
    commenti = commenti_da_elenco(elenco)
    dati = dati_account(account)
    dati["attesa"] = None
    firma = tuple(c["utente"] for c in commenti)
    adesso = time.time()
    if nuovo is None:
        nuovo = dati["esito"] in (None, "END") or adesso - dati["ultimo_pick"] > 120
    if nuovo:
        # primo sguardo a un post: la lista parte dall'inizio e il 40% si conta da capo,
        # cosi' il primo commento nuovo di ogni post riceve sempre una risposta
        log(account, "--- commenti di un post nuovo ---")
        dati.update(ultima=None, stallo=0, nuovi_post=0, risposte_post=0, tentativi={}, credito=100 - quota())
        dati["schermo"], dati["da_osservare"] = "inizio", True
        dati["spostamento"] = maggioranza(dati["visti"]["inizio"], 0)
    elif dati["esito"] != "PICK" and firma != dati["ultima"] and dati["ultima"]:
        # dopo uno scroll di solito il commento in alto e' tagliato: si vede il suo Reply
        # ma non il suo nome, quindi i Reply sono uno in piu' dei nomi
        dati["schermo"], dati["da_osservare"] = "scroll", True
        dati["spostamento"] = maggioranza(dati["visti"]["scroll"], 1)
    dati["ultimo_pick"] = adesso
    con_reply = any(c.get("con_reply") for c in commenti)
    if con_reply:
        # il telefono ha letto anche i Reply: il numero e' gia' quello giusto
        dati["spostamento"], dati["da_osservare"] = 0, False
    # schermata identica dopo uno scroll (non dopo una risposta) = fine della lista
    if firma == dati["ultima"] and dati["esito"] != "PICK":
        dati["stallo"] += 1
    elif firma != dati["ultima"]:
        dati["stallo"] = 0
    dati["ultima"] = firma
    dati["nomi"] = {c["numero"]: c["utente"] for c in commenti}

    if not commenti:
        # con la scritta di Facebook la lista e' caricata ma non ha commenti di Instagram;
        # senza niente forse sta ancora caricando: si aspetta un giro in piu'
        facebook = re.search(r"\d+ comments? from facebook", elenco, re.IGNORECASE)
        if dati["stallo"] >= (1 if facebook else 2):
            log(account, "nessun commento di Instagram"
                + (" (ci sono solo commenti di Facebook, da Instagram non si rispondono)" if facebook else "")
                + " -> END, passo al post dopo")
            dati["nuovi_post"] = dati["risposte_post"] = 0
            return "END", None
        log(account, "nessun commento riconosciuto a schermo"
            + (" (solo commenti di Facebook)" if facebook else ""))
        return "NO_MATCH", None

    candidati, visti = [], set()
    nuovi = scelti = gia = propri = 0
    for c in commenti:
        utente = c["utente"]
        if not utente or utente in visti:
            continue
        visti.add(utente)
        if e_proprio(account, utente):
            propri += 1
            continue
        esito = deciso(dati, utente)
        if esito is None:
            # 40% esatto: ogni commento nuovo aggiunge 40, ogni 100 si risponde a uno
            nuovi += 1
            dati["credito"] += quota()
            if dati["credito"] >= 100:
                dati["credito"] -= 100
                esito = "si"
                scelti += 1
            else:
                esito = "skip"
            ricorda(account, utente, esito, c["commento"])
        else:
            gia += 1
        if esito == "si":
            candidati.append(c)
    dati["nuovi_post"] += nuovi

    log(account, f"{nuovi + gia} commenti a schermo"
        + (f" (+{propri} dell'account)" if propri else "")
        + f": {nuovi} nuovi ({scelti} scelti), {gia} gia' visti prima -> da rispondere: {len(candidati)}")

    if dati["stallo"] >= 4 or (dati["stallo"] >= 2 and not candidati):
        log(account, f"la lista non scorre piu': commenti finiti -> END (in questo post: "
                     f"{dati['nuovi_post']} commenti nuovi, {dati['risposte_post']} risposte pubblicate)")
        dati["nuovi_post"] = dati["risposte_post"] = 0
        dati["tentativi"] = {}
        return "END", None
    if not candidati:
        if dati["stallo"] == 1:
            log(account, "la schermata non e' cambiata, riprovo a scorrere")
        return "NO_MATCH", None
    # il Reply dell'ultimo nome in basso puo' essere ancora fuori schermo: prima si scorre
    ultimo = commenti[-1]["numero"]
    scelta = next((c for c in candidati if c["numero"] != ultimo), None)
    if scelta is None:
        if dati["stallo"] == 0 and len(commenti) > 1 and not con_reply:
            log(account, f"@{candidati[0]['utente']} e' l'ultimo in basso: scorro un po' e gli rispondo dopo")
            return "NO_MATCH", None
        scelta = candidati[0]
    return "PICK", scelta


def impara_spostamento(account, dati, premuto, reale):
    """Si e' aperto il Reply di un altro: capisce di quanto sono sfasati nomi e Reply
    in questa schermata (es. il primo commento in alto e' tagliato: si vede il suo
    Reply ma non il suo nome) e lo corregge per le prossime scelte."""
    posizioni = [n for n, u in dati["nomi"].items() if u == reale]
    if posizioni:
        vero = min(posizioni, key=lambda n: abs(n - premuto))
    elif premuto == 1 and dati["schermo"] == "scroll":
        vero = 0  # il primo Reply era di un commento tagliato in alto
    else:
        return None
    spostamento = premuto - vero
    if not -2 <= spostamento <= 2:
        return None
    if spostamento != dati["spostamento"]:
        dati["spostamento"] = spostamento
        log(account, f"nomi e Reply sfasati di {spostamento}: correggo le prossime scelte")
    return spostamento


def conferma(account, utente_casella):
    """Il telefono ha premuto Reply e dice di chi e' la casella aperta.
    Si risponde a quella persona (la risposta e' generica), salvo eccezioni."""
    with lock:
        dati = dati_account(account)
        attesa = dati["attesa"]
        if not attesa or time.time() - attesa["quando"] > 180:
            log(account, "conferma senza scelta in attesa -> NO_MATCH")
            return "NO_MATCH"
        scelto = attesa["utente"]
        reale = nome_utente(utente_casella)
        visto = dati["spostamento"] if reale == scelto else None
        if reale and reale != scelto:
            visto = impara_spostamento(account, dati, attesa["premuto"], reale)
        if visto is not None and dati["da_osservare"]:
            dati["visti"][dati["schermo"]].append(visto)
            dati["da_osservare"] = False
        motivo = None
        if not reale:
            motivo = "la casella di risposta non si e' aperta"
        elif e_proprio(account, reale):
            motivo = f"il Reply premuto e' sotto un commento di @{reale} (l'account stesso)"
        elif deciso(dati, reale) in GIA_SERVITO:
            motivo = f"il Reply premuto e' di @{reale}, che ha gia' una risposta"
        elif reale not in dati["nomi"].values() and not (attesa["premuto"] == 1 and dati["schermo"] == "scroll"):
            # solo dopo uno scroll il primo Reply puo' essere di un nome non a schermo (commento
            # tagliato in alto): altrimenti la casella e' stata letta male (es. una @menzione)
            motivo = f"nella casella c'e' @{reale}, che non e' tra i nomi a schermo"
        if motivo:
            non_riuscito(account, dati, scelto, motivo, casella_vuota=not reale)
            return "NO_MATCH"
        commento = attesa["commento"] if reale == scelto else ""

    # la risposta si chiede solo ora, per la persona della casella aperta
    inizio = time.time()
    errore = False
    try:
        risposta = chiedi_risposta(account, {"utente": reale, "commento": commento})
    except Exception as e:
        log(account, "commentbot non ha risposto:", e)
        risposta, errore = "", True

    with lock:
        dati = dati_account(account)
        if dati["attesa"] is not attesa:
            return "NO_MATCH"
        if not risposta:
            if errore:
                dati["ai_ko_fino"] = time.time() + 60
            non_riuscito(account, dati, scelto, "nessuna risposta valida da commentbot")
            return "NO_MATCH"
        if reale != scelto:
            log(account, f"il Reply premuto e' di @{reale} (scelto @{scelto}): rispondo a @{reale}")
            tentativi = dati["tentativi"].get(scelto, 0)
            if deciso(dati, reale) == "si" and tentativi < 2:
                dati["tentativi"][scelto] = tentativi + 1  # @reale usa il suo posto, @scelto si riprova
            else:
                ricorda(account, scelto, "fallito", f"aperto @{reale}")
        # segnato subito: anche se la conferma finale si perde non gli risponde una seconda volta
        ricorda(account, reale, "in_corso", risposta)
        attesa["reale"], attesa["risposta"] = reale, risposta
    log(account, f"rispondo a @{reale}: \"{risposta}\" ({time.time() - inizio:.1f}s)")
    return f"@{reale} {risposta}"


def non_riuscito(account, dati, scelto, motivo, casella_vuota=False):
    """Il Reply non e' andato: si riprova la stessa persona (lo sfasamento ora e'
    corretto), dopo 2 tentativi la si salta e il suo posto passa al prossimo commento nuovo."""
    tentativi = dati["tentativi"].get(scelto, 0)
    if tentativi < 2:
        dati["tentativi"][scelto] = tentativi + 1
        if casella_vuota and dati["spostamento"] > -2:
            dati["spostamento"] -= 1  # premuto un Reply oltre l'ultimo a schermo
        log(account, f"{motivo} -> riprovo @{scelto}")
    else:
        log(account, f"{motivo} -> salto @{scelto}, il prossimo commento nuovo prende il suo posto")
        ricorda(account, scelto, "fallito", motivo)
        rimborsa(dati)
    dati["attesa"] = None


def fatto(account):
    with lock:
        dati = dati_account(account)
        attesa = dati["attesa"]
        if attesa and attesa.get("reale"):
            ricorda(account, attesa["reale"], "risposto", attesa["risposta"])
            dati["risposte_post"] += 1
            log(account, f"risposta pubblicata a @{attesa['reale']}, salvata in memoria")
        dati["attesa"] = None
    return "ACK_OK"


class Gestore(BaseHTTPRequestHandler):
    def rispondi(self, testo):
        dati = testo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)

    def gestisci(self):
        url = urlparse(self.path)
        parametri = parse_qs(url.query, keep_blank_values=True)
        lunghezza = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(lunghezza).decode("utf-8", errors="replace") if lunghezza else ""
        # /azzera e /telefoni solo dal browser del PC, non da internet tramite ngrok
        dal_pc = self.client_address[0] == "127.0.0.1" and not self.headers.get("X-Forwarded-For")
        account = "?"
        try:
            if url.path == "/ciao":
                self.rispondi(ciao(codici_telefono((parametri.get("dev") or [""])[0]), unquote(corpo)))
            elif url.path in ("/pick", "/confirm", "/ack"):
                account = chi_e(parametri)
                if not account:
                    self.rispondi({"/pick": "END", "/confirm": "NO_MATCH", "/ack": "ACK_OK"}[url.path])
                elif url.path == "/pick":
                    elenco = unquote(corpo)
                    (CARTELLA / f"ultima_schermata_{slug(account)}.txt").write_text(elenco, encoding="utf-8")
                    if not elenco.strip():
                        log(account, "il telefono non ha mandato nessun testo")
                    nuovo = (parametri.get("nuovo") or [""])[0]
                    self.rispondi(scegli(account, elenco, {"1": True, "0": False}.get(nuovo)))
                elif url.path == "/confirm":
                    casella = (parametri.get("u") or [""])[0] or re.sub(r"^u=", "", corpo.strip())
                    self.rispondi(conferma(account, casella))
                else:
                    self.rispondi(fatto(account))
            elif url.path == "/azzera" and dal_pc:
                self.rispondi(pagina_azzera((parametri.get("acc") or [""])[0].strip()))
            elif url.path == "/telefoni" and dal_pc:
                self.rispondi(pagina_telefoni())
            else:
                self.rispondi("RELAY_OK")
        except Exception as e:
            log(account, "errore:", e)
            self.rispondi("NO_MATCH")

    do_GET = gestisci
    do_POST = gestisci

    def log_message(self, *args):
        pass


def pagina_azzera(nome):
    if not nome:
        nomi = sorted(f.stem for f in CARTELLA_MEMORIA.glob("*.txt") if f.name != "account_instagram.txt")
        return ("Scrivi anche il nome del telefono, per esempio:\n"
                "http://127.0.0.1:8787/azzera?acc=elisa\n\n"
                f"Telefoni con una memoria: {', '.join(nomi) or 'nessuno'}")
    tenuti, dimenticati = azzera(nome)
    return (f"Memoria azzerata per {nome}: dimenticate {dimenticati} decisioni, "
            f"tenute {tenuti} persone che hanno gia' una risposta. Ora puoi rifare il test.")


def pagina_telefoni():
    dal_file, per_instagram = leggi_telefoni()
    with lock_telefoni:
        da_geelark = dict(telefoni_geelark)
    nomi = {}
    for nome in list(dal_file.values()) + list(da_geelark.values()) + list(per_instagram.values()) \
            + list(carica_instagram()):
        nomi.setdefault(nome.casefold(), nome)
    righe = ["TELEFONI CHE IL RELAY CONOSCE", ""]
    for nome in sorted(nomi.values(), key=str.casefold):
        codici = sorted({c for c, n in list(dal_file.items()) + list(da_geelark.items()) if stesso_nome(n, nome)})
        propri = sorted(io_di(nome))
        righe.append(f"{nome}:  Instagram {', '.join('@' + u for u in propri) or '? (non ancora letto)'}"
                     f"  -  codice {', '.join(codici) or '?'}")
    if len(righe) == 2:
        righe.append("nessuno per ora")
    righe += ["", "Nomi presi da GeeLark con la chiave API" if GEELARK_TOKEN.strip()
              else "Chiave API di GeeLark non messa: i nomi vengono solo da telefoni.txt"]
    return "\n".join(righe)


def mostra_telefoni_geelark():
    aggiorna_da_geelark(dopo=0)
    with lock_telefoni:
        nomi = sorted(set(telefoni_geelark.values()), key=str.casefold)
    if nomi:
        log("GeeLark", f"chiave API ok, {len(nomi)} telefoni: {', '.join(nomi)}")


if __name__ == "__main__":
    prepara_file_telefoni()
    print(f"Relay acceso sulla porta {PORTA}. Lascia questa finestra aperta.")
    if GEELARK_TOKEN.strip():
        threading.Thread(target=mostra_telefoni_geelark, daemon=True).start()
    else:
        print("Chiave API di GeeLark non messa: i nomi dei telefoni li leggo da telefoni.txt")
    ThreadingHTTPServer(("0.0.0.0", PORTA), Gestore).serve_forever()
