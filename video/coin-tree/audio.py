"""Synthesises the 5 s soundtrack (music bed + SFX) for the coin-tree Short -> audio.wav"""
import numpy as np, wave, json, soundfile as sf

TIM = json.load(open('timings.json'))
P = [(p['start'], p['end']) for p in TIM['phrases']]
WHIP_A, WHIP_B = P[0][1], P[1][0]
COIN_IN, LAUGH, LAPSE_A, LAPSE_B, TREE = P[1][0] + .62, P[2][0], P[3][0], P[3][1], P[4][0] - .04
SR, DUR = 48000, TIM['duration']
N = int(SR * DUR)
mix = np.zeros(N)
rng = np.random.default_rng(3)
t_all = np.arange(N) / SR


def add(sig, at, gain=1.0):
    i = int(at * SR)
    j = min(N, i + len(sig))
    if i < N:
        mix[i:j] += sig[: j - i] * gain


def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def pluck(freq, dur=0.6, bright=0.5):
    """Karplus-Strong plucked string (ukulele-ish)."""
    n = int(dur * SR)
    p = int(SR / freq)
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for k in range(n):
        out[k] = buf[k % p]
        buf[k % p] = (1 - bright * 0.5) * 0.5 * (buf[k % p] + buf[(k + 1) % p]) + bright * 0.25 * buf[k % p]
    return out * env(n, 0.002, dur * 0.45)


def bell(freq, dur=0.8):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * freq * m * t) for m, a in [(1, 1), (2.76, .4), (5.4, .2)])
    return s * env(n, 0.002, dur * 0.3)


def noise_sweep(dur, f0, f1, gain=1.0):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    # one-pole low-pass with swept cutoff
    fc = np.geomspace(f0, f1, n)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty(n); s = 0.0
    for k in range(n):
        s = a[k] * s + (1 - a[k]) * x[k]; y[k] = s
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return y * shape * gain * 4


NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)

# --- music bed: bouncy plucked chords, 132 bpm 8ths ---
beat = 60 / 132 / 2
prog = [(0.0, [60, 64, 67]), (beat * 4, [55, 59, 62, 67]), (beat * 8, [57, 60, 64]), (beat * 12, [53, 57, 60, 65])]
t = 0.0
step = 0
while t < LAUGH:  # happy section
    chord = [c for s, c in prog if s <= (t % (beat * 16))][-1]
    note = chord[step % len(chord)] + (12 if step % 4 == 2 else 0)
    add(pluck(NOTE(note), 0.5), t, 0.32)
    if step % 4 == 0:
        add(pluck(NOTE(chord[0] - 12), 0.8, 0.3), t, 0.4)
    t += beat; step += 1
# "Everyone laughed" / time-lapse: sparse, minor, a little silly
for i, m in enumerate([57, 60, 57, 56, 55, 56, 57, 59]):
    add(pluck(NOTE(m), 0.35, 0.7), LAUGH + i * beat * 1.0, 0.3)
# reveal: big major chord strum + bells
for k, m in enumerate([48, 55, 60, 64, 67, 72]):
    add(pluck(NOTE(m), 1.3, 0.4), TREE + k * 0.012, 0.35)
for k, m in enumerate([84, 88, 91, 96]):
    add(bell(NOTE(m), 0.9), TREE + .08 + k * 0.07, 0.12)

# --- sound effects ---
add(bell(1568, .7), 0.55, 0.22); add(bell(2093, .6), 0.55, 0.13)            # coin sparkle on "one coin"
add(noise_sweep(WHIP_B - WHIP_A + .1, 400, 6000), WHIP_A - .04, 0.55)                     # whip-pan whoosh
n = int(.25 * SR); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * (90 - 40 * tt / .25) * tt) * env(n, .002, .08), COIN_IN, 0.9)   # coin thud into dirt
for k in range(6):                                                # dirt patter
    add(rng.normal(0, 1, int(.03 * SR)) * env(int(.03 * SR), .001, .008), COIN_IN + .05 + k * .06 + rng.uniform(0, .03), .25)
for k in range(8):                                                # comic "ha" boops while they laugh
    n = int(.09 * SR); tt = np.arange(n) / SR
    f = (520 if k % 2 else 600) * (1 - tt * 1.5)
    add(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .003, .04), LAUGH + .05 + k * .085, .07)
for k in range(10):                                               # time-lapse clock ticks
    n = int(.02 * SR)
    add(np.sin(2 * np.pi * 2400 * np.arange(n) / SR) * env(n, .0005, .004), LAPSE_A + k * (LAPSE_B - LAPSE_A) / 10, .3)
add(noise_sweep(LAPSE_B - LAPSE_A, 200, 3000, .6), LAPSE_A + .05, 0.5)                   # rising swell into the reveal
n = int(.18 * SR); tt = np.arange(n) / SR                         # "pop" as the tree bursts up
add(np.sin(2 * np.pi * (180 + 900 * tt / .18) * tt) * env(n, .001, .06), TREE, .8)
for k in range(40):                                               # coin shower jingle
    f = rng.uniform(3000, 5200)
    add(bell(f, .25), TREE + .4 + rng.uniform(0, DUR - TREE - .5), rng.uniform(.03, .07))

mix = np.tanh(mix * 1.2)  # gentle soft clip / glue
# narration on top; duck music + SFX ~7 dB while the voice speaks
voice, vsr = sf.read('voice.wav'); voice = voice[:N] if voice.ndim == 1 else voice[:N, 0]
voice = np.pad(voice, (0, N - len(voice)))
vol = np.convolve(np.abs(voice), np.ones(2400) / 2400, mode='same')
duck = 1 - .55 * np.clip(vol / (vol.max() * .25), 0, 1)
mix = mix * duck * .55 + voice * 1.0
mix = mix / np.abs(mix).max() * .95
fade = np.ones(N); fade[-int(.12 * SR):] = np.linspace(1, 0, int(.12 * SR))
mix *= fade
pcm = (np.stack([mix, mix], 1) * 0.9 * 32767).astype('<i2')
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
