# IG REEL VIRALE — reel con la canzone di un reel virale (GeeLark)

Obiettivo (il flusso vero, da fare dopo la prova): warm-up leggero di 5-8 minuti → nei Reels trova un reel con una
**canzone** (non "Original audio") e **almeno 2K like**, usata in **almeno 1.000 reel** → "Use audio" → il video del
task → caption di CommentBot → reel normale (non trial) **condiviso anche su Facebook** → warm-up di 3 minuti dopo →
chiude Instagram.

## Il percorso (come lo fa una persona, 9 ottobre)

1. Nei **Reels**, un reel con tanti like (il numero sotto il cuore, es. "4,127") e una canzone.
2. Il **quadratino della canzone** in basso a destra → si apre un menu piccolo: "Remix and sequence" e sotto la canzone
   con scritto **"Audio"**.
3. **"Audio"** → la pagina della canzone (es. "Replay (feat. Flo Rida)", "0:28 · 15K reels", tutti i reel che la usano)
   → **"Use audio"**.
4. Si apre la fotocamera dei reel (POST / STORY / **REEL**): il **quadratino in basso a sinistra** apre la galleria
   ("New reel", "Recents").
5. L'ultimo video arrivato (quello del task) → poi editor, Next, pagina finale, come nel trial.

## Caption: liste di CommentBot

400 in italiano (`caption_reel_it.txt`) e 400 in tedesco (`caption_reel_de.txt`), una per riga. Stesso sistema delle
note: italiane o tedesche dal paese del proxy (o dal campo Lingua), ogni telefono le usa in un ordine suo e non ne
ripete nessuna finché non le ha usate tutte. Se nel task scrivi una **Caption**, usa quella.

## Adesso: la prova v4 (`IG_REEL_VIRALE_PROVA_IMPORT.json`, "IG REEL VIRALE PROVA v4")

**Non pubblica niente.** Parametri:
- **Video**: un video qualsiasi (non viene pubblicato);
- **Caption**: vuota (prende una caption dalla lista) oppure una tua;
- **Lingua**: vuota (decide dal proxy).

Nei Reels **non aspetta più GeeLark**: dove sono il cuore e il quadratino della canzone lo chiede ad Android (la "mappa",
che ha sempre funzionato anche quando GeeLark era cieco) e tocca con ADB in quel punto.

Cosa fa:
1. carica il video, apre Instagram e va sui **Reels**;
2. guarda i reel come una persona: 25% 1,5-3 secondi, 45% 3,5-7 secondi, 30% 8-14 secondi; scorre **veloce**
   (147-180 millisecondi, a caso) e ogni tanto mette **like** (2-4 nel giro): tocca il cuore se GeeLark lo vede vuoto,
   altrimenti **doppio tocco sul video** (il doppio tocco mette il like e non lo toglie mai);
3. dal 4° reel: se ci sono almeno 2K like (o non si leggono) tocca il **quadratino della canzone**; nel menu tocca
   **"Audio"** (se GeeLark non vede il menu, tocca per posizione sopra il quadratino); se è "Original audio" chiude;
4. sulla pagina della canzone: è **virale** se ha il bollino **"Trending"** (lo vede Android, anche quando GeeLark non vede
   la pagina) oppure se è usata in almeno 1.000 reel; se no torna indietro e cerca ancora (dal 12° reel basta una
   canzone, solo nella prova);
5. **"Use audio"** → galleria in basso a sinistra → il video del task → Next → pagina finale: scrive la caption, scorre
   fino a Facebook e **si ferma**: niente Share, chiude Instagram.

**Pannello "Level up your videos with Edits" ("Get App")**: prima di toccare qualcosa in fotocamera, galleria, editor e
pagina finale controlla se c'è (lo cercano sia GeeLark sia Android) e lo chiude **toccando al centro**, sopra il pannello.
Non tocca mai "Get App". Se per sbaglio si apre il Play Store, preme "indietro", torna a Instagram, chiude il pannello e
riprova (mai "Install").

Se GeeLark non trova un bottone, lo tocca per posizione (Reels in basso, "Use audio", galleria, primo video). Screenshot
e "spia" la prima volta che apre il menu e la pagina della canzone, poi fotocamera, galleria, editor e pagina finale.
Nel **riepilogo**: like messi, pannelli Edits chiusi, volte nel Play Store, i reel guardati (like e motivo), la canzone scelta, cosa ha toccato per posizione, fin dove
è arrivato, la caption, la riga di Facebook.

Non tocca mai: follow, commenti, "Remix and sequence", "Use on Edits", la registrazione, Share. Non toglie mai un like.

Provala su **Melina e su Elixa**, poi mandami log e screenshot.

## Prove

- Prova v1 (Elixa, 9 ottobre 00:43): non ha toccato niente. I testi dei reel (like, nome della canzone) per GeeLark non
  sono testi normali, e dalle 00:44:16 alla fine GeeLark era **cieco**: ogni ricerca rispondeva "nessun elemento" in
  0,01 secondi (normalmente almeno 1 secondo), anche per il cuore e il quadratino che Android vedeva. Inoltre il
  quadratino apre un menu piccolo, non subito la pagina dell'audio. Sistemato nella v2.
- Prova v2 (Elixa, 9 ottobre 01:13): lentissima e non ha toccato niente. Al 2° reel GeeLark non trovava il cuore che
  Android vedeva e il flusso lo aspettava (35-40 secondi), dalle 01:15:12 GeeLark era cieco e il flusso aspettava 15
  secondi a ogni controllo (circa un minuto per reel); niente like; scorrimento lento (280 ms). Sistemato nella v3: posizioni
  da Android, tocchi con ADB, scorrimento 147-180 ms, like nel giro.
- Prova v3 (Elixa, 9 ottobre 01:34): reels, like col doppio tocco, quadratino, menu, "Audio" e "Use audio" giusti; galleria,
  video ed editor giusti. Nell'editor è comparso il pannello di Edits: GeeLark vede Next anche sotto il pannello e il
  tocco su Next è finito su "Get App" (Play Store). GeeLark non vede la pagina della canzone, Android sì (c'è anche il
  bollino "Trending"). Sistemato nella v4: chiude il pannello prima di toccare, si protegge dal Play Store, canzone virale
  dal bollino "Trending".
