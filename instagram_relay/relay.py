# ==========================================================
#  RELAY INSTAGRAM - risponde ai commenti leggendo il TESTO
#  Il telefono GeeLark legge i nomi a schermo con i nodi RPA e li manda qui.
#  Il relay decide a chi rispondere (2 commenti nuovi ogni 5 = 40%), chiede
#  la risposta al bot Hermes "commentbot" e dice al telefono QUALE "Reply"
#  premere. Gira sul tuo PC, ngrok lo rende raggiungibile dal cloud.
# ==========================================================

# ---------- 1) COMPILA QUI (solo questa parte) ----------

# Il bot Hermes "commentbot" (DeepSeek Flash), raggiunto tramite il
# multiplexer del profilo default. La chiave e' la voce API_SERVER_KEY in
# C:\Users\bstaa\AppData\Local\hermes\profiles\commentbot\.env
URL_API = "http://127.0.0.1:8643/p/commentbot/v1/chat/completions"
CHIAVE_API = "INCOLLA_QUI_API_SERVER_KEY_DI_COMMENTBOT"
MODELLO = "commentbot"

PORTA = 8787                 # la stessa porta che dai a ngrok
PERCENTUALE_RISPOSTE = 0.40  # 0.40 = risponde a 2 commenti nuovi ogni 5 (conteggio fisso, non a sorte)
GIORNI_MEMORIA = 7           # una persona gia' decisa (risposta o saltata) non viene riconsiderata
                             # per questi giorni, cosi' non risponde mai due volte allo stesso
                             # commento. Se Melina pubblica meno di un post ogni 2 giorni metti 14.
TIMEOUT_AI = 25              # secondi massimi di attesa per commentbot

# Lo stile delle risposte lo decide commentbot. Se vuoi aggiungere istruzioni
# per un account specifico crea il file persona_<nome account>.txt nella
# cartella del relay e scrivile li'.
PERSONA = ""

# ---------- 2) DA QUI IN GIU' NON TOCCARE NIENTE ----------

import json
import re
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

CARTELLA = Path(__file__).resolve().parent
CARTELLA_MEMORIA = CARTELLA / "memoria"
CARTELLA_MEMORIA.mkdir(exist_ok=True)

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
    return re.sub(r"[^A-Za-z0-9._-]+", "_", account).strip("_") or "account"


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
        stato.pop(account, None)
    log(account, f"memoria azzerata: tenute {len(tenuti)} persone con risposta, "
                 f"dimenticate {len(memoria) - len(tenuti)} decisioni")
    return len(tenuti), len(memoria) - len(tenuti)


def persona(account):
    file = CARTELLA / f"persona_{slug(account)}.txt"
    return file.read_text(encoding="utf-8").strip() if file.exists() else PERSONA


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


