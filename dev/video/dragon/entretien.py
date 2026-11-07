"""Instagram et TikTok « L'entretien d'embauche du dragon » (30,6 s), 7 novembre 2026, 3e vidéo d'ouverture.
Demande de Nathan (7/11, 11 h 40) : « une vidéo décalée au maximum… lâche-toi sur les blagues, que rien ne
soit prévisible ». Format des réels qui font réagir : accroche datée, série numérotée (Question 1/4 à 4/4),
retournement, dernier gag, question à un chiffre. Chaque texte reste au moins 2,4 s ; la carte de fin 4,6 s.
Images : Nano Banana 2.1 ; animation : Wan 3.0 Prime (fal.ai). Carte de fin : annonce/c7.mp4.
Zones d'Instagram et TikTok évitées : 220 px en haut, 470 px en bas, colonne des boutons à droite (x > 930).
Usage : python3 entretien.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, os, math, subprocess
from PIL import Image, ImageDraw, ImageFilter

_open = Image.open
Image.open = lambda p, *a, **k: Image.new('RGB', (941, 1672), (20, 20, 30)) if isinstance(p, str) and not os.path.exists(p) else _open(p, *a, **k)
import montage as M
import fete as F
import inaug2 as I
Image.open = _open

W, H, FPS = 1080, 1920, 30
XT = 500
A = 'entretien/'
SCRATCH = '/tmp/claude-0/-home-claude/2200d18c-fb03-5130-b93c-65df657ebe08/scratchpad/entretien/'

# (début, fin, clip, départ dans le clip, vitesse)
SHOTS = [
    (0.0, 3.0, 'e1', 0.0, 1.0),     # le dragon en costume face au Grand Maître
    (3.0, 6.4, 'e2', 0.0, 1.0),     # Q1 : « Je suis très chaud. » La chaise prend feu
    (6.4, 9.8, 'e3', 0.0, 1.0),     # Q2 : « Je suis très chaud. » La barbe flambe
    (9.8, 13.4, 'e4', 0.0, 1.0),    # Q3 : le vétéran des anniversaires
    (13.4, 14.9, 'e1', 3.0, 1.0),   # Q4 : « Où vous voyez-vous dans 5 ans ? »
    (14.9, 17.2, 'e5', 0.0, 1.0),   # … « À votre place. » Rôles inversés
    (17.2, 20.2, 'e6', 0.0, 1.0),   # le Grand Maître sort la quête
    (20.2, 23.2, 'e7', 0.0, 1.0),   # les enfants dans les rues
    (23.2, 26.0, 'e8', 0.0, 1.0),   # salle d'attente
    (26.0, 30.6, '../annonce/c7', 0.0, 1.0),   # carte de fin
]
FIN0 = 26.0
END = 30.6
R1_T = 4.3             # réponse 1
R2_T = 7.7             # réponse 2
R3_T = 11.0            # réponse 3
VET_T = 12.1           # tampon VÉTÉRAN
R4_T = 14.3            # « À votre place. »
SWAP_T = 14.9          # coupe sèche, rôles inversés
QUETE_T = 18.2         # LA QUÊTE DU CHEVALIER
IMPACTS = [VET_T, SWAP_T, QUETE_T]
PUNCH = [(R1_T, 1.05), (R2_T, 1.07), (VET_T, 1.1), (SWAP_T, 1.08), (QUETE_T, 1.06)]

_CF = {}
def frames(name):
    if name not in _CF:
        _CF.clear()
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', A + name + '.mp4', '-vf',
                              f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        n = len(raw) // (W * H * 3)
        _CF[name] = [raw[i * W * H * 3:(i + 1) * W * H * 3] for i in range(n)]
    return _CF[name]
def clip_at(name, t):
    fr = frames(name); i = min(len(fr) - 1, max(0, int(round(t * FPS))))
    return Image.frombuffer('RGB', (W, H), fr[i]).convert('RGBA')

E = {}
def T_(s, size=86, fill=None, font=None, maxw=860, stroke=12):
    if isinstance(fill, list): fill = fill + [fill[-1]] * 8
    return M.text_img(s, font or M.TITLE, size, fill=fill or M.WHITE, stroke=stroke, maxw=maxw)

def question(n, q):
    return T_(f'Question {n} :\n« {q} »', 68, [M.GOLD, M.WHITE])
def answer(a, size=84):
    return T_(f'« {a} »', size, M.GOLD, maxw=880, stroke=14)

def build():
    G = M.GOLD
    E['h1'] = T_('7 NOVEMBRE · 10 H 00', 84, G, maxw=900)
    E['h2'] = T_('Entretien d\'embauche.\nPoste : animateur\nd\'anniversaire.', 72, [M.WHITE, M.WHITE, G])
    E['q1'] = question('1/4', 'Votre plus grande qualité ?')
    E['q2'] = question('2/4', 'Votre plus grand défaut ?')
    E['q3'] = question('3/4', 'Une expérience avec les enfants ?')
    E['q4'] = question('4/4', 'Où vous voyez-vous dans 5 ans ?')
    E['r1'] = answer('Je suis très chaud.')
    E['r2'] = answer('Je suis très chaud.')
    E['r3'] = answer('J\'ai survécu à un\nanniversaire de 8 ans.', 70)
    E['r4'] = answer('À votre place.', 92)
    E['vet'] = F.stamp('VÉTÉRAN', 120)
    E['mieux'] = T_('« Moi, j\'ai mieux\nqu\'un animateur : »', 74, [M.WHITE, M.WHITE])
    E['quete'] = M.banner('LA QUÊTE\nDU CHEVALIER', 84)
    E['open2'] = T_('À ton prénom.\nDans les rues de ta ville.\nSans animateur.', 70, [M.WHITE, G, G])
    E['chom'] = T_('Ils cherchent toujours\ndu travail.', 76, [M.WHITE, G])
    E['q'] = T_('Tu l\'embaucherais ?', 80, M.WHITE)
    E['opts'] = T_('1 oui · 2 non\n3 en stage', 76, [M.GOLD, M.GOLD])
    E['cta'] = M.banner('LA QUÊTE EST OUVERTE\nLIEN EN BIO', 64)
    E['url'] = T_('maquetelegendaire.fr', 60, stroke=10)

SPE = M.Sparkles(40, (40, 220, 1000, 1400), 11, size=(7, 18))
SPG = M.Sparkles(60, (60, 500, 1000, 1500), 23, size=(8, 22))

def arrow(im, x, y, t, s=1.0):
    d = ImageDraw.Draw(im); y += 12 * abs(math.sin(t * 6))
    pts = [(x - 22 * s, y - 56 * s), (x + 22 * s, y - 56 * s), (x + 22 * s, y), (x + 50 * s, y), (x, y + 52 * s), (x - 50 * s, y), (x - 22 * s, y)]
    d.polygon(pts, fill=M.GOLD + (255,)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=6)

def shade(im, y0, y1, a=120):
    g = Image.new('L', (1, y1 - y0))
    for y in range(y1 - y0): g.putpixel((0, y), int(a * (1 - y / (y1 - y0)) ** 1.4))
    layer = Image.new('RGBA', (W, y1 - y0), (10, 12, 30, 0)); layer.putalpha(g.resize((W, y1 - y0)))
    im.alpha_composite(layer, (0, y0))

def zoom(im, z, cy=0.5):
    if z <= 1.001: return im
    w, h = int(W / z), int(H / z); x0 = (W - w) // 2; y0 = int((H - h) * cy)
    return im.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.BICUBIC)

def punch(t):
    z = 1.0
    for t0, zz in PUNCH:
        if t0 <= t < t0 + 1.6:
            u = (t - t0) / 0.12
            z = max(z, 1 + (zz - 1) * (min(1, u) if u < 1 else 1 - 0.35 * min(1, (t - t0 - .12) / 1.4)))
    return z

def shake(im, t):
    amp = 0
    for t0 in IMPACTS:
        if t0 <= t < t0 + .45: amp = max(amp, 22 * math.exp(-(t - t0) * 9))
    if amp < 1: return im
    dx = int(amp * math.sin(t * 97)); dy = int(amp * math.cos(t * 83))
    big = im.resize((W + 48, H + 85), Image.BILINEAR)
    return big.crop((24 + dx, 42 + dy, 24 + dx + W, 42 + dy + H))

def frame(t):
    for (a, b, c, off, sp) in SHOTS:
        if a <= t < b: break
    lt = t - a
    im = clip_at(c, off + lt * sp)
    im = zoom(im, punch(t))
    P = M.paste; pop = M.pop
    if a < FIN0: shade(im, 0, 900, 160)
    if a == 0.0:
        P(im, E['h1'], XT, 280, pop(t, 0.0, .14))
        P(im, E['h2'], XT, 530, pop(t, 0.5, .18))
    elif c == 'e2':
        P(im, E['q1'], XT, 350, pop(t, a, .16))
        P(im, E['r1'], XT, 640, pop(t, R1_T, .14))
    elif c == 'e3':
        P(im, E['q2'], XT, 350, pop(t, a, .16))
        P(im, E['r2'], XT, 640, pop(t, R2_T, .14))
    elif c == 'e4':
        P(im, E['q3'], XT, 350, pop(t, a, .16))
        P(im, E['r3'], XT, 660, pop(t, R3_T, .14))
        F.stamp_at(im, E['vet'], t, VET_T, XT, 1250, .9)
    elif c == 'e1':
        P(im, E['q4'], XT, 350, pop(t, a, .16))
        P(im, E['r4'], XT, 640, pop(t, R4_T, .14))
    elif c == 'e5':
        P(im, E['r4'], XT, 640, 1.0)
    elif c == 'e6':
        P(im, E['mieux'], XT, 330, pop(t, a, .16))
        if t >= QUETE_T: SPG.draw(im, t - QUETE_T, .8)
        P(im, E['quete'], XT, 620, pop(t, QUETE_T, .16) * (1 + .03 * math.exp(-((t - QUETE_T) % .6) * 10)))
    elif c == 'e7':
        P(im, E['open2'], XT, 400, pop(t, a, .18))
    elif c == 'e8':
        P(im, E['chom'], XT, 360, pop(t, a + .3, .16))
    else:
        SPE.draw(im, lt, .7)
        P(im, E['q'], XT, 330, pop(lt, 0.0, .18))
        P(im, E['opts'], XT, 500, pop(lt, .25, .18))
        if lt > .5: arrow(im, XT, 650, lt)
        P(im, E['cta'], XT, 820, pop(lt, .8) * (1 + .03 * math.exp(-(lt % .6) * 10)))
        P(im, E['url'], XT, 975, pop(lt, 1.2))
    if lt < .07 and a > 0:
        I.flash(im, (255, 240, 200), .32 * (1 - lt / .07))
    for t0, col in [(SWAP_T, (255, 255, 255)), (QUETE_T, (255, 230, 150))]:
        if t0 <= t < t0 + .25: I.flash(im, col, .45 * (1 - (t - t0) / .25))
    return shake(im, t)

def main():
    build()
    args = sys.argv[1:]
    if '--preview' in args:
        os.makedirs(SCRATCH, exist_ok=True)
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'{SCRATCH}p_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'entretien.mp4'
    tmp = out[:-4] + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son16.wav',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, out); print('ok', out)

if __name__ == '__main__':
    main()
