# PIANO DELLA GIORNATA — un telefono (prova senza storia con link e senza post a immagini)

I flussi sono quelli del branch `claude/compassionate-darwin-qis1g9`.
Regola d'oro: **mai due task sullo stesso telefono nello stesso momento** (lascia sempre la pausa).
Telefoni diversi possono fare lo stesso piano in parallelo (meglio sfalsati di 15-30 minuti).

| # | Orario (esempio) | Cosa | Flusso GeeLark (file) | Parametri | Durata |
|---|---|---|---|---|---|
| 1 | 09:00 | Scroll intenso (storie, home, reel con like/salvati/repost, notifiche, DM) **+ nota + storia** | `IG WARMUP v10.4` (`instagram_warmup/IG_WARMUP_IMPORT.json`) | Minuti **35**, Storia = la foto, Lingua vuota | ~35 min |
| — | 09:35 | Pausa | | | 40 min |
| 2 | 10:15 | Warm-up reel + **REEL 1** (canzone virale, anche su Facebook) | `IG REEL VIRALE v3` (`instagram_reel_virale/IG_REEL_VIRALE_IMPORT.json`) | Video = reel 1, Minuti **15**, Caption vuota, SoloProva spento | ~22 min |
| — | 10:40 | Pausa | | | 30 min |
| 3 | 11:10 → 13:35 | **10 trial reel** in fila | `IG TRIAL REEL v7` (`instagram_trial/IG_TRIAL_REEL_IMPORT.json`) | 10 task, Upload in order `01.mp4…10.mp4`, Bulk schedule **ogni 15 min**, caption senza hashtag | ~2h 25 |
| — | 13:35 | **Pausa lunga** | | | **2h 30** |
| 4 | 16:05 | Warm-up reel + **REEL 2** | `IG REEL VIRALE v3` | Video = reel 2, Minuti **15** | ~22 min |
| — | 16:30 | Pausa | | | 1h 30 |
| 5 | 18:00 | **CommentBot**: risponde ai commenti dei reel 1 e 2 | `IG POST v9.11` (`instagram_relay/IG_POST_v9_IMPORT.json`) + `relay.py` | **PC acceso**: prima `avvia.bat` (relay + ngrok) | — |
| — | dopo CommentBot | Pausa | | | ~1h |
| 6 | 19:30 | Warm-up reel + **REEL 3** (prima serata) | `IG REEL VIRALE v3` | Video = reel 3, Minuti **15** | ~22 min |

## Perché queste pause

- **Dopo i trial: 2h 30** (minimo 2h, massimo 3h). Sono già 2 ore e mezza di Instagram quasi di fila; una persona vera
  a quel punto chiude l'app. Così Instagram ha anche il tempo di far girare reel 1 e trial prima del reel 2.
- **Tra i reel normali almeno 3 ore** (qui: 10:15 → 16:05 → 19:30), così non si rubano la spinta a vicenda.
- **CommentBot tra il reel 2 e il reel 3**: a quell'ora sotto il reel 1 e il reel 2 ci sono già commenti a cui rispondere.
- Reel 3 alle 19:30: è la fascia serale, quella con più persone online.

## Da ricordare

- La **nota** si fa una volta ogni 24 ore: nel passo 1 la mette solo se sono passate 24 ore dall'ultima.
- Se nel passo 1 il campo **Storia** è vuoto, la storia non si fa (non è un errore).
- **Trial**: 10 task ogni 15 minuti durano circa 2h 20-2h 25. Per stare proprio in 2 ore metti **ogni 12 minuti**
  (restano 3,5-5,5 minuti di pausa tra un task e l'altro: si può fare, ma 15 è più sicuro).
- Il **trial 1** deve partire quando il reel 1 è già finito (il reel virale dura 20-25 minuti).
- Al primo giro: **REEL VIRALE con SoloProva acceso** se vuoi vedere che arriva fino alla fine senza pubblicare.
- Il **CommentBot** è l'unico pezzo che ha bisogno del **PC acceso** (relay + ngrok); tutti gli altri girano da soli su GeeLark.

## Da fare dopo (non in questa prova)

- Storia con **link + musica** (dopo il reel 3).
- **Post a immagini** con canzone e caption.
