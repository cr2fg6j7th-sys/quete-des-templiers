"""Instagram « Le dragon doit annoncer l'ouverture » (26 s), 7 novembre 2026.
Format des réels qui ont le plus fait réagir et regarder : accroche datée, série de tentatives ratées
(« Tentative 1/4 »… on veut voir la suivante), réussite surprise, dernier gag, question à réponse d'un
chiffre (« 1, 2, 3 ou 4 ? »). Chaque texte reste au moins 2,4 s ; la carte de fin 4,4 s.
Images : Nano Banana 2.1 (fal.ai) d'après les personnages existants ; animation : Wan 3.0 Prime (fal.ai).
Zones d'Instagram évitées : 220 px en haut, 470 px en bas, colonne des boutons à droite (x > 930).
Usage : python3 annonce.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, os, math, subprocess
from PIL import Image, ImageDraw, ImageFilter

# Les modules d'outils chargent à l'import des images d'anciennes vidéos : une image vide les remplace.
_open = Image.open
Image.open = lambda p, *a, **k: Image.new('RGB', (941, 1672), (20, 20, 30)) if isinstance(p, str) and not os.path.exists(p) else _open(p, *a, **k)
import montage as M
import fete as F
import inaug2 as I
Image.open = _open

W, H, FPS = 1080, 1920, 30
XT = 500                                   # centre des textes, à gauche de la colonne des boutons
A = 'annonce/'
SCRATCH = '/tmp/claude-0/-home-claude/2200d18c-fb03-5130-b93c-65df657ebe08/scratchpad/ouv/'

# (début, fin, clip, départ dans le clip, vitesse)
SHOTS = [
    (0.0, 3.0, 'c1', 0.0, 1.0),     # le dragon prend sa respiration
    (3.0, 6.0, 'c2', 0.0, 1.0),     # tentative 1 : la trompette crache du feu
    (6.0, 9.0, 'c3', 0.3, 1.0),     # tentative 2 : le pigeon revient grillé
    (9.0, 12.0, 'c4', 0.0, 1.0),    # tentative 3 : la barbe du Grand Maître
    (12.0, 15.0, 'c5', 0.0, 1.0),   # tentative 4 : papa appuie sur le bouton
    (15.0, 19.2, 'c6', 0.0, 1.0),   # les enfants chevaliers sortent de partout
    (19.2, 22.0, 'c8', 0.8, 1.0),   # tentative 5 : « pouet »
    (22.0, 26.4, 'c7', 0.0, 1.0),   # carte de fin
]
FIN0 = 22.0
END = 26.4
STAMP = {3: 4.9, 6: 7.9, 9: 10.9}           # tampons ÉCHEC (début du plan -> instant)
ATCHOUM_T = 9.15
BIP_T = 13.3
POUET_T = 20.1

_CF = {}
def frames(name):
    if name not in _CF:
        _CF.clear()                         # un seul clip en mémoire à la fois (1080 x 1920, ~1 Go décodé)
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
def T_(s, size=86, fill=None, font=None, maxw=780, stroke=12):
    if isinstance(fill, list): fill = fill + [fill[-1]] * 8
    return M.text_img(s, font or M.TITLE, size, fill=fill or M.WHITE, stroke=stroke, maxw=maxw)

def label(n, what):
    """« Tentative n/4 : » en or, et ce qui est tenté en blanc, sur deux lignes."""
    return T_(f'Tentative {n} :\n{what}', 84, [M.GOLD, M.WHITE])

def build():
    G = M.GOLD
    E['h1'] = T_('7 NOVEMBRE · 9 H 00', 84, G, maxw=900)
    E['h2'] = T_('Mission du dragon :\nprévenir TOUS les\nchevaliers du royaume.', 78, [M.WHITE, M.WHITE, M.WHITE])
    E['t1'] = label('1/4', 'la trompette')
    E['t2'] = label('2/4', 'le pigeon voyageur')
    E['t3'] = label('3/4', 'le Grand Maître')
    E['t4'] = label('4/4', 'papa et son téléphone')
    E['t5'] = label('5', 'le dragon insiste')
    E['echec'] = F.stamp('ÉCHEC', 120)
    E['total'] = F.stamp('ÉCHEC TOTAL', 100)
    E['atch'] = I.burst('ATCHOUM !', 640, 380, 100)
    E['bip'] = T_('bip.', 70, M.WHITE, font=M.BODY, stroke=10)
    E['open'] = M.banner('LA QUÊTE DU CHEVALIER\nEST OUVERTE !', 74)
    E['open2'] = T_('À ton prénom.\nDans les rues\nde ta ville.', 74, [M.WHITE, G, G])
    E['pouet'] = T_('pouet.', 92, M.WHITE, font=M.BODY, stroke=12)
    E['q'] = T_('Ta tentative préférée :\n1, 2, 3 ou 4 ?', 88, [M.WHITE, G])
    E['cta'] = M.banner('LA QUÊTE EST OUVERTE\nLIEN EN BIO', 70)
    E['url'] = T_('maquetelegendaire.fr', 64, stroke=10)

SPE = M.Sparkles(40, (40, 220, 1000, 1400), 11, size=(7, 18))

def arrow(im, x, y, t):
    """Flèche dorée qui rebondit vers le bas, vers les commentaires."""
    d = ImageDraw.Draw(im); y += 14 * abs(math.sin(t * 6))
    pts = [(x - 26, y - 70), (x + 26, y - 70), (x + 26, y), (x + 60, y), (x, y + 64), (x - 60, y), (x - 26, y)]
    d.polygon(pts, fill=M.GOLD + (255,)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=7)

def shade(im, y0, y1, a=120):
    """Voile sombre en dégradé derrière les textes du haut, pour qu'ils se lisent sur un ciel clair."""
    g = Image.new('L', (1, y1 - y0))
    for y in range(y1 - y0): g.putpixel((0, y), int(a * (1 - y / (y1 - y0)) ** 1.4))
    layer = Image.new('RGBA', (W, y1 - y0), (10, 12, 30, 0)); layer.putalpha(g.resize((W, y1 - y0)))
    im.alpha_composite(layer, (0, y0))

