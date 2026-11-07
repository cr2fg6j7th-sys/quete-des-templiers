"""Instagram et TikTok « Le petit chevalier recrute sa troupe » (31,8 s), 7 novembre 2026, 2e vidéo d'ouverture.
Même format que annonce.py (accroche datée, recrues 1/4 à 4/4, réussite, question à un chiffre), avec des
chutes qu'on ne voit pas venir (demande de Nathan du 7/11 : « effet blague, effet waouh… très surprenantes ») :
le destrier EN PANNE, papa EN VEILLE DEPUIS 2018, la petite sœur RECRUTÉE puis PROMUE GÉNÉRALE, le chien
revenu pour le goûter, et le twist : pendant ce temps, le chat a déjà réservé la quête.
Images : Nano Banana 2.1 et Wan 3.0 Prime (fal.ai) ; plan du chat : FLUX.1 Kontext et Wan 2.2 (Hugging Face).
Carte de fin : le clip du dragon de annonce.py (annonce/c7.mp4).
Zones d'Instagram et TikTok évitées : 220 px en haut, 470 px en bas, colonne des boutons à droite (x > 930).
Usage : python3 troupe.py [sortie.mp4] [--preview t1 t2 ...]"""
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
A = 'troupe/'
SCRATCH = '/tmp/claude-0/-home-claude/2200d18c-fb03-5130-b93c-65df657ebe08/scratchpad/troupe/'

# (début, fin, clip, départ dans le clip, vitesse)
SHOTS = [
    (0.0, 3.0, 'c1', 0.0, 1.0),     # le chevalier saute sur son lit
    (3.0, 6.0, 'c2', 1.3, 1.0),     # recrue 1 : le destrier… EN PANNE
    (6.0, 9.0, 'c3', 1.2, 1.0),     # recrue 2 : le chat jette le casque, REFUSÉ
    (9.0, 12.4, 'c4', 1.2, 1.0),    # recrue 3 : papa, EN VEILLE DEPUIS 2018
    (12.4, 16.4, 'c5', 0.3, 1.0),   # recrue 4 : la petite sœur, RECRUTÉE puis PROMUE GÉNÉRALE
    (16.4, 20.6, 'c6', 0.0, 0.75),  # la troupe et le dragon à la porte : LA QUÊTE EST OUVERTE
    (20.6, 23.8, 'c7', 0.0, 1.0),   # recrue 5 : le chien revient… pour le goûter
    (23.8, 27.2, 'c8', 0.0, 1.0),   # pendant ce temps, le chat a déjà réservé la quête
    (27.2, 31.8, '../annonce/c7', 0.0, 1.0),   # carte de fin
]
FIN0 = 27.2
END = 31.8
FALL_T = 4.95          # le chevalier tombe sur les fesses
PANNE_T = 5.0
MEOW_T = 6.3
CLANG_T = 7.55         # le casque touche le sol
REFUSE_T = 8.0
RONFLE_T = 9.3
VEILLE_T = 10.5
CRI_T = 13.45
OK_T = 13.7
GENERALE_T = 14.7
GOUTER_T = 21.6
WOUF_T = 21.0
TAP_T = 24.35
REVEAL_T = 25.1
IMPACTS = [PANNE_T, REFUSE_T, VEILLE_T, OK_T, GENERALE_T, 16.4, REVEAL_T]   # tremblements d'écran
PUNCH = [(VEILLE_T, 1.07), (GENERALE_T, 1.09), (GOUTER_T, 1.06), (REVEAL_T, 1.1)]  # zooms brusques

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
    """« Recrue n/4 : » en or, et la recrue en blanc, sur deux lignes."""
    return T_(f'Recrue {n} :\n{what}', 84, [M.GOLD, M.WHITE])

