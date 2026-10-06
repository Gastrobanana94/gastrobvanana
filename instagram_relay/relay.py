# ==========================================================
#  RELAY INSTAGRAM - risponde ai commenti leggendo il TESTO
#  Il telefono GeeLark legge i testi a schermo con i nodi RPA
#  (For Loop Elements + Get element data), il relay sceglie il commento con
#  il bot Hermes "commentbot" e dice al telefono QUALE "Reply" cliccare.
#  Gira sul tuo PC, ngrok lo rende raggiungibile dal cloud.
# ==========================================================

# ---------- 1) COMPILA QUI (solo questa parte) ----------

# Il bot Hermes "commentbot" (DeepSeek Flash), raggiunto tramite il
# multiplexer del profilo default. La chiave e' la voce API_SERVER_KEY in
# C:\Users\bstaa\AppData\Local\hermes\profiles\commentbot\.env
URL_API = "http://127.0.0.1:8643/p/commentbot/v1/chat/completions"
CHIAVE_API = "INCOLLA_QUI_API_SERVER_KEY_DI_COMMENTBOT"
MODELLO = "commentbot"

PORTA = 8787                 # la stessa porta che dai a ngrok
PERCENTUALE_RISPOSTE = 0.40  # 0.40 = risponde a circa 4 commenti nuovi su 10
TIMEOUT_AI = 25              # secondi massimi di attesa per commentbot

# Lo stile delle risposte lo decide commentbot. Se vuoi aggiungere istruzioni
# per un account specifico crea il file persona_<nome account>.txt nella
# cartella del relay e scrivile li'.
PERSONA = ""

# ---------- 2) DA QUI IN GIU' NON TOCCARE NIENTE ----------

import hashlib
import json
import random
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
    r"\d+[.,]?\d*\s?[kKmM]?|\d+\s?(s|m|h|d|w|y|min|sec|hr|std|tag|tage|wo)\.?)$",
    re.IGNORECASE,
)

lock = threading.Lock()
stato = {}  # per account: memoria, ultima schermata, scelta in attesa


def log(*parti):
    print(time.strftime("%H:%M:%S"), *parti, flush=True)


def slug(account):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", account).strip("_") or "account"


def dati_account(account):
    if account not in stato:
        memoria = {}
        file = CARTELLA_MEMORIA / f"{slug(account)}.txt"
        if file.exists():
            for riga in file.read_text(encoding="utf-8").splitlines():
                parti = riga.split("\t")
                if len(parti) >= 2:
                    memoria[parti[0]] = parti[1]
        stato[account] = {"memoria": memoria, "ultima": None, "attesa": None}
    return stato[account]


def ricorda(account, chiave, esito, utente="", testo=""):
    dati_account(account)["memoria"][chiave] = esito
    riga = "\t".join([chiave, esito, utente, time.strftime("%Y-%m-%d %H:%M:%S"),
                      testo.replace("\t", " ").replace("\n", " ")])
    with open(CARTELLA_MEMORIA / f"{slug(account)}.txt", "a", encoding="utf-8") as f:
        f.write(riga + "\n")


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


def chiave(*parti):
    return hashlib.sha1("|".join(parti).lower().encode("utf-8")).hexdigest()[:16]


def commenti_da_elenco(elenco):
    """Il telefono manda i testi a schermo uno per riga, dall'alto in basso.
    Se tra i testi c'e' "Reply", ogni "Reply" chiude un commento (nome + testo).
    Altrimenti Instagram ha mostrato solo i nomi: il commento N e' quello
    dell'N-esimo nome, che corrisponde all'N-esimo pulsante Reply."""
    righe = []
    for riga in elenco.splitlines():
        riga = re.sub(r"\s+", " ", riga).strip()
        if COMPOSER.match(riga):
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
                if pezzi:
                    utente = next((p for p in pezzi if e_nome(p)), "")
                    corpo = " ".join(p for p in pezzi if p != utente)
                    commenti.append({"numero": numero, "utente": utente, "commento": corpo,
                                     "chiave": chiave(*pezzi)})
                pezzi = []
            elif not RUMORE.match(riga) and riga not in pezzi:
                pezzi.append(riga)
        return commenti

    oggi = time.strftime("%Y-%m-%d")
    nomi = [r for r in righe if e_nome(r)]
    for numero, utente in enumerate(nomi, start=1):
        commenti.append({"numero": numero, "utente": utente, "commento": "",
                         "chiave": chiave(utente, oggi)})
    return commenti


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
    testo = pulisci(testo.strip(" \"'«»“”„"))
    if len(testo) > 200:
        taglio = max(testo.rfind(s, 0, 200) for s in ".!?")
        testo = testo[:taglio + 1] if taglio > 40 else testo[:200]
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
        "breve (massimo 1-2 frasi), senza virgolette, senza @nome e senza altro testo."
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


