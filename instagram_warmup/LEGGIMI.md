# IG WARMUP — giro di riscaldamento su Instagram (GeeLark)

File da importare in GeeLark: `IG_WARMUP_IMPORT.json` (flusso "IG WARMUP v9").
Fa tutto GeeLark, anche col PC spento.

## Dopo l'import: la chiave DeepSeek (una volta sola)

La Nota la scrive l'AI (DeepSeek). Nel file **non c'è nessuna chiave**: apri il flusso in GeeLark, apri il nodo
**"AI: scrive la nota"** e al posto di `INCOLLA_QUI_LA_CHIAVE_DEEPSEEK` incolla la tua chiave **nuova**.
Senza chiave il giro si fa tutto lo stesso, ma la nota no e il task finisce con `[Nota]`.

## Parametri del task

- **Minuti**: quanto dura il giro (già impostato a 30).
- **Storia**: la foto o il video da pubblicare nella storia. Se lo lasci vuoto, quel giro non pubblica storie.
- **EmojiStoria**: le emoji tra cui sceglie 1-2 a caso per la caption della storia (già impostate: 😂 🙈 😏 🤭 🥰 😍).
- **NoteLang**: lingua della nota: `de` tedesco, qualsiasi altra cosa italiano (già impostato `de`).

## Cosa fa (ordine a caso, circa 30 minuti)

All'inizio chiude e riapre Instagram (si parte puliti), poi fa questi pezzi **in ordine a caso**.
Le storie di altri e la pubblicazione della storia vengono sempre prima della home, perché servono la home in cima.

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
  3. musica: canzone **a caso tra le prime 8 di "For you"** → "Done";
  4. 1-2 emoji in "Add a caption...";
  5. **"Your stories"** (mai "Close Friends").
- **Nota**: **una ogni 24 ore** (il telefono si ricorda quando l'ha fatta; un'ora di margine).

Alla fine torna alla home del telefono. Nel log c'è il **riepilogo** (ordine, like, commenti, profili, salvati, repost,
storia, nota).

## Errori (il resto del giro è comunque fatto)

- `[Storia]`: storia non pubblicata (il file non è arrivato, "Add to story" non si apre, l'ultima foto non è quella del task,
  l'editor non si apre, non trova "Your stories"). C'è lo screenshot del momento.
- `[Nota]`: nota non pubblicata (manca la chiave DeepSeek, non trova il tasto per la nuova nota o "Share").

## Attenzione

- Un task di warm-up e un task trial reel **non devono girare insieme sullo stesso telefono**: lascia spazio tra i due.
- Prima prova: un task con **Minuti 10** e una foto, e guarda il telefono. Controlla nello screenshot
  "storia prima di pubblicare" che la foto sia quella giusta, poi mandami il log.

## Versioni

- v8: il warm-up di prima (like a ogni giro, follow, repost e storie di reel a caso, DM e commenti con l'AI).
- v9: giro di 30 minuti in ordine a caso con i numeri decisi insieme; storia con musica ed emoji; nota ogni 24 ore;
  niente follow, niente risposte AI, niente controlli dell'account. Se Instagram si chiude per un "indietro" di troppo lo
  riapre; se resta aperta una schermata senza la barra in basso torna indietro; prima di toccare "Home" o "Reels"
  guarda se c'è già.
