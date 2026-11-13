"""Narration with Kokoro TTS -> voice.wav (48 kHz) + timings.json (phrase and caption times).
Usage: python3 voice.py <dir containing kokoro-v1.0.onnx and voices-v1.0.bin>"""
import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE, SPEED, GAP, LEAD = 'am_michael', 1.12, 0.10, 0.10
# each phrase: spoken text, caption chunks (1-2 words, as shown on screen)
PHRASES = [
    ("This man sold the Brooklyn Bridge.", ["This man", "sold the", "Brooklyn Bridge."]),
    ("Not once.", ["Not once."]),
    ("Again and again.", ["Again", "and again."]),
    ("He'd find newcomers fresh off the boat,", ["He'd find", "newcomers", "fresh off", "the boat,"]),
    ("flash his official-looking papers,", ["flash his", "official-", "looking papers,"]),
    ("and make an offer:", ["and make", "an offer:"]),
    ("buy the bridge, and charge a toll to cross it.", ["buy the", "bridge,", "and charge", "a toll", "to cross it."]),
    ("They paid him in cash.", ["They paid", "him in", "CASH."]),
    ("The next morning, they set up a toll booth,", ["The next", "morning,", "they set up", "a toll booth,"]),
    ("until the police dragged them away.", ["until", "the police", "dragged", "them away."]),
    ("He was finally caught,", ["He was", "finally", "caught,"]),
    ("and spent the rest of his life in prison.", ["and spent", "the rest", "of his life", "in prison."]),
    ("But his trick lives on:", ["But his", "trick", "lives on:"]),
    ("If you believe that, I've got a bridge to sell you.", ["If you", "believe that,", "I've got", "a bridge", "to sell you."]),
]
# pause after each phrase; longer ones give room for whip-pans and time-jump dissolves
GAPS = [0.08, 0.06, 0.30, 0.08, 0.08, 0.10, 0.12, 0.30, 0.10, 0.30, 0.08, 0.30, 0.12]

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

total = t + 1.1
mix = np.zeros(int(total * SR))
for s, a in clips:
    i = int(s * SR); mix[i:i + len(a)] += a
mix = mix / np.abs(mix).max() * 0.9
sf.write('voice.wav', mix, SR)
out['duration'] = round(total, 3)
json.dump(out, open('timings.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
