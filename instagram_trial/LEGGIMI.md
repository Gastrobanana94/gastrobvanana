# IG TRIAL REEL — pubblica trial reels da GeeLark

File da importare in GeeLark: `IG_TRIAL_REEL_IMPORT.json` (flusso "IG TRIAL REEL v2").
Non serve né il relay né ngrok: fa tutto GeeLark, anche col PC spento.

## Un task = un trial reel

Nella pagina "Create task" ci sono:

- **Publish time**: quando pubblicarlo.
- **Caption**: la descrizione (niente hashtag).
- **Video**: il video (uno solo).
- **SoloProva**: se è acceso fa tutto ma **non preme Share** (per vedere come si muove).

Per tanti video: **Add** il telefono → un task per video → **Upload in order** (il 1° video al task 1, il 2° al task 2…)
→ **Bulk schedule** → **Edit table** per le descrizioni → **Save**.
Chiama i video `01.mp4 … 10.mp4` (con lo zero) e lascia almeno 15 minuti tra due task sullo stesso telefono.

## Cosa fa

1. Tastiera GeeRunner, permessi a Instagram, svuota la cartella **Download** del telefono e ci mette il video del task.
2. Apre Instagram → Profilo → menu (tre righe) → **Account type and tools** → **Trial reels** → **Create trial reel**
   (se esce il pop-up di spiegazione lo chiude).
3. Galleria: sceglie l'album **Download** (lì c'è solo il video del task) e tocca il video → **Next**.
4. Scrive la descrizione, scorre giù e spegne **Facebook solo per questo reel** ("Don't share this reel").
5. **Share**, poi aspetta che carichi e fa gli screenshot.

## Sicurezza: si ferma con errore e NON pubblica se…

- non vede "This is a trial reel" (in galleria e nella pagina finale);
- non trova l'album Download (non sceglie un video a caso);
- non riesce a spegnere Facebook;
- il video non è arrivato sul telefono.

Non tocca mai: etichetta AI, interruttore Trial, audio, copertina, tag, posizione, "Stop sharing all reels".

## Versioni

- v1: prima versione.
- v2 (prova del 7 ottobre su Frankfurt): dopo la descrizione non preme più "indietro" per chiudere la tastiera
  (con la tastiera già chiusa tornava al video e lo scroll apriva il montaggio); prima di ogni scroll controlla
  di essere ancora sulla pagina finale, altrimenti si ferma con `[Pagina finale]`.

## Errori (si vedono nel task di GeeLark)

`[Video]` `[Profilo]` `[Menu]` `[Trial reels]` `[Sicurezza]` `[Galleria]` `[Editor]` `[Descrizione]` `[Pagina finale]` `[Facebook]` `[Share]`:
il testo dice cosa non ha trovato, e c'è lo screenshot del momento.
