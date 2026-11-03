"""Bande-son médiévale du « Rapport d'incident » (100 bpm, une mesure = 2,4 s = un plan).
Mêmes temps forts que la version 3, mais orchestre du Moyen Âge :
bourdon de cornemuse, bombarde, flûte à bec, vielle à roue, cor naturel, luth,
tambours de guerre (davul), tambourin, timbales (nacaires) et gong.
Modes anciens : ré dorien pour l'ennui, ré mixolydien pour la quête, quintes à vide."""
import numpy as np, wave, sys
from functools import lru_cache

SR = 44100
DUR = 26.0
N = int(SR * DUR)
mix = np.zeros(N)
rng = np.random.default_rng(21)
B = 0.6
BAR = 4 * B

def put(sig, t, g=1.0):
    i = int(round(t * SR))
    if i >= N or i < 0: return
    sig = sig[: N - i]; mix[i:i + len(sig)] += sig * g

def env(n, a=.005, r=.1):
    e = np.ones(n); A = min(n, max(1, int(a * SR))); R = min(n, max(1, int(r * SR)))
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def T(d): return np.arange(int(d * SR)) / SR

def lp(s, a):
    out = np.empty_like(s); y = 0.0
    for i, x in enumerate(s): y = a * y + (1 - a) * x; out[i] = y
    return out

# ---------------- instruments ----------------
def reed(f, t, n_h=16, tilt=0.75, odd=0.35):
    """Anche nasale (cornemuse, bombarde) : beaucoup d'harmoniques, les impaires renforcées."""
    ph = 2 * np.pi * f * t
    s = np.zeros_like(t)
    for k in range(1, n_h + 1):
        if k * f > 9000: break
        a = (1 / k ** tilt) * (1 + odd * (k % 2))
        if 3 <= k <= 6: a *= 1.5          # formant nasillard
        s += a * np.sin(k * ph)
    return s / 5

@lru_cache(None)
def chanter(m, d, grace=None, vol=1.0):
    """Note de cornemuse/bombarde, avec petite note d'agrément au début."""
    t = T(d); f = hz(m)
    fr = np.full_like(t, f)
    if grace is not None:
        g = int(.035 * SR); fr[:g] = hz(grace)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.8 * t) * (t > .15)
    s = np.zeros_like(t)
    for k in range(1, 15):
        if k * f > 9000: break
        a = (1 / k ** .7) * (1 + .4 * (k % 2)) * (1.5 if 3 <= k <= 6 else 1)
        s += a * np.sin(k * ph * vib)
    return s / 6 * env(len(t), .008, min(.06, d * .3)) * vol

@lru_cache(None)
def recorder(m, d):
    t = T(d); ph = 2 * np.pi * hz(m) * t
    breath = lp(rng.uniform(-1, 1, len(t)), .3) * .08
    s = np.sin(ph) + .25 * np.sin(2 * ph) + .08 * np.sin(3 * ph) + breath
    return s * env(len(t), .03, min(.08, d * .3)) * (1 + .03 * np.sin(2 * np.pi * 5 * t))

@lru_cache(None)
def horn(m, d):
    """Cor naturel / trompette de héraut."""
    t = T(d); f = hz(m)
    ph = 2 * np.pi * f * t + .2 * np.sin(2 * np.pi * 5 * t) * (t > .2)
    br = np.clip(t / .06, 0, 1) * .7 + .3
    s = sum((1 / k ** .9) * np.sin(k * ph) * br ** (k * .4) for k in range(1, 11))
    return s / 3.2 * env(len(t), .03, min(.15, d * .4))

@lru_cache(None)
def lute(m, d=.4):
    f = hz(m); n = int(d * SR); p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        j = i % p; out[i] = buf[j]; buf[j] = 0.496 * (buf[j] + buf[(j + 1) % p])
    return out * env(n, .002, .06)

def drone(m, d, buzz_beats=None):
    """Bourdon de cornemuse (deux tuyaux légèrement désaccordés) + chien de vielle."""
    t = T(d)
    s = reed(hz(m), t, 12, .9, .5) + .8 * reed(hz(m - 12) * 1.0015, t, 12, .9, .5)
    return s * env(len(t), .15, .3) * .5

def davul(g=1, f0=62):
    t = T(.5); f = f0 + 70 * np.exp(-t * 25)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    skin = lp(rng.uniform(-1, 1, len(t)), .55) * np.exp(-t * 35)
    return (body + .45 * skin) * g
DAVUL = davul(.75); DAVUL_HI = davul(.8, 140)
def frame_drum():
    t = T(.25); f = 180 + 60 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) + .6 * lp(rng.uniform(-1, 1, len(t)), .2) * np.exp(-t * 40)
FRAME = frame_drum()
def tamb():
    t = T(.14); n = rng.uniform(-1, 1, len(t)); n = n - lp(n, .4)
    jingle = sum(np.sin(2 * np.pi * f * t) for f in (5200, 6900, 8300)) * .15
    return (n + jingle) * np.exp(-t * 28)
