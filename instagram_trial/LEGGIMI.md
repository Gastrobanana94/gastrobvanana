# IG TRIAL REEL — pubblica trial reels da GeeLark

File da importare in GeeLark: `IG_TRIAL_REEL_IMPORT.json` (flusso "IG TRIAL REEL v3").
Non serve né il relay né ngrok: fa tutto GeeLark, anche col PC spento.

## Un task = warm-up + un trial reel

Nella pagina "Create task" ci sono:

- **Publish time**: quando parte.
- **Caption**: la descrizione (niente hashtag).
- **Video**: il video (uno solo).
- **SoloProva**: se è acceso fa tutto ma **non preme Share** (e il warm-up dura 1 minuto invece di 7-10).

Un task dura circa **11-14 minuti** (warm-up 7-10 + pubblicazione 3-4).

Per 10 trial reel su un telefono: **Add** il telefono → 10 task (uno per video) → **Upload in order**
(il 1° video al task 1, il 2° al task 2…) → **Bulk schedule** con **intervallo 25 minuti** → **Edit table**
per le descrizioni → **Save**.
Con 25 minuti tra un task e l'altro restano 10-15 minuti di pausa con Instagram chiuso.
10 trial reel ≈ **4 ore** per telefono (i telefoni diversi vanno in parallelo).
Chiama i video `01.mp4 … 10.mp4` (con lo zero).

## Cosa fa

1. Tastiera GeeRunner, permessi a Instagram, svuota la cartella **Download** del telefono e ci mette il video del task.
2. Trova dov'è il video e chiede ad Android se è il video più recente del telefono.
3. Apre Instagram, va sui **Reels** e li guarda scorrendo per **7-10 minuti** (warm-up; ogni reel 4-14 secondi, niente like).
4. Profilo → menu (tre righe) → **Account type and tools** → **Trial reels** → **Create trial reel**
   (se esce il pop-up di spiegazione lo chiude).
5. Galleria: se il video del task è il più recente prende il primo; altrimenti apre il suo album (**Download**),
   dove c'è solo lui → **Next**.
6. Scrive la descrizione, scorre giù e spegne **Facebook solo per questo reel** ("Don't share this reel").
7. **Share**, aspetta che carichi, fa gli screenshot e torna alla **home del telefono**.

## Sicurezza: si ferma con errore e NON pubblica se…

- non vede "This is a trial reel" (in galleria e nella pagina finale);
- non è sicuro di scegliere il video del task (non è il più recente e non trova il suo album);
- non riesce a spegnere Facebook;
- il video non è arrivato sul telefono;
- non è più sulla pagina finale quando deve scorrere.

Non tocca mai: etichetta AI, interruttore Trial, audio, copertina, tag, posizione, "Stop sharing all reels", like.

## Versioni

- v1: prima versione.
- v2 (prova del 7 ottobre su Frankfurt): dopo la descrizione non preme più "indietro" per chiudere la tastiera
  (con la tastiera già chiusa tornava al video e lo scroll apriva il montaggio); prima di ogni scroll controlla
  di essere ancora sulla pagina finale, altrimenti si ferma con `[Pagina finale]`.
- v3: warm-up sui Reels 7-10 minuti; il controllo "il video è arrivato?" non usa più `${...}` (GeeLark lo
  cancellava e il controllo leggeva sempre vuoto); scelta del video: il più recente secondo Android, altrimenti
  il suo album Download (scorrendo la lista degli album); se non trova l'album scrive nel log cosa vede.

## Errori (si vedono nel task di GeeLark)

`[Video]` `[Profilo]` `[Menu]` `[Trial reels]` `[Sicurezza]` `[Galleria]` `[Editor]` `[Descrizione]` `[Pagina finale]` `[Facebook]` `[Share]`:
il testo dice cosa non ha trovato, e c'è lo screenshot del momento.
