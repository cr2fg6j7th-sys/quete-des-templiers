"""Bande-son de « Le dragon doit annoncer l'ouverture » (26 s) : marche médiévale, feu, pigeon,
éternuement, « bip », grosse fanfare de l'ouverture, « pouet » et trombone triste, accord final.
Les instants viennent de annonce.py (même découpage)."""
import numpy as np, wave
exec(open('son4.py').read().split('# =========== A.')[0])
import re
src = open('annonce.py').read()
def const(name): return float(re.search(rf'^{name} = ([0-9.]+)', src, re.M).group(1))
ATCHOUM_T, BIP_T, POUET_T, END, FIN0 = const('ATCHOUM_T'), const('BIP_T'), const('POUET_T'), const('END'), const('FIN0')
STAMPS = [4.9, 7.9, 10.9]

DUR = END; N = int(SR * DUR); mix = np.zeros(N)
TRIP = B / 3

def drums(t0, t1, g=1.0):
    k = 0
    while t0 + k * B < t1:
        tk = t0 + k * B
        put(DAVUL, tk, (.9 if k % 2 == 0 else .6) * g)
        if tk + 2 * TRIP < t1: put(DAVUL, tk + 2 * TRIP, .4 * g)
        if k % 2: put(FRAME, tk, .8 * g); put(NAKER, tk, .4 * g)
        for j in range(3):
            if tk + j * TRIP < t1: put(TAMB, tk + j * TRIP, (.28 if j == 0 else .15) * g)
        k += 1
def fan(notes, t0, g=.6):
    for m, bt, d in notes:
        put(horn(m - 12, d * B * .95), t0 + bt * B, g); put(horn(m - 24, d * B * .95), t0 + bt * B, g * .2)
def cut(t0, t1, fade=.04):
    a, b = int((t0 - fade) * SR), int(t0 * SR); mix[a:b] *= np.linspace(1, 0, b - a); mix[b:int(t1 * SR)] = 0
def roar(t, d=1.6, g=.9):
    tt = T(d); n = lp(rng.uniform(-1, 1, len(tt)), .7)
    crack = (rng.uniform(0, 1, len(tt)) > .9985) * rng.uniform(-1, 1, len(tt)) * 6
    put((n * 2.2 + lp(crack, .3)) * np.exp(-tt * 1.6) * np.clip(tt / .05, 0, 1), t, g)
def claps(t, n=6, g=.5):
    for i in range(n):
        tt = T(.06); put(lp(rng.uniform(-1, 1, len(tt)), .2) * np.exp(-tt * 70) * 1.4, t + i * .16 + rng.uniform(0, .02), g)
def stamp(t, g=1.0):
    put(DAVUL, t, 1.3 * g); put(NAKER, t, .6 * g); put(whoosh(.18), t - .12, .25 * g)
def roll(t0, t1, g=.35):                    # roulement de tambour
    k = 0
    while t0 + k * .05 < t1:
        put(TAMB, t0 + k * .05, g * (.6 + .4 * (k % 2)) * (0.5 + 0.5 * (k * .05) / max(.1, t1 - t0))); k += 1
def glide(f0, f1, d, g=.4, harm=6, vib=0.0):
    tt = T(d); f = np.linspace(f0, f1, len(tt)) * (1 + vib * np.sin(2 * np.pi * 6 * tt))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k ** .9) * np.sin(k * ph) for k in range(1, harm + 1)) / 2.5
    return s * env(len(tt), .01, .08) * g
def flaps(t0, d, rate=9, g=.45):            # battements d'ailes
    k = 0
    while k / rate < d:
        tt = T(.07); put(lp(rng.uniform(-1, 1, len(tt)), .35) * np.exp(-tt * 45), t0 + k / rate, g * rng.uniform(.7, 1)); k += 1
def sizzle(t0, d, g=.18):
    tt = T(d); n = rng.uniform(-1, 1, len(tt)) * (rng.uniform(0, 1, len(tt)) > .7)
    put(lp(n, .5) * np.minimum(1, tt / .1) * np.exp(-tt * 1.2), t0, g)

