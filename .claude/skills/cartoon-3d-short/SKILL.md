---
name: cartoon-3d-short
description: Make a vertical (1080x1920, 30 fps) narrated 3D cartoon Short in the "2D bean characters in toon-shaded 3D sets" explainer/fable style (KnoxClips-style), rendered in code with three.js in headless Chromium, with a Kokoro TTS voiceover, word-by-word captions, a synthesised soundtrack, and an H.264 MP4 out. Use when the user asks for an animated Short / Reel / TikTok "like that video", a cartoon explainer or fable video, or a 3D animation with voiceover and captions.
---

# Cartoon 3D Short

A code-only pipeline: no 3ds Max, no Blender. Everything (models, lights, camera, captions, sound) is generated, so any shot can be changed and re-rendered.

```
script ─► voice.py ─► voice.wav + timings.json ─► index.html (three.js shots) ─► render.mjs (frames) ─► audio.py ─► ffmpeg ─► MP4
```

The template (`template/`) is a complete working 25 s Short ("The Man Who Sold the Brooklyn Bridge"). Copy it and replace the script, the props and the shots. Don't start from a blank page.

## Steps

1. **Set up** (one time per project): `scripts/setup.sh <project-dir>`
   - Copies the template and installs three.js and the Nunito font from npm, plus kokoro-onnx from PyPI.
   - Downloads the Kokoro voice model from GitHub releases. HuggingFace is not needed.
   - Network needs: npm, PyPI and github.com.
2. **Write the script.** Edit `PHRASES` and `GAPS` in `voice.py` (rules below).
   - Run `python3 voice.py <project>/.tts`, which writes `voice.wav` and `timings.json`.
   - Read the printed phrase times: every shot and caption keys off them.
3. **Build the shots** in `index.html`. Each entry in `SHOTS` has:
   - `a`/`b`: time range, derived from phrase times (`P[i].s` / `P[i].e`)
   - `light`: preset `day` | `sunrise` | `sunset` | `prison`
   - `focus` and `span`: the shadow-camera area
   - `grade`: `[saturation, brightness]`
   - `run(t)`: poses the characters and props and calls `setCam(keys, t)`

   `TRANS` sets a whip-pan or dissolve at each shot boundary. Reuse `bean({...})`, `pose()`, `signBoard()`, `signTex()`, `building()` and `outlined()`.
4. **Preview before the full render.** From the project dir, run `scripts/preview.sh /tmp/p.jpg 30 150 300 ...` with one frame per shot, then Read the image.
   - Check each shot: is the camera inside or behind geometry? Are faces blocked? Are captions over faces? Are signs cut off?
   - Fix and repeat. Expect 2–3 rounds.
5. **Render.** Run `scripts/render_all.sh 3 short.mp4`. This renders 3 parallel processes, then the soundtrack, then loudnorm to −14 LUFS, then the MP4.
   - Speed is roughly 5 s per frame effective, so 25 s of video takes about an hour. Run it in the background and wait for the notification.
6. **Check the result.** Tile 1 fps stills from the MP4, look at them, then send the file.

## Style rules (measured from the reference videos)

**Script**
- Fable or "why…?" explainer with a clear payoff or moral. That format got 3.5M views; vague self-help titles flopped.
- Short present- or past-tense statements, about 175–185 wpm.
- Use lists of three ending in a one-word punch ("Every coin, every house, every field: gone."), repetition ("Everyone is poor. Everyone is hungry."), and time jumps as their own beat ("3 days later,").
- Set up a contrast ("The first group…") and put a twist at the end.
- Captions are 1–2 words per chunk (`chunks` in `PHRASES`). Keep the punctuation. Give the punch word a colour (gold for money, green for cash).

**Look**
- Flat black-outlined 2D characters: bean body, stick limbs, faces drawn on a canvas texture. Use inverted-hull outlines (`outlined()`).
- Characters stand in 3D toon sets with real perspective and cast shadows.
- A two-band toon ramp, not three. A prop carries each character's identity (top hat, cap, police hat, bow tie, mustache).
- In-world infographics: numbers on signs, boards and gauges inside the scene, not flat overlays.
- Faces: big, readable expressions (`happy`, `laugh`, `shock`, `sly`, `sad`, `wink`), blinking every ~2 s, breathing idle.

**Light and colour**
- One warm directional sun key, a violet-tinted hemisphere fill (shadows read purple, not grey), and soft shadows.
- Colour tells the story; brightness barely moves in daylight:
  - saturated for fortune (saturation ×1.1–1.3)
  - desaturated for loss or doubt (×0.45–0.6)
  - dark and cool for consequence (prison or night)
  - warm sunset for the ending
- Show time passing with light: a sun sweep, long shadows, sunrise.

**Camera and cuts**
- No hard cuts. Within a shot, use one continuous C1-smooth path (time-based Hermite through keys, which is what `setCam` does).
- Between scenes, use a whip-pan (with 14 motion-blur sub-frames) or a dissolve for time or mood jumps.
- The picture changes every 0.5–1.5 s, roughly with each caption phrase. Add small zoom punches on repeated words and a short camera shake on impacts.
- Motion blur on every frame (3–4 sub-frames, 180° shutter) and 1.33–1.5× supersampling.

**Captions**
- Nunito 900, 92 px, white with a 15 px dark outline and a soft drop shadow.
- Centred at 68.5% of the height, with a small scale-pop when each chunk appears.
- Keep faces above that line in every shot.

**Sound**
- Kokoro voice `am_michael`, speed ~1.12–1.2, with phrases placed by `voice.py`.
- Plucked-string music bed that changes per act.
- Sound effects on every visual event: whoosh, stamp, ticks, ka-ching, pop, clang, whistle.
- Music is ducked about 7 dB under the voice, and the final mix is normalised to −14 LUFS.

## Pitfalls

- A camera inside or behind big geometry fills the frame with one flat colour. Check every shot's camera keys against the set's bounding boxes (ramps, walls, railings).
- Characters and props reused across shots are re-posed by each shot's `run()`. `hideAll()` runs first, so any shot must set everything it shows.
- Text on canvas textures needs the font loaded first. The template awaits `document.fonts.load`.
- `render.mjs` serves the project dir. Add MIME types there for any new file type the page fetches.
- YouTube blocks cloud servers, so reference footage must come from the user (phone screen recordings work).
- Only make original stories and characters. Don't recreate another channel's specific characters or videos.
