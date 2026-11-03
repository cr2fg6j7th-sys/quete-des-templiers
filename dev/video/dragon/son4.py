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

# =========== A. l'ennui, en ré dorien : 0 -> 7,2 s ===========
put(DAVUL, 0, 1.2); put(GONG, 0, .45); put(DAVUL_HI, .02, .5)        # coup du titre
put(drone(50, 7.25), 0, .22)                                            # bourdon ré-la
for bar in range(3):
    t0 = bar * BAR
    for k, (d, g) in enumerate([(0, 1), (1.5, .55), (2, .85), (3, .6), (3.5, .45)]):
        put(DAVUL, t0 + d * B, .75 * g)
    for k in range(8): put(TAMB, t0 + k * B / 2, .22 if k % 2 else .32)
    for k in [1, 3]: put(FRAME, t0 + k * B, .45)
    hurdy_chien(50, t0, [0.5, 1.5, 2.5, 3.5], .2)
    for i, m in enumerate([38, 45, 38, 45, 36, 43, 36, 43] if bar < 2 else [34, 41, 34, 41, 33, 40, 33, 45]):
        put(lute(m + 12, .3), t0 + i * B / 2, .55)
# la flûte qui soupire (ré dorien : ré fa mi ré do ré)
motif = [(74, 0, .5), (77, .5, .5), (76, 1, .5), (74, 1.5, 1.0), (72, 2.5, .5), (74, 3, .9)]
for bar in range(3):
    tr = [0, -2, -3][bar]
    for m, bt, d in motif:
        put(recorder(m + tr, d * B * .9), bar * BAR + bt * B, .5)
        put(chanter(m + tr - 12, d * B * .9, None, .6), bar * BAR + bt * B, .2)

# =========== B. la montée : 7,2 -> 9,6 s ===========
t0 = 3 * BAR
put(drone(50, BAR - .1), t0, .25)
steps = []; x = t0; dt = B / 2
while x < t0 + BAR - .2:
    steps.append(x); x += dt; dt = max(.045, dt * .85)
for i, s in enumerate(steps):
    put(DAVUL_HI, s, .35 + .7 * i / len(steps)); put(NAKER, s, .2 + .4 * i / len(steps))
for i, m in enumerate([62, 64, 65, 67, 69, 71, 72, 74]):               # la bombarde grimpe
    put(chanter(m, B / 2 * .9, m + 2, .9), t0 + i * B / 2, .55)
t = T(BAR - .15); sw = lp(rng.uniform(-1, 1, len(t)), .88) * (t / t[-1]) ** 2 * 3
put(sw, t0, .55)
rev = GONG[: int(1.4 * SR)][::-1]; put(rev, 4 * BAR - 1.4, .7)

# =========== C. IMPACT + quête qui s'éveille : 9,6 -> 14,4 s ===========
D = 4 * BAR
put(DAVUL, D, 1.6); put(GONG, D, .9); put(DAVUL_HI, D, .8)
for m in [50, 57, 62, 69]: put(horn(m, 1.1), D, .35)                    # quinte à vide, très médiéval
for i, m in enumerate([62, 66, 69, 74, 78, 81, 86]):
    put(lute(m, .5), D + .04 + i * .045, .35)
put(drone(50, 2 * BAR + .05), D, .3)
for bar in range(2):
    t0 = D + bar * BAR
    for k in range(16):                                                  # tambours de guerre en doubles croches
        put(DAVUL, t0 + k * B / 4, .75 if k % 4 == 0 else (.42 if k % 2 == 0 else .24))
        put(TAMB, t0 + k * B / 4, .16 if k % 2 else .24)
    for k in [1, 3]: put(FRAME, t0 + k * B, .7); put(NAKER, t0 + k * B, .4)
    hurdy_chien(50, t0, [0, .5, 1, 1.5, 2, 2.5, 3, 3.5], .22)
    # appel de cor de héraut sur les harmoniques naturelles
    fanfare([(62, 0, .5), (62, .5, .25), (62, .75, .25), (69, 1, 1), (66, 2, .5), (69, 2.5, .5), (74, 3, 1)] if bar == 0 else
            [(74, 0, .5), (74, .5, .25), (74, .75, .25), (78, 1, .5), (76, 1.5, .5), (74, 2, .5), (69, 2.5, .5), (74, 3, 1)], t0, .7)
    fanfare([(62, 0, .5), (62, .5, .25), (62, .75, .25), (69, 1, 1), (66, 2, .5), (69, 2.5, .5), (74, 3, 1)] if bar == 0 else
            [(74, 0, .5), (74, .5, .25), (74, .75, .25), (78, 1, .5), (76, 1.5, .5), (74, 2, .5), (69, 2.5, .5), (74, 3, 1)], t0, .15, -12)
    for k in range(8): put(lute([50, 57, 62, 57][k % 4] + (0 if bar == 0 else 2 * (k >= 4)), .3), t0 + k * B / 2, .4)
