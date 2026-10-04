# ==========================================================
#  SERVER MCP "FACEBOOK" PER HERMES AGENT
#  Da' a Hermes gli strumenti per usare il TUO account Facebook
#  tramite un browser nel cloud (Browser Use Cloud) che resta
#  loggato grazie a un profilo salvato, con il TUO proxy.
#
#  Non lo avvii tu a mano: lo avvia Hermes da solo.
#  A mano servono solo:
#     python facebook_mcp_server.py --login  CONFIG.json   (primo accesso)
#     python facebook_mcp_server.py --prova  CONFIG.json   (controllo chiave)
# ==========================================================

import asyncio
import json
import sys
import threading
import time
from pathlib import Path

from browser_use_sdk import BrowserUse, CustomProxy

ISTRUZIONI_BROWSER = (
    "Stai usando il browser di una persona che e' GIA' loggata su Facebook "
    "(www.facebook.com). Non uscire mai dall'account, non cambiare password, "
    "email o impostazioni di sicurezza, non fare pagamenti. "
    "Se Facebook chiede di rifare il login o un codice di verifica, FERMATI "
    "e scrivi nel risultato: LOGIN_RICHIESTO. "
    "Alla fine scrivi in italiano, in modo chiaro, cosa hai fatto e cosa hai visto."
)


def carica_config(percorso):
    cfg = json.loads(Path(percorso).read_text(encoding="utf-8"))
    cfg.setdefault("profilo_browser", "facebook-hermes")
    cfg.setdefault("proxy", None)
    cfg.setdefault("paese_proxy", "it")
    cfg.setdefault("chiudi_dopo_minuti", 10)
    cfg.setdefault("passi_massimi", 60)
    return cfg


