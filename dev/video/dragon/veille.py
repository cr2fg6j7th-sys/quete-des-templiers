"""TikTok « La veille de l'ouverture » (25 s), texte à l'écran, sans voix off.
Zones TikTok à éviter : 150 px en haut, 400 px en bas, colonne de droite (x > 900).
Usage : python3 veille.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess
from PIL import Image, ImageFilter
import montage as M
import fete as F
import court as C
import inaug2 as I

W, H, FPS = M.W, M.H, M.FPS
CX, CY = M.SW / 2, M.SH / 2
XT = 470                      # centre des textes, un peu à gauche de la colonne de boutons
CLIPS = {1: ('ia/m1.mp4', 0.0), 3: ('ia/n2.mp4', 0.7), 4: ('ia/n4.mp4', 1.1),
         5: ('ia/f7.mp4', 0.0), 6: ('ia/f8.mp4', 0.0), 7: ('ia/n5.mp4', 1.7)}
RATE = {1: 30, 3: 30, 4: 30, 5: 16, 6: 14, 7: 30}
SHOTS = [
    (0.0, 2.8, 1, (1.00, CX, CY), (1.05, CX, CY + 20)),
    (2.8, 6.0, 2, (1.02, CX, CY), (1.14, CX, CY - 60)),
    (6.0, 10.0, 3, (1.06, CX, CY - 40), (1.00, CX, CY)),
    (10.0, 13.5, 4, (1.08, CX + 30, CY - 40), (1.16, CX + 90, CY - 80)),
    (13.5, 16.1, 5, (1.02, CX, CY), (1.10, CX, CY - 40)),
    (16.1, 19.0, 6, (1.02, CX, CY), (1.10, CX, CY - 30)),
    (19.0, 22.0, 7, (1.04, CX, CY), (1.10, CX - 40, CY - 30)),
]
END = 25.0
SNEEZE_T = 6.0 + (2.45 - 0.7)       # jet de feu du clip n2
HIC_T = 10.0 + (1.75 - 1.1)         # petite flamme du clip n4
NOTICE_T = 22.7
NY = 1250

E = {}
def T_(s, size=86, fill=None, font=None, maxw=820, stroke=12):
    if isinstance(fill, list): fill = fill + [fill[-1]] * 8
    return M.text_img(s, font or M.TITLE, size, fill=fill or M.WHITE, stroke=stroke, maxw=maxw)
def build():
    G = M.GOLD
    E['h1'] = T_("Demain, j'ouvre\nma petite entreprise.", 92, [M.WHITE, G])
    E['h2'] = T_('Effectif :', 76, M.GOLD)
    E['g1'] = F.stamp('1 PAPA', 56); E['g2'] = F.stamp('1 DRAGON', 56); E['g3'] = F.stamp('1 GRAND MAÎTRE', 44)
    E['t1'] = T_('21 h 04.', 120, G); E['t1b'] = T_('Le site est prêt.', 84)
    E['t2'] = T_('21 h 05.', 120, G); E['t2b'] = T_('Le dragon teste\nl\'inauguration.', 84)
    E['t3'] = T_('21 h 06.', 120, G); E['t3b'] = T_("Le Grand Maître\nn'a plus de barbe.", 84)
    E['atch'] = I.burst('ATCHOUM !', 640, 390, 100)
    E['hic'] = I.burst('HIC !', 460, 320, 110)
    E['v1'] = T_('Ce que je vends :', 76, G)
    E['v2'] = T_("une chasse au trésor\nde chevalier pour\nl'anniversaire de ton\nenfant (7-10 ans),", 70, font=M.BODY, stroke=10)
    E['v3'] = T_('à son prénom,\ndans les rues\nde ta ville.', 84, [M.WHITE, M.WHITE, G])
    E['v4'] = M.banner('24,90 €\nPOUR TOUTE LA BANDE', 64)
    E['a1'] = T_("L'aperçu\nest gratuit.", 92, G)
    E['a2'] = T_('Et si tu partages,\nle dragon touche\nenfin sa paie.', 72, font=M.BODY, stroke=10)
    E['p1'] = M.banner('OUVERTURE DEMAIN\n7 NOVEMBRE', 76)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 72)
    E['url'] = T_('maquetelegendaire.fr', 66, stroke=10)
    bg = I.SRC[5].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg

def src_for(k, lt):
    if k == 2:
        im = M.SRC[6].copy(); ui = M.phone_ui(min(2.4, lt * 1.2)); im.paste(ui, (M.SCR[0], M.SCR[1]), ui)
        return im
    return M.clip_src(700 + k, lt)

def frame(t):
    if t >= SHOTS[-1][1]:
        return end_card(t - SHOTS[-1][1], t)
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.05 * math.exp(-lt * 10)
    for t0, amp in ((SNEEZE_T, 26), (HIC_T, 12)):
        if t0 <= t < t0 + .5:
            s = amp * math.exp(-(t - t0) * 7); cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    im, v = M.shoot(src_for(k, lt), z, cx, cy)
    P = M.paste; pop = M.pop
    if k == 1:
        P(im, E['h1'], XT, 265, pop(t, 0.0, .16))
        P(im, E['h2'], XT, 425, pop(t, 0.6))
        F.stamp_at(im, E['g1'], t, 0.8, 250, 1020, .8)
        F.stamp_at(im, E['g3'], t, 1.25, 820, 520, .8)
        F.stamp_at(im, E['g2'], t, 1.7, 450, 1440, .8)
    elif k == 2:
        P(im, E['t1'], XT, 300, pop(t, a, .14)); P(im, E['t1b'], XT, 430, pop(t, a + .35))
    elif k == 3:
        P(im, E['t2'], XT, 300, pop(t, a, .14)); P(im, E['t2b'], XT, 470, pop(t, a + .35))
        if SNEEZE_T <= t < SNEEZE_T + 1.6: P(im, E['atch'], XT, 1300, pop(t, SNEEZE_T, .14))
        if t >= SNEEZE_T: I.flash(im, (255, 170, 60), .55 * math.exp(-(t - SNEEZE_T) * 6))
    elif k == 4:
        P(im, E['t3'], XT, 300, pop(t, a, .14)); P(im, E['t3b'], XT, 470, pop(t, a + .35))
        if HIC_T <= t < HIC_T + 1.4: P(im, E['hic'], 300, 900, pop(t, HIC_T, .12))
    elif k == 5:
        P(im, E['v1'], XT, 290, pop(t, a, .14)); P(im, E['v2'], XT, 520, pop(t, a + .3))
    elif k == 6:
        P(im, E['v3'], XT, 380, pop(t, a, .16)); P(im, E['v4'], XT, 1330, pop(t, a + .9, .18))
    elif k == 7:
        P(im, E['a1'], XT, 340, pop(t, a, .16)); P(im, E['a2'], XT, 1290, pop(t, a + .7))
    if lt < 0.07 and k != 1:
        I.flash(im, (255, 240, 200), .35 * (1 - lt / 0.07))
    if t > SHOTS[-1][1] - 0.2:
        I.flash(im, (12, 16, 40), .78 * (t - (SHOTS[-1][1] - 0.2)) / 0.2)
    return im

def end_card(lt, t):
    im = E['endbg'].copy(); C.SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], XT, 330, pop(lt, 0.0, .18))
    P(im, E['cta'], XT, 590, pop(lt, 0.5) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], XT, 790, pop(lt, 0.9))
    C.draw_notice(im, t, NOTICE_T, XT, NY)
    return im

def main():
    M.build(); C.build(); build()
    n = C.notice_base('AVIS DU ROYAUME', 'Envoie-la au parent qui a', 'un anniversaire à préparer.', '(Dragon non fourni.)')
    C.E['notice'] = n.resize((int(n.width * .74), int(n.height * .74)), Image.LANCZOS)
    for k, c in CLIPS.items():
        M.CLIPS[700 + k] = c; M.CLIP_RATE[700 + k] = RATE[k]
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'/tmp/claude-0/-home-claude/2ee4b4d0-d95a-5544-aef9-689c530b467a/scratchpad/v_{ts}.jpg', quality=85)
        return
    out = args[0] if args else 'veille.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son12.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