def nome_utente(testo):
    return re.sub(r"[^a-z0-9._]", "", str(testo or "").lower().lstrip("@"))


def scegli(account, elenco):
    inizio = time.time()
    commenti = commenti_da_elenco(elenco)
    with lock:
        dati = dati_account(account)
        firma = tuple(c["chiave"] for c in commenti)
        if firma and firma == dati["ultima"]:
            log(account, "schermata uguale alla precedente -> END")
            return "END"
        dati["ultima"] = firma

        candidati = []
        for c in commenti:
            if not c["utente"] or e_proprio(account, c["utente"]):
                continue
            esito = dati["memoria"].get(c["chiave"])
            if esito is None:
                esito = "si" if random.random() < PERCENTUALE_RISPOSTE else "skip"
                ricorda(account, c["chiave"], esito, c["utente"], c["commento"])
            if esito == "si":
                candidati.append(c)

    solo_nomi = bool(commenti) and not any(c["commento"] for c in commenti)
    log(account, f"{len(commenti)} commenti a schermo, {len(candidati)} da valutare"
        + (" (letti solo i nomi)" if solo_nomi else "")
        + (" (nessun commento riconosciuto)" if not commenti else ""))
    if not candidati:
        return "NO_MATCH"

    c = random.choice(candidati)
    try:
        risposta = chiedi_risposta(account, c)
    except Exception as e:
        log(account, "commentbot non ha risposto:", e)
        return "NO_MATCH"
    if not risposta:
        with lock:
            ricorda(account, c["chiave"], "scartato_ai", c["utente"], c["commento"])
        return "NO_MATCH"

    utente = nome_utente(c["utente"])
    with lock:
        dati["attesa"] = {"chiave": c["chiave"], "utente": utente,
                          "risposta": risposta, "quando": time.time()}
    log(account, f"scelto @{utente} (Reply n.{c['numero']}) -> \"{risposta}\" ({time.time() - inizio:.1f}s)")
    return f"PICK|{c['numero']}|0|0|{utente}|{risposta}"


def conferma(account, utente_casella):
    with lock:
        dati = dati_account(account)
        attesa = dati["attesa"]
        if not attesa or time.time() - attesa["quando"] > 180:
            log(account, "conferma senza scelta in attesa -> NO_MATCH")
            return "NO_MATCH"
        if nome_utente(utente_casella) != attesa["utente"]:
            log(account, f"NOME SBAGLIATO: casella {utente_casella!r}, scelto @{attesa['utente']} -> NO_MATCH")
            ricorda(account, attesa["chiave"], "nome_sbagliato", attesa["utente"], utente_casella)
            dati["attesa"] = None
            return "NO_MATCH"
        log(account, f"nome confermato @{attesa['utente']}")
        return attesa["risposta"]


def fatto(account):
    with lock:
        dati = dati_account(account)
        attesa = dati["attesa"]
        if attesa:
            ricorda(account, attesa["chiave"], "risposto", attesa["utente"], attesa["risposta"])
            dati["attesa"] = None
            log(account, f"risposta pubblicata a @{attesa['utente']}, salvata in memoria")
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
        account = (parametri.get("acc") or ["account"])[0]
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
                self.rispondi(conferma(account, corpo))
            elif url.path == "/ack":
                self.rispondi(fatto(account))
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
