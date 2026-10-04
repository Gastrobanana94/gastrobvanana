# Creatore di agenti Hermes per Facebook (con Brave)

Crea un agente [Hermes Agent](https://hermes-agent.nousresearch.com) che usa **il tuo Brave sul tuo PC**,
con **il tuo proxy**, per lavorare sul **tuo account Facebook**. Tu gli dai gli ordini e lui li esegue:
legge e risponde ai messaggi, risponde ai commenti, pubblica post e così via.

```
Tu ──> Hermes (il cervello) ──> Brave dell'agente sul tuo PC ──> il tuo proxy ──> Facebook
```

- Brave dell'agente ha una **memoria separata** dal tuo Brave normale: il login a Facebook resta salvato lì.
- Il **proxy** è impostato dentro Brave. Funziona anche con utente e password, sia HTTP sia SOCKS5.
- Telegram lo colleghi tu quando vuoi: il creatore non lo tocca.

## Installazione su Windows (passo per passo)

**1. Installa Hermes Agent.** Apri **PowerShell** e incolla:
```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```
Quando ha finito, chiudi PowerShell.

**2. Scarica il creatore.** Apri il **Prompt dei comandi** (cmd) e incolla queste righe:
```bat
cd %USERPROFILE%
mkdir hermes_creatore
cd hermes_creatore
curl -LO https://raw.githubusercontent.com/gastrobanana94/gastrobvanana/claude/lucid-newton-b982ou/hermes_creatore/crea_agente.py
curl -LO https://raw.githubusercontent.com/gastrobanana94/gastrobvanana/claude/lucid-newton-b982ou/hermes_creatore/avvia_brave.py
curl -LO https://raw.githubusercontent.com/gastrobanana94/gastrobvanana/claude/lucid-newton-b982ou/hermes_creatore/requirements.txt
pip install -r requirements.txt
```

**3. Crea l'agente:**
```bat
python crea_agente.py
```
Scegli **1** e rispondi alle domande: nome, le tue istruzioni e il proxy. Il creatore:
1. crea l'agente in Hermes;
2. scrive la sua personalità, le tue istruzioni e le regole di sicurezza;
3. lo collega al Brave dell'agente, con il tuo proxy;
4. ti fa scegliere il modello AI (Telegram puoi saltarlo);
5. apre Brave: **entra su Facebook a mano una volta**, il login resta salvato.

Ti servono **Brave** (https://brave.com/download/) e una chiave per un modello AI (OpenRouter, Nous Portal, Anthropic...).

## Usarlo ogni giorno

Nella cartella `hermes_creatore` trovi due file da doppio clic:

1. **`AVVIA_BRAVE_<nome>.bat`** apre Brave dell'agente con il proxy. **Lascia aperta quella finestra nera.**
2. **`PARLA_CON_<nome>.bat`** apre la chat con l'agente.

Esempi di ordini:
- "Leggi i messaggi non letti e dimmi chi mi ha scritto"
- "Rispondi a Giulia che la consegna arriva venerdì"
- "Pubblica un post con le offerte di questa settimana: ..."

Mentre lavora puoi guardare Brave e vedere cosa fa.

Se hai attivato le **risposte automatiche** o colleghi **Telegram**, tieni acceso anche `hermes -p <nome> gateway start`.

## Problemi comuni

| Problema | Soluzione |
|---|---|
| "Non trovo Brave" | Installa Brave, oppure scrivi il percorso di `brave.exe` in `percorso_brave` dentro `brave_config.json` |
| L'agente dice che il browser non risponde | Doppio clic su `AVVIA_BRAVE_<nome>.bat` |
| Facebook chiede di nuovo il login | Entra a mano nella finestra di Brave dell'agente |
| Vuoi cambiare istruzioni o proxy | Rilancia `python crea_agente.py`, scegli 1 e usa lo stesso nome |

## Dove sono i file (per i più esperti)

Nella cartella del profilo Hermes (su Windows `%LOCALAPPDATA%\hermes\profiles\<nome>\`):

| File | Cosa contiene |
|---|---|
| `SOUL.md` | personalità, tue istruzioni, regole di sicurezza (puoi modificarlo) |
| `skills/social-media/facebook-agente/SKILL.md` | come usare bene Facebook |
| `config.yaml` | `browser.cdp_url`: l'indirizzo del Brave dell'agente |
| `facebook/brave_config.json` | proxy e porta di controllo (**privato**) |
| `facebook/brave-memoria/` | la memoria di Brave dell'agente (login di Facebook) |

## Sicurezza

- L'agente prende ordini solo da te. Quello che scrivono gli altri nei messaggi o nei commenti non vale mai come ordine.
- Non cambia password né impostazioni di sicurezza e non fa pagamenti.
- Prima di cancellare, bloccare o mandare messaggi a molte persone ti chiede conferma.
- La porta di controllo di Brave è aperta solo sul tuo PC (127.0.0.1).
- Usalo con moderazione: troppi messaggi automatici possono far bloccare l'account da Facebook.
