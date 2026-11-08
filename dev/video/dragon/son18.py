"""Bande-son de « Le lendemain de l'anniversaire » (34,6 s) : coq et horloge du réveil, basse pizzicato
d'enquête pendant les 4 indices (effort et couinement de la couronne, bain qui glougloute, canard en
caoutchouc, ronflements, langue de belle-mère, mouettes, tiroir-caisse et miaou du chat), déclics de
photos, glissando et marche de la quête, disque rayé du retournement, disco médiévale de l'after avec le
« chut » du dragon, fanfare de fin. Tous les instants viennent de lendemain.py (même découpage)."""
import numpy as np, wave
exec(open('son4.py').read().split('# =========== A.')[0])
import re
src = open('lendemain.py').read()
def const(name): return float(re.search(rf'^{name} = ([0-9.]+)', src, re.M).group(1))
GLUE_T, SNORE_T, ROYAUME_T, THON_T, ZERO_T, DJ_T, FIN0, END = [const(n) for n in
    ('GLUE_T', 'SNORE_T', 'ROYAUME_T', 'THON_T', 'ZERO_T', 'DJ_T', 'FIN0', 'END')]
I1_S, I2_S, I3_S, I4_S, PHOTO_S, SOUV_S, QUI_S, AFTER_S = [float(x) for x in
    re.search(r'^I1_S, I2_S, I3_S, I4_S, PHOTO_S, SOUV_S, QUI_S, AFTER_S = (.*?)\s+#', src, re.M).group(1).split(',')]

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
def claps(t, n=6, g=.5):
    for i in range(n):
        tt = T(.06); put(lp(rng.uniform(-1, 1, len(tt)), .2) * np.exp(-tt * 70) * 1.4, t + i * .16 + rng.uniform(0, .02), g)
def clap(t, g=.4):
    tt = T(.08); put(lp(rng.uniform(-1, 1, len(tt)), .25) * np.exp(-tt * 45) * 1.4, t, g)
def stamp(t, g=1.0):
    put(DAVUL, t, 1.3 * g); put(NAKER, t, .6 * g); put(whoosh(.18), t - .12, .25 * g)
def glide(f0, f1, d, g=.4, harm=6, vib=0.0, vr=6):
    tt = T(d); f = np.linspace(f0, f1, len(tt)) * (1 + vib * np.sin(2 * np.pi * vr * tt))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k ** .9) * np.sin(k * ph) for k in range(1, harm + 1)) / 2.5
    return s * env(len(tt), .01, .08) * g
def pizz(m, t, g=.35):
    tt = T(.25); f = hz(m)
    put((np.sin(2 * np.pi * f * tt) + .4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 18), t, g)
def enquete(t0, t1, g=.32):
    """Basse pizzicato d'enquête, mineure, sur des croches."""
    line = [45, 52, 48, 52, 45, 52, 47, 51]
    k = 0
    while t0 + k * B / 2 < t1 - .05:
        pizz(line[k % 8], t0 + k * B / 2, g * (1.0 if k % 2 == 0 else .7))
        if k % 4 == 2: put(tick(), t0 + k * B / 2, .25)
        k += 1
def dun(t, m=38, g=.6):
    put(horn(m, .9), t, g); put(horn(m + 7, .9), t, g * .6); put(horn(m + 12, .9), t, g * .5); put(DAVUL, t, 1.2); put(GONG, t, .35)
def indice(t):                              # coup de l'étiquette « INDICE n/4 »
    put(whoosh(.25), t - .12, .35); put(DAVUL, t, 1.0); put(NAKER, t, .5); put(bell(1568, .6), t + .05, .15)
def tooter(t, g=.5):                        # langue de belle-mère qui se déroule
    put(glide(520, 430, .55, 1, 9, .05, 9), t, g); put(glide(430, 300, .5, 1, 9, .04, 7), t + .55, g * .8)
def scratch(t, g=.5):                       # disque rayé
    tt = T(.35); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 3 * tt))
    put(lp(rng.uniform(-1, 1, len(tt)), .2) * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), .005, .05), t, g)
