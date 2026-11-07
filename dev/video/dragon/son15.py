"""Bande-son de « Le petit chevalier recrute sa troupe » (31,8 s) : réveil en fanfare et ressorts du lit,
le chevalier qui tombe sur les fesses, le miaou et le casque qui tombe, les ronflements de papa et le son
de mise en veille, le cri de guerre et la promotion de la petite sœur, la sonnette et la grosse fanfare de
l'ouverture, le « wouf » du chien, la musique de conspirateur du chat, « DUN DUN DUNNN », carte de fin.
Tous les instants viennent de troupe.py (même découpage)."""
import numpy as np, wave
exec(open('son4.py').read().split('# =========== A.')[0])
import re
src = open('troupe.py').read()
def const(name): return float(re.search(rf'^{name} = ([0-9.]+)', src, re.M).group(1))
(FALL_T, PANNE_T, MEOW_T, CLANG_T, REFUSE_T, RONFLE_T, VEILLE_T, CRI_T, OK_T, GENERALE_T, GOUTER_T, WOUF_T,
 TAP_T, REVEAL_T, END, FIN0) = [const(n) for n in ('FALL_T', 'PANNE_T', 'MEOW_T', 'CLANG_T', 'REFUSE_T', 'RONFLE_T',
 'VEILLE_T', 'CRI_T', 'OK_T', 'GENERALE_T', 'GOUTER_T', 'WOUF_T', 'TAP_T', 'REVEAL_T', 'END', 'FIN0')]
OUVERT_T = 16.4; CHAT_T = 23.8

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
def stamp(t, g=1.0):
    put(DAVUL, t, 1.3 * g); put(NAKER, t, .6 * g); put(whoosh(.18), t - .12, .25 * g)
def roll(t0, t1, g=.35):                    # roulement de tambour
    k = 0
    while t0 + k * .05 < t1:
        put(TAMB, t0 + k * .05, g * (.6 + .4 * (k % 2)) * (0.5 + 0.5 * (k * .05) / max(.1, t1 - t0))); k += 1
def glide(f0, f1, d, g=.4, harm=6, vib=0.0, vr=6):
    tt = T(d); f = np.linspace(f0, f1, len(tt)) * (1 + vib * np.sin(2 * np.pi * vr * tt))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k ** .9) * np.sin(k * ph) for k in range(1, harm + 1)) / 2.5
    return s * env(len(tt), .01, .08) * g
def boing(t, f=180, g=.5):                  # ressort du lit
    tt = T(.35); f_ = f * (1 + .6 * np.exp(-tt * 9) * np.sin(2 * np.pi * 14 * tt))
    put(np.sin(2 * np.pi * np.cumsum(f_) / SR) * np.exp(-tt * 7), t, g)
def thud(t, g=1.0):                         # chute sur les fesses
    put(DAVUL, t, 1.2 * g); tt = T(.4); put(lp(rng.uniform(-1, 1, len(tt)), .93) * np.exp(-tt * 10) * 3, t, .5 * g)
def clang(t, g=.5):                         # casque de métal qui tombe et rebondit
    for dt, a in [(0, 1), (.22, .55), (.36, .3)]:
        tt = T(.9); s = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec) for f, dec in [(1180, 5), (1730, 7), (2610, 9), (3420, 11)])
        put(s * env(len(tt), .001, .2) / 3, t + dt, g * a)
def snore(t, g=.55):                        # inspiration sifflante puis ronflement grave
    tt = T(.7); put(lp(rng.uniform(-1, 1, len(tt)), .6) * np.sin(np.pi * tt / .7) ** 2, t, .25 * g)
    tt = T(1.0); buzz = np.sign(np.sin(2 * np.pi * 70 * tt)) * (1 + .5 * np.sin(2 * np.pi * 9 * tt))
    put(lp(buzz + .6 * rng.uniform(-1, 1, len(tt)), .85) * np.sin(np.pi * tt / 1.0) ** 1.5, t + .75, g)
def sleep_chime(t, g=.35):                  # « mise en veille » : trois notes qui descendent et s'éteignent
    for i, f in enumerate([988, 784, 523]):
        put(bell(f, .9), t + i * .17, g * (1 - i * .15))
def bark(t, g=.7):                          # « wouf. »
    tt = T(.05); put(lp(rng.uniform(-1, 1, len(tt)), .3) * np.exp(-tt * 40), t, .6 * g)
    put(glide(520, 300, .22, 1, 10), t + .01, g)
def pizz(m, t, g=.35):                      # pizzicato de conspirateur
    tt = T(.25); f = hz(m)
    put((np.sin(2 * np.pi * f * tt) + .4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 18), t, g)

