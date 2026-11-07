"""Instagram et TikTok « L'entretien d'embauche du dragon » (34 s), 7 novembre 2026, 3e vidéo d'ouverture.
Demande de Nathan (7/11, 11 h 40) : « une vidéo décalée au maximum… lâche-toi sur les blagues, que rien ne
soit prévisible ». Format des réels qui font réagir : accroche datée, série numérotée (Question 1/4 à 4/4),
retournement, dernier gag, question à un chiffre. La carte de fin reste 4,6 s.
12 h 15 (« les blagues ne sont pas assez drôles ») : réponses qui contredisent l'image, « 5 secondes plus
tard », le chat de la vidéo 2 en dernier candidat.
12 h 19 (« soigne le montage pour que ce soit beau et facile à comprendre ») : bulles de BD qui pointent
vers celui qui parle (le Grand Maître pose les questions, le dragon répond), étiquette « QUESTION n/4 »,
narration en légende en haut, voile plus léger, rythme plus posé (chaque réponse reste 1,3 s à 2,4 s).
Images : Nano Banana 2.1 ; animation : Wan 3.0 Prime (fal.ai). Plan du chat : troupe/c8.mp4 ; carte de fin :
annonce/c7.mp4.
Zones d'Instagram et TikTok évitées : 220 px en haut, 470 px en bas, colonne des boutons à droite (x > 930).
Usage : python3 entretien.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, os, math, subprocess
from PIL import Image, ImageDraw, ImageFilter

_open = Image.open
Image.open = lambda p, *a, **k: Image.new('RGB', (941, 1672), (20, 20, 30)) if isinstance(p, str) and not os.path.exists(p) else _open(p, *a, **k)
import montage as M
import fete as F
import inaug2 as I
Image.open = _open

W, H, FPS = 1080, 1920, 30
XT = 500
A = 'entretien/'
SCRATCH = '/tmp/claude-0/-home-claude/2200d18c-fb03-5130-b93c-65df657ebe08/scratchpad/entretien/'
CAT = '../troupe/c8'
END_CLIP = '../annonce/c7'

# (début, fin, clip, départ dans le clip, vitesse)
SHOTS = [
    (0.0, 3.0, 'e1', 0.0, 1.0),     # le dragon en costume face au Grand Maître
    (3.0, 6.4, 'e2', 0.0, 1.0),     # Q1 : « Mon sang-froid. » La chaise brûle derrière lui
    (6.4, 9.8, 'e3', 0.0, 1.0),     # Q2 : « Le perfectionnisme. » La barbe flambe
    (9.8, 14.0, 'e4', 0.0, 1.0),    # Q3 : « Une fois. 12 enfants de 8 ans. » « On n'en parle pas. »
    (14.0, 16.2, 'e1', 2.8, 1.0),   # Q4 : « Où vous voyez-vous dans 5 ans ? » « À votre place. »
    (16.2, 18.4, 'e5', 0.0, 1.0),   # 5 secondes plus tard : rôles inversés
    (18.4, 22.0, 'e6', 0.0, 1.0),   # « Et vous, votre plus grande qualité ? » LA QUÊTE DU CHEVALIER
    (22.0, 25.0, 'e7', 0.0, 1.0),   # les enfants dans les rues
    (25.0, 26.8, 'e8', 0.0, 1.0),   # salle d'attente : le poste a été supprimé
    (26.8, 29.4, CAT, 0.0, 1.0),    # candidat suivant : le chat couronné (vidéo 2)
    (29.4, 34.0, END_CLIP, 0.0, 1.0),   # carte de fin
]
FIN0 = 29.4
END = 34.0
R1_T = 4.3             # « Mon sang-froid. »
R2_T = 7.7             # « Le perfectionnisme. »
R3_T = 10.8            # « Une fois. 12 enfants de 8 ans. »
R3B_T = 12.4           # « … On n'en parle pas. »
VET_T = 12.9           # tampon VÉTÉRAN
R4_T = 14.9            # « À votre place. »
SWAP_T = 16.2          # coupe sèche : 5 secondes plus tard
QUETE_T = 19.9         # LA QUÊTE DU CHEVALIER
KIDS_T = 22.0
WAIT_T = 25.0
CHAT_T = 26.8          # candidat suivant
DEJA_T = 27.6          # « Déjà réservé. »
IMPACTS = [VET_T, SWAP_T, QUETE_T, DEJA_T]
BASEZ = {'e1': (1.15, .3, .85), 'e2': (1.15, .3, .85), 'e3': (1.15, .3, .85), 'e5': (1.15, .3, .85), 'e8': (1.2, .65, .9)}   # recadrage : personnages plus grands
PUNCH = [(R1_T, 1.04), (R2_T, 1.05), (R3B_T, 1.05), (VET_T, 1.08), (SWAP_T, 1.06), (QUETE_T, 1.05), (DEJA_T, 1.08)]

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
    """Étiquette dorée « QUESTION n/4 » : repère de la série, toujours au même endroit."""
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
    E['h1'] = T_('7 NOVEMBRE · 10 H 00', 84, G, maxw=900)
    E['h2'] = T_('Entretien d\'embauche :\nanimateur d\'anniversaire.\nCandidat : un dragon.', 64, [M.WHITE, M.WHITE, G], maxw=900)
    for n in range(1, 5): E[f'tag{n}'] = tag(f'QUESTION {n}/4')
    GM_TAIL = (300, 300)                     # de la bulle (en haut) vers la tête du Grand Maître, à droite
    DR_TAIL = (-200, 170)                    # de la bulle vers la tête du dragon, en bas à gauche
    E['q1'] = bubble('Votre plus grande\nqualité ?', GM_TAIL)
    E['q2'] = bubble('Votre plus grand\ndéfaut ?', GM_TAIL)
    E['q3'] = bubble('Vous avez déjà animé\nun anniversaire ?', (420, 60))
    E['q4'] = bubble('Où vous voyez-vous\ndans 5 ans ?', GM_TAIL)
    E['r1'] = bubble('Mon sang-froid.', DR_TAIL, 80)
    E['r2'] = bubble('Le perfectionnisme.', DR_TAIL, 78)
    E['r3'] = bubble('Une fois.\n12 enfants de 8 ans.', (0, 110), 76)
    E['r3b'] = bubble('… On n\'en parle pas.', (0, 110), 76)
    E['r4'] = bubble('À votre place.', DR_TAIL, 84)
    E['vet'] = F.stamp('VÉTÉRAN', 116)
    E['plus5'] = T_('5 secondes plus tard.', 86, M.GOLD, maxw=900)
    E['q5'] = bubble('Et vous, votre plus\ngrande qualité ?', (-300, 380))
    E['quete'] = M.banner('LA QUÊTE\nDU CHEVALIER', 84)
    E['open2'] = T_('À ton prénom.\nDans les rues de ta ville.\nSans animateur.', 70, [M.WHITE, G, G])
    E['chom'] = T_('Le poste a été\nsupprimé.', 82, [M.WHITE, G])
    E['suiv'] = T_('Candidat suivant :', 86, M.WHITE, maxw=900)
    E['deja'] = bubble('Déjà réservé.', (80, -380), 92)
    E['q'] = T_('Tu l\'embaucherais ?', 80, M.WHITE)
    E['opts'] = T_('1 oui · 2 non\n3 en stage', 76, [M.GOLD, M.GOLD])
    E['cta'] = M.banner('LA QUÊTE EST OUVERTE\nLIEN EN BIO', 64)
    E['url'] = T_('maquetelegendaire.fr', 60, stroke=10)

SPE = M.Sparkles(40, (40, 220, 1000, 1400), 11, size=(7, 18))
SPG = M.Sparkles(60, (60, 500, 1000, 1500), 23, size=(8, 22))

def PB(im, key, bx, by, sc=1.0):
    """Pose une bulle pour que le centre de son cadre (pas de sa queue) tombe en (bx, by)."""
    b, (cx, cy) = E[key]
    M.paste(im, b, bx + (b.width / 2 - cx) * sc, by + (b.height / 2 - cy) * sc, sc)

def arrow(im, x, y, t, s=1.0):
    d = ImageDraw.Draw(im); y += 12 * abs(math.sin(t * 6))
    pts = [(x - 22 * s, y - 56 * s), (x + 22 * s, y - 56 * s), (x + 22 * s, y), (x + 50 * s, y), (x, y + 52 * s), (x - 50 * s, y), (x - 22 * s, y)]
    d.polygon(pts, fill=M.GOLD + (255,)); d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=6)

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

def office(im, t, a, n, r, rt):
    """Plan du bureau : étiquette, question du Grand Maître (en haut), réponse du dragon (au-dessus de lui)."""
    pop = M.pop
    M.paste(im, E[f'tag{n}'], XT, 290, pop(t, a, .14))
    PB(im, f'q{n}', 540, 540, pop(t, a + .15, .16))
    PB(im, r, 430, 930, pop(t, rt, .14))

def frame(t):
    for (a, b, c, off, sp) in SHOTS:
        if a <= t < b: break
    lt = t - a
    im = clip_at(c, off + lt * sp)
    bz, bcx, bcy = BASEZ.get(c, (1.0, .5, .5))
    im = zoom(im, bz * punch(t), bcy, bcx)
    P = M.paste; pop = M.pop
    if a < FIN0: shade(im, 0, 760, 120)
    if a == 0.0:
        P(im, E['h1'], XT, 290, pop(t, 0.0, .14))
        P(im, E['h2'], XT, 520, pop(t, 0.5, .18))
    elif c == 'e2':
        office(im, t, a, 1, 'r1', R1_T)
    elif c == 'e3':
        office(im, t, a, 2, 'r2', R2_T)
    elif c == 'e4':
        P(im, E['tag3'], XT, 290, pop(t, a, .14))
        PB(im, 'q3', 480, 470, pop(t, a + .15, .16))
        if t < R3B_T: PB(im, 'r3', 500, 770, pop(t, R3_T, .14))
        else: PB(im, 'r3b', 500, 720, pop(t, R3B_T, .14))
        F.stamp_at(im, E['vet'], t, VET_T, XT, 1010, .85)
    elif c == 'e1':
        office(im, t, a, 4, 'r4', R4_T)
    elif c == 'e5':
        P(im, E['plus5'], XT, 320, pop(t, a + .05, .14))
    elif c == 'e6':
        if t < QUETE_T: PB(im, 'q5', 520, 440, pop(t, a + .1, .16))
        else:
            SPG.draw(im, t - QUETE_T, .8)
            P(im, E['quete'], XT, 420, pop(t, QUETE_T, .16) * (1 + .03 * math.exp(-((t - QUETE_T) % .6) * 10)))
    elif c == 'e7':
        P(im, E['open2'], XT, 400, pop(t, a, .18))
    elif c == 'e8':
        P(im, E['chom'], XT, 360, pop(t, a + .15, .16))
    elif c == CAT:
        P(im, E['suiv'], XT, 320, pop(t, a, .14))
        if t >= DEJA_T: SPG.draw(im, t - DEJA_T, .8)
        PB(im, 'deja', 430, 1400, pop(t, DEJA_T, .14))
    else:
        SPE.draw(im, lt, .7)
        P(im, E['q'], XT, 330, pop(lt, 0.0, .18))
        P(im, E['opts'], XT, 500, pop(lt, .25, .18))
        if lt > .5: arrow(im, XT, 650, lt)
        P(im, E['cta'], XT, 820, pop(lt, .8) * (1 + .03 * math.exp(-(lt % .6) * 10)))
        P(im, E['url'], XT, 975, pop(lt, 1.2))
    if lt < .07 and a > 0:
        I.flash(im, (255, 240, 200), .32 * (1 - lt / .07))
    for t0, col in [(SWAP_T, (255, 255, 255)), (QUETE_T, (255, 230, 150))]:
        if t0 <= t < t0 + .25: I.flash(im, col, .45 * (1 - (t - t0) / .25))
    return shake(im, t)

def main():
    build()
    args = sys.argv[1:]
    if '--preview' in args:
        os.makedirs(SCRATCH, exist_ok=True)
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'{SCRATCH}p_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'entretien.mp4'
    tmp = out[:-4] + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'son16.wav',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for f_ in range(int(END * FPS)):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, out); print('ok', out)

if __name__ == '__main__':
    main()