# ----- 0 -> 3 : accroche, le dragon prend sa respiration -----
fan([(74, 0, .5), (79, .5, 1.0)], 0.0, .5); put(GONG, 0, .25)
roll(0.6, 2.9, .3)
tt = T(1.6); put(lp(rng.uniform(-1, 1, len(tt)), .9) * (tt / tt[-1]) ** 2 * 1.6, 1.3, .35)     # inspiration
put(drone(50, 3.0), 0, .10)
# ----- 3 -> 6 : la trompette crache du feu -----
put(glide(233, 220, .35, .55, 9), 2.95, .9)       # « BWAAAH » de trompette, coupé par le feu
put(DAVUL, 3.0, 1.4); put(GONG, 3.0, .5); roar(3.05, 2.2, 1.1)
for k in range(int(2.6 / (B / 2))): put(lute([62, 66, 69, 66][k % 4], .25), 3.4 + k * B / 2, .22)
stamp(STAMPS[0])
# ----- 6 -> 9 : le pigeon revient, grillé -----
put(whoosh(.35), 5.85, .4); flaps(6.0, 1.4)
put(glide(420, 330, .28, .25, 4, .04), 7.25, 1); put(glide(380, 300, .32, .25, 4, .04), 7.55, 1)   # « rrrou ? »
for k in range(int(2.8 / (B / 2))): put(lute([60, 64, 67, 64][k % 4], .25), 6.2 + k * B / 2, .2)
stamp(STAMPS[1])
# ----- 9 -> 12 : la barbe du Grand Maître -----
tt = T(.5); put(lp(rng.uniform(-1, 1, len(tt)), .9) * (tt / tt[-1]) ** 2 * 1.4, ATCHOUM_T - .5, .3)
roar(ATCHOUM_T, .9, .9); put(DAVUL, ATCHOUM_T, 1.0); sizzle(ATCHOUM_T + .3, 1.6)
drums(9.0, 12.0, .45)
stamp(STAMPS[2], 1.2); put(GONG, STAMPS[2], .45)
# ----- 12 -> 15 : papa, « bip », silence, puis ça monte -----
for k in range(int((BIP_T - 12.1) / (B / 2))): put(lute([57, 60, 64, 60][k % 4], .25), 12.1 + k * B / 2, .16)
put(np.sin(2 * np.pi * 1320 * T(.12)) * env(int(.12 * SR), .003, .03), BIP_T, .35)
roll(14.0, 15.0, .45); tt = T(1.0); put(lp(rng.uniform(-1, 1, len(tt)), .6) * (tt / tt[-1]) ** 2, 14.0, .3)
# ----- 15 -> 19,2 : LA QUÊTE EST OUVERTE -----
put(DAVUL, 15.0, 1.6); put(DAVUL_HI, 15.0, .7); put(GONG, 15.0, .6)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (79, 1, 1), (81, 2, .5), (83, 2.5, .5), (86, 3, 1.5)], 15.0, .6)
drums(15.0, 19.15, .85); claps(15.3, 8, .45); claps(17.1, 8, .4)
air = [(74, 4.5, .5), (76, 5, .5), (78, 5.5, .5)]
for m, bt, d in air: put(chanter(m - 12, d * B * .97), 15.0 + bt * B, .6)
put(drone(50, 4.1), 15.0, .2)
for k in range(int(4.1 / (B / 2))): put(lute([50, 57, 62, 57][k % 4], .3), 15.0 + k * B / 2, .25)
# ----- 19,2 -> 21,6 : le dragon insiste : « pouet », trombone triste -----
cut(19.2, POUET_T - .05)
put(whoosh(.3), 19.05, .3)
tt = T(.8); put(lp(rng.uniform(-1, 1, len(tt)), .9) * (tt / tt[-1]) ** 2 * 1.2, POUET_T - .8, .25)
put(glide(311, 262, .32, .6, 7), POUET_T, 1.0)                                   # pouet.
for i, (f0, d) in enumerate([(233, .28), (220, .28), (208, .28), (196, .7)]):
    put(glide(f0, f0 * (.94 if i == 3 else .99), d, .45, 8, .03 if i == 3 else 0), POUET_T + .45 + i * .3, .7)
# ----- carte de fin -----
put(DAVUL, FIN0, 1.3); put(GONG, FIN0, .35); put(whoosh(), FIN0 - .15, .3)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], FIN0, .5)
drums(FIN0, FIN0 + 3.2, .6)
for k in range(int(3.2 / (B / 2))): put(lute([62, 66, 69, 66][k % 4], .25), FIN0 + k * B / 2, .22)
FIN = FIN0 + 3.2
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
for m in [38, 50, 57, 62, 66, 69]:
    h = horn(m, 1.1).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.3) * .8
mix[int((DUR - .3) * SR):] *= np.linspace(1, 0, N - int((DUR - .3) * SR))
with wave.open('son14.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son14.wav')
