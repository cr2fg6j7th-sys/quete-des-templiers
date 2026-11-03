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

# ================== FÊTE PARFAITE : gigue médiévale en mi (même tempo, 100 bpm) ==================
TR = 2                       # tout un ton plus haut que la vidéo précédente (mi au lieu de ré)
def m_(x): return x + TR
TRIP = B / 3                 # croche de triplet : rythme de gigue / saltarello
def puff(t0, g=1.0):
    """« Pouf » comique : petit nuage + glissando de bombarde qui retombe."""
    t = T(.5); n = lp(rng.uniform(-1, 1, len(t)), .7) * np.exp(-t * 9)
    put(n, t0, .9 * g); put(DAVUL_HI, t0, .7 * g); put(NAKER, t0, .5 * g)
    tt = T(.45); f = hz(m_(72)) * (1 - .35 * (tt / tt[-1]))
    s = sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(tt), .01, .12)
    put(s, t0 + .05, .45 * g)

def jig_drums(t0, bars=1, g=1.0, stop=99):
    for bar in range(bars):
        b0 = t0 + bar * BAR
        for k in range(4):
            tk = b0 + k * B
            if tk < stop: put(DAVUL, tk, (.9 if k % 2 == 0 else .6) * g)
            if tk + 2 * TRIP < stop: put(DAVUL, tk + 2 * TRIP, .4 * g)
            if k % 2 and tk < stop: put(FRAME, tk, .8 * g); put(NAKER, tk, .4 * g)
            for j in range(3):
                if tk + j * TRIP < stop: put(TAMB, tk + j * TRIP, (.28 if j == 0 else .15) * g)

# ---------- A. la préparation : gigue légère à la flûte, 0 -> 7,2 s ----------
put(DAVUL, 0, 1.2); put(GONG, 0, .4); put(DAVUL_HI, .02, .5)
put(drone(m_(52) - 2, 7.25), 0, .2)
jig_drums(0, 3, .75)
# flûte qui sautille (gigue), coupée à chaque « pouf »
jig = [76, 79, 81, 79, 76, 74, 76, 79, 83, 81, 79, 76]   # 12 triplets = une mesure
for bar in range(3):
    for i, m in enumerate(jig):
        tt = bar * BAR + i * TRIP
        if bar >= 1 and abs(tt - (bar * BAR + 1.2)) < 0.42 and tt >= bar * BAR + 1.0: continue   # silence autour du pouf
        put(recorder(m_(m) + (0 if bar == 0 else -2 * (bar == 2)), TRIP * .9), tt, .42)
    for i, m in enumerate([40, 47, 52, 47]):
        put(lute(m_(m) + 12, .3), bar * BAR + i * B, .45)
    hurdy_chien(m_(52) - 12, bar * BAR, [0, 1, 2, 3], .16)
puff(3.6); puff(6.0, 1.1)

# ---------- B. le gâteau brûle + montée : 7,2 -> 9,6 s ----------
t0 = 3 * BAR
put(drone(m_(52) - 2, BAR - .1), t0, .22)
jig_drums(t0, 1, .7, stop=8.35)
puff(8.4, 1.25)
steps = []; x = 8.6; dt = .18
while x < 9.45:
    steps.append(x); x += dt; dt = max(.04, dt * .82)
for i, s in enumerate(steps):
    put(DAVUL_HI, s, .4 + .7 * i / len(steps)); put(NAKER, s, .2 + .4 * i / len(steps))
for i, m in enumerate([64, 66, 67, 69, 71, 72]):
    put(chanter(m_(m), .14, None, .9), 8.65 + i * .14, .5)
rev = GONG[: int(1.1 * SR)][::-1]; put(rev, 9.6 - 1.1, .6)

# ---------- C. ALERTE, le Grand Maître confisque le briquet : 9,6 -> 14,4 s ----------
D = 4 * BAR
put(DAVUL, D, 1.6); put(GONG, D, .9); put(DAVUL_HI, D, .8)
for m in [52, 59, 64, 71]: put(horn(m_(m) - 2, 1.0), D, .35)
put(drone(m_(52) - 2, 2 * BAR + .05), D, .28)
for bar in range(2):
    t0 = D + bar * BAR
    for k in range(12):                                   # tambours de guerre en triolets
        put(DAVUL, t0 + k * TRIP, .8 if k % 3 == 0 else .3)
        put(TAMB, t0 + k * TRIP, .2 if k % 3 == 0 else .12)
    for k in [1, 3]: put(FRAME, t0 + k * B, .7); put(NAKER, t0 + k * B, .4)
    call = [(64, 0, .33), (64, .33, .33), (64, .67, .33), (71, 1, 1), (68, 2, .67), (71, 2.67, .33), (76, 3, 1)] if bar == 0 else \
           [(76, 0, .33), (76, .33, .33), (76, .67, .33), (79, 1, .67), (78, 1.67, .33), (76, 2, .67), (71, 2.67, .33), (76, 3, 1)]
    for m, bt, d in call:
        put(horn(m_(m) - 2, d * B * .95), t0 + bt * B, .62); put(horn(m_(m) - 14, d * B * .95), t0 + bt * B, .13)
    for k in range(4): put(lute(m_([40, 47, 52, 47][k]) + 10, .4), t0 + k * B, .4)