def snore(t, g=.5):                          # inspiration (souffle) puis ronflement grave qui vibre
    tt = T(.7); n = lp(rng.uniform(-1, 1, len(tt)), .35) * np.sin(np.pi * tt / .7) ** 2
    put(n, t, g * .5)
    tt = T(.9); buzz = np.sign(np.sin(2 * np.pi * 34 * tt)) * .6 + lp(rng.uniform(-1, 1, len(tt)), .15)
    put(lp(buzz, .25) * np.sin(np.pi * tt / .9) ** 1.5, t + .75, g)
def blub(t, g=.25):                         # bulle qui remonte
    put(glide(220, 700, .09, 1, 2), t, g)
def squeak(t, g=.35, f0=900, f1=1350, d=.16):   # canard en caoutchouc, couronne qui couine
    put(glide(f0, f1, d, 1, 5, .08, 30), t, g); put(glide(f1, f0 * .9, d * .8, 1, 5, .08, 30), t + d, g * .8)
def gull(t, g=.25):
    put(glide(1500, 950, .28, 1, 4, .03, 12), t, g); put(glide(1400, 900, .22, 1, 4, .03, 12), t + .32, g * .8)
def rooster(t, g=.4):                       # cocorico de dessin animé
    for f0, f1, d, dt in [(520, 760, .16, 0), (760, 700, .14, .18), (700, 980, .55, .34)]:
        put(glide(f0, f1, d, 1, 7, .03, 18), t + dt, g)
def kaching(t, g=.4):                       # tiroir-caisse
    tt = T(.12); put(lp(rng.uniform(-1, 1, len(tt)), .5) * np.exp(-tt * 40), t, g * .7)
    put(bell(2637, .7), t + .08, g * .5); put(bell(3520, .9), t + .14, g * .45)
def meow(t, g=1):
    put(glide(620, 880, .18, .3, 6, .03), t, g); put(glide(880, 520, .4, .3, 6, .04), t + .18, g)
def shutter(t, g=.45):
    tt = T(.05); put(lp(rng.uniform(-1, 1, len(tt)), .6) * np.exp(-tt * 90), t, g); put(tick(), t + .07, g)
def shh(t, d=.7, g=.35):                    # « chut »
    tt = T(d); n = rng.uniform(-1, 1, len(tt)); n = n - lp(n, .2)
    put(n * env(len(tt), .05, .25), t, g)

