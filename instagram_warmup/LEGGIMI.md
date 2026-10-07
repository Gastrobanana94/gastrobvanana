# IG WARMUP — giro di riscaldamento su Instagram (GeeLark)

File da importare in GeeLark:
- `IG_WARMUP_IMPORT.json`: il warm-up (flusso "IG WARMUP v10", 239 KB): **un solo flusso** che fa il giro, poi la nota,
  poi la storia, poi chiude Instagram;
- `IG_TEST_NOTA_STORIA_IMPORT.json`: **prova veloce** (flusso "IG TEST NOTA + STORIA v3.2", 150 KB): apre Instagram, pubblica
  **prima la nota** e **poi la storia** con musica e caption, e basta (pochi minuti). Parametri: Storia (la foto) e Lingua.
  Fa la nota anche se ne è già stata fatta una nelle ultime 24 ore.

Fa tutto GeeLark, anche col PC spento.

## Limite di GeeLark: 256 KB per flusso

Un flusso sopra i 256 KB (262.144 byte) si importa, ma quando lo lanci resta fermo su "Start execution" e non fa niente
(scoperto il 7 ottobre: la prova v3 da 264.651 byte non partiva, la v2 da 259.256 sì). Per starci, dalla v10:
le liste di note e caption sono dentro il flusso **compresse** (metà del peso; il flusso le ricostruisce identiche,
stesso ordine di prima su ogni telefono) e i controlli "sono ancora in Instagram? vedo la barra in basso?" si fanno una
volta sola prima di ogni pezzo del giro.

## Note e caption: liste di CommentBot (niente AI, niente chiavi)

Le note le ha scritte **CommentBot**: 999 in italiano (`note_it.txt`) e 997 in tedesco (`note_de.txt`), una per riga,
già controllate (massimo 60 caratteri, niente link, @ o hashtag, niente doppioni). Sono **dentro il flusso**: non serve
nessuna chiave, nessun relay, nessun PC acceso.
Ogni telefono le usa in un **ordine suo** e **non ne ripete nessuna** finché non le ha usate tutte (quasi 3 anni con una al giorno).
Le **caption delle storie** funzionano uguale: 1000 in italiano (`caption_storie_it.txt`) e 1000 in tedesco
(`caption_storie_de.txt`), dentro il flusso, mai ripetute sullo stesso telefono (alcune sono solo emoji).
Per cambiarle: si modificano i file `.txt` e si rifà il flusso.

**Italiane o tedesche (note e caption) lo decide da solo, dal proxy del telefono**: chiede a internet da che paese esce (ip-api.com) e
- 🇮🇹 Italia (o San Marino, Vaticano) → lista **italiana**;
- 🇩🇪 Germania, 🇦🇹 Austria, 🇨🇭 Svizzera (o Liechtenstein) → lista **tedesca**.
Se quel controllo non risponde guarda il fuso orario del telefono (Roma → italiano; Berlino, Vienna, Zurigo → tedesco) e poi
la lingua del telefono; se non capisce niente usa il tedesco. Nel riepilogo del log c'è scritto quale lista ha usato e perché.

## Parametri del task

- **Minuti**: quanto dura tutto (già impostato a 30): il giro finisce un paio di minuti prima per lasciare tempo a nota
  e storia.
- **Storia**: la foto o il video da pubblicare nella storia. Se lo lasci vuoto, quel giro non pubblica storie.
- **Lingua**: **lasciala vuota** (decide dal proxy, per note e caption). Scrivi `it` o `de` solo per forzare le liste su
  un telefono con il proxy di un altro paese: quello che scrivi vince sul proxy.

## Cosa fa (circa 30 minuti)

1. Chiude e riapre Instagram (si parte puliti).
2. **Il giro**, pezzi **in ordine a caso** (le storie di altri sempre prima della home, perché servono la home in cima):
   storie di altri, home, reels (due blocchi), notifiche, DM.
3. **La nota** (se sono passate 24 ore): Instagram chiuso e riaperto (home in cima), poi la nota.
4. **La storia** (se nel task c'è il file).
5. Torna alla home del telefono e **chiude Instagram**.

I pezzi:

- **Storie di altri** (1-3 min): mai la sua; ogni tanto tocca a destra per saltare.
- **Home** (2-4 min): scorre solo verso il basso, non tocca mai "Home" (la ricaricherebbe). Ogni tanto 1 like (massimo 2)
  e a volte apre un reel dal feed.
- **Reels** (tutto il tempo che resta, in due blocchi):
  - quanto guarda ogni reel: 50% 5-10 secondi, 25% 15-25 secondi, 25% 2-3 secondi;
  - nel giro: **like 0-10**, **commenti 0-10** (li apre, li legge, li chiude), **profili dell'autore 0-8** (griglia e a volte
    un post), **salvati 1-2**, **repost 1-3** (con il tasto repost, non nella storia). Sparsi a caso tra i reel;
  - mai togliere un like, mai "annulla repost", mai commenti o follow.