for x in [12.35, 12.55, 12.75, 13.1, 13.22, 13.34, 13.46, 13.58]: put(tick(), x, .45)
put(bell(1480, 1.0), 13.8, .4); put(bell(1976, 1.0), 13.86, .2)
for i in range(6): put(DAVUL_HI, 13.8 + i * TRIP / 1.0 * .5, .3 + .1 * i)

# ---------- D. la quête : gigue à la cornemuse, mi mixolydien : 14,4 -> 21,6 s ----------
M = 6 * BAR
stop = 20.2
put(GONG, M, .35); put(DAVUL, M, 1.2)
put(drone(m_(52) - 2, stop - M + .05), M, .3)
tune = [  # (note, triolet) : 12 triolets par mesure, 2 mesures et demie
    (76, 0), (78, 1), (80, 2), (81, 3), (83, 5), (81, 6), (80, 7), (78, 8), (80, 9), (78, 10), (76, 11),
    (74, 12), (76, 13), (78, 14), (80, 15), (83, 17), (85, 18), (83, 20), (81, 21), (80, 22), (78, 23),
    (76, 24), (80, 25), (83, 26), (88, 27), (86, 29)]
for i, (m, k) in enumerate(tune):
    tt = M + k * TRIP
    nxt = tune[i + 1][1] if i + 1 < len(tune) else k + 3
    d = (nxt - k) * TRIP * .96
    if tt >= stop: break
    gr = m + 2 if k % 3 == 0 else None
    put(chanter(m_(m) - 12, d, (m_(gr) - 12) if gr else None), tt, .9)
    put(chanter(m_(m), d, m_(gr) if gr else None, .5), tt, .2)
for half in range(5):
    t0 = M + half * 2 * B
    r = [40, 40, 45, 38, 40][half]
    for k in range(6):
        if t0 + k * TRIP * 2 < stop: put(lute(m_([r + 12, r + 19, r + 24][k % 3]), .3), t0 + k * 2 * TRIP, .38)
jig_drums(M, 3, 1.0, stop=stop)
hurdy_chien(m_(52) - 12, M, [b for b in [0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9] if M + b * B < stop], .18)
for i in range(6): put(bell(2217 + i * 160, .5), 16.85 + i * .1, .08)     # lettre dorée (plan 8)
# chute : tout s'arrête, « REFUSÉ » tombe sur le temps, petite plainte de bombarde
c0, c1 = int(stop * SR), int(20.4 * SR)
mix[c0:c1] *= np.linspace(1, 0, c1 - c0) ** 3
put(DAVUL, 20.4, 1.6); put(GONG, 20.4, .7); put(DAVUL_HI, 20.4, .7)
for m in [52, 59, 64]: put(horn(m_(m) - 2, .5), 20.4, .3)
tt = T(.7); f = hz(m_(64)) * (1 - .3 * (tt / tt[-1]) ** 1.3)
s = sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(tt), .01, .2)
put(s, 20.75, .45)
put(NAKER, 21.15, .5); put(NAKER, 21.35, .5)

# ---------- E. écran final : 21,6 -> 26 s ----------
E0 = 9 * BAR
put(drone(m_(52) - 2, 4.4), E0, .26); put(GONG, E0, .25)
fin = [(76, 0, .33), (76, .33, .33), (76, .67, .33), (80, 1, .67), (83, 1.67, .33), (88, 2, 1), (83, 3, .67), (80, 3.67, .33),
       (81, 4, .67), (80, 4.67, .33), (78, 5, .67), (80, 5.67, .33)]
for m, bt, d in fin:
    put(horn(m_(m) - 2, d * B * .95), E0 + bt * B, .62); put(horn(m_(m) - 14, d * B * .95), E0 + bt * B, .13)
jig_drums(E0, 2, .9, stop=E0 + 6 * B)
for k in range(12): put(lute(m_([64, 71, 76, 71][k % 4]) - 2, .3), E0 + k * B / 2, .28)
FIN = E0 + 6 * B
put(DAVUL, FIN, 1.6); put(GONG, FIN, .8)
for m in [40, 52, 59, 64, 71, 76]: put(horn(m_(m) - 2, .65), FIN, .3)

W_ = whoosh()
for k in range(1, 10): put(W_, k * BAR - .2, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.35) * .96
mix[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))
out = sys.argv[1] if len(sys.argv) > 1 else 'son5.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok', out)
