"""Bande-son du TikTok « C'est ouvert ! » : fanfare, coup de ciseaux, marche de la quête. Aucun bruit de feu."""
import numpy as np, wave
exec(open('son11.py').read().split('S1, S2, S3, S4, S5')[0].replace('import inaug2 as V', 'import ouverture as V'))

S = [s[0] for s in V.SHOTS]; FIN0 = V.SHOTS[-1][1]
# 0 -> 2,8 : « C'est ouvert ! »
put(DAVUL, 0, 1.3); put(GONG, 0, .35)
fan([(74, 0, .33), (78, .33, .33), (81, .67, .33), (86, 1, 1.5)], 0, .5)
put(drone(50, S[1]), 0, .14)
# 2,8 -> 7,8 : marche sur la pointe des pieds, puis coupe du ruban et fanfare
for k in range(int((V.CUT_T - .1 - S[1]) / (B / 2))):
    put(lute([62, 66, 69, 66][k % 4], .25), S[1] + k * B / 2, .3)
for x in (V.CUT_T, V.CUT_T + .05): put(tick(), x, .9); put(bell(3200, .15), x, .1)
put(DAVUL, V.CUT_T + .1, 1.3); put(GONG, V.CUT_T + .1, .4)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], V.CUT_T + .1, .5)
claps(V.CUT_T + .4, 10)
# 7,8 -> 19 : la quête (cornemuse, tambours, luth)
Q0 = S[2]
put(whoosh(), Q0 - .2, .3); put(DAVUL, Q0, 1.2)
put(drone(50, FIN0 - Q0 + .05), Q0, .22)
air = [(74, 0, .5), (76, .5, .5), (78, 1, .5), (79, 1.5, .5), (81, 2, 1), (83, 3, .5), (81, 3.5, .5),
       (79, 4, .5), (81, 4.5, .5), (83, 5, .5), (86, 5.5, .5), (83, 6, 1), (81, 7, .5), (79, 7.5, .5),
       (78, 8, .5), (79, 8.5, .5), (81, 9, 1), (78, 10, .5), (76, 10.5, .5), (74, 11, 1)]
for m, bt, d in air:
    gr = m + 2 if bt % 1 == 0 else None
    put(chanter(m - 12, d * B * .97, (gr - 12) if gr else None), Q0 + bt * B, .75)
drums(Q0, FIN0 - .05, .8)
for k in range(int((FIN0 - Q0) / (B / 2))): put(lute([50, 57, 62, 57][k % 4], .3), Q0 + k * B / 2, .25)
put(bell(), S[5] + .9, .3); put(bell(1568), S[5] + 1.05, .25)      # la paie du dragon : pièces
# carte de fin
put(DAVUL, FIN0, 1.4); put(GONG, FIN0, .35); put(whoosh(), FIN0 - .2, .3)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], FIN0, .55)
drums(FIN0, FIN0 + 4 * B - .05, .85)
FIN = FIN0 + 4 * B
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
for m in [38, 50, 57, 62, 66, 69]:
    h = horn(m, .9).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.3) * .8
mix = np.clip(mix, -1, 1) * .97
mix[int((DUR - .25) * SR):] *= np.linspace(1, 0, N - int((DUR - .25) * SR))
with wave.open('son13.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son13.wav')
