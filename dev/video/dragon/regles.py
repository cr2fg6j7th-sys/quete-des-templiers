"""Instagram et TikTok « Le règlement de l'anniversaire » (30,4 s), revue marketing du 8 novembre 2026.
Format des réels qui font réagir (claude/video-ouverture-dragon.md) : heure en accroche, série numérotée
(Règle 1/4 à 4/4, puis une 5e « hors série »), retournement (papa éliminé), question à un chiffre, fin lisible.
Gratuit : uniquement des images déjà dans le dépôt (annonce/, entretien/, img/), animées en zoom lent ;
bande-son synthétisée par son17.py. Aucune génération payante.
Zones d'Instagram et TikTok : texte entre x 60 et 940, y 230 et 1500.
Usage : python3 regles.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, os, math, subprocess
from PIL import Image, ImageDraw

_open = Image.open
Image.open = lambda p, *a, **k: Image.new('RGB', (941, 1672), (20, 20, 30)) if isinstance(p, str) and not os.path.exists(p) else _open(p, *a, **k)
import montage as M
import fete as F
import inaug2 as I
Image.open = _open

W, H, FPS = 1080, 1920, 30
XT = 500
SCRATCH = os.environ.get('SCRATCH', '/tmp/regles/')

# (début, fin, image, zoom départ, zoom fin, centre x, centre y)
SHOTS = [
    (0.0, 3.4, 'img/dragon-debout.jpg', 1.00, 1.08, .5, .55),
    (3.4, 8.0, 'annonce/s2.jpg', 1.05, 1.14, .55, .45),
    (8.0, 12.6, 'entretien/i3.jpg', 1.20, 1.32, .55, .62),
    (12.6, 17.2, 'annonce/s5.jpg', 1.05, 1.18, .5, .5),
    (17.2, 21.8, 'annonce/s6.jpg', 1.00, 1.10, .5, .6),
    (21.8, 25.4, 'entretien/i4.jpg', 1.00, 1.10, .5, .5),
    (25.4, 30.4, 'img/lettre.jpg', 1.00, 1.06, .5, .6),
]
R1_S, R2_S, R3_S, R4_S, R5_S, FIN0 = 3.4, 8.0, 12.6, 17.2, 21.8, 25.4
END = 30.4
ST1 = R1_S + 2.0       # RESPECTÉE (la règle reste seule 1,85 s)
ST2 = R2_S + 2.0       # PRESQUE
EL3 = R3_S + 1.9       # « Premier éliminé : »
ST3 = R3_S + 2.6       # PAPA
ST4 = R4_S + 2.0       # RESPECTÉE
R5_B = R5_S + 1.0      # « Le dragon reste calme. »
ST5 = R5_S + 2.2       # EN COURS
IMPACTS = [ST1, ST2, ST3, ST4, ST5]
PUNCH = [(t, 1.05) for t in IMPACTS]

_IMG = {}
def still(p):
    if p not in _IMG:
        im = Image.open(p).convert('RGB')
        s = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
        x0 = (im.width - W) // 2; y0 = (im.height - H) // 2
        _IMG[p] = im.crop((x0, y0, x0 + W, y0 + H))
    return _IMG[p]

def kb(p, z, cx, cy):
    im = still(p)
    w, h = W / z, H / z
    x0 = min(max(cx * W - w / 2, 0), W - w); y0 = min(max(cy * H - h / 2, 0), H - h)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)).convert('RGBA')

E = {}
def T_(s, size=86, fill=None, maxw=860, stroke=12):
    if isinstance(fill, list): fill = fill + [fill[-1]] * 8
    return M.text_img(s, M.TITLE, size, fill=fill or M.WHITE, stroke=stroke, maxw=maxw)

NAVY = (24, 30, 64)
GREEN = (24, 120, 60)
def tag(txt, size=54):
    f = M.font(M.TITLE, size); w = int(f.getlength(txt)) + 70; h = int(size * 1.25) + 26
    im = Image.new('RGBA', (w + 16, h + 18), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 10, w + 8, h + 10], h // 2, fill=(0, 0, 0, 120))
    d.rounded_rectangle([2, 2, w, h], h // 2, fill=M.GOLD + (255,), outline=(0, 0, 0, 255), width=5)
    d.text((w / 2 + 1, h / 2 + size * 0.06), txt, font=f, fill=NAVY + (255,), anchor='mm')
    return im

def card(txt, size=70):
    """Règle écrite par maman : carte crème sans queue (ce n'est pas un personnage qui parle)."""
    b, _ = M.bubble(txt, (0, 1), size, 800)
    return b

def build():
    G = M.GOLD
    E['h1'] = T_('SAMEDI · 13 H 58', 88, G, maxw=900)
    E['h2'] = T_('Le règlement de\nl\'anniversaire.\nSigné : maman.', 70, [M.WHITE, M.WHITE, G], maxw=900)
    for n in range(1, 5): E[f'tag{n}'] = tag(f'RÈGLE {n}/4')
    E['tag5'] = tag('RÈGLE 5/4')
    E['r1'] = card('« Pas de feu\ndans la maison. »')
    E['r2'] = card('« On ne touche pas\nà la barbe de papy. »')
    E['r3'] = card('« Zéro écran\naujourd\'hui. »')
    E['r4'] = card('« Et surtout :\npersonne ne s\'ennuie. »')
    E['r5n'] = T_('Ajoutée à 16 h 30 :', 74, G, maxw=900)
    E['r5'] = card('« Le dragon\nreste calme. »', 76)
    E['s1'] = F.stamp('RESPECTÉE', 96, GREEN)
    E['c1'] = T_('(C\'était dehors.)', 66, M.WHITE)
    E['s2'] = F.stamp('PRESQUE', 108)
    E['c2'] = T_('Juste effleurée.', 66, M.WHITE)
    E['el'] = T_('Premier éliminé :', 76, M.WHITE)
    E['s3'] = F.stamp('PAPA', 130)
    E['s4'] = F.stamp('RESPECTÉE', 96, GREEN)
    E['c4'] = T_('Une heure de quête\ndans les rues.', 64, [M.WHITE, G])
    E['s5'] = F.stamp('EN COURS', 104)
    E['q'] = T_('Chez toi, quelle règle\nsaute en premier ?', 74, [M.WHITE, M.WHITE])
    E['opts'] = T_('1 · 2 · 3 · 4 · 5', 84, G)
    E['cta'] = M.banner('LA QUÊTE DU CHEVALIER\nLIEN EN BIO', 62)
    E['url'] = T_('maquetelegendaire.fr', 58, stroke=10)

SPE = M.Sparkles(40, (40, 220, 1000, 1400), 11, size=(7, 18))
SPG = M.Sparkles(60, (60, 500, 1000, 1500), 23, size=(8, 22))

def shade(im, y0, y1, a=120, up=False):
    g = Image.new('L', (1, y1 - y0))
    for y in range(y1 - y0):
        u = y / (y1 - y0)
        g.putpixel((0, y), int(a * ((u if up else 1 - u) ** 1.4)))
    layer = Image.new('RGBA', (W, y1 - y0), (10, 12, 30, 0)); layer.putalpha(g.resize((W, y1 - y0)))
    im.alpha_composite(layer, (0, y0))

def zoom(im, z):
    if z <= 1.001: return im
    w, h = int(W / z), int(H / z); x0 = (W - w) // 2; y0 = (H - h) // 2
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
        if t0 <= t < t0 + .45: amp = max(amp, 20 * math.exp(-(t - t0) * 9))
    if amp < 1: return im
    dx = int(amp * math.sin(t * 97)); dy = int(amp * math.cos(t * 83))
    big = im.resize((W + 48, H + 85), Image.BILINEAR)
    return big.crop((24 + dx, 42 + dy, 24 + dx + W, 42 + dy + H))

def arrow(im, x, y, t, s=1.0):
    d = ImageDraw.Draw(im); y += 12 * abs(math.sin(t * 6))
    pts = [(x - 22 * s, y - 56 * s), (x + 22 * s, y - 56 * s), (x + 22 * s, y), (x + 50 * s, y), (x, y + 52 * s), (x - 50 * s, y), (x - 22 * s, y)]
    d.polygon(pts, fill=M.GOLD + (255,)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=6)

def rule(im, t, a, n, key, st, skey, ckey=None, ct=None, sy=1000, cy=1230):
    P = M.paste; pop = M.pop
    P(im, E[f'tag{n}'], XT, 300, pop(t, a, .14))
    P(im, E[key], XT, 520, pop(t, a + .15, .16))
    F.stamp_at(im, E[skey], t, st, XT, sy, .9)
    if ckey and t >= ct: P(im, E[ckey], XT, cy, pop(t, ct, .16))

def frame(t):
    for (a, b, p, z0, z1, cx, cy) in SHOTS:
        if a <= t < b: break
    lt = t - a
    u = M.ease(lt / (b - a))
    im = kb(p, z0 + (z1 - z0) * u, cx, cy)
    im = zoom(im, punch(t))
    P = M.paste; pop = M.pop
    if a < FIN0:
        shade(im, 0, 780, 130)
        if a > 0: shade(im, 900, 1500, 90, up=True)
    else:
        shade(im, 0, 1300, 150); shade(im, 1300, 1920, 110, up=True)
    if a == 0.0:
        P(im, E['h1'], XT, 300, pop(t, 0.0, .14))
        P(im, E['h2'], XT, 560, pop(t, 0.5, .18))
    elif a == R1_S:
        rule(im, t, a, 1, 'r1', ST1, 's1', 'c1', ST1 + .7)
    elif a == R2_S:
        rule(im, t, a, 2, 'r2', ST2, 's2', 'c2', ST2 + .7)
    elif a == R3_S:
        P(im, E['tag3'], XT, 300, pop(t, a, .14))
        P(im, E['r3'], XT, 520, pop(t, a + .15, .16))
        if t >= EL3: P(im, E['el'], XT, 860, pop(t, EL3, .14))
        F.stamp_at(im, E['s3'], t, ST3, XT, 1060, .95)
    elif a == R4_S:
        rule(im, t, a, 4, 'r4', ST4, 's4', 'c4', ST4 + .6)
        if t >= ST4: SPG.draw(im, t - ST4, .7)
    elif a == R5_S:
        P(im, E['r5n'], XT, 300, pop(t, a + .05, .14))
        P(im, E['tag5'], XT, 420, pop(t, a + .3, .14))
        P(im, E['r5'], XT, 640, pop(t, R5_B, .16))
        F.stamp_at(im, E['s5'], t, ST5, XT, 1080, .9)
    else:
        SPE.draw(im, lt, .7)
        P(im, E['q'], XT, 380, pop(lt, 0.0, .18))
        P(im, E['opts'], XT, 590, pop(lt, .3, .18))
        if lt > .6: arrow(im, XT, 760, lt)
        P(im, E['cta'], XT, 960, pop(lt, .9) * (1 + .03 * math.exp(-(lt % .6) * 10)))
        P(im, E['url'], XT, 1130, pop(lt, 1.3))
    if lt < .07 and a > 0:
        I.flash(im, (255, 240, 200), .32 * (1 - lt / .07))
    return shake(im, t)

def main():
    build()
    args = sys.argv[1:]
    if '--preview' in args:
        os.makedirs(SCRATCH, exist_ok=True)
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'{SCRATCH}p_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'regles.mp4'
    tmp = out[:-4] + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son17.wav',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
                          '-map_metadata', '-1', tmp], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, out); print('ok', out)

if __name__ == '__main__':
    main()
