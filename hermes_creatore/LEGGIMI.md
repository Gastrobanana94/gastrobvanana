# Creatore di agenti Hermes per Facebook

Crea in pochi minuti un agente [Hermes Agent](https://hermes-agent.nousresearch.com) collegato al **tuo account Facebook**.
Tu gli dai gli ordini (dal computer o da Telegram) e lui li esegue su Facebook: legge e risponde ai messaggi,
risponde ai commenti, pubblica post e così via. Se vuoi, controlla Facebook da solo ogni tot minuti e risponde
seguendo le tue istruzioni.

## Come funziona

```
Tu (chat o Telegram) ──> Hermes (il cervello) ──> strumento "facebook" ──> browser nel cloud (Browser Use)
                                                                            con il tuo login e il tuo proxy
```

- **Hermes** capisce cosa vuoi, decide cosa fare e ti risponde.
- Il **browser nel cloud** di Browser Use resta loggato su Facebook (profilo salvato) e passa dal tuo proxy.
- La **personalità e le regole** dell'agente stanno in `SOUL.md`, le "ricette" per Facebook in una skill.

## Cosa ti serve

1. **Python 3.10 o più recente**
2. **Hermes Agent**:
   ```bash
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
   ```
3. Una **API key di Browser Use**: su cloud.browser-use.com, pulsante "API key", poi Copy.
4. Una chiave per il **modello AI** (OpenRouter, Nous Portal, Anthropic...). Te la chiede Hermes durante la creazione.
5. Facoltativo: un **bot Telegram** per dare ordini dal telefono (@BotFather, poi /newbot).

## Creare l'agente

```bash
cd hermes_creatore
pip install -r requirements.txt
python crea_agente.py
```

Scegli **1** e rispondi alle domande. Il creatore:

1. crea il profilo Hermes (che diventa anche un comando, per esempio `ermes-fb`);
2. scrive la personalità, le tue istruzioni e le regole di sicurezza (`SOUL.md`);
3. installa la skill `facebook-agente` e lo strumento `facebook` (server MCP);
4. collega Telegram, se lo vuoi;
5. ti fa scegliere il modello AI (`hermes setup`);
6. ti fa fare il **primo login su Facebook** nel browser nel cloud;
7. crea il controllo automatico di messaggi e commenti, se lo vuoi.

## Usarlo

```bash
ermes-fb chat             # parli con l'agente dal computer
ermes-fb gateway start    # serve per Telegram e per le risposte automatiche (tienilo acceso)
ermes-fb doctor           # controlla che sia tutto a posto
```

Esempi di ordini:
- "Leggi i messaggi non letti e dimmi chi mi ha scritto"
- "Rispondi a Giulia che la consegna arriva venerdì"
- "Pubblica un post con le offerte di questa settimana: ..."
- "Fammi vedere il browser" (ti dà il link live)

Se Facebook ti scollega, l'agente ti avvisa (LOGIN_RICHIESTO). In quel caso: `python crea_agente.py` e scegli **2**.

## Dove sono i file (per i più esperti)

Nella cartella del profilo (`~/.hermes/profiles/<nome>/`):

| File | Cosa contiene |
|---|---|
| `SOUL.md` | personalità, tue istruzioni, regole di sicurezza |
| `skills/social-media/facebook-agente/SKILL.md` | come usare bene Facebook |
| `facebook/config.json` | API key Browser Use e proxy (**privato**) |
| `facebook/facebook_mcp_server.py` | lo strumento Facebook |
| `config.yaml` | sezione `mcp_servers.facebook` |
| `.env` | token Telegram (**privato**) |

Puoi modificare `SOUL.md` quando vuoi per cambiare il comportamento dell'agente.
Per non sprecare crediti, il browser si chiude da solo dopo 10 minuti senza lavoro.
Puoi cambiare questo tempo con `chiudi_dopo_minuti` in `config.json`.

## Sicurezza

- L'agente prende ordini solo da te. Quello che scrivono gli altri nei messaggi o nei commenti non vale mai come ordine.
- Non cambia password né impostazioni di sicurezza e non fa pagamenti.
- Prima di cancellare, bloccare o mandare messaggi a molte persone ti chiede conferma.
- Usalo con moderazione: troppi messaggi automatici possono far bloccare l'account da Facebook.