class BrowserFacebook:
    """Una sola sessione di browser alla volta, riusata tra un comando e l'altro."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.client = BrowserUse(api_key=cfg["api_key"])
        self.sessione_id = None
        self.live_url = None
        self.ultimo_uso = 0.0
        self.lock = threading.Lock()
        threading.Thread(target=self._chiusura_automatica, daemon=True).start()

    # ---------- profilo e sessione ----------

    def profilo_id(self):
        nome = self.cfg["profilo_browser"]
        for p in self.client.profiles.list(query=nome).items:
            if p.name == nome:
                return str(p.id)
        return str(self.client.profiles.create(name=nome).id)

    def _opzioni_rete(self):
        px = self.cfg.get("proxy")
        if px and px.get("host"):
            return {
                "custom_proxy": CustomProxy(
                    host=px["host"],
                    port=int(px["port"]),
                    username=px.get("user") or None,
                    password=px.get("pass") or None,
                )
            }
        return {"proxy_country_code": self.cfg["paese_proxy"]}

    def nuova_sessione(self, start_url=None):
        s = self.client.sessions.create(
            profile_id=self.profilo_id(),
            keep_alive=True,
            start_url=start_url,
            **self._opzioni_rete(),
        )
        return str(s.id), s.live_url

    def _apri_se_serve(self):
        if self.sessione_id:
            try:
                stato = self.client.sessions.get(self.sessione_id).status
                if str(getattr(stato, "value", stato)).lower() == "active":
                    return
            except Exception:
                pass
            self.sessione_id = None
        self.sessione_id, self.live_url = self.nuova_sessione()

    def chiudi(self):
        if self.sessione_id:
            try:
                self.client.sessions.stop(self.sessione_id)
            except Exception:
                pass
        self.sessione_id = None
        self.live_url = None

    def _chiusura_automatica(self):
        # Chiude il browser se nessuno lo usa da un po': cosi' non consumi crediti.
        limite = float(self.cfg["chiudi_dopo_minuti"]) * 60
        while True:
            time.sleep(30)
            if self.sessione_id and time.time() - self.ultimo_uso > limite:
                if self.lock.acquire(blocking=False):
                    try:
                        self.chiudi()
                    finally:
                        self.lock.release()

    # ---------- lavoro ----------

    def esegui(self, istruzione):
        with self.lock:
            self.ultimo_uso = time.time()
            for tentativo in range(2):
                try:
                    self._apri_se_serve()
                    risultato = self.client.run(
                        istruzione,
                        session_id=self.sessione_id,
                        max_steps=int(self.cfg["passi_massimi"]),
                        system_prompt_extension=ISTRUZIONI_BROWSER,
                    )
                    self.ultimo_uso = time.time()
                    return str(risultato.output or "(nessun risultato testuale)")
                except Exception as errore:
                    # La sessione puo' essere scaduta: la riapro una volta sola.
                    self.sessione_id = None
                    if tentativo == 1:
                        return f"ERRORE durante il lavoro su Facebook: {errore}"


# ==========================================================
#  STRUMENTI CHE HERMES VEDE
# ==========================================================

def crea_server(cfg):
    try:
        from mcp.server.mcpserver import MCPServer as Server  # mcp 2.x
    except ImportError:
        from mcp.server.fastmcp import FastMCP as Server  # mcp 1.x

    browser = BrowserFacebook(cfg)
    server = Server(
        "facebook",
        instructions=(
            "Strumenti per agire sull'account Facebook dell'utente, gia' loggato, "
            "tramite un browser nel cloud. Usa facebook_esegui per qualsiasi azione "
            "su Facebook (leggere/rispondere messaggi e commenti, pubblicare, cercare...)."
        ),
    )

    @server.tool()
    async def facebook_esegui(istruzione: str) -> str:
        """Esegue un'azione sull'account Facebook dell'utente (gia' loggato).

        Scrivi l'istruzione in modo preciso e completo, come la daresti a una persona
        davanti al computer. Esempi:
        - "Apri Messenger, leggi le conversazioni non lette e riportami mittente e testo."
        - "Rispondi a Mario Rossi su Messenger con: 'Ciao Mario, domani alle 10 va bene.'"
        - "Pubblica sulla pagina 'Pizzeria Da Gino' questo post: '...'."
        Restituisce il resoconto di cosa e' stato fatto e visto.
        Se il resoconto contiene LOGIN_RICHIESTO, avvisa l'utente che deve rifare il login.
        """
        return await asyncio.to_thread(browser.esegui, istruzione)

    @server.tool()
    async def facebook_link_live() -> str:
        """Restituisce il link per guardare dal vivo il browser che usa Facebook."""
        def _link():
            with browser.lock:
                browser._apri_se_serve()
                browser.ultimo_uso = time.time()
                return browser.live_url or "Link non disponibile."
        return await asyncio.to_thread(_link)

    @server.tool()
    async def facebook_chiudi_browser() -> str:
        """Chiude il browser nel cloud per non consumare crediti. Si riapre da solo al prossimo comando."""
        def _chiudi():
            with browser.lock:
                browser.chiudi()
            return "Browser chiuso."
        return await asyncio.to_thread(_chiudi)

    return server


# ==========================================================
#  USO A MANO: primo login e controllo
# ==========================================================

def login(cfg):
    browser = BrowserFacebook(cfg)
    sessione_id, live_url = browser.nuova_sessione(start_url="https://www.facebook.com")
    print()
    print("1) Apri questo link nel tuo browser:")
    print("  ", live_url)
    print("2) Dentro la pagina che si apre, entra su Facebook con email e password")
    print("   (e il codice di verifica, se te lo chiede).")
    input("3) Quando vedi la tua home di Facebook, torna qui e premi INVIO... ")
    browser.client.sessions.stop(sessione_id)
    print("Fatto! Il login e' salvato nel profilo del browser.")


def prova(cfg):
    client = BrowserUse(api_key=cfg["api_key"])
    client.profiles.list(query=cfg["profilo_browser"])
    print("OK: la chiave di Browser Use funziona.")


if __name__ == "__main__":
    argomenti = sys.argv[1:]
    if len(argomenti) == 2 and argomenti[0] == "--login":
        login(carica_config(argomenti[1]))
    elif len(argomenti) == 2 and argomenti[0] == "--prova":
        prova(carica_config(argomenti[1]))
    elif len(argomenti) == 1:
        crea_server(carica_config(argomenti[0])).run()
    else:
        print("Uso: python facebook_mcp_server.py [--login|--prova] CONFIG.json")
        sys.exit(1)