def stamp_lines(lines, size, col):
    """Tampon sur plusieurs lignes, même dessin que fete.stamp (fond crème, cadre et lettres pleines)."""
    f = M.font(M.TITLE, size); lh = int(size * 1.12)
    w = int(max(f.getlength(l) for l in lines)) + 90; h = lh * len(lines) + 60
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w - 4, h - 4], 22, fill=(255, 246, 225, 235), outline=col + (255,), width=12)
    d.rounded_rectangle([22, 22, w - 22, h - 22], 14, outline=col + (255,), width=4)
    for i, l in enumerate(lines):
        d.text((w / 2, 30 + lh * i + lh / 2 + size * 0.08), l, font=f, fill=col + (255,), anchor='mm')
    sh = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); sh.paste((0, 0, 0, 110), (10, 14, w + 6, h + 10))
    sh = sh.filter(ImageFilter.GaussianBlur(8)); sh.alpha_composite(im, (6, 4))
    return sh.rotate(-10, expand=True, resample=Image.BICUBIC)

GREEN = (24, 130, 60)
ROYAL = (150, 95, 0)
def build():
    G = M.GOLD
    E['h1'] = T_('7 NOVEMBRE · 7 H 12', 84, G, maxw=900)
    E['h2'] = T_('La quête est ouverte.\nIl lui faut une troupe.\nTout de suite.', 68, [M.WHITE, M.WHITE, G], maxw=880)
    E['t1'] = label('1/4', 'le destrier')
    E['t2'] = label('2/4', 'le chat')
    E['t3'] = label('3/4', 'papa')
    E['t4'] = label('4/4', 'la petite sœur')
    E['t5'] = label('5', 'le chien')
    E['panne'] = F.stamp('EN PANNE', 116)
    E['refuse'] = F.stamp('REFUSÉ', 120)
    E['veille'] = stamp_lines(['EN VEILLE', 'DEPUIS 2018'], 84, (196, 18, 30))
    E['ok'] = F.stamp('RECRUTÉE !', 100, col=GREEN)
    E['gen'] = stamp_lines(['PROMUE', 'GÉNÉRALE'], 112, ROYAL).rotate(18, expand=True, resample=Image.BICUBIC)
    E['ronfle'] = T_('rrrron… pfffff…', 60, M.WHITE, font=M.BODY, stroke=10)
    E['open'] = M.banner('LA QUÊTE DU CHEVALIER\nEST OUVERTE !', 74)
    E['open2'] = T_('À ton prénom.\nDans les rues\nde ta ville.', 74, [M.WHITE, G, G])
    E['gouter'] = T_('Il a appris qu\'il y avait\nun goûter.', 66, [M.WHITE, G], maxw=880)
    E['pdt'] = T_('Pendant ce temps,\nle chat…', 84, [M.WHITE, G])
    E['reveal'] = M.banner('… A DÉJÀ RÉSERVÉ\nLA QUÊTE.', 78)
    E['q'] = T_('Chez toi, qui organise\nvraiment l\'anniversaire ?', 64, [M.WHITE, M.WHITE], maxw=880)
    E['opts'] = T_('1 papa · 2 maman\n3 le chat', 70, [M.GOLD, M.GOLD], maxw=880)
    E['cta'] = M.banner('LA QUÊTE EST OUVERTE\nLIEN EN BIO', 64)
    E['url'] = T_('maquetelegendaire.fr', 60, stroke=10)

SPE = M.Sparkles(40, (40, 220, 1000, 1400), 11, size=(7, 18))
SPG = M.Sparkles(60, (60, 600, 1000, 1500), 23, size=(8, 22))

def arrow(im, x, y, t, s=1.0):
    """Flèche dorée qui rebondit vers le bas, vers les commentaires."""
    d = ImageDraw.Draw(im); y += 12 * abs(math.sin(t * 6))
    pts = [(x - 22 * s, y - 56 * s), (x + 22 * s, y - 56 * s), (x + 22 * s, y), (x + 50 * s, y), (x, y + 52 * s), (x - 50 * s, y), (x - 22 * s, y)]
    d.polygon(pts, fill=M.GOLD + (255,)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=6)

