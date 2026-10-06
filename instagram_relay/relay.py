# ==========================================================
#  RELAY INSTAGRAM - risponde ai commenti leggendo il TESTO
#  Il telefono GeeLark manda l'elenco di cosa c'e' a schermo
#  (uiautomator dump), il relay sceglie il commento con
#  il bot Hermes "commentbot" e dice al telefono DOVE cliccare "Reply".
#  Gira sul tuo PC, ngrok lo rende raggiungibile dal cloud.
# ==========================================================

# ---------- 1) COMPILA QUI (solo questa parte) ----------

# Il bot Hermes "commentbot" (che usa DeepSeek Flash). Sono i valori
# API_SERVER_PORT e API_SERVER_KEY del file .env del profilo commentbot
# (di solito in ~/.hermes/profiles/commentbot/.env).
URL_API = "http://127.0.0.1:8642/v1/chat/completions"
CHIAVE_API = "INCOLLA_QUI_API_SERVER_KEY_DI_COMMENTBOT"
MODELLO = "commentbot"

PORTA = 8787                 # la stessa porta che dai a ngrok
PERCENTUALE_RISPOSTE = 0.40  # 0.40 = risponde a circa 4 commenti nuovi su 10
TIMEOUT_AI = 25              # secondi massimi di attesa per commentbot

# Come deve rispondere l'account. Per un account specifico crea il file
# persona_<nome account>.txt nella cartella del relay e scrivilo li'.
PERSONA = (
    "Sei la persona proprietaria di questo profilo Instagram e rispondi ai "
    "commenti sotto i tuoi post. Rispondi nella stessa lingua del commento, "
    "in modo breve (massimo 1-2 frasi), naturale e simpatico, come farebbe "
    "una persona vera. Puoi usare al massimo un'emoji."
)

# ---------- 2) DA QUI IN GIU' NON TOCCARE NIENTE ----------

import hashlib
import json
import random
import re
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CARTELLA = Path(__file__).resolve().parent
CARTELLA_MEMORIA = CARTELLA / "memoria"
CARTELLA_MEMORIA.mkdir(exist_ok=True)

PAROLE_REPLY = {"reply", "rispondi", "antworten", "responder", "répondre", "repondre"}
PAROLE_COMPOSER = ("add a comment", "aggiungi un commento", "kommentar hinzufügen",
                   "kommentieren", "reply to", "rispondi a", "antworten an")
RUMORE = re.compile(
    r"^(like|mi piace|gefällt mir|reply|rispondi|antworten|see translation|"
    r"visualizza traduzione|übersetzung anzeigen|author|autore|autor|"
    r"liked by creator|view \d+ more repl(y|ies)|hide replies|"
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


def leggi_bounds(b):
    n = [int(x) for x in re.findall(r"-?\d+", b or "")]
    return tuple(n) if len(n) == 4 else None


def commenti_a_schermo(xml_testo):
    """Raggruppa il testo a schermo in commenti, ognuno col suo pulsante Reply."""
    radice = ET.fromstring(xml_testo)
    nodi = []
    for n in radice.iter("node"):
        bb = leggi_bounds(n.get("bounds"))
        if not bb or bb[2] <= bb[0] or bb[3] <= bb[1]:
            continue
        nodi.append({
            "testo": (n.get("text") or "").strip(),
            "desc": (n.get("content-desc") or "").strip(),
            "id": n.get("resource-id") or "",
            "bb": bb,
        })

    # dove inizia la casella "Add a comment": sotto di li' non c'e' lista
    fondo = 10 ** 6
    for n in nodi:
        etichetta = (n["testo"] + " " + n["desc"]).lower()
        if n["id"].endswith("layout_comment_thread_edittext") or any(p in etichetta for p in PAROLE_COMPOSER):
            fondo = min(fondo, n["bb"][1])

    pulsanti = []
    for n in nodi:
        if n["testo"].lower() in PAROLE_REPLY or n["desc"].lower() in PAROLE_REPLY:
            x1, y1, x2, y2 = n["bb"]
            if y2 <= fondo and not any(abs(p[1] - y1) < 15 and abs(p[0] - x1) < 40 for p in pulsanti):
                pulsanti.append(n["bb"])
    pulsanti.sort(key=lambda b: b[1])

    commenti = []
    sopra = None
    for numero, (x1, y1, x2, y2) in enumerate(pulsanti, start=1):
        inizio = sopra if sopra is not None else y1 - 500
        pezzi = []
        for n in nodi:
            nx1, ny1, nx2, ny2 = n["bb"]
            centro_y = (ny1 + ny2) / 2
            if ny2 - ny1 > 500 or not (inizio < centro_y < y1 + 5):
                continue
            for valore in (n["testo"], n["desc"]):
                valore = re.sub(r"\s+", " ", valore).strip()
                if valore and not RUMORE.match(valore) and valore not in pezzi:
                    pezzi.append(valore)
        sopra = y2
        if not pezzi:
            continue
        testo = " | ".join(pezzi)
        commenti.append({
            "numero": numero,
            "x": (x1 + x2) // 2,
            "y": (y1 + y2) // 2,
            "testo": testo,
            "chiave": hashlib.sha1(testo.lower().encode("utf-8")).hexdigest()[:16],
        })
    return commenti


def chiedi_a_commentbot(account, candidati):
    elenco = "\n".join(f"[{i}] {c['testo']}" for i, c in enumerate(candidati, start=1))
    istruzioni = (
        persona(account) + "\n\n"
        "Ti do alcuni commenti letti dallo schermo dell'app (ogni riga contiene "
        "il nome utente e il testo del commento, a volte con pezzi di interfaccia). "
        "Scegline UNO a cui rispondere. Salta i commenti scritti dal proprietario "
        "del profilo, lo spam, i commenti offensivi e quelli incomprensibili.\n"
        'Rispondi SOLO con JSON: {"scelta": numero, "utente": "nome utente '
        'esatto del commento scelto, senza @", "risposta": "testo"} '
        'oppure {"scelta": 0} se nessuno va bene.'
    )
    corpo = json.dumps({
        "model": MODELLO,
        "messages": [
            {"role": "system", "content": istruzioni},
            {"role": "user", "content": elenco},
        ],
        "stream": False,
    }).encode("utf-8")
    richiesta = urllib.request.Request(URL_API, data=corpo, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHIAVE_API}",
    })
    with urllib.request.urlopen(richiesta, timeout=TIMEOUT_AI) as r:
        risposta = json.loads(r.read().decode("utf-8"))
    contenuto = risposta["choices"][0]["message"]["content"]
    trovato = re.search(r"\{.*\}", contenuto, re.DOTALL)
    return json.loads(trovato.group(0) if trovato else contenuto)


