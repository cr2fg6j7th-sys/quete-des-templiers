"""Montage « Rapport d'incident » à partir des 9 images fixes (animation 2D : zooms,
tremblements, étincelles, lueur, bulles BD, textes, écran final).
Usage : python3 montage.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

U = '/mnt/user-data/uploads/'
IMG = {
    1: 'Le_dragon_studieux_au_parchemin_vierge.png',
    2: 'Le_mai_tre_ennuye__et_le_dragon_ze_le_.png',
    3: '7BE61344-40EB-40E1-9026-36E9ED126DBD.png',
    4: 'AC69A1C3-FE3C-411B-BA7A-2F7525078722.png',
    5: '52C7C7C9-434D-4ADA-8B23-02B89AC59D4F.png',
    6: '2C2BFB56-7939-4141-950F-E3AA45067A2E.png',
    7: '3958388A-65EB-4E0C-A710-3E58D1B70438.png',
    8: '129B5815-92F7-48D4-A92C-17B993B6ADAC.png',
    9: 'BA2DC171-A6CC-4D34-A035-4A8C85409BB9.png',
}
W, H, FPS = 1080, 1920, 30
F = 'fonts/'
TITLE = F + 'luckiest-guy-latin-400-normal.ttf'
BODY = F + 'alegreya-sans-latin-900-normal.ttf'
SEMI = F + 'alegreya-sans-latin-800-normal.ttf'
GOLD = (255, 205, 70)
WHITE = (255, 255, 255)
RED = (200, 30, 40)
INK = (25, 22, 40)

def font(p, s): return ImageFont.truetype(p, s)

SRC = {k: Image.open(U + v).convert('RGB') for k, v in IMG.items()}
SW, SH = SRC[1].size  # 941 x 1672

# ---------- plans animés par Wan 2.2 (Hugging Face) ----------
import os
CLIPS = {1: ('ia/c1.mp4', 0.9), 2: ('ia/c2.mp4', 0.5), 3: ('ia/c3.mp4', 0.0), 4: ('ia/c4.mp4', 0.6), 5: ('ia/c5.mp4', 0.1)}
CLIP_FPS = 16
_CF = {}
def clip_frames(k):
    if k not in _CF:
        path, _ = CLIPS[k]
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        w, h = 480, 832
        n = len(raw) // (w * h * 3)
        _CF[k] = [Image.frombuffer('RGB', (w, h), raw[i * w * h * 3:(i + 1) * w * h * 3]) for i in range(n)]
    return _CF[k]
def clip_src(k, lt):
    fr = clip_frames(k); off = CLIPS[k][1]
    x = min(len(fr) - 1.001, max(0, (lt + off) * CLIP_FPS))
    i = int(x); a = x - i
    im = Image.blend(fr[i], fr[min(i + 1, len(fr) - 1)], a) if a > 0.05 else fr[i]
    im = im.resize((SW, SH), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, x): return a + (b - a) * x

# ---------- éléments graphiques ----------
def text_img(txt, path, size, fill=WHITE, stroke=9, maxw=900, lh=1.05, align='center'):
    f = font(path, size)
    lines = []
    for para in txt.split('\n'):
        cur = ''
        for w_ in para.split(' '):
            t = (cur + ' ' + w_).strip()
            if f.getlength(t) <= maxw or not cur: cur = t
            else: lines.append(cur); cur = w_
        lines.append(cur)
    # pas de mot isolé sur la dernière ligne
    if '\n' not in txt and len(lines) > 1 and ' ' not in lines[-1]:
        prev = lines[-2].split(' ')
        if len(prev) > 1: lines[-2] = ' '.join(prev[:-1]); lines[-1] = prev[-1] + ' ' + lines[-1]
    asc, desc = f.getmetrics(); lhpx = int((asc + desc) * lh)
    wmax = int(max(f.getlength(l) for l in lines)) + stroke * 2 + 8
    top = int(size * 0.28)
    im = Image.new('RGBA', (wmax, lhpx * len(lines) + stroke * 2 + 8 + top), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = f.getlength(l)
        x = (wmax - lw) / 2 if align == 'center' else stroke + 4
        col = fill[i] if isinstance(fill, list) else fill
        d.text((x, top + stroke + 4 + i * lhpx), l, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
    # ombre portée
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').point(lambda a: a * 0.55))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    out = Image.new('RGBA', (im.width + 10, im.height + 12), (0, 0, 0, 0))
    out.alpha_composite(sh, (8, 10)); out.alpha_composite(im, (0, 0))
    return out

def bubble(txt, tail, size=62, maxw=640, fill=(255, 252, 240)):
    """Bulle BD. tail = (dx, dy) : pointe de la queue, relative au centre bas de la bulle."""
    t = text_img(txt, BODY, size, fill=INK, stroke=0, maxw=maxw, lh=1.08)
    pad_x, pad_y = 46, 30
    bw, bh = t.width + pad_x * 2, t.height - int(size * 0.28) + pad_y * 2
    tx, ty = tail
    m = 12 + max(0, abs(tx) - bw // 2) + 0
    cw, ch = bw + 2 * m + 2 * abs(tx), bh + abs(ty) + 2 * m + 40
    im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox = (cw - bw) // 2; oy = m if ty > 0 else ch - bh - m
    box = [ox, oy, ox + bw, oy + bh]
    cx = ox + bw / 2; base_y = oy + bh if ty > 0 else oy
    tip = (cx + tx, base_y + ty)
    tri = [(cx - 34 + tx * 0.25, base_y - (8 if ty > 0 else -8)), (cx + 26 + tx * 0.25, base_y - (8 if ty > 0 else -8)), tip]
    for o, col in [(7, (0, 0, 0, 255)), (0, fill + (255,))]:
        d.rounded_rectangle([box[0] - o, box[1] - o, box[2] + o, box[3] + o], radius=46 + o, fill=col)
    d.polygon(tri, fill=(0, 0, 0, 255))
    # queue intérieure
    inner = [(tri[0][0] + 9, tri[0][1] - (2 if ty > 0 else -2)), (tri[1][0] - 9, tri[1][1] - (2 if ty > 0 else -2)),
             (tip[0] - (tip[0] - cx) * 0.12, tip[1] - (14 if ty > 0 else -14))]
    d.polygon(inner, fill=fill + (255,))
    d.rounded_rectangle(box, radius=46, fill=fill + (255,))
    im.alpha_composite(t, (int(ox + pad_x), int(oy + pad_y - 6 - size * 0.28)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').point(lambda a: a * 0.45))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    out = Image.new('RGBA', (cw + 12, ch + 14), (0, 0, 0, 0))
    out.alpha_composite(sh, (9, 11)); out.alpha_composite(im, (0, 0))
    return out, (int(ox + bw / 2), int(oy + bh / 2))

def banner(txt, size=78):
    t = text_img(txt, TITLE, size, fill=[WHITE, GOLD], stroke=0, maxw=880, lh=1.08)
    bw, bh = 1000, t.height + 40
    im = Image.new('RGBA', (bw + 20, bh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, bw + 10, bh + 10], 26, fill=(0, 0, 0, 255))
    d.rounded_rectangle([18, 18, bw + 2, bh + 2], 20, fill=RED + (255,))
    for x in range(-bh, bw, 70):  # bandes d'alerte discrètes
        d.polygon([(x + 18, bh + 2), (x + 48, bh + 2), (x + 48 + bh - 16, 18), (x + 18 + bh - 16, 18)], fill=(220, 50, 55, 255))
    d.rounded_rectangle([18, 18, bw + 2, bh + 2], 20, outline=GOLD + (255,), width=5)
    im.alpha_composite(t, ((im.width - t.width) // 2, (im.height - t.height) // 2 + 4))
    return im

def stamp(txt, size=120, col=(190, 20, 30)):
    f = font(TITLE, size); w = int(f.getlength(txt)) + 70; h = size + 60
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, w - 6, h - 6], 18, outline=col + (235,), width=10)
    d.text((35, 28), txt, font=f, fill=col + (235,))
    # texture d'encre irrégulière
    a = np.array(im); rng = np.random.default_rng(3)
    holes = rng.random(a.shape[:2]) < 0.08; a[..., 3][holes] = (a[..., 3][holes] * 0.3).astype(np.uint8)
    return Image.fromarray(a).rotate(-12, expand=True, resample=Image.BICUBIC)

# ---------- caméra ----------
def view(k, z, cx, cy):
    vw, vh = SW / z, SH / z
    x0 = min(max(cx - vw / 2, 0), SW - vw); y0 = min(max(cy - vh / 2, 0), SH - vh)
    return x0, y0, vw, vh

def shoot(img, z, cx, cy):
    x0, y0, vw, vh = view(None, z, cx, cy)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + vw, y0 + vh)).convert('RGBA'), (x0, y0, vw, vh)

def to_screen(v, px, py):
    x0, y0, vw, vh = v
    return (px - x0) * W / vw, (py - y0) * H / vh

# ---------- effets ----------
def star(d, x, y, r, a, col=(255, 225, 120)):
    if r < 1: return
    c = col + (int(255 * a),)
    d.polygon([(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22),
               (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)], fill=c)
    d.ellipse([x - r * .25, y - r * .25, x + r * .25, y + r * .25], fill=(255, 255, 240, int(255 * a)))

class Sparkles:
    def __init__(s, n, box, seed, rise=0.0, size=(10, 26)):
        r = random.Random(seed)
        s.p = [(r.uniform(box[0], box[2]), r.uniform(box[1], box[3]), r.uniform(0, 6.28),
                r.uniform(1.5, 3.5), r.uniform(*size), r.uniform(.5, 1.5)) for _ in range(n)]
        s.rise = rise
    def draw(s, im, t, alpha=1.0, burst=0.0):
        d = ImageDraw.Draw(im)
        for x, y, ph, sp, sz, rs in s.p:
            a = (0.5 + 0.5 * math.sin(ph + t * sp * 2)) * alpha
            yy = y - s.rise * rs * t * 60
            star(d, x, yy, sz * (0.6 + 0.6 * a) * (1 + burst), a)

def glow(size, col=(255, 210, 90)):
    g = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    a = np.zeros((size, size)); yy, xx = np.mgrid[:size, :size]
    r = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2
    arr = np.zeros((size, size, 4), np.uint8); arr[..., :3] = col; arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr)
GLOW = glow(520)

def pop(t, t0, dur=0.22):
    """Échelle d'apparition : 0 -> 1,12 -> 1."""
    x = (t - t0) / dur
    if x <= 0: return 0
    if x >= 1: return 1
    return 1.12 * math.sin(x * math.pi / 2) if x < .7 else lerp(1.12, 1, (x - .7) / .3)

