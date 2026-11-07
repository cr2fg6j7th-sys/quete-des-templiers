"""Bande-son de « L'entretien d'embauche du dragon » (39 s) : musique d'attente guindée (luth et
pizzicato) pendant l'entretien, bruitages de chute à chaque réponse (feu qui prend, barbe qui grésille,
langue de belle-mère triste, accord dramatique), whoosh et gong de l'inversion des rôles, scintillement
et fanfare de la quête, marche des enfants, musique d'attente solitaire et « ding » du ticket, fin.
Tous les instants viennent de entretien.py (même découpage)."""
import numpy as np, wave
exec(open('son4.py').read().split('# =========== A.')[0])
import re
src = open('entretien.py').read()
def const(name): return float(re.search(rf'^{name} = ([0-9.]+)', src, re.M).group(1))
(R1_T, R2_T, R3_T, R3B_T, VET_T, R4_T, SWAP_T, QUETE_T, CHAT_T, DEJA_T, END, FIN0) = [const(n) for n in
 ('R1_T', 'R2_T', 'R3_T', 'R3B_T', 'VET_T', 'R4_T', 'SWAP_T', 'QUETE_T', 'CHAT_T', 'DEJA_T', 'END', 'FIN0')]
Q1_S, Q2_S, Q3_S, Q4_S, PROD_S = [float(x) for x in re.search(r'^Q1_S, Q2_S, Q3_S, Q4_S, PROD_S = (.*?)\s+#', src, re.M).group(1).split(',')]
KIDS_T, WAIT_T = const('KIDS_T'), const('WAIT_T')

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
def glide(f0, f1, d, g=.4, harm=6, vib=0.0, vr=6):
    tt = T(d); f = np.linspace(f0, f1, len(tt)) * (1 + vib * np.sin(2 * np.pi * vr * tt))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k ** .9) * np.sin(k * ph) for k in range(1, harm + 1)) / 2.5
    return s * env(len(tt), .01, .08) * g
def pizz(m, t, g=.35):
    tt = T(.25); f = hz(m)
    put((np.sin(2 * np.pi * f * tt) + .4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 18), t, g)
def fire(t, d=1.6, g=.8):                   # le feu qui prend : souffle, puis crépitement
    tt = T(d); n = lp(rng.uniform(-1, 1, len(tt)), .75)
    crack = (rng.uniform(0, 1, len(tt)) > .997) * rng.uniform(-1, 1, len(tt)) * 5
    put((n * 1.8 + lp(crack, .3)) * np.minimum(1, tt / .12) * np.exp(-tt * 1.2), t, g)
def sizzle(t, d=1.2, g=.25):
    tt = T(d); n = rng.uniform(-1, 1, len(tt)) * (rng.uniform(0, 1, len(tt)) > .7)
    put(lp(n, .5) * np.minimum(1, tt / .1) * np.exp(-tt * 1.5), t, g)
def lounge(t0, t1, g=.18, root=57):          # musique d'attente guindée : luth + pizzicato, accords simples
    prog = [[root, root + 4, root + 7], [root + 5, root + 9, root + 12], [root + 7, root + 11, root + 14], [root, root + 4, root + 7]]
    k = 0
    while t0 + k * B / 2 < t1:
        ch = prog[(k // 4) % 4]
        put(lute(ch[k % 3], .3), t0 + k * B / 2, g)
        if k % 2 == 0: pizz(ch[0] - 12, t0 + k * B / 2, g * 1.6)
        k += 1
def dun(t, m=38, g=.6):                     # accord dramatique
    put(horn(m, .9), t, g); put(horn(m + 7, .9), t, g * .6); put(horn(m + 12, .9), t, g * .5); put(DAVUL, t, 1.2); put(GONG, t, .35)
def tooter(t, g=.5):                        # langue de belle-mère triste
    put(glide(520, 430, .55, 1, 9, .05, 9), t, g); put(glide(430, 300, .5, 1, 9, .04, 7), t + .55, g * .8)
def scratch(t, g=.5):                       # disque rayé
    tt = T(.35); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 3 * tt))
    put(lp(rng.uniform(-1, 1, len(tt)), .2) * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), .005, .05), t, g)
def slurp(t, g=.3):
    tt = T(.5); put(lp(rng.uniform(-1, 1, len(tt)), .55) * (np.sin(2 * np.pi * 7 * tt) > 0) * np.sin(np.pi * tt / .5), t, g)

