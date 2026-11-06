"""« L'inauguration » (25 s, Instagram) : le dragon maire, trois tentatives.
Usage : python3 inaug2.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess, random
from PIL import Image, ImageDraw, ImageFilter
import montage as M
import fete as F
import court as C

def big(p): return Image.open(p).convert('RGB').resize((M.SW, M.SH), Image.LANCZOS)
SRC = {1: big('ia/j1.jpg'), 2: big('ia/j1.jpg'), 3: big('ia/i3.jpg'), 4: big('ia/i3.jpg'), 5: big('ia/i5.jpg')}
CLIPS = {1: 'ia/n1.mp4', 2: 'ia/n2.mp4', 3: 'ia/n3.mp4', 4: 'ia/n4.mp4', 5: 'ia/n5.mp4'}
W, H, FPS = M.W, M.H, M.FPS
CX, CY = M.SW / 2, M.SH / 2
# (début, fin, scène, (zoom, cx, cy) début, fin, décalage dans le clip)
SHOTS = [
    (0.0, 7.8, 1, (1.00, CX, CY), (1.10, CX, CY - 60), 0.0),
    (7.8, 12.0, 2, (1.06, CX, CY - 40), (1.00, CX, CY), 0.7),
    (12.0, 14.8, 3, (1.04, CX, CY), (1.16, CX - 60, CY - 30), 0.0),
    (14.8, 18.3, 4, (1.10, CX, CY - 30), (1.04, CX, CY), 0.4),
    (18.3, 21.9, 5, (1.02, CX, CY), (1.10, CX + 40, CY - 40), 0.2),
]
END = 25.1
SNEEZE_T = 9.55       # instant du « TCHOUM » (aligné sur le jet de feu du clip 2)
HIC_T = 16.15         # instant du hoquet (aligné sur la petite flamme du clip 4)
CUT_T = 19.6          # le Grand Maître coupe le ruban
NOTICE_T = 22.6
NY = 1330
SUBS = [(0.15, 2.55, 'Mesdames, messieurs…'), (2.55, 4.45, 'demain, la quête ouvre !'),
        (4.45, 5.6, 'Je déclare…'), (5.6, 7.0, "l'inauguration…")]
OUV_T = 7.0

def burst(txt, w=900, h=540, size=140):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = random.Random(3); pts = []; n = 24
    for i in range(n * 2):
        a = math.pi * i / n; rad = (1.0 if i % 2 == 0 else .72) * r.uniform(.9, 1.05)
        pts.append((w / 2 + math.cos(a) * w * .48 * rad, h / 2 + math.sin(a) * h * .48 * rad))
    d.polygon([(x + 10, y + 12) for x, y in pts], fill=(0, 0, 0, 120))
    d.polygon(pts, fill=(200, 30, 40, 255))
    d.polygon([(w / 2 + (x - w / 2) * .82, h / 2 + (y - h / 2) * .82) for x, y in pts], fill=(255, 205, 70, 255))
    t = M.text_img(txt, M.TITLE, size, fill=(200, 30, 40), stroke=14, maxw=w - 120)
    im.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2 - 8))
    return im

E = {}
def build():
    T, B_ = M.TITLE, M.BODY
    E['subs'] = [(a, b, M.text_img(s, T, 82, fill=M.WHITE, stroke=12, maxw=860)) for a, b, s in SUBS]
    E['ouv'] = burst('OUVERTE !', 900, 500, 150)
    E['n1'] = F.stamp('TENTATIVE N° 1', 70)
    E['n2'] = F.stamp('TENTATIVE N° 2', 70)
    E['n3'] = F.stamp('TENTATIVE N° 3', 70)
    E['atch'] = burst('ATCHOUM !', 700, 420, 110)
    E['hic'] = burst('HIC !', 520, 360, 120)
    E['echec'] = F.stamp('ÉCHEC', 130)
    E['bougepas'] = M.text_img("Le Grand Maître\nn'a pas bougé.", B_, 70, stroke=10, maxw=900)
    E['inaug'] = M.bubble('Inauguré.', (180, 150), 72, 520)
    E['ok'] = M.text_img('Inauguration : réussie.', T, 84, fill=M.GOLD, stroke=11, maxw=1000)
    E['barbe'] = M.text_img('Barbe : à refaire.', B_, 80, stroke=10, maxw=1000)
    E['p1'] = M.banner('OUVERTURE\nLE 7 NOVEMBRE', 84)
    E['p2'] = M.text_img('Une chasse au trésor de chevalier\npour les 7-10 ans, dans ta ville.', B_, 62, stroke=9, maxw=1000)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 76)
    E['url'] = M.text_img('maquetelegendaire.fr', T, 72, stroke=10)
    bg = SRC[5].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

def clip_src(k, lt, off):
    M.CLIPS[600 + k] = (CLIPS[k], off)
    return M.clip_src(600 + k, lt)

def flash(im, col, a):
    if a > 0: im.alpha_composite(Image.new('RGBA', (W, H), col + (int(255 * min(1, a)),)))

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1], t)
    for (a, b, k, p0, p1, off) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.05 * math.exp(-lt * 10)
    for t0, amp in ((OUV_T, 14), (SNEEZE_T, 26), (HIC_T, 12), (CUT_T, 8)):
        if t0 <= t < t0 + .5:
            s = amp * math.exp(-(t - t0) * 7); cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    if k == 1 and t >= OUV_T: z *= 1 + 0.08 * math.exp(-(t - OUV_T) * 8)
    src = clip_src(k, lt, off)
    im, v = M.shoot(src, z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        for (s0, s1, el) in E['subs']:
            if s0 <= t < s1: P(im, el, W / 2, 1360, pop(t, s0, .12))
        if t >= OUV_T: P(im, E['ouv'], W / 2, 1300, pop(t, OUV_T, .16))
    elif k == 2:
        F.stamp_at(im, E['n1'], t, a + 0.1, W / 2, 290, .9)
        if SNEEZE_T <= t < 11.15: P(im, E['atch'], 380, 560, pop(t, SNEEZE_T, .14) * (1 + .05 * math.sin(t * 30)))
        flash(im, (255, 170, 60), .55 * math.exp(-(t - SNEEZE_T) * 6) if t >= SNEEZE_T else 0)
        F.stamp_at(im, E['echec'], t, 11.2, W / 2, 1300, .9)
    elif k == 3:
        F.stamp_at(im, E['n2'], t, a + 0.1, W / 2, 290, .9)
    elif k == 4:
        F.stamp_at(im, E['n2'], t, a - 5, W / 2, 290, .9)
        if t >= HIC_T: P(im, E['hic'], 330, 640, pop(t, HIC_T, .12))
        if t >= HIC_T + 1.0: P(im, E['bougepas'], W / 2, 1350, pop(t, HIC_T + 1.0))
    elif k == 5:
        F.stamp_at(im, E['n3'], t, a + 0.1, W / 2, 290, .9)
        if t >= CUT_T - .1: b_, _ = E['inaug']; P(im, b_, 760, 500, pop(t, CUT_T - .1))
        if t >= CUT_T + .7: P(im, E['ok'], W / 2, 1330, pop(t, CUT_T + .7, .18))
        if t >= CUT_T + 1.2: P(im, E['barbe'], W / 2, 1440, pop(t, CUT_T + 1.2))
    if lt < 0.07 and k != 1:
        flash(im, (255, 240, 200), .35 * (1 - lt / 0.07))
    if t > SHOTS[-1][1] - 0.2:
        flash(im, (12, 16, 40), .78 * (t - (SHOTS[-1][1] - 0.2)) / 0.2)
    return im

def end_card(lt, t):
    im = E['endbg'].copy(); C.SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], W / 2, 330, pop(lt, 0.0, .18))
    P(im, E['p2'], W / 2, 540, pop(lt, 0.3))
    P(im, E['cta'], W / 2, 760, pop(lt, 0.6) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], W / 2, 950, pop(lt, 0.9))
    C.draw_notice(im, t, NOTICE_T, W / 2, NY)
    return im

def main():
    M.build(); C.build(); build()
    n = C.notice_base('AVIS DU ROYAUME', 'Envoie-la au parent qui a', 'un anniversaire à préparer.', '(Extincteur fourni.)')
    C.E['notice'] = n.resize((int(n.width * .8), int(n.height * .8)), Image.LANCZOS)
    # chaque clip est étiré ou resserré pour remplir exactement son plan
    for (a, b, k, p0, p1, off) in SHOTS:
        M.CLIPS[600 + k] = (CLIPS[k], off); nfr = len(M.clip_frames(600 + k))
        M.CLIP_RATE[600 + k] = RATE.get(k) or (nfr - 1) / (b - a + off)
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'/tmp/claude-0/-home-claude/2ee4b4d0-d95a-5544-aef9-689c530b467a/scratchpad/i2_{ts}.jpg', quality=85)
        return
    out = args[0] if args else 'inauguration.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son11.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

RATE = {2: 30, 3: 30, 4: 30, 5: 30}   # vitesse imposée (images du clip par seconde) si besoin
if __name__ == '__main__':
    main()