def paste(im, el, cx, cy, sc=1.0, alpha=1.0, rot=0):
    if sc <= 0.02 or alpha <= 0: return
    e = el
    if abs(sc - 1) > 1e-3: e = el.resize((max(1, int(el.width * sc)), max(1, int(el.height * sc))), Image.BICUBIC)
    if rot: e = e.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1: e = e.copy(); e.putalpha(e.getchannel('A').point(lambda a: int(a * alpha)))
    im.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))

# ---------- écran du téléphone (P6) ----------
SCR = (306, 400, 632, 1058)
def phone_ui(t):
    w, h = SCR[2] - SCR[0], SCR[3] - SCR[1]
    k = 3; im = Image.new('RGBA', (w * k, h * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * k, h * k], 40 * k // 3, fill=(255, 248, 230, 255))
    d.rectangle([0, 0, w * k, 70 * k], fill=(22, 30, 64, 255))
    d.text((w * k / 2, 37 * k), 'Ma Quête Légendaire', font=font(SEMI, 22 * k), fill=GOLD, anchor='mm')
    d.text((w * k / 2, 112 * k), 'Le héros du jour', font=font(BODY, 30 * k), fill=INK, anchor='mm')
    def field(y, label, val, caret):
        d.text((26 * k, y * k), label, font=font(SEMI, 19 * k), fill=(110, 100, 90))
        d.rounded_rectangle([22 * k, (y + 28) * k, (w - 22) * k, (y + 84) * k], 12 * k, fill=WHITE, outline=(200, 185, 160), width=2 * k)
        d.text((38 * k, (y + 56) * k), val + ('|' if caret else ''), font=font(BODY, 30 * k), fill=INK, anchor='lm')
    name = 'Léo'[: max(0, min(3, int((t - 0.3) / 0.2)))]
    city = 'Obernai'[: max(0, min(7, int((t - 1.05) / 0.08)))]
    blink = int(t * 4) % 2 == 0
    field(170, 'Prénom', name, t < 1.0 and blink)
    field(290, 'Ville', city, 1.0 <= t < 1.9 and blink)
    pressed = t >= 1.8
    by = 470
    col = (150, 20, 30) if pressed else (200, 30, 40)
    s = 0.94 if 1.8 <= t < 1.95 else 1
    bx0, bx1 = 22 * k + (1 - s) * w * k / 2, (w - 22) * k - (1 - s) * w * k / 2
    d.rounded_rectangle([bx0, by * k, bx1, (by + 72) * k], 36 * k, fill=col)
    d.text((w * k / 2, (by + 36) * k), 'Lancer la quête', font=font(BODY, 30 * k), fill=WHITE, anchor='mm')
    d.text((w * k / 2, (by + 120) * k), 'Prête en 2 minutes', font=font(SEMI, 20 * k), fill=(120, 105, 90), anchor='mm')
    im = im.resize((w, h), Image.LANCZOS)
    if pressed:
        f = max(0, 1 - (t - 1.8) / 0.6)
        wht = Image.new('RGBA', (w, h), (255, 240, 190, int(200 * f)))
        mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], 40, fill=255)
        im.paste(Image.alpha_composite(im, wht), (0, 0), mask)
    return im