def pulisci(testo):
    return re.sub(r"\s+", " ", str(testo or "")).replace("|", "/").strip()


def nome_utente(testo):
    return re.sub(r"[^a-z0-9._]", "", str(testo or "").lower().lstrip("@"))


def scegli(account, xml_testo):
    inizio = time.time()
    commenti = commenti_a_schermo(xml_testo)
    with lock:
        dati = dati_account(account)
        firma = tuple(c["chiave"] for c in commenti)
        if firma and firma == dati["ultima"]:
            log(account, "schermata uguale alla precedente -> END")
            return "END"
        dati["ultima"] = firma

        candidati = []
        for c in commenti:
            esito = dati["memoria"].get(c["chiave"])
            if esito is None:
                esito = "si" if random.random() < PERCENTUALE_RISPOSTE else "skip"
                ricorda(account, c["chiave"], esito, testo=c["testo"])
            if esito == "si":
                candidati.append(c)

    log(account, f"{len(commenti)} commenti a schermo, {len(candidati)} da valutare")
    if not candidati:
        return "NO_MATCH"

    try:
        scelta = chiedi_a_commentbot(account, candidati)
    except Exception as e:
        log(account, "commentbot non ha risposto:", e)
        return "NO_MATCH"

    indice = int(scelta.get("scelta") or 0)
    if not 1 <= indice <= len(candidati):
        with lock:
            for c in candidati:
                ricorda(account, c["chiave"], "scartato_ai", testo=c["testo"])
        log(account, f"nessun commento adatto ({time.time() - inizio:.1f}s)")
        return "NO_MATCH"

    c = candidati[indice - 1]
    utente = nome_utente(scelta.get("utente"))
    risposta = pulisci(scelta.get("risposta"))
    if not utente or not risposta:
        return "NO_MATCH"
    with lock:
        dati["attesa"] = {"chiave": c["chiave"], "utente": utente,
                          "risposta": risposta, "quando": time.time()}
    log(account, f"scelto @{utente} -> \"{risposta}\" ({time.time() - inizio:.1f}s)")
    return f"PICK|{c['numero']}|{c['x']}|{c['y']}|{utente}|{risposta}"


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
                if "<hierarchy" not in corpo:
                    log(account, "il telefono non ha mandato la schermata (dump vuoto)")
                    self.rispondi("NO_MATCH")
                else:
                    self.rispondi(scegli(account, corpo))
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
