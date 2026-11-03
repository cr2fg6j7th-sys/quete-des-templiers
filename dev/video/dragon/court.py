"""« Souffle les bougies » : vidéo courte de 7,2 s (série Le dragon pas payé).
Usage : python3 court.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess, os
from PIL import Image, ImageFilter
import montage as M
import fete as F

A = '/mnt/user-data/attachments/2ee4b4d0-d95a-5544-aef9-689c530b467a/'
SRC = {1: Image.open(A + 'b06818c3-image.png').convert('RGB'),
       2: Image.open(A + '971bdb8f-image.png').convert('RGB')}
W, H, FPS = M.W, M.H, M.FPS
END = 7.2
CLIPS = {k: (f'ia/s{k}.mp4', 0.1) for k in (1, 2) if os.path.exists(f'ia/s{k}.mp4')}

# (début, fin, image, (z0, cx0, cy0), (z1, cx1, cy1))
SHOTS = [
    (0.0, 2.4, 1, (1.04, 470, 836), (1.22, 470, 760)),   # on s'approche des joues gonflées
    (2.4, 4.8, 2, (1.22, 470, 800), (1.08, 470, 860)),   # on recule sur le désastre
]
STAMP_T = 3.0
SHARE_T = 3.5      # le bandeau de partage arrive et reste jusqu'à la fin
SHARE_Y = 1330

from PIL import ImageDraw
def share_pill(txt, size=56):
    """Bandeau de partage : pastille crème à bord doré, avion en papier dessiné, texte foncé."""
    t = M.text_img(txt, M.BODY, size, fill=M.INK, stroke=0, maxw=820, lh=1.05)
    ic = 100; pad = 36
    w = t.width + ic + pad * 3; h = max(t.height - int(size * .28), ic) + 44
    im = Image.new('RGBA', (w + 16, h + 18), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, w + 8, h + 8], h // 2, fill=(0, 0, 0, 120))
    d.rounded_rectangle([0, 0, w, h], h // 2, fill=(255, 250, 235, 255), outline=M.GOLD + (255,), width=6)
    cx, cy = pad + ic / 2, h / 2                                   # avion en papier rouge
    d.ellipse([cx - ic / 2, cy - ic / 2, cx + ic / 2, cy + ic / 2], fill=(200, 30, 40, 255))
    s = ic * .30
    d.polygon([(cx - s, cy - s * .15), (cx + s, cy - s * .75), (cx + s * .25, cy + s * .85)], fill=(255, 255, 255, 255))
    d.polygon([(cx - s * .1, cy + s * .05), (cx + s, cy - s * .75), (cx + s * .05, cy + s * .55)], fill=(225, 225, 235, 255))
    im.alpha_composite(t, (int(pad * 2 + ic), int((h - t.height) / 2 - size * .14)))
    return im

import random
def notice_base(title='AVIS DE SÉCURITÉ', l1='Envoie-la à celui qui', l2='gère les bougies.', l3='(Surtout pas au dragon.)'):
    """Avis officiel du royaume : parchemin aux bords irréguliers, sceau de cire, titre rouge."""
    w, h = 900, 330
    im = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = random.Random(4); pts = []
    for i in range(48):                                   # contour déchiré
        a = i / 48
        if a < .25: x, y = 15 + a / .25 * w, 15
        elif a < .5: x, y = 15 + w, 15 + (a - .25) / .25 * h
        elif a < .75: x, y = 15 + w - (a - .5) / .25 * w, 15 + h
        else: x, y = 15, 15 + h - (a - .75) / .25 * h
        pts.append((x + r.uniform(-6, 6), y + r.uniform(-6, 6)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(x + 8, y + 10) for x, y in pts], fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d.polygon(pts, fill=(246, 230, 196, 255), outline=(120, 80, 40, 255))
    d.line(pts + [pts[0]], fill=(120, 80, 40, 255), width=5)
    for i in range(160):                                   # grain du parchemin
        x, y = r.uniform(30, w), r.uniform(30, h)
        d.ellipse([x, y, x + 3, y + 3], fill=(200, 170, 120, 90))
    # sceau de cire rouge
    sx, sy = 105, 15 + h / 2
    d.ellipse([sx - 62, sy - 62, sx + 62, sy + 62], fill=(170, 20, 30, 255))
    d.ellipse([sx - 46, sy - 46, sx + 46, sy + 46], outline=(120, 10, 20, 255), width=5)
    d.text((sx, sy + 4), 'Q', font=M.font(M.TITLE, 64), fill=(120, 10, 20, 255), anchor='mm')
    tx = 190 + (w - 190) / 2 + 8
    d.text((tx, 78), title, font=M.font(M.TITLE, 58), fill=(185, 20, 30, 255), anchor='mm')
    d.line([(tx - 270, 118), (tx + 270, 118)], fill=(185, 20, 30, 200), width=4)
    d.text((tx, 172), l1, font=M.font(M.BODY, 58), fill=M.INK, anchor='mm')
    d.text((tx, 232), l2, font=M.font(M.BODY, 58), fill=M.INK, anchor='mm')
    d.text((tx, 296), l3, font=M.font(M.SEMI, 42), fill=(140, 60, 40), anchor='mm')
    return im.rotate(-2.5, expand=True, resample=Image.BICUBIC)

def flame_layer(t, burn):
    """Petite flamme qui danse sur le coin du parchemin, avec un peu de fumée. burn : 0 -> 1 (le coin noircit)."""
    L = Image.new('RGBA', (360, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    bx, by = 230, 330
    d.ellipse([bx - 70 * (.6 + burn), by - 50 * (.6 + burn), bx + 70 * (.6 + burn), by + 40 * (.6 + burn)], fill=(40, 25, 15, 200))
    for i, (col, sc) in enumerate([((255, 120, 20), 1.0), ((255, 190, 40), .7), ((255, 245, 180), .4)]):
        fl = 1 + .18 * math.sin(t * 23 + i) + .1 * math.sin(t * 37 + i * 2)
        hgt = 150 * sc * fl * (.7 + .5 * burn); wid = 60 * sc
        sway = 12 * math.sin(t * 9 + i)
        d.polygon([(bx - wid, by), (bx + wid, by), (bx + sway * .5 + wid * .2, by - hgt * .6), (bx + sway, by - hgt), (bx + sway * .5 - wid * .3, by - hgt * .55)], fill=col + (235,))
        d.ellipse([bx - wid, by - wid * .9, bx + wid, by + wid * .6], fill=col + (235,))
    for k in range(3):                                     # fumée
        ph = (t * .9 + k / 3) % 1
        x = bx + 20 * math.sin(t * 2 + k) - 10; y = by - 170 - ph * 200; rr = 18 + ph * 40
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(90, 90, 95, int(110 * (1 - ph))))
    return L.filter(ImageFilter.GaussianBlur(1.5))

def draw_notice(im, t, t0, x, y, slam=True):
    if t < t0: return
    lt = t - t0
    sc = (1 + 1.2 * max(0, 1 - lt / .12)) if slam else 1.0
    M.paste(im, E['notice'], x, y, sc, alpha=min(1, lt / .12 + .3) if slam else 1)
    if lt > .45:                                            # le coin prend feu
        burn = min(1, (lt - .45) / 2.5)
        M.paste(im, flame_layer(t, burn), x + 400, y + 60, 0.85)

# ---------- souffle de feu : jet de la bouche au gâteau, puis le gâteau s'embrase ----------
FIRE_T0, FIRE_HIT = 1.92, 2.06
MOUTH = (222 * 941 / 480, 390 * 1672 / 832)      # dans l'image source (941 x 1672)
CAKE = (265 * 941 / 480, 565 * 1672 / 832)
def fire_col(a):
    """a : 0 (coeur, blanc-jaune) -> 1 (bord, rouge sombre)."""
    stops = [(0, (255, 250, 210)), (.25, (255, 215, 80)), (.55, (255, 140, 30)), (.8, (230, 60, 20)), (1, (120, 20, 10))]
    for (a0, c0), (a1, c1) in zip(stops, stops[1:]):
        if a <= a1:
            u = (a - a0) / (a1 - a0); return tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3))
    return stops[-1][1]
def fire_layer(t, v):
    lt = t - FIRE_T0
    if lt < 0: return None
    mx, my = M.to_screen(v, *MOUTH); cx, cy = M.to_screen(v, *CAKE)
    reach = min(1, lt / (FIRE_HIT - FIRE_T0))
    rnd = random.Random(int(t * 30))
    outer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); do = ImageDraw.Draw(outer)
    inner = Image.new('RGBA', (W, H), (0, 0, 0, 0)); di = ImageDraw.Draw(inner)
    # jet : enveloppe orange-rouge large, coeur jaune-blanc étroit, avec turbulence
    for i in range(420):
        s = (i / 420 + t * 3.1) % 1 * reach
        wob = math.sin(s * 14 - t * 30) * 18 * s
        x = mx + (cx - mx) * s + wob + rnd.gauss(0, 12 + 95 * s)
        y = my + (cy - my) * s + rnd.gauss(0, 6 + 22 * s)
        r = 10 + 55 * s * rnd.uniform(.5, 1.2)
        do.ellipse([x - r, y - r, x + r, y + r], fill=fire_col(min(1, .3 + s * .35 + rnd.uniform(0, .15))) + (170,))
        if i % 2 == 0:
            xc = mx + (cx - mx) * s + wob * .5 + rnd.gauss(0, 4 + 30 * s); rc = 6 + 26 * s
            di.ellipse([xc - rc, y - rc, xc + rc, y + rc], fill=fire_col(min(1, s * .35 + rnd.uniform(0, .15))) + (230,))
    # le gâteau s'embrase
    if lt > FIRE_HIT - FIRE_T0:
        g = min(1, (lt - (FIRE_HIT - FIRE_T0)) / .18)
        half = 300 * (W / 1080) * (941 / v[2])
        base_y = cy + 35
        do.ellipse([cx - half * 1.05, base_y - 45, cx + half * 1.05, base_y + 45], fill=fire_col(.5) + (int(230 * g),))
        r2 = random.Random(7)
        for j in range(40):
            u = r2.uniform(-1, 1)
            bx = cx + u * half; by = base_y + r2.uniform(-25, 25) * (1 - abs(u))
            hgt = (180 + 330 * r2.random() * (.6 + .4 * math.sin(t * 17 + j * 2.3) ** 2)) * g * (1 - abs(u) * .55)
            wid = r2.uniform(28, 60)
            sway = 30 * math.sin(t * 10 + j * 1.3)
            for lay, k, dr in ((.7, 1.0, do), (.35, .62, do), (.08, .3, di)):
                pts = [(bx - wid * k, by)]
                for q in range(1, 6):
                    f = q / 6; w = wid * k * (1 - f) ** .8
                    pts.append((bx - w + sway * f ** 1.5, by - hgt * k * f))
                pts.append((bx + sway, by - hgt * k))
                for q in range(5, 0, -1):
                    f = q / 6; w = wid * k * (1 - f) ** .8
                    pts.append((bx + w + sway * f ** 1.5, by - hgt * k * f))
                pts.append((bx + wid * k, by))
                dr.polygon(pts, fill=fire_col(lay) + (235,))
    glow = outer.filter(ImageFilter.GaussianBlur(28))
    outer = outer.filter(ImageFilter.GaussianBlur(9))
    inner = inner.filter(ImageFilter.GaussianBlur(5))
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.alpha_composite(glow); out.alpha_composite(outer); out.alpha_composite(inner)
    return out

E = {}
def build():
    T, B_, S = M.TITLE, M.BODY, M.SEMI
    E['titre'] = M.text_img('Le dragon\na voulu aider.', T, 100, fill=[M.WHITE, M.GOLD], stroke=12, maxw=960)
    E['b1'] = M.bubble('Je m\'occupe\ndes bougies !', (-190, -110), 58, 700)
    E['b2'] = M.bubble('…Joyeux\nanniversaire ?', (-120, 160), 70, 700)
    E['echec'] = F.stamp('ÉCHEC', 140)
    E['p1'] = M.text_img('Pour la fête,\nprends plutôt la quête.', B_, 80, fill=[M.WHITE, M.GOLD], stroke=10, maxw=960)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 80)
    E['url'] = M.text_img('maquetelegendaire.fr', T, 78, stroke=10)
    E['notice'] = notice_base()
    bg = SRC[2].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

SPE = M.Sparkles(40, (30, 160, 1050, 1750), 29, size=(6, 16))
SMOKE = M.Sparkles(0, (0, 0, 1, 1), 1)

def clip_src(k, lt):
    M.CLIPS[200 + k] = CLIPS[k]
    return M.clip_src(200 + k, lt)

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1])
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.06 * math.exp(-lt * 10) + 0.02 * math.exp(-(t % 0.6) * 12)
    if k == 1 and lt > 1.5:                                   # il retient son souffle, puis crache le feu
        s = 4 * (lt - 1.5) + (14 if lt > FIRE_T0 else 0); cx += s * math.sin(t * 80); cy += s * math.cos(t * 67)
    if k == 2:                                                # secousse du POUF puis du tampon
        s = 26 * math.exp(-lt * 6) + (16 * math.exp(-(t - STAMP_T) * 9) if t >= STAMP_T else 0)
        cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    src = clip_src(k, lt) if k in CLIPS else SRC[k]
    im, v = M.shoot(src, z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        P(im, E['titre'], W / 2, 280, pop(t, 0.0, .18))
        b, _ = E['b1']; P(im, b, 880, 960, pop(t, 0.6))
        if lt > 1.6:                                          # les flammes rougeoient avant l'explosion
            im.alpha_composite(Image.new('RGBA', (W, H), (255, 120, 30, int(70 * (lt - 1.6) / 0.8))))
        fl = fire_layer(t, v)
        if fl is not None:                                    # souffle de feu
            im.alpha_composite(fl)
            im.alpha_composite(Image.new('RGBA', (W, H), (255, 140, 40, int(35 * min(1, (t - FIRE_T0) / .3)))))
            b, _ = E['b1']; P(im, b, 880, 960, 1.0)        # la bulle reste lisible au-dessus du feu
    else:
        if lt < 0.35:                                         # flash du souffle de feu
            f = 1 - lt / 0.35
            im.alpha_composite(Image.new('RGBA', (W, H), (255, 150 + int(90 * f), 60, int(255 * f))))
        b, _ = E['b2']; P(im, b, 760, 330, pop(t, a + 0.4))
        F.stamp_at(im, E['echec'], t, STAMP_T, 300, 1030, 0.85)
        draw_notice(im, t, SHARE_T, W / 2, SHARE_Y)
    if t > SHOTS[-1][1] - 0.2:
        f = (t - (SHOTS[-1][1] - 0.2)) / 0.2
        im.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, int(200 * f))))
        draw_notice(im, t, SHARE_T, W / 2, SHARE_Y, slam=False)
    return im

def end_card(lt):
    im = E['endbg'].copy(); SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], W / 2, 470, pop(lt, 0.0))
    P(im, E['cta'], W / 2, 790, pop(lt, 0.35) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], W / 2, 990, pop(lt, 0.7))
    draw_notice(im, lt + SHOTS[-1][1], SHARE_T, W / 2, SHARE_Y, slam=False)
    return im

def main():
    M.build(); build()
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'court_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'souffle-les-bougies.mp4'
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son6.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(n):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
