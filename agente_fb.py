# ==========================================================
#  AGENTE FACEBOOK - Browser Use Cloud + IL TUO PROXY
#  Il browser gira nel cloud (non sul tuo PC, non sul tuo wifi)
#  e si paga con i crediti del sito cloud.browser-use.com
# ==========================================================

# ---------- 1) COMPILA QUI (solo questa parte) ----------

API_KEY = "INCOLLA_QUI_LA_TUA_API_KEY"   # dal sito: pulsante "API key" -> Copy

PROXY_HOST = "123.45.67.89"   # indirizzo del tuo proxy (numeri o nome)
PROXY_PORT = 8080             # porta del tuo proxy (solo numero, senza virgolette)
PROXY_USER = "utente"         # utente del proxy  (se non ce l'hai metti: None)
PROXY_PASS = "password"       # password del proxy (se non ce l'hai metti: None)

NOME_PROFILO = "facebook-mio-proxy"   # nome della "memoria" del browser

# ---------- 2) DA QUI IN GIU' NON TOCCARE NIENTE ----------

from browser_use_sdk import BrowserUse, CustomProxy

client = BrowserUse(api_key=API_KEY)

proxy = CustomProxy(
    host=PROXY_HOST,
    port=PROXY_PORT,
    username=PROXY_USER,
    password=PROXY_PASS,
)


def trova_o_crea_profilo():
    for p in client.profiles.list(query=NOME_PROFILO).items:
        if p.name == NOME_PROFILO:
            return str(p.id)
    return str(client.profiles.create(name=NOME_PROFILO).id)


def login():
    profilo = trova_o_crea_profilo()
    sessione = client.sessions.create(
        profile_id=profilo,
        custom_proxy=proxy,
        start_url="https://www.facebook.com",
        keep_alive=True,
    )
    print()
    print("1) Apri questo link nel tuo browser:")
    print("  ", sessione.live_url)
    print("2) Dentro la pagina che si apre, entra su Facebook con email e password.")
    input("3) Quando sei dentro Facebook, torna qui e premi INVIO... ")
    client.sessions.stop(str(sessione.id))
    print("Fatto! Il login e' salvato. La prossima volta scegli 2.")


def lavora():
    profilo = trova_o_crea_profilo()
    sessione = client.sessions.create(
        profile_id=profilo, custom_proxy=proxy, keep_alive=True
    )
    print()
    print("Browser pronto. Se vuoi guardare l'agente, apri questo link:")
    print("  ", sessione.live_url)
    print()
    print("Scrivi un comando per l'agente e premi INVIO.")
    print("Scrivi  esci  per chiudere (cosi' non consumi crediti).")
    try:
        while True:
            print()
            comando = input("COMANDO > ").strip()
            if not comando:
                continue
            if comando.lower() == "esci":
                break
            print("L'agente sta lavorando, aspetta...")
            risultato = client.run(comando, session_id=str(sessione.id))
            print()
            print("===== RISULTATO =====")
            print(risultato.output)
    finally:
        client.sessions.stop(str(sessione.id))
        print("Browser chiuso.")


print("Cosa vuoi fare?")
print("  1 = Primo accesso a Facebook (lo fai solo la prima volta)")
print("  2 = Dai comandi all'agente (quanti ne vuoi)")
scelta = input("Scrivi 1 o 2 e premi INVIO: ").strip()

if scelta == "1":
    login()
elif scelta == "2":
    lavora()
else:
    print("Devi scrivere 1 oppure 2.")
