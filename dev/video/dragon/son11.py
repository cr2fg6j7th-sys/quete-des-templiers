"""Bande-son de « L'inauguration » (25 s) : musique médiévale + voix (dragon : Gemini Puck, Grand Maître : Gemini Algenib).
Les temps forts sont importés de inaug2.py pour rester synchrones avec l'image."""
import numpy as np, wave, sys
exec(open('son4.py').read().split('# =========== A.')[0])
import inaug2 as V

DUR = V.END; N = int(SR * DUR); mix = np.zeros(N)
TRIP = B / 3

def load(p):
    with wave.open(p) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
        if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1)
    if sr != SR: x = np.interp(np.arange(int(len(x) * SR / sr)) * sr / SR, np.arange(len(x)), x)
    return x / (np.abs(x).max() + 1e-9)

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
def cut(t, fade=.04):
    c0, c1 = int((t - fade) * SR), int(t * SR); mix[c0:c1] *= np.linspace(1, 0, c1 - c0); mix[c1:] = 0
def roar(t, d=1.6, g=.9):
    tt = T(d); n = lp(rng.uniform(-1, 1, len(tt)), .7)
    crack = (rng.uniform(0, 1, len(tt)) > .9985) * rng.uniform(-1, 1, len(tt)) * 6
    put((n * 2.2 + lp(crack, .3)) * np.exp(-tt * 1.6) * np.clip(tt / .05, 0, 1), t, g)
def claps(t, n=6):
    for i in range(n):
        tt = T(.06); put(lp(rng.uniform(-1, 1, len(tt)), .2) * np.exp(-tt * 70) * 1.4, t + i * .16 + rng.uniform(0, .02), .5)

S1, S2, S3, S4, S5 = [s[0] for s in V.SHOTS]
FIN0 = V.SHOTS[-1][1]

# --- 1. discours solennel : fanfare d'ouverture, puis bourdon discret sous la voix
put(DAVUL, 0, 1.0); put(GONG, 0, .25)
for i in range(8): put(DAVUL_HI, .02 + i * .06, .15 + .03 * i)
fan([(74, 0, .5), (74, .5, .25), (74, .75, .25), (78, 1, 1)], 0, .35)
put(drone(50, V.OUV_T), 0, .12)
for k in range(int(V.OUV_T / B)): put(lute([50, 57, 62, 57][k % 4], .4), k * B, .16)
# « OUVERTE ! » : coup de fanfare
put(DAVUL, V.OUV_T, 1.4); put(GONG, V.OUV_T, .5)
fan([(78, 0, .33), (81, .33, .33), (86, .67, 1.2)], V.OUV_T, .55)
# --- 2. tentative n° 1 : marche sur la pointe des pieds, éternuement, feu
for k in range(int((V.SNEEZE_T - .9 - S2) / (B / 2))):
    put(lute([62, 66, 69, 66][k % 4], .25), S2 + .1 + k * B / 2, .3)
tt = T(1.4); sw = lp(rng.uniform(-1, 1, len(tt)), .9) * (tt / tt[-1]) ** 2 * 2.5
put(sw, V.SNEEZE_T - 1.4, .35)
cut(V.SNEEZE_T - .02)
put(DAVUL, V.SNEEZE_T, 1.6); put(GONG, V.SNEEZE_T, .6); roar(V.SNEEZE_T, 1.8, 1.0)
tt = T(.9); f = hz(69) * (1 - .35 * (tt / tt[-1]) ** 1.3)               # le cor « se dégonfle »
put(sum((1 / k ** .7) * np.sin(2 * np.pi * k * np.cumsum(f) / SR) for k in range(1, 10)) / 5 * env(len(tt), .02, .25), 10.7, .45)
put(DAVUL_HI, 11.2, .7); put(NAKER, 11.2, .5)                           # tampon ÉCHEC
# --- 3. tentative n° 2 : tic-tac et tension
for i in range(int((V.HIC_T - S3) / .5)):
    put(tick(), S3 + .25 + i * .5, .5); put(tick(), S3 + .5 + i * .5, .3)
put(drone(45, V.HIC_T - S3), S3, .1)
tt = T(V.HIC_T - S3); put(np.sin(2 * np.pi * np.cumsum(500 + 700 * (tt / tt[-1]) ** 2) / SR) * (tt / tt[-1]) ** 2 * .5, S3, .06)
# --- 4. le hoquet : petite flamme, puis silence total
cut(V.HIC_T - .02)
put(whoosh(.25), V.HIC_T, .4); roar(V.HIC_T + .05, .6, .35)
tt = T(1.2); put(lp(rng.uniform(-1, 1, len(tt)), .3) * np.exp(-tt * 2.5) * .5, V.HIC_T + .3, .25)   # grésillement de la barbe
put(NAKER, V.HIC_T + 1.0, .35)
# --- 5. le Grand Maître coupe : clic de ciseaux, fanfare, applaudissements
for x in (V.CUT_T, V.CUT_T + .05): put(tick(), x, .9); put(bell(3200, .15), x, .1)
put(DAVUL, V.CUT_T + .9, 1.3); put(GONG, V.CUT_T + .9, .4)
fan([(78, 0, .33), (78, .33, .33), (78, .67, .33), (81, 1, .67), (83, 1.67, .33), (86, 2, .67)], V.CUT_T + .9, .5)
claps(V.CUT_T + .5, 8)
drums(V.CUT_T + .9, FIN0, .7)
# --- carte de fin : la quête (cornemuse + tambours), accord final
put(DAVUL, FIN0, 1.4); put(GONG, FIN0, .35); put(whoosh(), FIN0 - .2, .3)
put(drone(50, DUR - FIN0), FIN0, .22)
air = [(74, 0, .5), (76, .5, .5), (78, 1, .5), (79, 1.5, .5), (81, 2, 1), (83, 3, .5), (81, 3.5, .5)]
for m, bt, d in air: put(chanter(m - 12, d * B * .97, None), FIN0 + bt * B, .8)
drums(FIN0, DUR - .9, .85)
FIN = FIN0 + 4 * B
put(DAVUL, FIN, 1.5); put(DAVUL_HI, FIN, .6)
for m in [38, 50, 57, 62, 66, 69]:
    h = horn(m, .9).copy(); h *= np.linspace(1, 0, len(h)) ** .8; put(h, FIN, .3)

mix = np.tanh(mix / np.percentile(np.abs(mix), 99.5) * 1.3) * .8
# --- voix (ajoutées après le limiteur, musique baissée dessous)
VOX = [('voix_inaug/dragon_discours.wav', .15, .95), ('voix_inaug/atchoum.wav', V.SNEEZE_T - 2.25, .95),
       ('voix_inaug/hic.wav', V.HIC_T - .3, .9), ('voix_inaug/gm_algenib.wav', V.CUT_T - .25, 1.0)]
duck = np.ones(N); vox = np.zeros(N)
for p, t0, g in VOX:
    x = load(p); i = int(t0 * SR); x = x[: N - i]; vox[i:i + len(x)] += x * g
    a, b = i, i + len(x); duck[a:b] = np.minimum(duck[a:b], .45)
duck = np.convolve(duck, np.ones(2205) / 2205, 'same')
mix = mix * duck + vox
mix = np.clip(mix, -1, 1) * .97
mix[int((DUR - .25) * SR):] *= np.linspace(1, 0, N - int((DUR - .25) * SR))
with wave.open('son11.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok son11.wav')