TAMB = tamb()
def naker():  # petites timbales médiévales
    t = T(.2); return np.sin(2 * np.pi * 330 * t) * np.exp(-t * 25) + .3 * rng.uniform(-1, 1, len(t)) * np.exp(-t * 60)
NAKER = naker()
def gong(d=3.0):
    t = T(d); s = np.zeros_like(t)
    for f, a, dec in [(98, 1, 1.0), (141, .7, 1.3), (196, .6, 1.6), (277, .5, 2.0), (389, .35, 2.4), (523, .25, 3.0), (707, .2, 3.6)]:
        s += a * np.sin(2 * np.pi * f * t * (1 + .002 * np.sin(2 * np.pi * .7 * t))) * np.exp(-t * dec)
    s += .4 * lp(rng.uniform(-1, 1, len(t)), .5) * np.exp(-t * 12)
    return s * env(len(t), .004, .3) / 2.5
GONG = gong()
def bell(f=1318, d=1.2):
    t = T(d); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.4 * t) + .25 * np.sin(2 * np.pi * f * 3.9 * t)) * np.exp(-t * 3.5)
def tick(): t = T(.03); return np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 180)
def whoosh(d=.32):
    t = T(d); n = lp(rng.uniform(-1, 1, len(t)), .8); return n * np.sin(np.pi * t / d) ** 2 * 2.2

def hurdy_chien(m, t0, beats, g=.25):
    """Coups rythmés du chien de la vielle à roue (le grésillement qui marque le temps)."""
    for b in beats:
        t = T(.12); f = hz(m)
        saw = 2 * ((f * t) % 1) - 1
        buzz = saw * (1 + .6 * np.sign(np.sin(2 * np.pi * 60 * t)))
        put(buzz * np.exp(-t * 18) * .6, t0 + b * B, g)

def fanfare(notes, t0, g=.5, oct_=0):
    for m, bt, d in notes:
        put(horn(m + oct_, d * B * .95), t0 + bt * B, g)

# ===== « Mission : décoller Léo de sa tablette » : 21,6 s, 100 bpm, en sol (troisième variante) =====
N = int(SR * 21.6); mix = np.zeros(N)
TR = -2                                   # un ton plus bas que la vidéo des bougies : couleur différente
def m_(x): return x + 5 + TR              # ré -> sol
TRIP = B / 3
def puff(t0, g=1.0):
    t = T(.5); n = lp(rng.uniform(-1, 1, len(t)), .7) * np.exp(-t * 9)
    put(n, t0, .9 * g); put(DAVUL_HI, t0, .7 * g); put(NAKER, t0, .5 * g)
    tt = T(.45); f = hz(m_(72)) * (1 - .35 * (tt / tt[-1]))
    s = sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(tt), .01, .12)
    put(s, t0 + .05, .45 * g)
def drums(t0, bars, g=1.0, stop=99, trip=True):
    for bar in range(bars):
        b0 = t0 + bar * BAR
        for k in range(4):
            tk = b0 + k * B
            if tk < stop: put(DAVUL, tk, (.9 if k % 2 == 0 else .6) * g)
            if trip and tk + 2 * TRIP < stop: put(DAVUL, tk + 2 * TRIP, .4 * g)
            if k % 2 and tk < stop: put(FRAME, tk, .8 * g); put(NAKER, tk, .4 * g)
            for j in range(3 if trip else 4):
                d = j * (TRIP if trip else B / 4)
                if tk + d < stop: put(TAMB, tk + d, (.28 if j == 0 else .14) * g)
def chip(f, d, g=1.0):                    # petit son de jeu vidéo (onde carrée)
    t = T(d); return np.sign(np.sin(2 * np.pi * f * t)) * env(len(t), .002, .02) * .35 * g

# ---- A. 0 -> 7,2 : gigue moqueuse (crumhorn + flûte), deux « pouf » sur les tampons ----
put(DAVUL, 0, 1.2); put(GONG, 0, .35); put(DAVUL_HI, .02, .5)
put(drone(m_(50), 7.25), 0, .18)
drums(0, 3, .75, stop=7.15)
mock = [74, 74, 77, 76, 74, 72, 74, 70, 72, 74, 69, 69]          # 12 triolets par mesure
for bar in range(3):
    for i, m in enumerate(mock):
        tt = bar * BAR + i * TRIP
        if bar >= 1 and bar * BAR + 1.05 <= tt <= bar * BAR + 1.55: continue
        put(chanter(m_(m) - 12, TRIP * .85, None, .7), tt, .4)
        if i % 3 == 0: put(recorder(m_(m), TRIP * .8), tt, .25)
    for i, m in enumerate([43, 50, 55, 50]): put(lute(m_(m), .3), bar * BAR + i * B, .45)
puff(3.6); puff(6.0, 1.15)