- **Notifiche**: le apre, scorre e torna indietro.
- **DM**: apre la lista e guarda 1-3 chat, **senza scrivere niente** (niente richieste).
- **Storia** (se c'è il file):
  1. tocca il "+" piccolo sulla sua foto in alto a sinistra;
  2. controlla con Android che l'ultima foto aggiunta sia quella del task e la tocca (subito dopo la fotocamera);
  3. musica: canzone **a caso tra le prime 8 di "For you"** (toccarla la fa solo sentire) → la **freccia "→"** nella
     barra in basso per sceglierla → "Done";
  4. in "Add a caption..." una **caption dalla lista** (italiana o tedesca come le note);
  5. conferma la caption con la **freccia blu** a destra della casella (mentre è aperta copre "Your stories"). Non preme
     "indietro" (aprirebbe "Discard edits?"); se quella finestra compare tocca "Keep editing", mai "Discard" o "Save draft";
  6. **"Your stories"** (mai "Close Friends"). Se per sbaglio tocca una parola della caption (si apre il correttore) lo
     chiude e riprova una volta.
- **Nota**: **una ogni 24 ore** (il telefono si ricorda quando l'ha fatta; un'ora di margine), presa dalla **lista di
  CommentBot** italiana o tedesca secondo il paese del proxy (o Lingua), mai la stessa due volte sullo stesso telefono.
  Nei DM tocca **la tua foto** (quella con la bolla sopra e la scritta "Your note" sotto); se c'è già una nota attiva
  sceglie "Leave a new note".

Alla fine torna alla home del telefono e chiude Instagram. Nel log c'è il **riepilogo** (ordine, like, commenti,
profili, salvati, repost, nota, storia).

## Errori (il resto del giro è comunque fatto)

- `[Storia]`: storia non pubblicata (il file non è arrivato, "Add to story" non si apre, l'ultima foto non è quella del task,
  l'editor non si apre, non trova "Your stories", la freccia blu non conferma la caption). C'è lo screenshot del momento.
- `[Nota]`: nota non pubblicata (nei DM non trova la tua foto con "Your note", non trova dove scrivere o "Share").

## La "spia" nel log

Nella prova veloce, in alcuni momenti (DM, nota aperta, canzone in ascolto, caption scritta, storia non pubblicata), e
nel warm-up solo quando la storia non viene pubblicata, il flusso scrive nel log
i bottoni di Instagram che ci sono sullo schermo (nome, posizione) e se la tastiera è aperta. Non tocca niente: serve a
capire subito cosa è cambiato se qualcosa non va. Nel log è il nodo "spia (...)": il testo è dopo "spiaOut".

## Attenzione

- Un task di warm-up e un task trial reel **non devono girare insieme sullo stesso telefono**: lascia spazio tra i due.
- La prova veloce (v3.1) è andata bene il 7 ottobre alle 23:15: nota, musica, caption e "Your stories".
  Prossima prova: il warm-up v10 con **Minuti 10** e una foto, poi mandami il log.

## Versioni

- v8: il warm-up di prima (like a ogni giro, follow, repost e storie di reel a caso, DM e commenti con l'AI).
- v9: giro di 30 minuti in ordine a caso con i numeri decisi insieme; storia con musica ed emoji; nota ogni 24 ore;
  niente follow, niente risposte AI, niente controlli dell'account. Se Instagram si chiude per un "indietro" di troppo lo
  riapre; se resta aperta una schermata senza la barra in basso torna indietro; prima di toccare "Home" o "Reels"
  guarda se c'è già.
- v9.1: la nota la scrive CommentBot (prima aveva un testo suo). Del testo di CommentBot è tolta solo la parte
  "Errori e problemi" su Telegram, che dentro GeeLark non serve. Se la nota viene troppo lunga, un secondo tentativo.
- v9.2: niente più AI nel flusso: la nota viene dalla lista di CommentBot (999 italiane, 997 tedesche; tolte 4 con il sole e
  l'emoji della pioggia). Ogni telefono la gira in un ordine suo (dal suo android_id) senza ripetere.
- v9.3: la lista (italiana o tedesca) la sceglie dal paese del proxy del telefono; NoteLang vuoto = automatico.
- v9.4: caption delle storie dalla lista di CommentBot (non più emoji), stessa lingua delle note; NoteLang diventa
  **Lingua** e il parametro EmojiStoria non c'è più. Nuovo flusso di prova "IG TEST NOTA + STORIA v1".
- v9.5 / prova v2 (prova del 7 ottobre 21:38 su un telefono tedesco, fallita su nota e storia):
  - nota: Instagram ha cambiato i DM, il vecchio tasto non c'è più; ora tocca la tua foto sopra "Your note";
  - musica: toccare la canzone la faceva solo sentire; ora tocca anche la freccia "→" in basso e poi "Done";
  - caption: dopo averla scritta la casella restava aperta sopra "Your stories" e il tocco finiva su una parola
    (si apriva il correttore); ora prima la chiude con "indietro", poi tocca "Your stories";
  - se la storia non viene pubblicata esce davvero dall'editor (prima poteva restarci);
  - "spia" nel log.
- v9.6 / prova v3 (prova v2 del 7 ottobre sera: nota pubblicata, storia ferma sulla caption): la caption si conferma
  con la **freccia blu**; "indietro" con la caption aperta apriva "Discard edits?". Se la freccia blu pubblicasse
  già la storia, se ne accorge (vede la home) e non tocca altro.
- prova v3.1: la v3 non partiva (264 KB, sopra il limite di 256 KB di GeeLark). Stessa prova, ma 229 KB: liste scritte
  in modo più compatto, un solo blocco "esci dall'editor". Fa esattamente le stesse cose della v3.
- v10 / prova v3.2: **un solo flusso**: prima il giro (ordine a caso), poi la nota, poi la storia (dopo aver riaperto
  Instagram, come nella prova riuscita), poi chiude Instagram. 239 KB: liste compresse (stesse frasi, stesso ordine),
  controlli di navigazione una volta per pezzo, spia solo se la storia non va. Se la storia non va scarta la bozza e
  chiude Instagram (prima tornava alla home). Gli errori finali sono un solo passo.
