"""Bande-son médiévale de « Le dragon te parle » (100 bpm, B = 0,6 s, 19,8 s).
Musique de fond discrète sous la voix : reprend les instruments de son8.py
(bourdon, luth, flûte à bec, cor, davul, tambourin, gong).
Coupes du montage sur la grille : 6,0 / 7,8 / 9,0 / 11,7 / 13,2 / 14,4 / 16,8 s.
Usage : python3 son9.py  ->  son9.wav"""
import numpy as np, wave

# instruments de son8.py (tout ce qui précède la partition de « Jour J »)
_src = open('son8.py', encoding='utf-8').read().split('# ============ « Jour J')[0]
exec(_src, globals())

DUR = 19.8
N = int(SR * DUR)
mix = np.zeros(N)
CUTS = [6.0, 7.8, 9.0, 11.7, 13.2, 14.4, 16.8]
END_T = 16.8              # écran final
STOP = 14.4               # la musique s'arrête net sur la bourse vide

def groove(t0, t1, g=1.0, mode='dorien'):
    """Luth en croches, davul / tambour sur cadre / tambourin, sur la grille de 0,6 s."""
    notes = [62, 69, 74, 69] if mode == 'dorien' else [62, 69, 74, 78]
    k = 0; t = t0
    while t < t1 - 1e-6:
        beat = int(round(t / B))
        put(lute(notes[k % 4], .3), t, .22 * g)
        if abs(t / B - beat) < 1e-6:                       # sur le temps
            if beat % 2 == 0: put(DAVUL, t, .55 * g)
            else: put(FRAME, t, .45 * g); put(NAKER, t, .18 * g)
        put(TAMB, t, (.14 if k % 2 == 0 else .08) * g)
        k += 1; t += B / 2

# ---- 0 -> 9,0 : le dragon interpelle (ré dorien, retenu) ----
put(drone(50, 9.1), 0.0, .16)
put(DAVUL, 0.0, .9); put(bell(1174, 1.4), 0.0, .12)
groove(0.0, 9.0, .8, 'dorien')

# ---- 9,0 -> 14,4 : la quête (ré mixolydien, plus enlevé) ----
put(DAVUL, 9.0, 1.0); put(GONG[: int(1.2 * SR)] * np.linspace(1, 0, int(1.2 * SR)), 9.0, .22)
put(drone(50, 5.5), 9.0, .14)
groove(9.0, STOP, 1.0, 'mixolydien')
for i, m in enumerate([74, 78, 81, 83, 81, 78]):            # petite montée de flûte, en tierces de temps
    put(recorder(m, B / 2 * .9), 9.0 + 2 * B + i * B / 2, .14)
for m, bt, d in [(74, 0, .5), (78, .5, .5), (81, 1, 1)]:      # appel de cor sur la lettre dorée
    put(horn(m - 12, d * B * .95), 13.2 + bt * B, .28)

# ---- 14,4 : coupure nette, puis la plainte de la bombarde après « pas payé » ----
put(DAVUL, STOP, .7)
for i, (m, d) in enumerate([(69, .26), (68, .26), (67, .26), (66, .55)]):
    put(chanter(m, d, vol=.9), 15.9 + i * .27, .22)

# ---- 16,8 -> 19,8 : écran final, fanfare puis accord qui s'éteint ----
E0 = END_T
put(DAVUL, E0, 1.2); put(GONG, E0, .3)
dr = drone(50, 3.0); dr[int(2.2 * SR):] *= np.linspace(1, 0, len(dr) - int(2.2 * SR)) ** 1.5
put(dr, E0, .2)
for m, bt, d in [(74, 0, .33), (74, .33, .33), (74, .67, .33), (78, 1, .67), (81, 1.67, .33), (86, 2, .67), (81, 2.67, .33)]:
    put(horn(m - 12, d * B * .95), E0 + bt * B, .5); put(horn(m - 24, d * B * .95), E0 + bt * B, .1)
groove(E0, E0 + 3 * B, .9, 'mixolydien')
FIN = E0 + 4 * B
put(DAVUL, FIN, 1.3); put(DAVUL_HI, FIN, .5)
for m in [38, 50, 57, 62, 66, 69, 74]:
    h = horn(m, 1.0).copy(); h *= np.linspace(1, 0, len(h)) ** .9; put(h, FIN, .22)

W_ = whoosh()
for c in CUTS: put(W_, c - .2, .18)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.2) * .95
mix[int(19.5 * SR):] *= np.linspace(1, 0, N - int(19.5 * SR))
with wave.open('son9.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son9.wav')