def e_proprio(account, utente):
    """Il commento e' dell'account stesso (es. "Melina Berner" -> melinabernerr)."""
    parole = [p for p in re.findall(r"[a-z]+", account.lower()) if len(p) >= 4][:2]
    return bool(parole) and all(p in utente for p in parole)


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
    commento = c["commento"] or "(il testo non si legge: probabilmente un cuore ❤️ o un complimento)"
    messaggio = (
        f"Modella: {account}\n"
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


def scegli(account, elenco):
    inizio = time.time()
    with lock:
        risultato, c = _prepara(account, elenco)
        dati = dati_account(account)
        if c is not None and time.time() < dati["ai_ko_fino"]:
            log(account, "commentbot non risponde: salto per ora, riprovo tra poco")
            risultato, c = "NO_MATCH", None
        if c is None:
            dati["esito"] = risultato
            return risultato

    errore = False
    try:
        risposta = chiedi_risposta(account, c)
    except Exception as e:
        log(account, "commentbot non ha risposto:", e)
        risposta, errore = "", True

    with lock:
        dati = dati_account(account)
        if not risposta:
            if errore:
                dati["ai_ko_fino"] = time.time() + 60
            else:
                ricorda(account, c["utente"], "scartato_ai")
                rimborsa(dati)
            dati["esito"] = "NO_MATCH"
            return "NO_MATCH"
        premuto = max(1, c["numero"] + dati["spostamento"])
        dati["attesa"] = {"utente": c["utente"], "premuto": premuto, "risposta": risposta,
                          "quando": time.time()}
        dati["esito"] = "PICK"
    log(account, f"scelto @{c['utente']} (Reply n.{premuto}) -> \"{risposta}\" ({time.time() - inizio:.1f}s)")
    return f"PICK|{premuto}|0|0|{c['utente']}|{risposta}"


def _prepara(account, elenco):
    """Legge la schermata, decide i commenti nuovi e sceglie il prossimo a cui rispondere."""
    commenti = commenti_da_elenco(elenco)
    dati = dati_account(account)
    dati["attesa"] = None
    firma = tuple(c["utente"] for c in commenti)
    adesso = time.time()
    if dati["esito"] in (None, "END") or adesso - dati["ultimo_pick"] > 120:
        # primo sguardo a un post: la lista parte dall'inizio
        dati["schermo"], dati["da_osservare"] = "inizio", True
        dati["spostamento"] = maggioranza(dati["visti"]["inizio"], 0)
    elif dati["esito"] != "PICK" and firma != dati["ultima"]:
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
    if firma and firma == dati["ultima"] and dati["esito"] != "PICK":
        dati["stallo"] += 1
    elif firma != dati["ultima"]:
        dati["stallo"] = 0
    dati["ultima"] = firma
    dati["nomi"] = {c["numero"]: c["utente"] for c in commenti}

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

    if commenti:
        log(account, f"{nuovi + gia} commenti a schermo"
            + (f" (+{propri} dell'account)" if propri else "")
            + f": {nuovi} nuovi ({scelti} scelti), {gia} gia' visti prima -> da rispondere: {len(candidati)}")
    else:
        log(account, "nessun commento riconosciuto a schermo")

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
        tentativi = dati["tentativi"].get(scelto, 0)
        if motivo:
            if tentativi < 2:
                # si riprova la stessa persona: lo sfasamento ora e' corretto
                dati["tentativi"][scelto] = tentativi + 1
                if not reale and dati["spostamento"] > -2:
                    dati["spostamento"] -= 1  # premuto un Reply oltre l'ultimo a schermo
                log(account, f"{motivo} -> riprovo @{scelto} con un altro Reply")
            else:
                log(account, f"{motivo} -> salto @{scelto}, il prossimo commento nuovo prende il suo posto")
                ricorda(account, scelto, "fallito", motivo)
                rimborsa(dati)
            dati["attesa"] = None
            return "NO_MATCH"
        if reale != scelto:
            log(account, f"il Reply premuto e' di @{reale} (scelto @{scelto}): rispondo a @{reale}")
            if deciso(dati, reale) == "si" and tentativi < 2:
                dati["tentativi"][scelto] = tentativi + 1  # @reale usa il suo posto, @scelto si riprova
            else:
                ricorda(account, scelto, "fallito", f"aperto @{reale}")
        # segnato subito: anche se la conferma finale si perde non gli risponde una seconda volta
        ricorda(account, reale, "in_corso", attesa["risposta"])
        attesa["reale"] = reale
        log(account, f"rispondo a @{reale}")
        return f"@{reale} {attesa['risposta']}"


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
        parametri = parse_qs(url.query)
        account = (parametri.get("acc") or ["Melina Berner Frankfurt"])[0]
        lunghezza = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(lunghezza).decode("utf-8", errors="replace") if lunghezza else ""
        try:
            if url.path == "/pick":
                elenco = unquote(corpo)
                (CARTELLA / "ultima_schermata.txt").write_text(elenco, encoding="utf-8")
                if not elenco.strip():
                    log(account, "il telefono non ha mandato nessun testo")
                    self.rispondi("NO_MATCH")
                else:
                    self.rispondi(scegli(account, elenco))
            elif url.path == "/confirm":
                casella = (parametri.get("u") or [""])[0] or re.sub(r"^u=", "", corpo.strip())
                self.rispondi(conferma(account, casella))
            elif url.path == "/ack":
                self.rispondi(fatto(account))
            elif url.path == "/azzera":
                # solo dal browser del PC, non da internet tramite ngrok
                if self.client_address[0] != "127.0.0.1" or self.headers.get("X-Forwarded-For"):
                    self.rispondi("RELAY_OK")
                else:
                    tenuti, dimenticati = azzera(account)
                    self.rispondi(f"Memoria azzerata per {account}: dimenticate {dimenticati} decisioni, "
                                  f"tenute {tenuti} persone che hanno gia' una risposta. "
                                  "Ora puoi rifare il test.")
            else:
                self.rispondi("RELAY_OK")
        except Exception as e:
            log(account, "errore:", e)
            self.rispondi("NO_MATCH")

    do_GET = gestisci
    do_POST = gestisci

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Relay acceso sulla porta {PORTA}. Lascia questa finestra aperta.")
    ThreadingHTTPServer(("0.0.0.0", PORTA), Gestore).serve_forever()