def shade(im, y0, y1, a=120):
    """Voile sombre en dégradé derrière les textes du haut, pour qu'ils se lisent sur un fond clair."""
    g = Image.new('L', (1, y1 - y0))
    for y in range(y1 - y0): g.putpixel((0, y), int(a * (1 - y / (y1 - y0)) ** 1.4))
    layer = Image.new('RGBA', (W, y1 - y0), (10, 12, 30, 0)); layer.putalpha(g.resize((W, y1 - y0)))
    im.alpha_composite(layer, (0, y0))

def zoom(im, z, cy=0.5):
    """Zoom au centre (cy : hauteur du point fixe, de 0 à 1)."""
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
    cy = .35 if c == 'c8' else .5
    im = zoom(im, punch(t), cy)
    P = M.paste; pop = M.pop
    if a < FIN0: shade(im, 0, 860 if c in ('c6', 'c7') else 760, 150)
    if c == 'c1':
        P(im, E['h1'], XT, 280, pop(t, 0.0, .14))
        P(im, E['h2'], XT, 530, pop(t, 0.5, .18))
    elif c == 'c2':
        P(im, E['t1'], XT, 330, pop(t, a, .16))
        F.stamp_at(im, E['panne'], t, PANNE_T, XT, 1230, .9)
    elif c == 'c3':
        P(im, E['t2'], XT, 330, pop(t, a, .16))
        F.stamp_at(im, E['refuse'], t, REFUSE_T, XT, 1230, .9)
    elif c == 'c4':
        P(im, E['t3'], XT, 330, pop(t, a, .16))
        if t >= RONFLE_T: P(im, E['ronfle'], 470, 790, pop(t, RONFLE_T, .14) * (1 + .05 * math.sin((t - RONFLE_T) * 8)))
        F.stamp_at(im, E['veille'], t, VEILLE_T, XT, 1290, .9)
    elif c == 'c5':
        P(im, E['t4'], XT, 330, pop(t, a, .16))
        if t < GENERALE_T + .12: F.stamp_at(im, E['ok'], t, OK_T, XT, 1260, .85)
        if t >= GENERALE_T: SPG.draw(im, t - GENERALE_T, .9)
        F.stamp_at(im, E['gen'], t, GENERALE_T, XT, 1230, .9)
    elif c == 'c6':
        P(im, E['open'], XT, 340, pop(t, a, .18) * (1 + .025 * math.sin(lt * 7)))
        P(im, E['open2'], XT, 640, pop(t, a + 1.2, .18))
    elif c == 'c7':
        P(im, E['t5'], XT, 330, pop(t, a, .16))
        if t >= GOUTER_T: P(im, E['gouter'], XT, 600, pop(t, GOUTER_T, .16))
    elif c == 'c8':
        P(im, E['pdt'], XT, 330, pop(t, a, .16))
        if t >= REVEAL_T: SPG.draw(im, t - REVEAL_T, .8)
        P(im, E['reveal'], XT, 1370, pop(t, REVEAL_T, .14) * (1 + .03 * math.exp(-((t - REVEAL_T) % .6) * 10)))
    else:
        SPE.draw(im, lt, .7)
        P(im, E['q'], XT, 320, pop(lt, 0.0, .18))
        P(im, E['opts'], XT, 500, pop(lt, .25, .18))
        if lt > .5: arrow(im, XT, 650, lt)
        P(im, E['cta'], XT, 820, pop(lt, .8) * (1 + .03 * math.exp(-(lt % .6) * 10)))
        P(im, E['url'], XT, 975, pop(lt, 1.2))
    if lt < .07 and a > 0:
        I.flash(im, (255, 240, 200), .32 * (1 - lt / .07))
    for t0, col in [(OK_T, (180, 255, 180)), (GENERALE_T, (255, 220, 120)), (REVEAL_T, (255, 230, 150))]:
        if t0 <= t < t0 + .25: I.flash(im, col, .4 * (1 - (t - t0) / .25))
    return shake(im, t)

def main():
    build()
    args = sys.argv[1:]
    if '--preview' in args:
        os.makedirs(SCRATCH, exist_ok=True)
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'{SCRATCH}p_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'troupe.mp4'
    tmp = out[:-4] + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son15.wav',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, out); print('ok', out)

if __name__ == '__main__':
    main()
