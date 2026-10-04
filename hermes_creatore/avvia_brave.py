# ==========================================================
#  AVVIA BRAVE PER L'AGENTE HERMES
#  Apre Brave con:
#   - una "memoria" separata solo per l'agente (il login a Facebook resta salvato)
#   - il TUO proxy
#   - la porta di controllo che Hermes usa per guidare il browser
#
#  Avvio:  python avvia_brave.py CONFIG.json
#  (il creatore ti prepara un file .bat: fai doppio clic su quello)
#  LASCIA APERTA questa finestra finche' l'agente lavora.
# ==========================================================

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from urllib.parse import urlparse
from pathlib import Path


# ---------------------- trovare Brave ----------------------

def trova_brave(percorso_scelto=None):
    if percorso_scelto and Path(percorso_scelto).exists():
        return percorso_scelto
    candidati = []
    if sys.platform == "win32":
        for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(var)
            if base:
                candidati.append(Path(base) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe")
    elif sys.platform == "darwin":
        candidati.append(Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"))
    else:
        for nome in ("brave-browser", "brave", "brave-browser-stable"):
            trovato = shutil.which(nome)
            if trovato:
                candidati.append(Path(trovato))
        candidati += [Path("/opt/brave.com/brave/brave"), Path("/snap/bin/brave")]
    for c in candidati:
        if c.exists():
            return str(c)
    return None


# ---------------------- proxy locale con password ----------------------
# Brave (come Chrome) non accetta utente e password del proxy dalla riga di comando.
# Allora apriamo un piccolo proxy sul tuo PC (127.0.0.1) che aggiunge lui
# utente e password e passa tutto al tuo proxy vero.

def _leggi_testata(sock):
    dati = b""
    while b"\r\n\r\n" not in dati:
        pezzo = sock.recv(65536)
        if not pezzo:
            return None, b""
        dati += pezzo
        if len(dati) > 1024 * 1024:
            return None, b""
    testata, resto = dati.split(b"\r\n\r\n", 1)
    return testata.decode("latin-1"), resto


def _tubo(da, a):
    try:
        while True:
            pezzo = da.recv(65536)
            if not pezzo:
                break
            a.sendall(pezzo)
    except OSError:
        pass
    finally:
        for s in (da, a):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def _ricevi_esatti(sock, n):
    dati = b""
    while len(dati) < n:
        pezzo = sock.recv(n - len(dati))
        if not pezzo:
            raise OSError("connessione chiusa dal proxy")
        dati += pezzo
    return dati


def _socks5_connetti(px, host, porta):
    s = socket.create_connection((px["host"], int(px["port"])), timeout=30)
    if px.get("user"):
        s.sendall(b"\x05\x01\x02")
        if _ricevi_esatti(s, 2)[1] != 2:
            raise OSError("il proxy SOCKS5 non accetta utente e password")
        u, p = px["user"].encode(), (px.get("pass") or "").encode()
        s.sendall(b"\x01" + bytes([len(u)]) + u + bytes([len(p)]) + p)
        if _ricevi_esatti(s, 2)[1] != 0:
            raise OSError("utente o password del proxy SOCKS5 sbagliati")
    else:
        s.sendall(b"\x05\x01\x00")
        if _ricevi_esatti(s, 2)[1] != 0:
            raise OSError("il proxy SOCKS5 rifiuta la connessione")
    h = host.encode("idna")
    s.sendall(b"\x05\x01\x00\x03" + bytes([len(h)]) + h + int(porta).to_bytes(2, "big"))
    risposta = _ricevi_esatti(s, 4)
    if risposta[1] != 0:
        raise OSError(f"il proxy SOCKS5 non riesce a raggiungere {host}:{porta}")
    tipo = risposta[3]
    lunghezza = 4 if tipo == 1 else 16 if tipo == 4 else _ricevi_esatti(s, 1)[0]
    _ricevi_esatti(s, lunghezza + 2)
    s.settimeout(None)
    return s


def _gestisci_cliente(cliente, px):
    try:
        testata, resto = _leggi_testata(cliente)
        if not testata:
            cliente.close()
            return
        righe = testata.split("\r\n")
        metodo, indirizzo, versione = righe[0].split(" ", 2)
        intestazioni = [r for r in righe[1:] if r and not r.lower().startswith(
            ("proxy-authorization:", "proxy-connection:", "connection:"))]

        if px["tipo"] == "socks5":
            if metodo.upper() == "CONNECT":
                host, porta = indirizzo.rsplit(":", 1)
                remoto = _socks5_connetti(px, host.strip("[]"), porta)
                cliente.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            else:
                url = urlparse(indirizzo)
                remoto = _socks5_connetti(px, url.hostname, url.port or 80)
                percorso = (url.path or "/") + (f"?{url.query}" if url.query else "")
                nuova = [f"{metodo} {percorso} {versione}"] + intestazioni + ["Connection: close"]
                remoto.sendall(("\r\n".join(nuova) + "\r\n\r\n").encode("latin-1") + resto)
        else:
            remoto = socket.create_connection((px["host"], int(px["port"])), timeout=30)
            remoto.settimeout(None)
            nuova = [righe[0]] + intestazioni
            if px.get("user"):
                chiave = base64.b64encode(f"{px['user']}:{px.get('pass') or ''}".encode()).decode()
                nuova.append(f"Proxy-Authorization: Basic {chiave}")
            if metodo.upper() != "CONNECT":
                nuova.append("Connection: close")
            remoto.sendall(("\r\n".join(nuova) + "\r\n\r\n").encode("latin-1") + resto)

        threading.Thread(target=_tubo, args=(cliente, remoto), daemon=True).start()
        _tubo(remoto, cliente)
    except Exception as errore:
        try:
            cliente.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/plain\r\n\r\n"
                            + f"Errore proxy: {errore}".encode())
        except OSError:
            pass
        cliente.close()


def avvia_proxy_locale(px):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(200)
    porta = server.getsockname()[1]

    def ascolta():
        while True:
            cliente, _ = server.accept()
            threading.Thread(target=_gestisci_cliente, args=(cliente, px), daemon=True).start()

    threading.Thread(target=ascolta, daemon=True).start()
    return porta


def regola_proxy(px):
    """Restituisce il valore per --proxy-server di Brave."""
    if not px or not px.get("host"):
        return None
    serve_ponte = bool(px.get("user")) or px.get("tipo") == "socks5"
    if serve_ponte:
        return f"http://127.0.0.1:{avvia_proxy_locale(px)}"
    return f"http://{px['host']}:{int(px['port'])}"


# ---------------------- avvio ----------------------

def porta_pronta(porta):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def main(file_cfg):
    cfg = json.loads(Path(file_cfg).read_text(encoding="utf-8"))
    porta = int(cfg.get("porta_controllo", 9222))

    if porta_pronta(porta):
        print(f"Brave dell'agente e' gia' aperto (porta {porta}). Non serve fare altro.")
        return

    brave = trova_brave(cfg.get("percorso_brave"))
    if not brave:
        print("Non trovo Brave. Installalo da https://brave.com/download/")
        print("oppure scrivi il percorso di brave.exe in 'percorso_brave' dentro:")
        print("  ", file_cfg)
        input("Premi INVIO per chiudere...")
        return

    memoria = Path(cfg["cartella_memoria"])
    memoria.mkdir(parents=True, exist_ok=True)
    comando = [
        brave,
        f"--user-data-dir={memoria}",
        f"--remote-debugging-port={porta}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        # Evita che il vero indirizzo IP esca dalle chiamate WebRTC (lo nasconde il proxy)
        "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
        "--webrtc-ip-handling-policy=disable_non_proxied_udp",
    ]
    proxy = regola_proxy(cfg.get("proxy"))
    if proxy:
        comando.append(f"--proxy-server={proxy}")
        comando.append("--proxy-bypass-list=<-loopback>")
    comando.append(cfg.get("pagina_iniziale", "https://www.facebook.com"))

    processo = subprocess.Popen(comando)
    for _ in range(60):
        if porta_pronta(porta):
            break
        time.sleep(0.5)
    else:
        print("Brave si e' aperto ma la porta di controllo non risponde.")
        print("Chiudi TUTTE le finestre di Brave dell'agente e riprova.")

    print()
    print("Brave dell'agente e' APERTO.")
    if proxy:
        print("Sta usando il tuo proxy. Per controllare, apri https://whatismyipaddress.com")
    print("La prima volta entra su Facebook a mano: il login resta salvato.")
    print()
    print(">>> LASCIA APERTA QUESTA FINESTRA finche' l'agente lavora. <<<")
    print("Per spegnere: chiudi Brave (o premi CTRL+C qui).")
    try:
        processo.wait()
        # Su alcuni sistemi Brave passa il lavoro a un altro processo:
        # restiamo accesi (per il proxy) finche' la porta di controllo risponde.
        while porta_pronta(porta):
            time.sleep(5)
    except KeyboardInterrupt:
        processo.terminate()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python avvia_brave.py CONFIG.json")
        sys.exit(1)
    main(sys.argv[1])
