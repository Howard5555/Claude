"""Soundtrack for "The Man Who Sold the Brooklyn Bridge": music bed + SFX timed to timings.json,
music ducked under the narration (voice.wav) -> audio.wav"""
import json, wave, numpy as np, soundfile as sf

TIM = json.load(open('timings.json'))
P = [(p['start'], p['end']) for p in TIM['phrases']]
SR, DUR = 48000, TIM['duration']
N = int(SR * DUR)
mix = np.zeros(N)
rng = np.random.default_rng(7)
B0, B1, B2, B3, B4, B5 = P[2][1] + .15, P[5][1] + .05, P[6][1] + .06, P[7][1] + .15, P[9][1] + .15, P[11][1] + .15


def add(sig, at, gain=1.0):
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[max(0, -i):]; i = max(0, i); j = min(N, i + len(s))
    mix[i:j] += s[: j - i] * gain


def env(n, a=.005, d=.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def pluck(f, dur=.5, bright=.5):
    n = int(dur * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.empty(n)
    for k in range(n):
        out[k] = buf[k % p]
        buf[k % p] = (1 - bright * .5) * .5 * (buf[k % p] + buf[(k + 1) % p]) + bright * .25 * buf[k % p]
    return out * env(n, .002, dur * .45)


def bell(f, dur=.8, partials=((1, 1), (2.76, .4), (5.4, .2))):
    n = int(dur * SR); t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * m * t) for m, a in partials) * env(n, .002, dur * .3)


def lowpass_noise(dur, f0, f1, shape_pow=1.5):
    n = int(dur * SR); x = rng.normal(0, 1, n); fc = np.geomspace(f0, f1, n); a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty(n); s = 0.
    for k in range(n): s = a[k] * s + (1 - a[k]) * x[k]; y[k] = s
    return y * np.sin(np.linspace(0, np.pi, n)) ** shape_pow * 4


NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
beat = 60 / 120 / 2

# ---- music ----
# 1) sneaky-jaunty con theme (hook to cash): staccato bass + plucked melody, C major with chromatic steps
mel = [72, 74, 75, 76, 79, 76, 72, 67, 69, 72, 71, 69, 67, 64, 67, 65]
bass = [48, 55, 52, 55, 53, 57, 55, 59]
t, k = 0.0, 0
while t < B3 - .1:
    add(pluck(NOTE(bass[(k // 2) % len(bass)]), .35, .3), t, .38) if k % 2 == 0 else None
    if k % 2 == 1 or k % 4 == 0: add(pluck(NOTE(mel[k % len(mel)]), .3, .6), t, .2)
    t += beat; k += 1
# 2) morning: brighter, same tune up a 4th, stops when the police arrive
t, k = B3, 0
while t < P[9][0]:
    add(pluck(NOTE(mel[k % len(mel)] + 5), .3, .6), t, .18)
    if k % 2 == 0: add(pluck(NOTE(bass[(k // 2) % len(bass)] + 5), .35, .3), t, .32)
    t += beat; k += 1
# police chase: fast descending chromatic run
for i in range(10): add(pluck(NOTE(84 - i), .18, .7), P[9][0] + .3 + i * .1, .2)
# 3) prison: slow minor, low and sparse
for i, m in enumerate([45, 52, 48, 47, 45]):
    add(pluck(NOTE(m), 1.4, .2), B4 + .1 + i * .65, .4); add(pluck(NOTE(m + 12), 1.0, .2), B4 + .1 + i * .65 + .32, .15)
# 4) sunset: warm major strum, then a playful tag on the punchline
for k_, m in enumerate([48, 55, 60, 64, 67, 72]): add(pluck(NOTE(m), 2.0, .35), B5 + .05 + k_ * .015, .3)
for k_, m in enumerate([53, 57, 60, 65, 69]): add(pluck(NOTE(m), 1.8, .35), P[13][0] + k_ * .015, .25)
for k_, m in enumerate([72, 76, 79, 84]): add(pluck(NOTE(m), .4, .6), P[13][1] - .1 + k_ * .09, .2)

# ---- sound effects ----
n = int(.22 * SR); tt = np.arange(n) / SR
thud = np.sin(2 * np.pi * (110 - 50 * tt / .22) * tt) * env(n, .001, .06) + rng.normal(0, 1, n) * env(n, .001, .015) * .5
add(thud, P[1][0] + .15, .9)                                                      # SOLD! stamp
n2 = int(.03 * SR); tick = np.sin(2 * np.pi * 2200 * np.arange(n2) / SR) * env(n2, .0005, .006)
last = -1
for i in range(int((P[2][1] + .1 - P[2][0]) * SR / 400)):                         # counter ticks as the number climbs
    tt_ = P[2][0] + i * 400 / SR
    nval = 1 + int((((tt_ - P[2][0]) / (P[2][1] + .1 - P[2][0])) ** 1.6) * 18)
    if nval != last: add(tick, tt_, .35); last = nval
for B in (B0, B1, B2):                                                            # whip-pan whooshes
    add(lowpass_noise(.36, 400, 6000), B - .2, .5)
add(lowpass_noise(.35, 2000, 5000, 3) * .5, P[4][0] - .2, .35)                    # paper unroll rustle
add(bell(1568, .7), P[4][0] + .15, .16); add(bell(2349, .6), P[4][0] + .25, .1)   # deed sparkle
for i in range(8):                                                                # toll coins popping
    t0 = P[6][0] + .9 + (i % 4) * .22 + (i // 4) * .55
    add(bell(2637 + (i % 4) * 220, .3), t0, .09)
add(bell(1046, .9) + 0, P[7][0] + .55, .2); add(bell(2093, .7), P[7][0] + .58, .14)  # ka-ching
add(rng.normal(0, 1, int(.05 * SR)) * env(int(.05 * SR), .001, .01), P[7][0] + .5, .3)
for i in range(6):                                                                # morning birds
    n = int(.12 * SR); tt = np.arange(n) / SR
    add(np.sin(2 * np.pi * np.cumsum(3200 + 1400 * np.sin(tt * 60)) / SR) * env(n, .005, .04), B3 + .15 + i * .19 + rng.uniform(0, .05), .06)
n = int(.18 * SR); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * (180 + 900 * tt / .18) * tt) * env(n, .001, .06), P[8][0] + 1.0, .6)   # booth pops up
n = int(.9 * SR); tt = np.arange(n) / SR                                          # police whistle
f = 2600 + 250 * np.sign(np.sin(2 * np.pi * 9 * tt))
add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / .02) * np.exp(-tt / .6), P[9][0] - .05, .16)
clang = bell(310, 1.4, ((1, 1), (2.32, .7), (3.93, .5), (5.1, .35), (7.3, .2)))   # cell door clang
add(clang, P[10][0] + .78, .55); add(thud, P[10][0] + .78, .6)
add(bell(1760, .6), P[13][0] + 1.3, .14)                                          # wink ding

# ---- mix with narration ----
mix = np.tanh(mix * 1.1)
voice, _ = sf.read('voice.wav'); voice = voice if voice.ndim == 1 else voice[:, 0]
voice = np.pad(voice[:N], (0, max(0, N - len(voice))))
vol = np.convolve(np.abs(voice), np.ones(2400) / 2400, mode='same')
duck = 1 - .55 * np.clip(vol / (vol.max() * .25), 0, 1)
mix = mix * duck * .55 + voice
fade = np.ones(N); fade[-int(.3 * SR):] = np.linspace(1, 0, int(.3 * SR)); mix *= fade
mix = mix / np.abs(mix).max() * .95
pcm = (np.stack([mix, mix], 1) * 32767).astype('<i2')
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', DUR)
