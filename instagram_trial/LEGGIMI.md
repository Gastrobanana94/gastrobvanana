# IG TRIAL REEL — pubblica trial reels da GeeLark

File da importare in GeeLark: `IG_TRIAL_REEL_IMPORT.json` (flusso "IG TRIAL REEL v5").
Non serve né il relay né ngrok: fa tutto GeeLark, anche col PC spento.

## Un task = giro di 3-5 minuti + un trial reel

Nella pagina "Create task" ci sono:

- **Publish time**: quando parte.
- **Caption**: la descrizione (niente hashtag).
- **Video**: il video (uno solo).
- **SoloProva**: se è acceso fa tutto ma **non preme Share** (e il giro dura 1 minuto invece di 3-5).

Un task dura circa **6,5-8,5 minuti** (giro 3-5 + pubblicazione 3-4).

Per 10 trial reel su un telefono: **Add** il telefono → 10 task (uno per video) → **Upload in order**
(il 1° video al task 1, il 2° al task 2…) → **Bulk schedule** con **Tasks** e **intervallo 15 minuti** → **Edit table**
per le descrizioni → **Save**.
Bulk schedule scrive solo gli orari di partenza (es. 10:00, 10:15, 10:30…): con 15 minuti tra un task e
l'altro restano 6,5-8,5 minuti di pausa con Instagram chiuso.
10 trial reel ≈ **2 ore e 20** per telefono (i telefoni diversi vanno in parallelo).
Chiama i video `01.mp4 … 10.mp4` (con lo zero).

## Cosa fa

1. Tastiera GeeRunner, permessi a Instagram, svuota la cartella **Download** del telefono e ci mette il video del task.
2. Controlla che il video sia arrivato sul telefono.
3. Apre Instagram e fa un giro di **3-5 minuti** (a caso):
   - **storie di altri** (mai la propria): ogni tanto tocca a destra per saltare alla storia dopo;
   - **home**: scorre solo verso il basso, non la ricarica mai;
   - **reels**: ogni tanto mette **1 o 2 like** (mai togliere un like già messo) e su un reel apre i **commenti**,
     li scorre e li chiude (non scrive niente).
   Se le storie finiscono da sole proprio mentre preme "indietro" e Instagram si chiude, se ne accorge e lo riapre.
4. Profilo → menu (tre righe) → **Account type and tools** → **Trial reels** → **Create trial reel**
   (se esce il pop-up di spiegazione lo chiude).
5. Galleria: chiede ad Android qual è **l'ultimo video aggiunto**; se ha lo stesso nome del video del task tocca il
   **primo video** (GeeLark lo carica all'inizio del task, quindi è l'ultimo arrivato) → **Next**.
   Non apre album e non scorre la galleria. La data di scatto non conta (i metadati dei video sono a caso).
6. Scrive la descrizione, scorre giù e spegne **Facebook solo per questo reel** ("Don't share this reel").
7. **Share**, aspetta che carichi, fa gli screenshot e torna alla **home del telefono**.

## Sicurezza: si ferma con errore e NON pubblica se…

- non vede "This is a trial reel" (in galleria e nella pagina finale);
- per Android l'ultimo video aggiunto non è quello del task (es. un altro video salvato durante il giro);
- non riesce a spegnere Facebook;
- il video non è arrivato sul telefono;
- non è più sulla pagina finale quando deve scorrere.

Non tocca mai: etichetta AI, interruttore Trial, audio, copertina, tag, posizione, "Stop sharing all reels".
Nel giro non scrive commenti o messaggi e non toglie like.

## Versioni

- v1: prima versione.
- v2 (prova del 7 ottobre su Frankfurt): dopo la descrizione non preme più "indietro" per chiudere la tastiera
  (con la tastiera già chiusa tornava al video e lo scroll apriva il montaggio); prima di ogni scroll controlla
  di essere ancora sulla pagina finale, altrimenti si ferma con `[Pagina finale]`.
- v3: warm-up sui Reels 7-10 minuti; il controllo "il video è arrivato?" non usa più `${...}` (GeeLark lo
  cancellava e il controllo leggeva sempre vuoto); scelta del video: il più recente secondo Android, altrimenti
  il suo album Download (scorrendo la lista degli album); se non trova l'album scrive nel log cosa vede.
- v4: giro di 3-5 minuti diviso tra storie di altri, home e reels (al posto dei 7-10 minuti di soli reels).
- v5 (prova del 7 ottobre 02:35 su Frankfurt, fallita in galleria): Android metteva per primo un video di Telegram
  per la data di scatto (i metadati sono a caso), così il flusso apriva gli album e scorreva la galleria. Ora guarda
  solo l'ultimo video aggiunto (stesso nome del video del task) e tocca il primo: niente album, niente scroll.
  Giro: tocchi a destra nelle storie, 1-2 like e i commenti di un reel, niente tocco su "Home" (ricaricava la pagina);
  se Instagram si chiude mentre esce dalle storie lo riapre.

## Errori (si vedono nel task di GeeLark)

`[Video]` `[Profilo]` `[Menu]` `[Trial reels]` `[Sicurezza]` `[Galleria]` `[Editor]` `[Descrizione]` `[Pagina finale]` `[Facebook]` `[Share]`:
il testo dice cosa non ha trovato, e c'è lo screenshot del momento.