# ---------- les plans ----------
# (début, fin, image, (z0, cx0, cy0), (z1, cx1, cy1))
SHOTS = [
    (0.0, 2.4, 1, (1.08, 470, 820), (1.18, 480, 760)),
    (2.4, 4.8, 2, (1.02, 470, 840), (1.18, 600, 790)),
    (4.8, 7.2, 3, (1.00, 470, 836), (1.22, 480, 760)),
    (7.2, 9.6, 4, (1.15, 470, 700), (1.15, 470, 980)),
    (9.6, 12.0, 5, (1.18, 470, 720), (1.05, 470, 800)),
    (12.0, 14.4, 6, (1.05, 470, 760), (1.20, 470, 730)),
    (14.4, 16.8, 7, (1.00, 470, 836), (1.28, 470, 760)),
    (16.8, 19.2, 8, (1.05, 470, 836), (1.25, 560, 760)),
    (19.2, 21.6, 9, (1.04, 470, 836), (1.16, 470, 760)),
]
END = 26.0

E = {}  # éléments pré-rendus
def build():
    E['titre'] = text_img("RAPPORT D'INCIDENT N° 8", TITLE, 84, fill=GOLD, stroke=10, maxw=880)
    E['b1'] = bubble('14 h 31 :\npremier « on s\'ennuie ».', (60, -130), 60, 700)
    E['b2'] = bubble('Continue.', (340, 300), 70, 500)
    E['h32'] = text_img('14 h 32', TITLE, 66, fill=GOLD, stroke=9)
    E['blase'] = text_img('8 ANS. DÉJÀ BLASÉ.', TITLE, 92, stroke=11)
    E['bougies'] = text_img("Même les bougies s'ennuient.", BODY, 74, stroke=9, maxw=860)
    E['b4'] = bubble('14 h 40 :\ngâteau regardé…\nsans enthousiasme.', (-170, -150), 58, 640)
    E['page'] = text_img('Page 1 sur 47', TITLE, 64, fill=GOLD, stroke=9)
    E['alerte'] = banner('ALERTE :\nANNIVERSAIRE À SAUVER !', 74)
    E['b5'] = bubble("J'annule ma sieste.", (110, 110), 64, 520)
    E['prep'] = text_img('Héros : Léo. Mission : acceptée.', BODY, 68, stroke=9, maxw=860)
    E['lancee'] = text_img('QUÊTE LANCÉE.', TITLE, 104, fill=GOLD, stroke=12)
    E['ville'] = text_img('Dans les rues de ta ville.', BODY, 74, stroke=9, maxw=860)
    E['sourire'] = text_img('Sourire : retrouvé.', TITLE, 88, stroke=11)
    E['b9'] = bubble('Incident classé.', (-60, 120), 66, 520)
    E['solde'] = text_img('Salaire du dragon : 0 pièce.', BODY, 64, fill=GOLD, stroke=9, maxw=860)
    E['classe'] = stamp('CLASSÉ', 112)
    # écran final
    E['p1'] = text_img('Une vraie quête dans ta ville,', BODY, 70, stroke=9, maxw=900)
    E['p2'] = text_img('au prénom de ton enfant.', BODY, 70, fill=GOLD, stroke=9, maxw=900)
    E['cta'] = banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 78)
    E['url'] = text_img('maquetelegendaire.fr', TITLE, 76, stroke=10)
    E['chute'] = text_img('Doudou accepté.\nDragon : toujours pas payé.', SEMI, 56, fill=(235, 225, 210), stroke=6, maxw=880)
    end_bg = SRC[9].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    end_bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = end_bg

