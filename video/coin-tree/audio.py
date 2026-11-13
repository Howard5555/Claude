"""Synthesises the 5 s soundtrack (music bed + SFX) for the coin-tree Short -> audio.wav"""
import numpy as np, wave

SR, DUR = 48000, 5.0
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
while t < 2.3:  # happy section
    chord = [c for s, c in prog if s <= (t % (beat * 16))][-1]
    note = chord[step % len(chord)] + (12 if step % 4 == 2 else 0)
    add(pluck(NOTE(note), 0.5), t, 0.32)
    if step % 4 == 0:
        add(pluck(NOTE(chord[0] - 12), 0.8, 0.3), t, 0.4)
    t += beat; step += 1
# "Everyone laughed" / time-lapse: sparse, minor, a little silly
for i, m in enumerate([57, 60, 57, 56, 55, 56, 57, 59]):
    add(pluck(NOTE(m), 0.35, 0.7), 2.3 + i * beat * 1.0, 0.3)
# reveal: big major chord strum + bells
for k, m in enumerate([48, 55, 60, 64, 67, 72]):
    add(pluck(NOTE(m), 1.3, 0.4), 3.72 + k * 0.012, 0.35)
for k, m in enumerate([84, 88, 91, 96]):
    add(bell(NOTE(m), 0.9), 3.8 + k * 0.07, 0.12)

# --- sound effects ---
add(bell(1568, .7), 0.45, 0.22); add(bell(2093, .6), 0.45, 0.13)            # coin sparkle on "one coin"
add(noise_sweep(0.32, 400, 6000), 1.16, 0.55)                     # whip-pan whoosh
n = int(.25 * SR); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * (90 - 40 * tt / .25) * tt) * env(n, .002, .08), 2.0, 0.9)   # coin thud into dirt
for k in range(6):                                                # dirt patter
    add(rng.normal(0, 1, int(.03 * SR)) * env(int(.03 * SR), .001, .008), 2.05 + k * .06 + rng.uniform(0, .03), .25)
for k in range(8):                                                # comic "ha" boops while they laugh
    n = int(.09 * SR); tt = np.arange(n) / SR
    f = (520 if k % 2 else 600) * (1 - tt * 1.5)
    add(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .003, .04), 2.32 + k * .085, .07)
for k in range(10):                                               # time-lapse clock ticks
    n = int(.02 * SR)
    add(np.sin(2 * np.pi * 2400 * np.arange(n) / SR) * env(n, .0005, .004), 3.0 + k * .07, .3)
add(noise_sweep(0.7, 200, 3000, .6), 3.05, 0.5)                   # rising swell into the reveal
n = int(.18 * SR); tt = np.arange(n) / SR                         # "pop" as the tree bursts up
add(np.sin(2 * np.pi * (180 + 900 * tt / .18) * tt) * env(n, .001, .06), 3.72, .8)
for k in range(40):                                               # coin shower jingle
    f = rng.uniform(3000, 5200)
    add(bell(f, .25), 4.1 + rng.uniform(0, .85), rng.uniform(.03, .07))

mix = np.tanh(mix * 1.2)  # gentle soft clip / glue
fade = np.ones(N); fade[-int(.12 * SR):] = np.linspace(1, 0, int(.12 * SR))
mix *= fade
pcm = (np.stack([mix, mix], 1) * 0.9 * 32767).astype('<i2')
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
