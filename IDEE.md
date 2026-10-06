# Idee per le prossime automazioni

## Upload reels normali (NON trial reels) — da fare dopo i trial reels

- Usare **"audio di un altro reel"**. Il template di GeeLark "Post Reels video on Instagram"
  (copia in `riferimenti/GeeLark_Post_Reels_video_on_Instagram.json`) lo fa già con questi parametri:
  - `SameURL`: link del reel da cui prendere l'audio
  - `SameVolume`: volume dell'audio preso dall'altro reel (0-100)
  - `AcousticVolume`: volume dell'audio originale del nostro video (0-100)
- Come fa il template: apre il link `SameURL` in Instagram → tocca la copertina dell'audio
  (`media_album_art_button`) → menu ⋯ (`clips_ufi_more_button_component`) → "Audio" → "Use audio"
  → galleria → sceglie il video. I volumi li regola da "Audio Track" → "Volume" (cursore).
- **Per i trial reels NON si usa.**
- **Condivisione su Facebook sempre accesa.** (Nei trial reels invece si spegne solo per quel reel:
  "Don't share this reel", mai "Stop sharing all reels", che la spegnerebbe anche per i reel normali.)

## Regole per tutte le automazioni di upload

- **MAI l'etichetta AI** ("Add AI label" / `AITags` sempre spento): con l'etichetta i video vanno male subito.
- **Copertina: la sceglie sempre Instagram** (non caricarla).