SP5 = Sparkles(70, (40, 160, 1040, 1500), 5, size=(10, 30))
SP6 = Sparkles(26, (250, 380, 830, 1300), 6, rise=0.6)
SP8 = Sparkles(30, (600, 900, 1000, 1400), 8, rise=1.0, size=(8, 22))
SPE = Sparkles(40, (30, 160, 1050, 1750), 9, size=(6, 16))

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1])
    for i, (a, b, k, p0, p1) in enumerate(SHOTS):
        if a <= t < b: break
    u = (t - a) / (b - a); e = ease(u) * 0.85 + u * 0.15
    z = lerp(p0[0], p1[0], e); cx = lerp(p0[1], p1[1], e); cy = lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.045 * math.exp(-lt * 9)
    z *= 1 + (0.03 if t >= 9.6 else 0.014) * math.exp(-(t % 0.6) * 12)   # pulsation sur chaque temps          # petit coup de zoom à chaque coupe
    src = clip_src(k, lt) if k in CLIPS else SRC[k]
    if k == 5:                                   # tremblement de la rupture
        amp = 14 * math.exp(-lt * 2.2)
        cx += amp * math.sin(lt * 61); cy += amp * math.cos(lt * 47)
    if k == 7:                                   # foulée
        cy += 6 * abs(math.sin(lt * 9))
    if k == 6:
        src = src.copy(); src.paste(phone_ui(lt), (SCR[0], SCR[1]), phone_ui(lt))
    im, v = shoot(src, z, cx, cy)
    # -------- effets et textes --------
    if k == 1:
        paste(im, E['titre'], W / 2, 250, pop(t, 0.0, .18), rot=0)
        b, _ = E['b1']; paste(im, b, 510, 1250, pop(t, 0.6))
    elif k == 2:
        b, _ = E['b2']; paste(im, b, 400, 440, pop(t, a + 0.6))
    elif k == 3:
        paste(im, E['h32'], W / 2, 215, pop(t, a + 0.0))
        paste(im, E['blase'], W / 2, 320, pop(t, a + 0.3))
        paste(im, E['bougies'], W / 2, 1360, pop(t, a + 1.2))
    elif k == 4:
        b, _ = E['b4']; bx, by = to_screen(v, 470, 560); paste(im, b, min(820, max(300, bx + 190)), by + 330, pop(t, a + 0.15))
        paste(im, E['page'], W / 2, 1420, pop(t, a + 1.2), rot=4)
    elif k == 5:
        SP5.draw(im, lt, alpha=min(1, lt * 3))
        paste(im, E['alerte'], W / 2, 1240, pop(t, a + 0.0, .18), rot=-3)
        b, _ = E['b5']; paste(im, b, 330, 260, pop(t, a + 0.6))
        fl = max(0, 1 - lt / 0.25)
        if fl > 0: im.alpha_composite(Image.new('RGBA', (W, H), (255, 245, 220, int(255 * fl))))
    elif k == 6:
        SP6.draw(im, lt, alpha=0.6 + (0.4 if lt > 1.8 else 0), burst=max(0, 1.2 - (lt - 1.8) * 2) if lt > 1.8 else 0)
        paste(im, E['prep'], W / 2, 235, pop(t, a + 0.1))
    elif k == 7:
        paste(im, E['lancee'], W / 2, 1270, pop(t, a + 0.0, .18))
        paste(im, E['ville'], W / 2, 1395, pop(t, a + 0.6))
    elif k == 8:
        gx, gy = to_screen(v, 715, 1120)
        pul = 0.55 + 0.35 * math.sin(lt * 5) + 0.3 * min(1, lt)
        paste(im, GLOW, gx, gy, 1.0 + 0.15 * math.sin(lt * 5), alpha=min(1, pul))
        SP8.draw(im, lt, alpha=min(1, lt * 1.5))
        paste(im, E['sourire'], W / 2, 1330, pop(t, a + 0.6))
    elif k == 9:
        b, _ = E['b9']; paste(im, b, 420, 230, pop(t, a + 0.0))
        paste(im, E['solde'], W / 2, 1460, pop(t, a + 0.6))
        if t >= 21.0:
            x = (t - 21.0) / 0.12
            sc = 1 + 1.6 * max(0, 1 - x)
            sx, sy = to_screen(v, 470, 1010)
            paste(im, E['classe'], sx, sy, sc * 1.25, alpha=min(1, x + 0.3))
    if t >= 9.6 and lt < 0.08 and k != 5:
        im.alpha_composite(Image.new('RGBA', (W, H), (255, 240, 200, int(110 * (1 - lt / 0.08)))))
    # fondu vers l'écran final
    if t > SHOTS[-1][1] - 0.25:
        f = (t - (SHOTS[-1][1] - 0.25)) / 0.25
        im.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, int(200 * f))))
    return im

def end_card(lt):
    im = E['endbg'].copy()
    SPE.draw(im, lt, 0.7)
    paste(im, E['p1'], W / 2, 470, pop(lt, 0.0))
    paste(im, E['p2'], W / 2, 570, pop(lt, 0.3))
    sc = pop(lt, 0.6) * (1 + 0.04 * math.exp(-((lt % 0.6)) * 10))
    paste(im, E['cta'], W / 2, 820, sc)
    paste(im, E['url'], W / 2, 1010, pop(lt, 1.2))
    paste(im, E['chute'], W / 2, 1270, pop(lt, 1.8), alpha=min(1, max(0, (lt - 1.8) * 4)))
    return im

def main():
    build()
    args = sys.argv[1:]
    if '--preview' in args:
        i = args.index('--preview')
        for ts in args[i + 1:]:
            frame(float(ts)).convert('RGB').save(f'apercu_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'rapport-incident.mp4'
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son4.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out],
                         stdin=subprocess.PIPE)
    for f_ in range(n):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
        if f_ % 90 == 0: print(f_, '/', n, flush=True)
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
