# IG WARMUP — giro di riscaldamento su Instagram (GeeLark)

File da importare in GeeLark:
- `IG_WARMUP_IMPORT.json`: il warm-up (flusso "IG WARMUP v10.3", 242 KB): **un solo flusso** che fa il giro, poi la nota,
  poi la storia, poi chiude Instagram;
- `IG_TEST_NOTA_STORIA_IMPORT.json`: **prova veloce** (flusso "IG TEST NOTA + STORIA v3.2", 150 KB): apre Instagram, pubblica
  **prima la nota** e **poi la storia** con musica e caption, e basta (pochi minuti). Parametri: Storia (la foto) e Lingua.
  Fa la nota anche se ne è già stata fatta una nelle ultime 24 ore.

Fa tutto GeeLark, anche col PC spento.

## Limite di GeeLark: il flusso non deve essere troppo grande

Un flusso troppo grande si importa, ma quando lo lanci resta fermo su "Start execution" e non apre nemmeno Instagram
(7 ottobre: la prova v3 da 264.651 byte non partiva, la v2 da 259.256 sì; 8 ottobre: il warm-up v10.2 da 250.245 byte e
550 passi non partiva, la v10.1 da 243.854 byte e 532 passi sì). Il limite dipende anche dal numero di passi, quindi il
warm-up resta sotto la v10.1 (v10.3: 242.283 byte, 529 passi). Per starci, dalla v10:
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
  - mai togliere un like, mai "annulla repost", mai commenti o follow;
  - se per 2 reel di fila non vede i bottoni del reel (cuore, commenti, autore), i reels sono bloccati (una schermata
    "Suggested" che non si supera, o una finestrella di Instagram rimasta aperta): preme "indietro" e torna su Reels,
    senza toccare niente in quella schermata. La prima volta scrive la "spia" nel log.
- **Notifiche**: tocca il cuore in alto a destra, scorre e torna indietro.
- **DM**: apre la lista e guarda 1-2 chat, **senza scrivere niente** (niente richieste). Tocca solo le chat vere (le righe
  con "·", tipo "Reacted to your story · 3d", tra la riga "Filters" e "Accounts to follow"), sulla parte sinistra:
  **mai** "Accounts to follow", "Follow back", "Requests" o la foto (storia) della persona. Per ogni chat riapre la lista.
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
  Con la **v10.2 il conto delle 24 ore è ripartito da zero** (8 ottobre, 20:55; la prima volta con la v10.1 alle 15:50):
  le note fatte prima non contano, quindi al primo giro con la v10.2 ogni telefono mette la nota; poi di nuovo una ogni
  24 ore.

Alla fine torna alla home del telefono e chiude Instagram. Nel log c'è il **riepilogo** (ordine, like, commenti,
profili, salvati, repost, notifiche (1 = cuore trovato, pos = toccato in alto a destra), chat DM toccate, nota, storia). Se nel task manca la foto, alla voce storia
c'è scritto "nessuna foto nel task (campo Storia vuoto)": senza foto la storia non si fa e non è un errore.

## Errori (il resto del giro è comunque fatto)

- `[Storia]`: storia non pubblicata (il file non è arrivato, "Add to story" non si apre, l'ultima foto non è quella del task,
  l'editor non si apre, non trova "Your stories", la freccia blu non conferma la caption). C'è lo screenshot del momento.
- `[Nota]`: nota non pubblicata (nei DM non trova la tua foto con "Your note", non trova dove scrivere o "Share").

## La "spia" nel log

Nella prova veloce, in alcuni momenti (DM, nota aperta, canzone in ascolto, caption scritta, storia non pubblicata), e
nel warm-up solo quando qualcosa non va (storia non pubblicata, reels bloccati), il flusso scrive nel log
i bottoni di Instagram che ci sono sullo schermo (nome, posizione) e se la tastiera è aperta. Non tocca niente: serve a
capire subito cosa è cambiato se qualcosa non va. Nel log è il nodo "spia (...)": il testo è dopo "spiaOut".

## Attenzione

- Un task di warm-up e un task trial reel **non devono girare insieme sullo stesso telefono**: lascia spazio tra i due.
- La prova veloce (v3.1) è andata bene il 7 ottobre alle 23:15: nota, musica, caption e "Your stories".
- Il warm-up v10 (7 ottobre, Minuti 10) ha fatto giro e storia; nota giusta saltata (fatta 34 minuti prima); DM e
  notifiche non si aprivano (sistemato nella v10.1).
- Il warm-up v10.1 (8 ottobre 16:34, Minuti 17): nota pubblicata, notifiche aperte, la chat dei DM aperta (l'unica chat
  dell'account), mai toccati i suggeriti; storia non fatta perché nel task non c'era la foto; nei reels like, salvati e
  repost a 0 per due blocchi (sistemato nella v10.2).
- Il warm-up v10.2 (8 ottobre sera) non partiva: troppo grande (250 KB, 550 passi). Sistemato nella v10.3.
  Prossima prova: il warm-up v10.3 con la **foto nel campo Storia**, poi mandami il log. Con la foto, Instagram si apre
  dopo circa 30 secondi (prima carica la foto sul telefono).

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
- v10.1 (prova v10 del 7 ottobre sera: storia ok, DM e notifiche non si aprivano):
  - notifiche: il cuore in alto non ha più il nome "Notifications"; ora lo trova con il suo id ("notification") e controlla
    che sia quello in alto (lo stesso id c'è sul pallino dei DM in basso); se non lo trova tocca in alto a destra;
  - DM: le righe delle chat non hanno più il loro id; ora tocca le righe con "·" tra "Filters" e "Accounts to follow"
    (se non ce ne sono, solo la prima riga sotto "Filters"), mai i suggeriti o "Follow back". Riapre la lista prima di
    ogni chat e controlla che la chat si sia aperta (casella "Message..." in basso);
  - nota: il conto delle 24 ore riparte da zero (la nota era stata cancellata a mano: così al prossimo giro la rimette);
  - nel riepilogo anche notifiche e chat aperte; "spia" nel log se notifiche o chat non si aprono;
  - tolti 3 controlli doppi alla fine di storie, notifiche e DM (li rifà comunque il pezzo dopo): 244 KB.
- v10.2 (prova v10.1 dell'8 ottobre, 16:34):
  - reels: per circa 3 minuti una schermata "Suggested" che lo scorrimento non superava, e per circa 2,5 minuti una
    finestrella di Instagram rimasta aperta dopo un profilo: like 0/3, salvati 0/1, repost 0/1. Ora se per 2 reel di fila
    non vede i bottoni del reel preme "indietro" e torna su Reels (nel simulatore si sblocca in 25-36 secondi invece di
    2-4 minuti); la prima volta scrive la spia nel log;
  - nota: il conto delle 24 ore riparte di nuovo da zero (nota cancellata a mano un'altra volta);
  - riepilogo: "nessuna foto nel task" quando il campo Storia è vuoto;
  - tolte le spie di DM e notifiche (ora funzionano): 250 KB.
- v10.3 (la v10.2 restava ferma su "Start execution"): stesse cose della v10.2 ma più leggera, 242 KB e 529 passi (sotto
  la v10.1 che partiva):
  - reels bloccati: "indietro" e poi tocca Reels (prima rifaceva anche i controlli "sono in Instagram? sono sui reels?");
  - notifiche e DM: tolti i controlli che servivano solo al riepilogo (titolo "Notifications", casella "Message...");
    nel riepilogo ora c'è se il cuore è stato trovato e quante chat ha toccato;
  - DM: 1-2 chat per giro (prima 1-3);
  - nomi di alcuni passi più corti.