# ---- B. 7,2 -> 9,6 : le Grand Maître entre (gong, cors, carillon) ----
G0 = 3 * BAR
put(GONG, G0, .8); put(DAVUL, G0, 1.3)
for m in [50, 57, 62, 69]: put(horn(m_(m), 1.2), G0, .3)
call = [(62, .5, .5), (62, 1, .25), (62, 1.25, .25), (69, 1.5, 1.0), (66, 2.5, .5), (69, 3, .9)]
for m, bt, d in call: put(horn(m_(m), d * B * .95), G0 + bt * B, .55)
for i in range(6): put(bell(1568 * 2 ** ((5 - 2) / 12) + i * 90, .5), G0 + 1.4 + i * .08, .07)
steps = []; x = G0 + 1.6; dt = .2
while x < G0 + BAR - .1:
    steps.append(x); x += dt; dt = max(.045, dt * .8)
for i, s in enumerate(steps): put(DAVUL_HI, s, .3 + .6 * i / len(steps))
rev = GONG[: int(.9 * SR)][::-1]; put(rev, 4 * BAR - .9, .45)

# ---- C. 9,6 -> 14,4 : la course (cornemuse, estampie, tambours de guerre) ----
C0 = 4 * BAR
put(DAVUL, C0, 1.4); put(GONG, C0, .45)
put(drone(m_(50), 2 * BAR + .05), C0, .28)
air = [(74, 0, .5), (76, .5, .5), (78, 1, .5), (79, 1.5, .5), (81, 2, 1), (83, 3, .5), (81, 3.5, .5),
       (79, 4, .5), (81, 4.5, .5), (83, 5, .5), (86, 5.5, .5), (83, 6, 1), (81, 7, .5), (79, 7.5, .5)]
for m, bt, d in air:
    gr = m + 2 if bt % 1 == 0 else None
    put(chanter(m_(m) - 12, d * B * .97, (m_(gr) - 12) if gr else None), C0 + bt * B, .9)
    put(chanter(m_(m), d * B * .97, m_(gr) if gr else None, .5), C0 + bt * B, .2)
for half in range(4):
    r = [50, 50, 55, 57][half]
    for k in range(4): put(lute(m_([r, r + 7, r + 12, r + 7][k]), .3), C0 + half * 2 * B + k * B / 2, .38)
for bar in range(2):
    b0 = C0 + bar * BAR
    for k in range(16):
        put(DAVUL, b0 + k * B / 4, .75 if k % 4 == 0 else (.4 if k % 2 == 0 else .2))
        put(TAMB, b0 + k * B / 4, .2 if k % 2 == 0 else .12)
    for k in [1, 3]: put(FRAME, b0 + k * B, .75); put(NAKER, b0 + k * B, .4)
    put(GONG[: int(.4 * SR)] * np.linspace(1, 0, int(.4 * SR)), b0, .2)
    hurdy_chien(m_(50) - 12, b0, [0, .5, 1, 1.5, 2, 2.5, 3, 3.5], .18)

# ---- D. 14,4 -> 16,8 : chute — tout s'arrête, petite musique de jeu vidéo ----
D0 = 6 * BAR
put(DAVUL, D0, .9)
c0, c1 = int(D0 * SR), int((D0 + .12) * SR); mix[c0:c1] *= np.linspace(1, 0, c1 - c0)
tune = [(988, 0), (1175, .15), (1319, .3), (1175, .45), (988, .75), (880, .9), (988, 1.2), (1319, 1.35), (1568, 1.5), (1319, 1.8), (1175, 1.95)]
for f, dt_ in tune: put(chip(f, .12), D0 + .15 + dt_, .5)
for k in range(4): put(chip(110 if k % 2 == 0 else 147, .1, .8), D0 + .15 + k * B, .4)
put(NAKER, D0 + 2.2, .4)

# ---- E. 16,8 -> 21,6 : fanfare finale, accord final sur le temps, qui s'éteint ----
E0 = 7 * BAR
FIN = E0 + 7 * B                                         # 21,0 s
put(DAVUL, E0, 1.3); put(GONG, E0, .35)
dr = drone(m_(50), FIN - E0 + .6); dr[int((FIN - E0) * SR):] *= np.linspace(1, 0, len(dr) - int((FIN - E0) * SR)) ** 1.5
put(dr, E0, .25)
fin = [(74, 0, .33), (74, .33, .33), (74, .67, .33), (78, 1, .67), (81, 1.67, .33), (86, 2, 1), (81, 3, .67), (78, 3.67, .33),
       (79, 4, .67), (78, 4.67, .33), (76, 5, .67), (78, 5.67, .33), (81, 6, .9)]
for m, bt, d in fin:
    put(horn(m_(m) - 12, d * B * .95), E0 + bt * B, .62); put(horn(m_(m) - 24, d * B * .95), E0 + bt * B, .13)
drums(E0, 2, .9, stop=FIN - .01)
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
g = GONG[: int(.58 * SR)].copy(); g *= np.linspace(1, 0, len(g)) ** 1.2; put(g, FIN, .55)
for m in [38, 50, 57, 62, 69, 74]:
    h = horn(m_(m) - 12, .55).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

W_ = whoosh()
for k in (1, 2, 3, 4, 6, 7): put(W_, k * BAR - .2, .28)
mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.35) * .96
mix[int(21.52 * SR):] *= np.linspace(1, 0, N - int(21.52 * SR))
with wave.open('son7.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son7.wav')
