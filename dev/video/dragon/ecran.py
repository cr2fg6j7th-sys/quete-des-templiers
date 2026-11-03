"""« Mission : décoller Léo de sa tablette » (21,6 s, série Le dragon pas payé).
Usage : python3 ecran.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess, os
from PIL import Image, ImageFilter
import montage as M
import fete as F
import court as C

A = '/mnt/user-data/attachments/2ee4b4d0-d95a-5544-aef9-689c530b467a/'
FILES = {1: '86cecf0e', 2: '99be4a0e', 3: '92ba79c3', 4: 'ccbff233', 5: '70ce3f7e', 6: '10dc5ee2'}
SRC = {k: Image.open(A + v + '-image.png').convert('RGB').resize((941, 1672)) for k, v in FILES.items()}
W, H, FPS = M.W, M.H, M.FPS
END = 21.6
CLIPS = {k: (f'ia/t{k}.mp4', 0.05) for k in FILES if os.path.exists(f'ia/t{k}.mp4')}
SPEED = {5: 0.52}                       # la course au ralenti pour tenir 4,8 s

SHOTS = [
    (0.0, 2.4, 1, (1.04, 470, 836), (1.20, 470, 760)),
    (2.4, 4.8, 2, (1.04, 470, 836), (1.14, 540, 860)),
    (4.8, 7.2, 3, (1.04, 470, 836), (1.14, 520, 880)),
    (7.2, 9.6, 4, (1.06, 470, 760), (1.0, 470, 836)),
    (9.6, 14.4, 5, (1.02, 470, 836), (1.22, 470, 760)),
    (14.4, 16.8, 6, (1.04, 470, 836), (1.22, 470, 760)),
]
STAMPS = {2: 3.6, 3: 6.0}
NOTICE_T = 15.0

E = {}
def build():
    T, B_, S = M.TITLE, M.BODY, M.SEMI
    E['t1a'] = M.text_img('MISSION IMPOSSIBLE :', T, 92, fill=M.GOLD, stroke=11, maxw=1000)
    E['t1b'] = M.text_img('décoller Léo\nde sa tablette.', B_, 84, stroke=10, maxw=1000)
    E['t2'] = M.text_img('Tentative n° 1 :\nle « pestacle ».', B_, 82, fill=[M.WHITE, M.GOLD], stroke=10, maxw=1000)
    E['t3'] = M.text_img('Tentative n° 2 :\ndevenir un jeu vidéo.', B_, 82, fill=[M.WHITE, M.GOLD], stroke=10, maxw=1000)
    E['echec'] = F.stamp('ÉCHEC', 130)
    E['echec2'] = F.stamp('ÉCHEC TOTAL', 104)
    E['b4'] = M.bubble('Et si l\'écran\nles emmenait\ndehors ?', (-270, -280), 64, 600)
    E['t5a'] = M.text_img('Écran : le guide.', T, 90, fill=M.GOLD, stroke=11)
    E['t5b'] = M.text_img('La rue : le terrain de jeu.', B_, 78, stroke=10, maxw=1000)
    E['t6a'] = M.text_img('Mission accomplie.', T, 92, fill=M.GOLD, stroke=11)
    E['t6b'] = M.text_img('Enfin… presque.', B_, 80, stroke=10)
    E['p1'] = M.text_img('Une quête dans les vraies\nrues de ta ville,', B_, 76, stroke=10, maxw=1000)
    E['p2'] = M.text_img('guidée par ton téléphone.', B_, 76, fill=M.GOLD, stroke=10, maxw=1000)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 80)
    E['url'] = M.text_img('maquetelegendaire.fr', T, 76, stroke=10)
    bg = SRC[6].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

def clip_src(k, lt):
    M.CLIPS[300 + k] = CLIPS[k]
    return M.clip_src(300 + k, lt * SPEED.get(k, 1.0))

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1], t)
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.06 * math.exp(-lt * 10) + 0.02 * math.exp(-(t % 0.6) * 12)
    st = STAMPS.get(k)
    if st and t >= st:
        s = 16 * math.exp(-(t - st) * 9); cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    src = clip_src(k, lt) if k in CLIPS else SRC[k]
    im, v = M.shoot(src, z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        P(im, E['t1a'], W / 2, 230, pop(t, 0.0, .18))
        P(im, E['t1b'], W / 2, 380, pop(t, 0.3))
    elif k == 2:
        P(im, E['t2'], W / 2, 250, pop(t, a))
        F.stamp_at(im, E['echec'], t, STAMPS[2], W / 2, 1400)
    elif k == 3:
        P(im, E['t3'], W / 2, 250, pop(t, a))
        F.stamp_at(im, E['echec2'], t, STAMPS[3], W / 2, 1420, .95)
    elif k == 4:
        if lt < .25: im.alpha_composite(Image.new('RGBA', (W, H), (255, 235, 180, int(200 * (1 - lt / .25)))))
        b, _ = E['b4']; P(im, b, 800, 680, pop(t, a + 0.35))
    elif k == 5:
        P(im, E['t5a'], W / 2, 220, pop(t, a, .18))
        P(im, E['t5b'], W / 2, 330, pop(t, a + 0.6))
    elif k == 6:
        P(im, E['t6a'], W / 2, 230, pop(t, a, .18))
        P(im, E['t6b'], W / 2, 345, pop(t, a + 0.6))
        C.draw_notice(im, t, NOTICE_T, W / 2, 1330)
    if lt < 0.07 and k not in (1, 4):
        im.alpha_composite(Image.new('RGBA', (W, H), (255, 240, 200, int(90 * (1 - lt / 0.07)))))
    if t > SHOTS[-1][1] - 0.2:
        f = (t - (SHOTS[-1][1] - 0.2)) / 0.2
        im.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, int(200 * f))))
        C.draw_notice(im, t, NOTICE_T, W / 2, 1330, slam=False)
    return im

def end_card(lt, t):
    im = E['endbg'].copy(); C.SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], W / 2, 400, pop(lt, 0.0))
    P(im, E['p2'], W / 2, 560, pop(lt, 0.4))
    P(im, E['cta'], W / 2, 790, pop(lt, 0.9) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], W / 2, 1000, pop(lt, 1.4))
    C.draw_notice(im, t, NOTICE_T, W / 2, 1330, slam=False)
    return im

def main():
    M.build(); C.build(); build()
    C.E['notice'] = C.notice_base('AVIS DU ROYAUME', 'Envoie-la au parent qui', "négocie le temps d'écran.", '(Pas au dragon, il est occupé.)')
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'ecran_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'decoller-de-la-tablette.mp4'
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son7.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(n):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
