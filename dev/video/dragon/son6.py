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

# ============ « Souffle les bougies » : 7,2 s, gigue médiévale en mi, 100 bpm ============
N = int(SR * 7.2); mix = np.zeros(N)
TR = 2
def m_(x): return x + TR
TRIP = B / 3
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

# ---- 0 -> 2,4 s : la gigue démarre, le dragon gonfle les joues ----
put(DAVUL, 0, 1.2); put(GONG, 0, .35)
put(drone(m_(52) - 2, 2.4), 0, .2)
jig_drums(0, 1, .8, stop=2.0)
jig = [76, 79, 81, 79, 76, 74, 76, 79, 83]
for i, m in enumerate(jig):
    put(recorder(m_(m), TRIP * .9), i * TRIP, .45)
for i, m in enumerate([40, 47, 52]): put(lute(m_(m) + 12, .3), i * B, .45)
t = T(.9); inhale = lp(rng.uniform(-1, 1, len(t)), .9) * (t / t[-1]) ** 2 * 3     # grande inspiration
inhale[int(.42 * SR):] *= np.linspace(1, 0, len(inhale) - int(.42 * SR)) ** 3
put(inhale, 1.5, .5)
tt = T(.8); f = hz(m_(64)) * (1 + .5 * (tt / tt[-1]) ** 2)                         # bombarde qui monte
put(sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 9)) / 5 * env(len(tt), .05, .05), 1.6, .3)

# ---- 1,92 -> 2,4 s : rugissement du souffle de feu (bruit grave qui enfle + crépitements) ----
t = T(.52); roar = lp(rng.uniform(-1, 1, len(t)), .82)
roar *= np.clip(t / .06, 0, 1) * (0.7 + 0.3 * t / t[-1]) * (1 + .25 * np.sin(2 * np.pi * 11 * t))
put(roar * 2.4, 1.92, .55)
rum = np.sin(2 * np.pi * np.cumsum(70 + 30 * np.sin(2 * np.pi * 7 * t)) / SR) * np.clip(t / .05, 0, 1)
put(rum, 1.92, .35)
cr = rng.uniform(-1, 1, len(t)) * (rng.random(len(t)) < .015); put(cr, 1.95, .9)
# ---- 2,4 s : POUF (souffle de feu) ----
P0 = BAR
t = T(1.0); boom = lp(rng.uniform(-1, 1, len(t)), .75) * np.exp(-t * 3.5) * 2.2
put(boom, P0, .9); put(DAVUL, P0, 1.6); put(GONG, P0, .8); put(DAVUL_HI, P0, .8)
t = T(.6); crack = rng.uniform(-1, 1, len(t)) * (rng.random(len(t)) < .02) * np.exp(-t * 4)  # crépitement
put(crack, P0 + .1, 1.2)
# ---- 2,4 -> 4,8 s : silence gêné, plainte de bombarde, petit « pof pof » ----
tt = T(.9); f = hz(m_(67)) * (1 - .35 * (tt / tt[-1]) ** 1.3)
put(sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(tt), .02, .25), P0 + 1.0, .5)
put(NAKER, P0 + 1.95, .5); put(NAKER, P0 + 2.15, .5)
put(DAVUL, P0 + 2.4 - .6, .4); put(DAVUL, P0 + 2.4 - .3, .55)

# ---- 4,8 -> 7,2 s : fanfare de l'écran final ----
E0 = 2 * BAR
FIN = E0 + 3 * B                     # 6,6 s : accord final sur le dernier temps, qui s'éteint avant la coupe
put(DAVUL, E0, 1.3); put(GONG, E0, .35)
dr = drone(m_(52) - 2, 2.35); dr[int(1.8 * SR):] *= np.linspace(1, 0, len(dr) - int(1.8 * SR)) ** 1.5
put(dr, E0, .25)
fin = [(76, 0, .33), (76, .33, .33), (76, .67, .33), (80, 1, .67), (83, 1.67, .33), (88, 2, .67), (83, 2.67, .33)]
for m, bt, d in fin:
    put(horn(m_(m) - 2, d * B * .95), E0 + bt * B, .62); put(horn(m_(m) - 14, d * B * .95), E0 + bt * B, .13)
jig_drums(E0, 1, .9, stop=FIN - .01)
for k in range(6): put(lute(m_([64, 71, 76, 71][k % 4]) - 2, .3), E0 + k * B / 2, .28)
# accord final : court, avec une queue qui décroît jusqu'à 7,15 s
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
g = GONG[: int(.58 * SR)].copy(); g *= np.linspace(1, 0, len(g)) ** 1.2; put(g, FIN, .55)
for m in [40, 52, 59, 64, 71, 76]:
    h = horn(m_(m) - 2, .55).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)
for m in [64, 71, 76, 83]: put(lute(m_(m) - 2, .55), FIN + .01, .3)

W_ = whoosh()
put(W_, BAR - .2, .25); put(W_, 2 * BAR - .2, .3)
mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.35) * .96
mix[int(7.12 * SR):] *= np.linspace(1, 0, N - int(7.12 * SR))
with wave.open('son6.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son6.wav')