# ----- 0 -> 3 : accroche -----
fan([(74, 0, .33), (78, .33, .33), (81, .67, .67)], 0.0, .45); put(GONG, 0, .2)
lounge(0.6, Q1_S, .16)
# ----- 3 -> 6,4 : Q1 « Je suis très chaud. » -----
lounge(Q1_S, R1_T - .1, .16)
put(tick(), R1_T - .05, .4); fire(R1_T + .05, 2.0, .85); put(whoosh(.4), R1_T - .1, .4)
fan([(67, 0, .3), (72, .33, .5)], R1_T + .2, .35)
# ----- 6,4 -> 9,8 : Q2, même réponse -----
put(whoosh(.25), Q2_S - .1, .3)
lounge(Q2_S, R2_T - .1, .16)
put(tick(), R2_T - .05, .4); sizzle(R2_T + .1, 1.6, .35); fire(R2_T + .1, 1.2, .45)
fan([(67, 0, .3), (72, .33, .5)], R2_T + .2, .35)
# ----- 9,8 -> 13,4 : Q3, le vétéran -----
put(whoosh(.25), Q3_S - .1, .3)
lounge(Q3_S, R3_T - .1, .16)
put(drone(38, 3.4), R3_T, .35)                                      # gravité de film de guerre
tooter(R3B_T, .45)
stamp(VET_T); put(GONG, VET_T, .3)
# ----- 13,4 -> 17,2 : Q4, « À votre place. » puis inversion des rôles -----
put(whoosh(.25), Q4_S - .1, .3)
lounge(Q4_S, R4_T - .1, .16)
cut(R4_T - .05, R4_T)
dun(R4_T, 38, .55)
scratch(SWAP_T - .25, .55); put(whoosh(.35), SWAP_T - .2, .5)
put(DAVUL, SWAP_T, 1.5); put(GONG, SWAP_T, .55)
fan([(62, 0, .5), (65, .5, .5), (69, 1, .5), (74, 1.5, 1.2)], SWAP_T + .15, .55)   # thème du « nouveau patron »
# ----- 17,2 -> 20,2 : la quête -----
put(whoosh(.3), PROD_S - .1, .35)
lounge(PROD_S + .1, QUETE_T - .1, .14)
for i, f in enumerate([1568, 1976, 2349, 2637, 3136]): put(bell(f, .9), QUETE_T - .6 + i * .1, .12)
put(DAVUL, QUETE_T, 1.5); put(DAVUL_HI, QUETE_T, .7); put(GONG, QUETE_T, .5)
fan([(74, 0, .5), (79, .5, .5), (83, 1, .5), (86, 1.5, 1.4)], QUETE_T, .6)
claps(QUETE_T + .4, 8, .4)
# ----- 20,2 -> 23,2 : les enfants dans les rues -----
drums(KIDS_T, WAIT_T - .05, .8)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (79, 1, 1), (81, 2, .5), (83, 2.5, .5), (86, 3, 1)], KIDS_T, .5)
for k in range(int(3.0 / (B / 2))): put(lute([50, 57, 62, 57][k % 4], .3), KIDS_T + k * B / 2, .22)
# ----- 23,2 -> 26 : salle d'attente -----
cut(WAIT_T, WAIT_T + .05)
lounge(WAIT_T + .1, CHAT_T - .1, .12, 52)                              # même musique d'attente, plus triste
put(bell(1047, 1.0), WAIT_T + .5, .3)                               # « ding » du ticket
slurp(WAIT_T + 1.2, .3)
put(glide(300, 200, .5, .2, 6), WAIT_T + 1.3, 1)                   # soupir
# ----- 26 -> 28,6 : candidat suivant, le chat -----
cut(CHAT_T - .05, CHAT_T)
put(bell(1319, .8), CHAT_T, .3); put(bell(1047, 1.0), CHAT_T + .18, .3)   # « candidat suivant »
put(glide(620, 880, .18, .3, 6, .03), CHAT_T + .3, 1); put(glide(880, 520, .4, .3, 6, .04), CHAT_T + .48, 1)   # miaou
put(tick(), DEJA_T - .25, .6); put(bell(1976, .7), DEJA_T - .1, .25)
for i, (m, d) in enumerate([(38, .3), (38, .3), (37, 1.0)]):            # DUN DUN DUNNN
    tt = DEJA_T + [0, .3, .6][i]
    put(horn(m, d), tt, .55); put(horn(m + 12, d), tt, .35); put(DAVUL, tt, 1.2)
put(GONG, DEJA_T + .6, .45)
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
with wave.open('son16.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son16.wav')