# ----- 0 -> 3 : réveil, le chevalier saute sur son lit -----
fan([(74, 0, .33), (78, .33, .33), (81, .67, .67)], 0.0, .5); put(GONG, 0, .2)
for k, tb in enumerate([0.55, 1.05, 1.55, 2.05, 2.55]): boing(tb, 170 + 15 * (k % 2), .45)
for k in range(int(2.6 / (B / 2))): put(lute([62, 66, 69, 66][k % 4], .25), 0.4 + k * B / 2, .2)
put(drone(50, 3.0), 0, .08)
# ----- 3 -> 6 : le destrier EN PANNE -----
put(whoosh(.3), 2.85, .35)
for k in range(int(1.9 / (B / 2))): put(lute([60, 64, 67, 64][k % 4], .25), 3.1 + k * B / 2, .18)
put(glide(260, 340, .6, .25, 5), FALL_T - .65, 1)                       # le chevalier force
thud(FALL_T); put(glide(300, 180, .7, .22, 6, .05, 4), FALL_T + .35, 1)  # soupir du chien
stamp(PANNE_T); put(glide(330, 110, .6, .3, 8), PANNE_T + .1, 1)        # moteur qui cale
# ----- 6 -> 9 : le chat -----
put(glide(620, 880, .18, .3, 6, .03), MEOW_T, 1); put(glide(880, 520, .4, .3, 6, .04), MEOW_T + .18, 1)
for k in range(int(1.4 / (B / 2))): put(lute([57, 60, 64, 60][k % 4], .25), 6.1 + k * B / 2, .16)
clang(CLANG_T)
stamp(REFUSE_T)
# ----- 9 -> 12,4 : papa EN VEILLE DEPUIS 2018 -----
snore(RONFLE_T - .75); snore(RONFLE_T + 1.25, .6)
put(bell(1568, .5), 9.6, .12); put(bell(1568, .5), 9.95, .12)        # tic tic de l'épée sur l'épaule
stamp(VEILLE_T); sleep_chime(VEILLE_T + .15)
# ----- 12,4 -> 16,4 : la petite sœur RECRUTÉE… puis PROMUE GÉNÉRALE -----
roll(12.4, CRI_T, .3)
put(glide(420, 980, .55, .45, 7, .03), CRI_T, 1)                        # cri de guerre
put(DAVUL, OK_T, 1.3); put(DAVUL_HI, OK_T, .5)
fan([(74, 0, .33), (78, .33, .33), (81, .67, .5)], OK_T, .45)
roll(GENERALE_T - .45, GENERALE_T, .4)
put(DAVUL, GENERALE_T, 1.6); put(GONG, GENERALE_T, .6); put(DAVUL_HI, GENERALE_T, .7)
fan([(74, 0, .5), (79, .5, .5), (83, 1, .5), (86, 1.5, 1.6)], GENERALE_T, .65)
claps(GENERALE_T + .3, 8, .4)
# ----- 16,4 -> 20,6 : ding-dong, la troupe et le dragon -----
cut(OUVERT_T - .45, OUVERT_T - .4)
put(bell(659, 1.4), OUVERT_T - .35, .35); put(bell(523, 1.6), OUVERT_T, .35)
put(DAVUL, OUVERT_T + .3, 1.5); put(DAVUL_HI, OUVERT_T + .3, .7); put(GONG, OUVERT_T + .3, .55)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (79, 1, 1), (81, 2, .5), (83, 2.5, .5), (86, 3, 1.2)], OUVERT_T + .3, .6)
drums(OUVERT_T + .3, 20.55, .85); claps(OUVERT_T + .6, 8, .45); claps(18.2, 8, .4)
put(drone(50, 3.9), OUVERT_T + .3, .2)
for k in range(int(3.8 / (B / 2))): put(lute([50, 57, 62, 57][k % 4], .3), OUVERT_T + .3 + k * B / 2, .25)
# ----- 20,6 -> 23,8 : le chien revient… pour le goûter -----
cut(20.6, 20.75)
put(whoosh(.3), 20.45, .3)
for k in range(4): put(TAMB, 20.75 + k * .3, .25)                     # petits pas fiers
bark(WOUF_T)
fan([(67, 0, .5), (72, .5, .5), (76, 1, .5), (79, 1.5, 1.0)], WOUF_T + .3, .38)   # marche triomphale de poche
put(bell(1760, .6), GOUTER_T, .2); put(bell(2093, .7), GOUTER_T + .12, .2)        # « ding ! » du goûter
# ----- 23,8 -> 27,2 : pendant ce temps, le chat… -----
cut(CHAT_T, CHAT_T + .05)
put(whoosh(.25), CHAT_T - .1, .35)
for k, m in enumerate([45, 48, 45, 52, 45, 48, 51, 52]):                # musique de conspirateur
    pizz(m, CHAT_T + .1 + k * .15, .4)
put(tick(), TAP_T, .6); put(bell(1318, .8), TAP_T + .15, .25); put(bell(1976, .8), TAP_T + .3, .25)   # tap… paiement validé
for i, (m, d) in enumerate([(38, .3), (38, .3), (37, 1.2)]):            # DUN DUN DUNNN
    tt = REVEAL_T + [0, .32, .64][i]
    put(horn(m, d), tt, .55); put(horn(m + 12, d), tt, .35); put(DAVUL, tt, 1.2)
put(GONG, REVEAL_T + .64, .45)
# ----- carte de fin -----
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
with wave.open('son15.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son15.wav')
