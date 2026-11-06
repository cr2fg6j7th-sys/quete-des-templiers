"""Bande-son du TikTok « La veille de l'ouverture » (25 s) : marche médiévale + bruitages, éternuement et hoquet du dragon."""
import numpy as np, wave
exec(open('son11.py').read().split('S1, S2, S3, S4, S5')[0].replace('import inaug2 as V', 'import veille as V'))

S = [s[0] for s in V.SHOTS]; FIN0 = V.SHOTS[-1][1]
def clock(t):            # « tic » d'horloge pour chaque heure affichée
    put(bell(1760, .5), t, .16); put(tick(), t, .6)

# 0 -> 2,8 : titre, coup de fanfare
put(DAVUL, 0, 1.2); put(GONG, 0, .3)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (78, 1, 1.5)], 0, .45)
put(drone(50, S[2]), 0, .14)
# 2,8 -> 6 : marche légère du luth (le site est prêt)
for k in range(int((V.SNEEZE_T - 1.2 - S[1]) / (B / 2))):
    put(lute([62, 66, 69, 66][k % 4], .25), S[1] + k * B / 2, .3)
for k in range(int((V.SNEEZE_T - 1.2 - S[1]) / B)): put(FRAME, S[1] + k * B, .35)
clock(S[1]); clock(S[2]); clock(S[3])
# 6 -> 10 : inspiration, éternuement, feu
tt = T(1.4); put(lp(rng.uniform(-1, 1, len(tt)), .9) * (tt / tt[-1]) ** 2 * 2.5, V.SNEEZE_T - 1.4, .35)
cut(V.SNEEZE_T - .02)
put(DAVUL, V.SNEEZE_T, 1.6); put(GONG, V.SNEEZE_T, .6); roar(V.SNEEZE_T, 1.8, 1.0)
tt = T(.9); f = hz(69) * (1 - .35 * (tt / tt[-1]) ** 1.3)
put(sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(tt), .02, .25), V.SNEEZE_T + 1.1, .45)
clock(S[3])
# 10 -> 13,5 : tic-tac, hoquet, grésillement
for i in range(int((V.HIC_T - S[3]) / .25)): put(tick(), S[3] + .25 + i * .25, .35)
cut(V.HIC_T - .02)
put(whoosh(.25), V.HIC_T, .4); roar(V.HIC_T + .05, .6, .35)
tt = T(1.2); put(lp(rng.uniform(-1, 1, len(tt)), .3) * np.exp(-tt * 2.5) * .5, V.HIC_T + .3, .25)
put(NAKER, V.HIC_T + 1.2, .35); put(NAKER, V.HIC_T + 1.4, .35)
# 13,5 -> 22 : la quête (cornemuse + tambours), puis la paie du dragon
Q0 = S[4]
put(DAVUL, Q0, 1.4); put(GONG, Q0, .4); put(whoosh(), Q0 - .2, .3)
put(drone(50, FIN0 - Q0 + .05), Q0, .24)
air = [(74, 0, .5), (76, .5, .5), (78, 1, .5), (79, 1.5, .5), (81, 2, 1), (83, 3, .5), (81, 3.5, .5),
       (79, 4, .5), (81, 4.5, .5), (83, 5, .5), (86, 5.5, .5), (83, 6, 1), (81, 7, .5), (79, 7.5, .5),
       (78, 8, .5), (79, 8.5, .5), (81, 9, 1), (78, 10, .5), (76, 10.5, .5), (74, 11, 1), (76, 12, .5), (78, 12.5, .5), (74, 13, 1)]
for m, bt, d in air:
    gr = m + 2 if bt % 1 == 0 else None
    put(chanter(m - 12, d * B * .97, (gr - 12) if gr else None), Q0 + bt * B, .75)
drums(Q0, FIN0 - .05, .8)
for k in range(int((FIN0 - Q0) / (B / 2))): put(lute([50, 57, 62, 57][k % 4], .3), Q0 + k * B / 2, .25)
put(bell(), S[6] + .7, .3); put(bell(1568), S[6] + .85, .25)          # « touche enfin sa paie » : pièces
claps(S[6] + .2, 6)
# carte de fin : fanfare et accord final
put(DAVUL, FIN0, 1.4); put(GONG, FIN0, .35); put(whoosh(), FIN0 - .2, .3)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], FIN0, .55)
drums(FIN0, FIN0 + 4 * B - .05, .85)
FIN = FIN0 + 4 * B
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
for m in [38, 50, 57, 62, 66, 69]:
    h = horn(m, .9).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.3) * .8
vox = np.zeros(N)
for p, t0, g in [('voix_inaug/atchoum.wav', V.SNEEZE_T - 2.25, .9), ('voix_inaug/hic.wav', V.HIC_T - .3, .9)]:
    x = load(p); i = int(t0 * SR); x = x[: N - i]; vox[i:i + len(x)] += x * g
mix = np.clip(mix + vox, -1, 1) * .97
mix[int((DUR - .25) * SR):] *= np.linspace(1, 0, N - int((DUR - .25) * SR))
with wave.open('son12.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son12.wav')
