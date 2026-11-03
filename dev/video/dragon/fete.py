"""Montage « Opération fête parfaite » (série Le dragon pas payé).
Réutilise les outils de montage.py (bulles, textes, tampons, caméra, écran du téléphone).
Usage : python3 fete.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess
from PIL import Image, ImageFilter
import montage as M

A = '/mnt/user-data/attachments/2ee4b4d0-d95a-5544-aef9-689c530b467a/'
FILES = {1: 'dd9f27d4-image.png', 2: 'b2f31035-image.png', 3: 'd0a86201-image.png', 4: 'ba56aeb7-image.png',
         5: 'f7505acd-image.png', 7: 'c9b80f1e-image.png', 8: '93508271-image.png', 9: 'e90d9b33-image.png'}
SRC = {k: Image.open(A + f).convert('RGB') for k, f in FILES.items()}
SRC[6] = M.SRC[6]                       # le téléphone de la vidéo précédente
W, H, FPS = M.W, M.H, M.FPS
CLIPS = {}                              # plans animés (Hugging Face), ajoutés quand ils existent : {k: (fichier, décalage)}
import os
for k in (1, 2, 3, 4, 5, 7, 8, 9):
    p = f'ia/f{k}.mp4'
    if os.path.exists(p): CLIPS[k] = (p, 0.1)

def clip_src(k, lt):
    M.CLIPS[100 + k] = CLIPS[k]
    return M.clip_src(100 + k, lt)

# (début, fin, image, (z0, cx0, cy0), (z1, cx1, cy1))
SHOTS = [
    (0.0, 2.4, 1, (1.04, 470, 836), (1.14, 450, 760)),
    (2.4, 4.8, 2, (1.04, 470, 836), (1.16, 560, 760)),
    (4.8, 7.2, 3, (1.04, 470, 836), (1.14, 470, 900)),
    (7.2, 9.6, 4, (1.04, 470, 836), (1.16, 470, 860)),
    (9.6, 12.0, 5, (1.14, 470, 780), (1.04, 470, 836)),
    (12.0, 14.4, 6, (1.05, 470, 760), (1.18, 470, 730)),
    (14.4, 16.8, 7, (1.02, 470, 836), (1.20, 470, 820)),
    (16.8, 19.2, 8, (1.04, 470, 836), (1.16, 430, 760)),
    (19.2, 21.6, 9, (1.04, 470, 836), (1.14, 470, 760)),
]
END = 26.0
STAMP_T = {2: 3.6, 3: 6.0, 4: 8.4, 9: 20.4}     # tampons, sur les « pouf » de la musique

from PIL import ImageDraw
def stamp(txt, size=120, col=(196, 18, 30)):
    """Tampon lisible : fond crème presque opaque, cadre et lettres rouges pleines, légèrement penché."""
    f = M.font(M.TITLE, size); w = int(f.getlength(txt)) + 90; h = int(size * 1.25) + 50
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w - 4, h - 4], 22, fill=(255, 246, 225, 235), outline=col + (255,), width=12)
    d.rounded_rectangle([22, 22, w - 22, h - 22], 14, outline=col + (255,), width=4)
    d.text((w / 2, h / 2 + size * 0.08), txt, font=f, fill=col + (255,), anchor='mm')
    sh = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); sh.paste((0, 0, 0, 110), (10, 14, w + 6, h + 10))
    sh = sh.filter(ImageFilter.GaussianBlur(8)); sh.alpha_composite(im, (6, 4))
    return sh.rotate(-10, expand=True, resample=Image.BICUBIC)

E = {}
def build():
    T, B_, S = M.TITLE, M.BODY, M.SEMI
    E['titre'] = M.text_img('OPÉRATION\nFÊTE PARFAITE', T, 96, fill=[M.WHITE, M.GOLD], stroke=11, maxw=960)
    E['b1'] = M.bubble("Cette année, je\nm'occupe de TOUT.", (-170, 150), 64, 700)
    E['e1'] = M.text_img('Étape 1 : les ballons.', B_, 82, stroke=10, maxw=960)
    E['e2'] = M.text_img('Étape 2 : la déco.', B_, 82, stroke=10, maxw=960)
    E['e3'] = M.text_img('Étape 3 : les bougies.', B_, 82, stroke=10, maxw=960)
    E['b4'] = M.bubble('Il était moelleux…\navant.', (-30, -170), 64, 700)
    E['echec'] = stamp('ÉCHEC', 130)
    E['echec2'] = stamp('ÉCHEC TOTAL', 104)
    E['alerte'] = M.banner('ALERTE :\nFÊTE EN PÉRIL !', 82)
    E['b5'] = M.bubble('Pose ce briquet.', (-230, 120), 68, 600)
    E['prep'] = M.text_img('Préparation : 2 minutes.', B_, 78, stroke=10, maxw=960)
    E['cuisine'] = M.text_img('Dragon : interdit de cuisine.', B_, 70, fill=M.GOLD, stroke=9, maxw=960)
    E['ballons'] = M.text_img('Ballons : 0.', T, 92, stroke=11)
    E['aventure'] = M.text_img('Aventure : 100 %.', T, 92, fill=M.GOLD, stroke=11)
    E['enigme'] = M.text_img('Énigme résolue !', T, 96, fill=M.GOLD, stroke=11)
    E['sauvee'] = M.text_img('Fête : sauvée.', B_, 84, stroke=10)
    E['b9'] = M.bubble('Je refais\nle gâteau ?', (110, 150), 66, 600)
    E['refuse'] = stamp('REFUSÉ', 130)
    E['p1'] = M.text_img('Une quête au prénom\nde ton enfant,', B_, 74, stroke=9, maxw=940)
    E['p2'] = M.text_img('prête en 2 minutes.', B_, 74, fill=M.GOLD, stroke=9, maxw=940)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 78)
    E['url'] = M.text_img('maquetelegendaire.fr', T, 76, stroke=10)
    E['chute'] = M.text_img('Extincteur non fourni.\nDragon : toujours pas payé.', S, 58, fill=(235, 225, 210), stroke=6, maxw=900)
    bg = SRC[9].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

SP8 = M.Sparkles(34, (180, 300, 640, 760), 18, rise=0.7, size=(8, 24))
SPE = M.Sparkles(40, (30, 160, 1050, 1750), 19, size=(6, 16))

def stamp_at(im, el, t, t0, x, y, base=1.0):
    if t < t0: return 0
    u = (t - t0) / 0.12
    M.paste(im, el, x, y, base * (1 + 1.4 * max(0, 1 - u)), alpha=min(1, u + 0.3))
    return math.exp(-(t - t0) * 9)   # intensité du tremblement

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1])
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.06 * math.exp(-lt * 10)                              # coup de zoom à chaque coupe
    z *= 1 + 0.022 * math.exp(-(t % 0.6) * 12)                      # pulsation sur chaque temps
    st = STAMP_T.get(k)
    if st and t >= st:                                                # secousse quand le tampon tombe
        s = 16 * math.exp(-(t - st) * 9); cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    if k == 5:
        s = 12 * math.exp(-lt * 3); cx += s * math.sin(lt * 61); cy += s * math.cos(lt * 47)
    if k == 7: cy += 6 * abs(math.sin(lt * 9))
    src = clip_src(k, lt) if k in CLIPS else SRC[k]
    if k == 6:
        src = src.copy(); ui = M.phone_ui(lt); src.paste(ui, (M.SCR[0], M.SCR[1]), ui)
    im, v = M.shoot(src, z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        P(im, E['titre'], W / 2, 270, pop(t, 0.0, .18))
        b, _ = E['b1']; P(im, b, 720, 560, pop(t, 0.9))
    elif k == 2:
        P(im, E['e1'], W / 2, 240, pop(t, a))
        stamp_at(im, E['echec'], t, 3.6, W / 2, 1300)
    elif k == 3:
        P(im, E['e2'], W / 2, 240, pop(t, a))
        stamp_at(im, E['echec'], t, 6.0, W / 2, 760, 1.0)
    elif k == 4:
        P(im, E['e3'], W / 2, 210, pop(t, a))
        b, _ = E['b4']; P(im, b, 560, 1040, pop(t, a + 0.3))
        stamp_at(im, E['echec2'], t, 8.4, W / 2, 1420, 0.95)
    elif k == 5:
        M.SP5.draw(im, lt, alpha=min(1, lt * 3) * .7)
        P(im, E['alerte'], W / 2, 1020, pop(t, a, .18), rot=-3)
        b, _ = E['b5']; P(im, b, 760, 230, pop(t, a + 0.6))
        fl = max(0, 1 - lt / 0.25)
        if fl > 0: im.alpha_composite(Image.new('RGBA', (W, H), (255, 245, 220, int(255 * fl))))
    elif k == 6:
        M.SP6.draw(im, lt, alpha=0.6 + (0.4 if lt > 1.8 else 0), burst=max(0, 1.2 - (lt - 1.8) * 2) if lt > 1.8 else 0)
        P(im, E['prep'], W / 2, 235, pop(t, a))
        P(im, E['cuisine'], W / 2, 1400, pop(t, a + 0.6))
    elif k == 7:
        P(im, E['ballons'], W / 2, 1290, pop(t, a, .18))
        P(im, E['aventure'], W / 2, 1420, pop(t, a + 0.6, .18))
    elif k == 8:
        gx, gy = M.to_screen(v, 335, 450)
        pul = 0.6 + 0.3 * math.sin(lt * 6)
        P(im, M.GLOW, gx, gy, 0.8 + 0.12 * math.sin(lt * 6), alpha=pul)
        SP8.draw(im, lt, alpha=min(1, lt * 2))
        P(im, E['enigme'], W / 2, 235, pop(t, a, .18))
        P(im, E['sauvee'], W / 2, 1430, pop(t, a + 0.6))
    elif k == 9:
        b, _ = E['b9']; P(im, b, 330, 300, pop(t, a))
        sx, sy = M.to_screen(v, 560, 930)
        stamp_at(im, E['refuse'], t, 20.4, sx, sy)
    if lt < 0.07 and k != 5:                                          # éclat doré à chaque coupe
        im.alpha_composite(Image.new('RGBA', (W, H), (255, 240, 200, int(90 * (1 - lt / 0.07)))))
    if t > SHOTS[-1][1] - 0.25:
        f = (t - (SHOTS[-1][1] - 0.25)) / 0.25
        im.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, int(200 * f))))
    return im

def end_card(lt):
    im = E['endbg'].copy(); SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], W / 2, 440, pop(lt, 0.0))
    P(im, E['p2'], W / 2, 600, pop(lt, 0.3))
    P(im, E['cta'], W / 2, 820, pop(lt, 0.6) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], W / 2, 1010, pop(lt, 1.2))
    P(im, E['chute'], W / 2, 1270, pop(lt, 1.8), alpha=min(1, max(0, (lt - 1.8) * 4)))
    return im

def main():
    M.build(); build()
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'fete_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'operation-fete-parfaite.mp4'
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son5.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(n):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
