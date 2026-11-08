"""Bande-son du « Règlement de l'anniversaire » (30,4 s) : musique guindée pendant la lecture des règles,
un bruitage par règle (feu, grésillement, accord dramatique pour PAPA, marche des enfants, langue de
belle-mère triste), tampon à chaque verdict, fanfare et tambours de fin. Instants lus dans regles.py.
Tout est synthétisé (aucun service payant)."""
import numpy as np, wave, re
exec(open('son4.py').read().split('# =========== A.')[0])
src = open('regles.py').read()
ns = {}
for line in src.splitlines():
    if re.match(r'^(R1_S, R2_S|END |ST\d |EL3 |R5_B )', line): exec(line.split('#')[0], ns)
R1_S, R2_S, R3_S, R4_S, R5_S, FIN0, END = [ns[k] for k in ('R1_S', 'R2_S', 'R3_S', 'R4_S', 'R5_S', 'FIN0', 'END')]
ST1, ST2, ST3, ST4, ST5, EL3, R5_B = [ns[k] for k in ('ST1', 'ST2', 'ST3', 'ST4', 'ST5', 'EL3', 'R5_B')]
DUR = END; N = int(SR * DUR); mix = np.zeros(N)
TRIP = B / 3
body = open('son16.py').read().split('TRIP = B / 3\n')[1].split('# ----- 0 -> 3')[0]
exec(body)

# accroche
fan([(74, 0, .33), (78, .33, .33), (81, .67, .67)], 0.0, .45); put(GONG, 0, .2)
lounge(0.8, R1_S, .15)
# règle 1 : le feu, dehors
put(whoosh(.25), R1_S - .1, .3); lounge(R1_S, ST1 - .1, .15)
fire(ST1 - .9, 1.8, .7); stamp(ST1); fan([(67, 0, .3), (72, .33, .5)], ST1 + .2, .35)
# règle 2 : la barbe
put(whoosh(.25), R2_S - .1, .3); lounge(R2_S, ST2 - .1, .15)
sizzle(ST2 - .6, 1.6, .35); stamp(ST2); tooter(ST2 + .5, .3)
# règle 3 : papa éliminé
put(whoosh(.25), R3_S - .1, .3); lounge(R3_S, EL3 - .1, .15)
put(tick(), EL3 - .05, .5); cut(ST3 - .05, ST3); dun(ST3, 38, .6); stamp(ST3, 1.2)
# règle 4 : la quête dans les rues
put(whoosh(.3), R4_S - .1, .35); lounge(R4_S, ST4 - .1, .14)
stamp(ST4); claps(ST4 + .1, 8, .4)
drums(ST4, R5_S - .05, .8)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (79, 1, 1), (81, 2, .5)], ST4, .5)
# règle 5 : le dragon reste calme
cut(R5_S, R5_S + .05); scratch(R5_S - .2, .5)
lounge(R5_S + .2, ST5 - .1, .12, 52)
tooter(R5_B + .4, .45); stamp(ST5); put(GONG, ST5, .3)
# fin
put(DAVUL, FIN0, 1.3); put(GONG, FIN0, .35); put(whoosh(), FIN0 - .15, .3)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], FIN0, .5)
drums(FIN0, FIN0 + 3.6, .6)
for k in range(int(3.6 / (B / 2))): put(lute([62, 66, 69, 66][k % 4], .25), FIN0 + k * B / 2, .22)
FIN = FIN0 + 3.6
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
for m in [38, 50, 57, 62, 66, 69]:
    h = horn(m, 1.1).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.3) * .8
mix[int((DUR - .3) * SR):] *= np.linspace(1, 0, N - int((DUR - .3) * SR))
with wave.open('son17.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son17.wav')
