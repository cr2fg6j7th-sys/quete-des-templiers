"""TikTok « C'est ouvert ! » (7 novembre), sans aucune flamme ni fumée.
Zones TikTok à éviter : 150 px en haut, 400 px en bas, colonne de droite (x > 900).
Usage : python3 ouverture.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess
from PIL import Image, ImageFilter
import montage as M
import fete as F
import court as C
import inaug2 as I

W, H, FPS = M.W, M.H, M.FPS
CX, CY = M.SW / 2, M.SH / 2
XT = 470
CLIPS = {1: ('ia/m1.mp4', 0.0), 2: ('ia/o1.mp4', 0.0), 4: ('ia/f7.mp4', 0.0), 5: ('ia/f8.mp4', 0.0), 6: ('ia/n1.mp4', 3.0)}
RATE = {1: 30, 2: 30, 4: 16, 5: 14, 6: 30}
SHOTS = [
    (0.0, 2.8, 1, (1.00, CX, CY), (1.05, CX, CY + 20)),
    (2.8, 7.8, 2, (1.02, CX, CY), (1.08, CX, CY - 30)),
    (7.8, 10.6, 3, (1.02, CX, CY), (1.14, CX, CY - 60)),
    (10.6, 13.2, 4, (1.02, CX, CY), (1.10, CX, CY - 40)),
    (13.2, 16.1, 5, (1.02, CX, CY), (1.10, CX, CY - 30)),
    (16.1, 19.0, 6, (1.04, CX, CY), (1.10, CX, CY - 40)),
]
END = 22.4
CUT_T = 2.8 + 2.5        # le ruban est coupé (réglé sur le clip o1)
E = {}
T_ = None

def build():
    global T_
    def T_(s, size=86, fill=None, font=None, maxw=820, stroke=12):
        if isinstance(fill, list): fill = fill + [fill[-1]] * 8
        return M.text_img(s, font or M.TITLE, size, fill=fill or M.WHITE, stroke=stroke, maxw=maxw)
    G = M.GOLD
    E['h1'] = T_("C'EST OUVERT !", 120, G)
    E['h1b'] = T_('Ma petite entreprise\nouvre aujourd\'hui.', 72, font=M.BODY, stroke=10)
    E['g1'] = F.stamp('1 PAPA', 56); E['g2'] = F.stamp('1 DRAGON', 56); E['g3'] = F.stamp('1 GRAND MAÎTRE', 44)
    E['i1'] = T_('Inauguration\nofficielle.', 92, G)
    E['i2'] = T_('Le dragon voulait\ncouper le ruban.', 72, font=M.BODY, stroke=10)
    E['i3'] = T_('Le Grand Maître\na préféré s\'en charger.', 72, font=M.BODY, stroke=10)
    E['c1'] = T_('Tu tapes son prénom\net ta ville.', 76, maxw=900)
    E['c2'] = T_('Le Grand Maître\nl\'emmène en quête\ndans les rues\nde ta ville.', 72, maxw=900)
    E['c3'] = T_('Énigmes, défis,\nmot secret…\net il devient chevalier.', 76, [M.WHITE, M.WHITE, G])
    E['v4'] = M.banner('24,90 €\nPOUR TOUTE LA BANDE', 64)
    E['a1'] = T_("L'aperçu\nest gratuit.", 92, G)
    E['a2'] = T_('Le dragon, lui,\nattend toujours sa paie.', 72, font=M.BODY, stroke=10)
    E['p1'] = M.banner("C'EST OUVERT\nDEPUIS CE MATIN", 76)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 72)
    E['url'] = T_('maquetelegendaire.fr', 66, stroke=10)
    E['tag'] = T_('Anniversaire de chevalier · 7-10 ans', 56, font=M.BODY, stroke=9)
    bg = Image.open('ia/equipe.jpg').convert('RGB').resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

def src_for(k, lt):
    if k == 3:
        im = M.SRC[6].copy(); ui = M.phone_ui(min(2.4, lt * 1.2)); im.paste(ui, (M.SCR[0], M.SCR[1]), ui)
        return im
    return M.clip_src(800 + k, lt)

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1])
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.05 * math.exp(-lt * 10)
    if CUT_T <= t < CUT_T + .4: z *= 1 + 0.04 * math.exp(-(t - CUT_T) * 9)
    im, v = M.shoot(src_for(k, lt), z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        P(im, E['h1'], XT, 250, pop(t, 0.0, .18)); P(im, E['h1b'], XT, 420, pop(t, 0.4))
        F.stamp_at(im, E['g1'], t, 0.9, 250, 1020, .8)
        F.stamp_at(im, E['g3'], t, 1.3, 820, 560, .8)
        F.stamp_at(im, E['g2'], t, 1.7, 450, 1440, .8)
    elif k == 2:
        P(im, E['i1'], XT, 270, pop(t, a, .16))
        if t < CUT_T: P(im, E['i2'], XT, 1330, pop(t, a + .6))
        else: P(im, E['i3'], XT, 1330, pop(t, CUT_T))
    elif k == 3:
        P(im, E['c1'], XT, 330, pop(t, a, .14))
    elif k == 4:
        P(im, E['c2'], XT, 330, pop(t, a, .14))
    elif k == 5:
        P(im, E['c3'], XT, 360, pop(t, a, .14)); P(im, E['v4'], XT, 1330, pop(t, a + .9, .18))
    elif k == 6:
        P(im, E['a1'], XT, 340, pop(t, a, .16)); P(im, E['a2'], XT, 1310, pop(t, a + .7))
    if lt < 0.07 and k != 1:
        I.flash(im, (255, 240, 200), .35 * (1 - lt / 0.07))
    if t > SHOTS[-1][1] - 0.2:
        I.flash(im, (12, 16, 40), .78 * (t - (SHOTS[-1][1] - 0.2)) / 0.2)
    return im

def end_card(lt):
    im = E['endbg'].copy(); C.SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], XT, 330, pop(lt, 0.0, .18))
    P(im, E['tag'], XT, 520, pop(lt, 0.3))
    P(im, E['cta'], XT, 720, pop(lt, 0.6) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], XT, 920, pop(lt, 1.0))
    return im

def main():
    M.build(); C.build(); build()
    for k, c in CLIPS.items():
        M.CLIPS[800 + k] = c; M.CLIP_RATE[800 + k] = RATE[k]
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'/tmp/claude-0/-home-claude/2ee4b4d0-d95a-5544-aef9-689c530b467a/scratchpad/o_{ts}.jpg', quality=85)
        return
    out = args[0] if args else 'ouverture.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son13.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
