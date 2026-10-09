# IG STORIA LINK v2

Flusso nuovo e indipendente: **warm-up prima → storia con il link → warm-up dopo**.
Si genera dal warm-up (`instagram_warmup/IG_WARMUP_IMPORT.json`) con:

    python3 instagram_storia_link/genera_storia_link.py

Il file da importare in GeeLark è `IG_STORIA_LINK_IMPORT.json`.

## Parametri del task

| Parametro | Cosa metti | Se vuoto |
| --- | --- | --- |
| Link | il link di quell'account (senza spazi) | il task si ferma subito con errore |
| Storia | la foto (o il video) della storia | la storia non viene fatta (errore alla fine) |
| Testo | il testo che si vede sullo sticker | una caption della lista storie (italiano/tedesco dal proxy), mai ripetuta |
| MinutiPrima | minuti di warm-up prima | 8-12 minuti a caso |
| MinutiDopo | minuti di warm-up dopo | 3-5 minuti a caso |
| Lingua | `it` o `de` per forzare la lista | la decide il proxy |

## Cosa fa

1. Warm-up prima in ordine a caso: storie di altri, home, notifiche, reels a 140-190 ms (like, 1-2 salvati, a volte un repost).
2. Riapre Instagram pulito, tocca il `+` su "Your story" (se la galleria non si apre: tocca "Your story"; se ancora no: home, swipe a destra per la fotocamera e tocca il quadratino della galleria in basso a sinistra; la "spia" scrive nel log cosa c'era sullo schermo), sceglie la foto del task (controlla che sia proprio quella).
3. Faccina degli sticker → **LINK** (se non lo vede lo cerca scrivendo "link") → URL = Link → **Customize sticker text** → testo → **Done**.
4. Trascina lo sticker del link in basso (in uno di 4 punti facili da toccare), lentamente e oltre le griglie.
5. Musica a caso da "For you" (come il warm-up), poi **Your stories** (mai Close Friends). Niente caption sulla storia: il testo è sullo sticker.
6. Warm-up dopo (home e reels) e chiude Instagram.

Se lo sticker del link non riesce, la storia **non** viene pubblicata: esce dall'editor scartando, finisce il warm-up
e il task termina con l'errore `[Link] ...` e gli screenshot.