for x in [12.35, 12.55, 12.75, 13.1, 13.22, 13.34, 13.46, 13.58]: put(tick(), x, .45)
put(bell(), 13.8, .4); put(bell(1760, 1.0), 13.86, .2)
for i in range(8): put(DAVUL_HI, 13.8 + i * B / 8, .25 + .08 * i)

# =========== D. la quête : marche à la cornemuse, ré mixolydien : 14,4 -> 21,6 s ===========
M = 6 * BAR
stop = 20.4
put(GONG, M, .35); put(DAVUL, M, 1.2)
put(drone(50, stop - M + .05), M, .3)
# air d'estampie (ré mixolydien : do bécarre)
air = [
    (74, 0, .5), (76, .5, .5), (78, 1, .5), (79, 1.5, .5), (81, 2, 1), (79, 3, .5), (78, 3.5, .5),
    (76, 4, .5), (78, 4.5, .5), (79, 5, .5), (81, 5.5, .5), (83, 6, .5), (81, 6.5, .5), (79, 7, .5), (78, 7.5, .5),
    (76, 8, .5), (74, 8.5, .5), (72, 9, .5), (74, 9.5, .5), (76, 10, .5), (78, 10.5, .5), (74, 11, 1)]
prev = None
for m, bt, d in air:
    tt = M + bt * B
    if tt >= stop: break
    gr = m + 2 if (prev is None or prev == m or bt % 1 == 0) else None
    put(chanter(m - 12, d * B * .97, (gr - 12) if gr else None), tt, .95)
    put(chanter(m, d * B * .97, gr, .5), tt, .22)
    prev = m
chords = [50, 50, 55, 48, 50, 45]                                        # basses du luth (do bécarre au 4e)
for half in range(6):
    t0 = M + half * 2 * B
    if t0 >= stop: break
    for k in range(4):
        r = chords[half]
        put(lute([r + 12, r + 19, r + 24, r + 19][k], .3), t0 + k * B / 2, .4)
for bar in range(3):
    t0 = M + bar * BAR
    for k in range(4):
        tk = t0 + k * B
        if tk >= stop: continue
        put(DAVUL, tk, 1.0 if k % 2 == 0 else .7)
        if tk + B / 2 < stop: put(DAVUL, tk + B / 2, .45)
        if k % 2: put(FRAME, tk, .8); put(NAKER, tk, .45)
    for k in range(16):
        tk = t0 + k * B / 4
        if tk < stop: put(TAMB, tk, .18 if k % 4 else .3)
    hurdy_chien(50, t0, [b for b in [0, .5, 1, 1.5, 2, 2.5, 3, 3.5] if t0 + b * B < stop], .2)
for i in range(6): put(bell(2093 + i * 160, .5), 16.85 + i * .1, .08)    # émerveillement du plan 8
# chute : la cornemuse se dégonfle, deux « bonk », puis le tampon sur le temps
cut0, cut1 = int(stop * SR), int(21.0 * SR)
mix[cut0:cut1] *= np.linspace(1, 0, cut1 - cut0) ** 4
t = T(.55); f = hz(62) * (1 - .45 * (t / t[-1]) ** 1.5)
deflate = sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(t), .01, .15)
put(deflate, stop, .5)
put(DAVUL_HI, 20.6, .4); put(NAKER, 20.78, .5)
put(DAVUL, 21.0, 1.6); put(GONG, 21.0, .7)
for m in [50, 57, 62, 69]: put(horn(m, .5), 21.0, .32)

# =========== E. écran final : fanfare de héraut, 21,6 -> 26 s ===========
E0 = 9 * BAR
put(drone(50, 4.4), E0, .28); put(GONG, E0, .25)
fanfare([(74, 0, .5), (74, .5, .25), (74, .75, .25), (78, 1, .5), (81, 1.5, .5), (86, 2, 1), (81, 3, .5), (78, 3.5, .5),
         (79, 4, .5), (78, 4.5, .5), (76, 5, .5), (78, 5.5, .5)], E0, .7)
fanfare([(74, 0, .5), (74, .5, .25), (74, .75, .25), (78, 1, .5), (81, 1.5, .5), (86, 2, 1), (81, 3, .5), (78, 3.5, .5),
         (79, 4, .5), (78, 4.5, .5), (76, 5, .5), (78, 5.5, .5)], E0, .14, -12)
for k in range(12):
    tk = E0 + k * B / 2
    put(DAVUL, tk, .9 if k % 2 == 0 else .4)
    if k % 4 == 2: put(FRAME, tk, .8); put(NAKER, tk, .4)
    put(TAMB, tk, .2); put(TAMB, tk + B / 4, .12)
    put(lute([62, 69, 74, 69][k % 4], .3), tk, .3)
FIN = E0 + 6 * B
put(DAVUL, FIN, 1.6); put(GONG, FIN, .8)
for m in [38, 50, 57, 62, 69, 74]: put(horn(m, .65), FIN, .3)

# ---------- whoosh sur les coupes ----------
W_ = whoosh()
for k in range(1, 10): put(W_, k * BAR - .2, .3)

# ---------- sortie ----------
mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.35) * .96
mix[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))
out = sys.argv[1] if len(sys.argv) > 1 else 'son4.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok', out)