def frame(t):
    for (a, b, c, off, sp) in SHOTS:
        if a <= t < b: break
    lt = t - a
    im = clip_at(c, off + lt * sp)
    P = M.paste; pop = M.pop
    if c != 'c7': shade(im, 0, 860 if c == 'c6' else 760, 150)
    if c == 'c1':
        P(im, E['h1'], XT, 280, pop(t, 0.0, .14))
        P(im, E['h2'], XT, 520, pop(t, 0.5, .18))
    elif c == 'c2':
        P(im, E['t1'], XT, 330, pop(t, a, .16))
        F.stamp_at(im, E['echec'], t, STAMP[3], XT, 1230, .9)
    elif c == 'c3':
        P(im, E['t2'], XT, 330, pop(t, a, .16))
        F.stamp_at(im, E['echec'], t, STAMP[6], XT, 1230, .9)
    elif c == 'c4':
        P(im, E['t3'], XT, 330, pop(t, a, .16))
        if ATCHOUM_T <= t < ATCHOUM_T + 1.2: P(im, E['atch'], 360, 760, pop(t, ATCHOUM_T, .12), rot=8)
        F.stamp_at(im, E['total'], t, STAMP[9], XT, 1230, .9)
    elif c == 'c5':
        P(im, E['t4'], XT, 330, pop(t, a, .16))
        if t >= BIP_T: P(im, E['bip'], 640, 820, pop(t, BIP_T, .12))
    elif c == 'c6':
        P(im, E['open'], XT, 340, pop(t, a, .18) * (1 + .025 * math.sin(lt * 7)))
        P(im, E['open2'], XT, 640, pop(t, a + 1.2, .18))
    elif c == 'c8':
        P(im, E['t5'], XT, 330, pop(t, a, .16))
        if t >= POUET_T: P(im, E['pouet'], 330, 900, pop(t, POUET_T, .12), rot=-8)
    elif c == 'c7':
        SPE.draw(im, lt, .7)
        P(im, E['q'], XT, 380, pop(lt, 0.0, .18))
        if lt > .35: arrow(im, XT, 590, lt)
        P(im, E['cta'], XT, 830, pop(lt, .8) * (1 + .03 * math.exp(-(lt % .6) * 10)))
        P(im, E['url'], XT, 1010, pop(lt, 1.2))
    if lt < .07 and a > 0:
        I.flash(im, (255, 240, 200), .32 * (1 - lt / .07))
    if c == 'c4' and ATCHOUM_T <= t < ATCHOUM_T + .25:
        I.flash(im, (255, 170, 60), .4 * (1 - (t - ATCHOUM_T) / .25))
    return im

def main():
    build()
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'{SCRATCH}p_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'annonce.mp4'
    tmp = out[:-4] + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son14.wav',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, out); print('ok', out)

if __name__ == '__main__':
    main()
