"""« Jour J, 6 h 02 » : vidéo courte de 7,2 s (série Le dragon pas payé).
Usage : python3 reveil.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess, os
from PIL import Image, ImageFilter
import montage as M
import fete as F
import court as C

SRC = {1: Image.open('ia/rA.jpg').convert('RGB').resize((941, 1672)),
       2: Image.open('ia/rB.jpg').convert('RGB').resize((941, 1672))}
W, H, FPS = M.W, M.H, M.FPS
END = 7.2
CLIPS = {k: (f'ia/w{k}.mp4', 0.1) for k in (1, 2) if os.path.exists(f'ia/w{k}.mp4')}
SHOTS = [
    (0.0, 2.4, 1, (1.02, 470, 836), (1.14, 520, 900)),
    (2.4, 4.8, 2, (1.12, 500, 1120), (1.22, 540, 1210)),
]
STAMP_T = 3.0
NOTICE_T = 3.6
NY = 1440

E = {}
def build():
    T, B_, S = M.TITLE, M.BODY, M.SEMI
    E['titre'] = M.text_img('JOUR J.\n6 h 02.', T, 120, fill=[M.WHITE, M.GOLD], stroke=13, maxw=1000)
    E['b1'] = M.bubble("C'EST MON\nANNIVERSAIRE !", (-150, 130), 70, 700)
    E['b2'] = M.bubble("Le café d'abord.\nLa quête ensuite.", (-80, 200), 62, 700)
    E['heure'] = F.stamp('6 H 03', 130)
    E['p1'] = M.text_img('Pour la fête,\nprends plutôt la quête :', B_, 72, stroke=10, maxw=1000)
    E['p2'] = M.text_img('prête en 2 minutes,\nmême à 6 h du matin.', B_, 76, fill=M.GOLD, stroke=10, maxw=1000)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 80)
    E['url'] = M.text_img('maquetelegendaire.fr', T, 78, stroke=10)
    bg = SRC[2].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

def clip_src(k, lt):
    M.CLIPS[400 + k] = CLIPS[k]
    return M.clip_src(400 + k, lt)

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1], t)
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.06 * math.exp(-lt * 10) + 0.02 * math.exp(-(t % 0.6) * 12)
    if k == 1:                                    # le lit rebondit avec les sauts
        cy += 9 * abs(math.sin(lt * 7.5)) * min(1, lt * 2)
    if k == 2 and t >= STAMP_T:
        s = 16 * math.exp(-(t - STAMP_T) * 9); cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    src = clip_src(k, lt) if k in CLIPS else SRC[k]
    im, v = M.shoot(src, z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        if lt < .3: im.alpha_composite(Image.new('RGBA', (W, H), (255, 245, 220, int(170 * (1 - lt / .3)))))
        P(im, E['titre'], W / 2, 1480, pop(t, 0.05, .18))
        b, _ = E['b1']; P(im, b, 790, 250, pop(t, 0.7))
    else:
        b, _ = E['b2']; P(im, b, 760, 420, pop(t, a + 0.15))
        F.stamp_at(im, E['heure'], t, STAMP_T, 250, 300, .85)
        C.draw_notice(im, t, NOTICE_T, W / 2, NY)
    if lt < 0.07 and k != 1:
        im.alpha_composite(Image.new('RGBA', (W, H), (255, 240, 200, int(90 * (1 - lt / 0.07)))))
    if t > SHOTS[-1][1] - 0.2:
        f = (t - (SHOTS[-1][1] - 0.2)) / 0.2
        im.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, int(200 * f))))
        C.draw_notice(im, t, NOTICE_T, W / 2, NY, slam=False)
    return im

def end_card(lt, t):
    im = E['endbg'].copy(); C.SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], W / 2, 330, pop(lt, 0.0))
    P(im, E['p2'], W / 2, 545, pop(lt, 0.3))
    P(im, E['cta'], W / 2, 790, pop(lt, 0.6) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], W / 2, 990, pop(lt, 0.9))
    C.draw_notice(im, t, NOTICE_T, W / 2, NY, slam=False)
    return im

def main():
    M.build(); C.build(); build()
    n = C.notice_base('AVIS DU ROYAUME', 'Envoie-la au parent', "réveillé à l'aube.", '(Le dragon dort encore.)')
    C.E['notice'] = n.resize((int(n.width * .88), int(n.height * .88)), Image.LANCZOS)
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'reveil_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'jour-j-6h02.mp4'
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son8.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(n):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
