# IG STORIA LINK v3

Copia identica di **IG WARMUP v10.4** (`base_IG_WARMUP_v10_4.json`, il file mandato dall'utente il 10/10) con solo due modifiche:

1. **Niente nota**: tolti i passi della nota (al loro posto `notaDovuta = 0`).
2. **Sticker del link nella storia**, subito prima della musica: faccina degli sticker → **LINK** → URL = `Link` → **Customize sticker text** = `Testo` (vuoto = la caption della lista) → **Done** (se 'Add link' resta aperta: chiude la tastiera e Done di nuovo) → trascina il link in basso, lento, oltre le griglie. Se il link non riesce la storia non viene pubblicata (errore `storiaErr:link`).

Tutto il resto (warm-up, galleria, ultima foto aggiunta, caption, musica da For you, 'Your stories') e' quello di v10.4, invariato.

## Parametri del task
- `Minuti`, `Storia`, `Lingua`: come nel warm-up v10.4.
- `Link` (obbligatorio): il link di quell'account.
- `Testo` (facoltativo): il testo dello sticker.

Si rigenera con `python3 instagram_storia_link/genera_storia_link.py` (532 passi, 218 KB).
