"""Narration with Kokoro TTS -> voice.wav (48 kHz) + timings.json (phrase and caption times).
Usage: python3 voice.py <dir containing kokoro-v1.0.onnx and voices-v1.0.bin>"""
import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE, SPEED, GAP, LEAD = 'am_michael', 1.2, 0.10, 0.08
# each phrase: spoken text, caption chunks (1-2 words, as shown on screen)
PHRASES = [
    ("He found one coin.", ["He found", "one coin."]),
    ("He planted it.", ["He planted", "it."]),
    ("Everyone laughed.", ["Everyone", "laughed."]),
    ("Three days later,", ["3 days", "later,"]),
    ("it grew money.", ["it grew", "MONEY."]),
]
GAPS = [0.26, GAP, GAP, GAP]   # longer gap after phrase 1 leaves room for the whip-pan

k = Kokoro(f'{sys.argv[1]}/kokoro-v1.0.onnx', f'{sys.argv[1]}/voices-v1.0.bin')
SR = 48000
clips, out = [], {'phrases': [], 'captions': []}
t = LEAD
for i, (text, chunks) in enumerate(PHRASES):
    a, sr = k.create(text, voice=VOICE, speed=SPEED, lang='en-us')
    nz = np.where(np.abs(a) > 0.012)[0]
    a = a[max(0, nz[0] - 120): nz[-1] + 600]
    a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)  # -> 48 kHz
    dur = len(a) / SR
    clips.append((t, a))
    out['phrases'].append({'text': text, 'start': round(t, 3), 'end': round(t + dur, 3)})
    # caption chunk times: proportional to letter count (spoken words take time roughly by length)
    w = [len(c.replace('3', 'three')) + 2 for c in chunks]
    acc = t
    for c, wi in zip(chunks, w):
        out['captions'].append([round(acc, 3), c])
        acc += dur * wi / sum(w)
    t += dur + (GAPS[i] if i < len(GAPS) else 0)

total = t + 0.65
mix = np.zeros(int(total * SR))
for s, a in clips:
    i = int(s * SR); mix[i:i + len(a)] += a
mix = mix / np.abs(mix).max() * 0.9
sf.write('voice.wav', mix, SR)
out['duration'] = round(total, 3)
json.dump(out, open('timings.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
