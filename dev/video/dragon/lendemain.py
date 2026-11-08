"""Instagram et TikTok « Le lendemain de l'anniversaire » (34,6 s), dimanche 8 novembre 2026.
Demande de Nathan (8/11, 10 h) : « une vidéo drôle, plus drôle que l'entretien d'embauche… base-toi sur des
vidéos d'autres comptes ». Script validé à 10 h 04 (« produis-la avec Hugging Face en priorité »).
Format repris des réels « lendemain de soirée » (parodie de Very Bad Trip) : réveil daté, enquête en
4 indices absurdes numérotés, photos de la veille, retournement (ce n'étaient pas les enfants), question à
un chiffre. Mêmes règles de lecture que l'entretien : chaque chute reste au moins 2 s, carte de fin 4,6 s.
Images : FLUX.1 Kontext sur Hugging Face (l1 à l5), Nano Banana 2.1 sur fal.ai (l6, l7) une fois le quota
gratuit Hugging Face du jour épuisé ; animation : Wan 3.0 Prime (fal.ai). Souvenir de la quête :
entretien/e7.mp4 ; carte de fin : annonce/c7.mp4.
Zones d'Instagram et TikTok évitées : 220 px en haut, 470 px en bas, colonne des boutons à droite (x > 930).
Usage : python3 lendemain.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, os, math, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

_open = Image.open
Image.open = lambda p, *a, **k: Image.new('RGB', (941, 1672), (20, 20, 30)) if isinstance(p, str) and not os.path.exists(p) else _open(p, *a, **k)
import montage as M
import fete as F
import inaug2 as I
Image.open = _open

W, H, FPS = 1080, 1920, 30
XT = 500
A = 'lendemain/'
SCRATCH = '/tmp/claude-0/-home-claude/2200d18c-fb03-5130-b93c-65df657ebe08/scratchpad/lendemain/'
SOUV = '../entretien/e7'
END_CLIP = '../annonce/c7'

# (début, fin, clip, départ dans le clip, vitesse)
SHOTS = [
    (0.0, 3.6, 'l1', 0.0, 0.6),     # dimanche 7 h 03 : papa se réveille (ralenti : le clip pivote après 2,2 s)
    (3.6, 7.8, 'l2', 0.0, 1.0),     # indice 1 : la couronne… collée à la super-glue
    (7.8, 11.2, 'l3', 0.0, 1.0),    # indice 2 : le dragon dans la baignoire
    (11.2, 14.8, 'l4', 0.0, 1.0),   # indice 3 : le Grand Maître sur le toit
    (14.8, 18.4, 'l5', 0.0, 1.0),   # indice 4 : le chat a la carte bleue
    (18.4, 20.6, 'l6', 0.0, 1.0),   # les photos d'hier
    (20.6, 24.2, SOUV, 0.0, 1.0),   # 14 h : la quête, 12 chevaliers, zéro dégât
    (24.2, 25.8, 'l6', 2.4, 1.0),   # alors… qui a fait ça ?
    (25.8, 30.0, 'l7', 0.0, 1.0),   # 23 h : l'after des adultes
    (30.0, 34.6, END_CLIP, 0.0, 1.0),   # carte de fin
]
FIN0 = 30.0
END = 34.6
I1_S, I2_S, I3_S, I4_S, PHOTO_S, SOUV_S, QUI_S, AFTER_S = 3.6, 7.8, 11.2, 14.8, 18.4, 20.6, 24.2, 25.8   # débuts des plans
GLUE_T = 5.4           # « … collée à la super-glue. » (« Une couronne… » reste seul 1,65 s, la chute 2,4 s)
SNORE_T = 9.5          # bulle du dragon : « Encore 5 minutes… » (1,7 s)
ROYAUME_T = 13.0       # bulle du Grand Maître : « Je surveille le royaume. » (1,8 s)
THON_T = 16.5          # bulle du chat : « J'ai commandé 40 kg de thon. » (1,9 s)
ZERO_T = 21.7          # « 12 chevaliers. Zéro dégât. »
DJ_T = 27.9            # bulle du dragon DJ : « Chut ! Les enfants dorment ! » (2,1 s ; le bandeau 23 H reste 2,1 s)
IMPACTS = [GLUE_T, QUI_S, AFTER_S]
BASEZ = {}             # recadrages éventuels : clip -> (zoom, cx, cy)
# Image descendue de n px pour libérer le haut (textes) sans cacher les visages : le haut est complété
# par un miroir (carrelage, papier peint) ou en étirant la première ligne (ciel).
OFFY = {'l3': ('miroir', 200), 'l4': ('ciel', 300), 'l5': ('miroir', 150)}
PUNCH = [(GLUE_T, 1.06), (SNORE_T, 1.03), (ROYAUME_T, 1.03), (THON_T, 1.05), (QUI_S, 1.05), (AFTER_S, 1.05), (DJ_T, 1.03)]

# Positions des textes par plan (réglées sur les images d'aperçu)
LAY = {
    'h1': 290, 'h2': 470, 'h3': 650,
    'tag': 280, 'nar': 420,
    'glue': (XT, 1270),
    'snore': (235, 760, (150, 255)),
    'royaume': (245, 690, (195, 245)),
    'thon': (430, 470, (290, 400)),
    'photos': 300,
    'souv1': 300, 'souv2': 470,
    'qui': 340,
    'after': 330,
    'dj': (420, 330, (-150, 210)),
}

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

NAVY = (24, 30, 64)
def tag(txt, size=54):
    """Étiquette dorée « INDICE n/4 » : repère de la série, toujours au même endroit."""
    f = M.font(M.TITLE, size); w = int(f.getlength(txt)) + 70; h = int(size * 1.25) + 26
    im = Image.new('RGBA', (w + 16, h + 18), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 10, w + 8, h + 10], h // 2, fill=(0, 0, 0, 120))
    d.rounded_rectangle([2, 2, w, h], h // 2, fill=M.GOLD + (255,), outline=(0, 0, 0, 255), width=5)
    d.text((w / 2 + 1, h / 2 + size * 0.06), txt, font=f, fill=NAVY + (255,), anchor='mm')
    return im

def bubble(txt, tail, size=68, maxw=840):
    return M.bubble(txt, tail, size, maxw)

def build():
    G = M.GOLD
    E['h1'] = T_('DIMANCHE · 7 H 03', 92, G, maxw=900)
    E['h2'] = T_('Le lendemain\nde l\'anniversaire.', 76, M.WHITE, maxw=900)
    E['h3'] = T_('Papa ne se souvient\nde rien.', 72, [M.WHITE, G], maxw=900)
    for n in range(1, 5): E[f'tag{n}'] = tag(f'INDICE {n}/4')
    E['n1'] = T_('Une couronne…', 80, M.WHITE)
    E['glue'] = T_('… collée à la\nsuper-glue.', 92, [G, G])
    E['n2'] = T_('Un dragon\ndans la baignoire.', 74, [M.WHITE, M.WHITE])
    E['snore'] = bubble('Encore\n5 minutes…', LAY['snore'][2], 66)
    E['n3'] = T_('Le Grand Maître\nest sur le toit.', 74, M.WHITE)
    E['royaume'] = bubble('Je surveille\nle royaume.', LAY['royaume'][2], 66)
    E['n4'] = T_('Le chat a ta CB.', 80, M.WHITE)
    E['thon'] = bubble('J\'ai commandé\n40 kg de thon.', LAY['thon'][2], 72)
    E['photos'] = T_('Les photos d\'hier :', 84, G, maxw=900)
    E['souv1'] = T_('14 H · LA QUÊTE\nDANS LE VILLAGE', 74, [G, G], maxw=900)
    E['souv2'] = T_('12 chevaliers.\nZéro dégât.', 80, [M.WHITE, G])
    E['date'] = T_('07.11  14:02', 40, (255, 150, 40), font=M.BODY, stroke=0)
    E['qui'] = T_('Alors…\nqui a fait ça ?', 96, [M.WHITE, G])
    E['after'] = M.banner('23 H\nL\'AFTER DES ADULTES', 70)
    E['dj'] = bubble('Chut ! Les enfants\ndorment !', LAY['dj'][2], 68)
    E['q'] = T_('Chez toi, le lendemain\nd\'anniversaire :', 70, M.WHITE, maxw=920)
    E['opts'] = T_('1 ça va\n2 champ de bataille\n3 un dragon dans\nla baignoire', 66, [G, G, G, G], maxw=900)
    E['cta'] = M.banner('LA QUÊTE EST OUVERTE\nLIEN EN BIO', 60)
    E['url'] = T_('maquetelegendaire.fr', 56, stroke=10)

SPE = M.Sparkles(40, (40, 220, 1000, 1400), 11, size=(7, 18))
SPG = M.Sparkles(60, (60, 300, 1000, 1500), 23, size=(8, 22))

def PB(im, key, bx, by, sc=1.0):
    """Pose une bulle pour que le centre de son cadre (pas de sa queue) tombe en (bx, by)."""
    b, (cx, cy) = E[key]
    M.paste(im, b, bx + (b.width / 2 - cx) * sc, by + (b.height / 2 - cy) * sc, sc)

def shade(im, y0, y1, a=120):
    g = Image.new('L', (1, y1 - y0))
    for y in range(y1 - y0): g.putpixel((0, y), int(a * (1 - y / (y1 - y0)) ** 1.4))
    layer = Image.new('RGBA', (W, y1 - y0), (10, 12, 30, 0)); layer.putalpha(g.resize((W, y1 - y0)))
    im.alpha_composite(layer, (0, y0))

def zoom(im, z, cy=0.5, cx=0.5):
    if z <= 1.001: return im
    w, h = int(W / z), int(H / z); x0 = int((W - w) * cx); y0 = int((H - h) * cy)
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

def polaroid(im, lt):
    """La quête d'hier vue comme une photo du téléphone : photo bordée de blanc, inclinée, fond flouté."""
    bg = im.convert('RGB').resize((W // 6, H // 6)).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
    bg = ImageEnhance.Brightness(bg).enhance(.5).convert('RGBA')
    s = .76 + .02 * min(1, lt / 3.6)
    pw, ph = int(W * s), int(H * s)
    ph_ = Image.new('RGBA', (pw + 36, ph + 36), (250, 248, 240, 255))
    ph_.paste(im.resize((pw, ph), Image.BICUBIC), (18, 18))
    d = E['date']; ph_.alpha_composite(d, (pw - d.width - 10, ph - d.height - 6))
    rot = ph_.rotate(-2.5, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', rot.size, (0, 0, 0, 0)); sh.putalpha(rot.getchannel('A').point(lambda v: v * .5))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    x, y = (W - rot.width) // 2, 1010 - rot.height // 2
    bg.alpha_composite(sh, (x + 10, y + 18)); bg.alpha_composite(rot, (x, y))
    return bg

def lower(im, c):
    """Descend l'image du plan c (OFFY) et complète le haut."""
    if c not in OFFY: return im
    how, n = OFFY[c]
    out = Image.new('RGBA', (W, H)); out.paste(im.crop((0, 0, W, H - n)), (0, n))
    if how == 'miroir': top = im.crop((0, 0, W, n)).transpose(Image.FLIP_TOP_BOTTOM)
    else: top = im.crop((0, 0, W, 6)).resize((W, n), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    out.paste(top, (0, 0))
    return out

def indice(im, t, a, n, key, until=99):
    P = M.paste; pop = M.pop
    P(im, E[f'tag{n}'], XT, LAY['tag'], pop(t, a, .14))
    if t < until: P(im, E[key], XT, LAY['nar'], pop(t, a + .15, .16))

def frame(t):
    for (a, b, c, off, sp) in SHOTS:
        if a <= t < b: break
    lt = t - a
    im = clip_at(c, off + lt * sp)
    if c == SOUV: im = polaroid(im, lt)
    im = lower(im, c)
    bz, bcx, bcy = BASEZ.get(c, (1.0, .5, .5))
    im = zoom(im, bz * punch(t), bcy, bcx)
    P = M.paste; pop = M.pop
    if a < FIN0: shade(im, 0, 760, 125)
    if a == 0.0:
        P(im, E['h1'], XT, LAY['h1'], pop(t, 0.0, .14))
        P(im, E['h2'], XT, LAY['h2'], pop(t, 0.45, .18))
        P(im, E['h3'], XT, LAY['h3'], pop(t, 1.5, .16))
    elif c == 'l2':
        indice(im, t, a, 1, 'n1')
        if t >= GLUE_T: P(im, E['glue'], *LAY['glue'], pop(t, GLUE_T, .14))
    elif c == 'l3':
        indice(im, t, a, 2, 'n2')
        PB(im, 'snore', *LAY['snore'][:2], pop(t, SNORE_T, .14))
    elif c == 'l4':
        indice(im, t, a, 3, 'n3')
        PB(im, 'royaume', *LAY['royaume'][:2], pop(t, ROYAUME_T, .14))
    elif c == 'l5':
        indice(im, t, a, 4, 'n4', THON_T)
        PB(im, 'thon', *LAY['thon'][:2], pop(t, THON_T, .14))
    elif c == 'l6' and a == PHOTO_S:
        P(im, E['photos'], XT, LAY['photos'], pop(t, a + .1, .14))
    elif c == SOUV:
        P(im, E['souv1'], XT, LAY['souv1'], pop(t, a + .1, .16))
        P(im, E['souv2'], XT, LAY['souv2'], pop(t, ZERO_T, .16))
    elif c == 'l6':
        P(im, E['qui'], XT, LAY['qui'], pop(t, a + .05, .14))
    elif c == 'l7':
        SPG.draw(im, t - AFTER_S, .6)
        if t < DJ_T: P(im, E['after'], XT, LAY['after'], pop(t, AFTER_S, .16) * (1 + .03 * math.exp(-((t - AFTER_S) % .5) * 10)))
        else: PB(im, 'dj', *LAY['dj'][:2], pop(t, DJ_T, .14))
    else:
        SPE.draw(im, lt, .7)
        P(im, E['q'], XT, 330, pop(lt, 0.0, .18))
        P(im, E['opts'], XT, 590, pop(lt, .3, .18))
        P(im, E['cta'], XT, 895, pop(lt, .9) * (1 + .03 * math.exp(-(lt % .6) * 10)))
        P(im, E['url'], XT, 1040, pop(lt, 1.3))
    if lt < .07 and a > 0:
        I.flash(im, (255, 240, 200), .32 * (1 - lt / .07))
    for t0, col in [(AFTER_S, (255, 120, 220)), (GLUE_T, (255, 240, 180))]:
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
    out = args[0] if args else 'lendemain.mp4'
    tmp = out[:-4] + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son18.wav',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, out); print('ok', out)

if __name__ == '__main__':
    main()
