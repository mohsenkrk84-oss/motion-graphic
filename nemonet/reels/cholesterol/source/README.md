# Cholesterol reel — build steps

Run from a work folder that has `vo.mp3` (from `../refs/vo.mp3`).

1. `whiten.py` — fixed the cream-coloured faces in scenes 4 and 11 (seed points are in the chat log; outputs go to `/home/claude/work/img`).
2. `prep.py` — prepares `src/s01..s13.png` (border crop on 10, zero / half on the paper, LDL/HDL tags, scene-12 card with the real logo).
3. `timing.py vo.mp3` — tightens pauses into `vo_fit.wav`, groups speech segments per line (`groups.json`) and writes `timing.json`.
4. `render.py out.mp4` — silent 1080x1920 30fps video (camera moves + word-by-word captions).
5. `audio.py` — synthesized music + SFX, then mix with ffmpeg (sidechain duck + loudnorm -14 LUFS) and mux.
6. `cover.py` — separate cover image.

Captions and keywords live in `lines.py`.