# ----- 0 -> 3,6 : réveil -----
rooster(0.15, .35)
for k in range(8): put(tick(), 0.9 + k * .5, .35)                 # l'horloge
put(drone(36, 3.2), 0.4, .22)                                       # tête lourde
put(glide(420, 260, 1.1, .5, 6, .06, 4), 1.6, .25)                  # « ouille »
put(bell(2349, .5), 1.0, .06); put(bell(2794, .5), 1.18, .05)      # oiseaux
# ----- indice 1 : la couronne -----
indice(I1_S); enquete(I1_S + .1, GLUE_T - .1)
put(glide(180, 420, 1.0, .6, 8, .02, 9), GLUE_T - 1.05, .3)        # effort
squeak(GLUE_T - .3, .3, 1100, 1500, .1)
stamp(GLUE_T); put(GONG, GLUE_T, .3)
fan([(67, 0, .3), (72, .33, .5)], GLUE_T + .15, .35)
enquete(GLUE_T + .9, I2_S - .05, .26)
# ----- indice 2 : le dragon dans la baignoire -----
indice(I2_S); enquete(I2_S + .1, I3_S - .05, .26)
for k in range(9): blub(I2_S + .4 + k * .33 + rng.uniform(0, .1), .2)
squeak(I2_S + 1.0, .25)
snore(SNORE_T - .75, .55)
# ----- indice 3 : le Grand Maître sur le toit -----
indice(I3_S); enquete(I3_S + .1, I4_S - .05, .26)
gull(I3_S + .6, .2)
snore(I3_S + .2, .4)
tooter(ROYAUME_T - .4, .45)
gull(ROYAUME_T + 1.2, .18)
# ----- indice 4 : le chat a la carte bleue -----
indice(I4_S); enquete(I4_S + .1, THON_T - .1, .26)
kaching(I4_S + .5, .4)
meow(THON_T, 1)
for k in range(3): kaching(THON_T + .7 + k * .3, .3)                # le thon se commande
# ----- les photos d'hier -----
cut(PHOTO_S - .02, PHOTO_S)
for k in range(3): shutter(PHOTO_S + .1 + k * .18)
dun(PHOTO_S + .5, 38, .5)
# ----- 14 h : la quête -----
for i, f in enumerate([1047, 1319, 1568, 2093, 2637, 3136]): put(bell(f, .9), SOUV_S - .3 + i * .06, .12)
drums(SOUV_S + .2, QUI_S - .05, .7)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (79, 1, 1), (81, 2, .5), (83, 2.5, .5), (86, 3, 1)], SOUV_S + .2, .5)
for k in range(int((QUI_S - SOUV_S - .3) / (B / 2))): put(lute([50, 57, 62, 57][k % 4], .3), SOUV_S + .2 + k * B / 2, .2)
put(bell(1976, .8), ZERO_T, .2); put(bell(2637, .9), ZERO_T + .1, .15)
# ----- alors… qui a fait ça ? -----
scratch(QUI_S - .25, .55); cut(QUI_S - .02, QUI_S + .05)
for i, (m, d) in enumerate([(38, .3), (38, .3), (37, .7)]):        # DUN DUN DUNNN
    tt = QUI_S + .1 + [0, .3, .6][i]
    put(horn(m, d), tt, .5); put(horn(m + 12, d), tt, .3); put(DAVUL, tt, 1.1)
# ----- 23 h : l'after des adultes (disco médiévale) -----
PB_ = .5
put(whoosh(.35), AFTER_S - .2, .5); put(DAVUL, AFTER_S, 1.5); put(GONG, AFTER_S, .4)
bass = [38, 50, 38, 50, 41, 53, 43, 55]
k = 0
while AFTER_S + k * PB_ / 2 < FIN0 - .05:
    t = AFTER_S + k * PB_ / 2
    duck = .45 if DJ_T - .05 <= t < DJ_T + .75 else 1.0          # la musique baisse pendant le « chut »… à peine
    if k % 2 == 0: put(DAVUL, t, .9 * duck)
    else: put(TAMB, t, .3 * duck); put(horn(bass[(k // 2) % 8], PB_ * .45), t, .28 * duck)
    if k % 4 == 2: clap(t, .45 * duck)
    if k % 2 == 0: put(lute([62, 66, 69, 74][(k // 2) % 4], .25), t, .18 * duck)
    k += 1
fan([(74, 0, .5), (78, .5, .5), (81, 1, .5), (86, 1.5, 1)], AFTER_S + .1, .4)
scratch(DJ_T - .3, .5); shh(DJ_T, .75, .4)
put(DAVUL, DJ_T + .8, 1.4); scratch(DJ_T + .8, .4)                    # … et ça repart plus fort
# ----- carte de fin -----
cut(FIN0 - .03, FIN0)
put(DAVUL, FIN0, 1.3); put(GONG, FIN0, .35); put(whoosh(), FIN0 - .15, .3)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], FIN0, .5)
drums(FIN0, FIN0 + 3.4, .6)
for k in range(int(3.4 / (B / 2))): put(lute([62, 66, 69, 66][k % 4], .25), FIN0 + k * B / 2, .22)
FIN = FIN0 + 3.4
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
for m in [38, 50, 57, 62, 66, 69]:
    h = horn(m, 1.1).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.3) * .8
mix[int((DUR - .3) * SR):] *= np.linspace(1, 0, N - int((DUR - .3) * SR))
with wave.open('son18.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son18.wav')
