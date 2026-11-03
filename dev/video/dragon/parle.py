"""« Le dragon te parle » : vidéo de 19,8 s, voix Gemini TTS (Fenrir) et sous-titres mot à mot.
Fichiers : ia/k1-k3.mp4 (le dragon parle), ia/f7.mp4 (course), ia/f8.mp4 (lettre dorée),
ia/p1.mp4 (le dragon pleure), img/phone.jpg, img/bourse-pleure.jpg, voix.wav (voix brute de fal.ai), son9.wav (python3 son9.py).
Usage : python3 parle.py [sortie.mp4] [--preview t1 t2 ...]"""
import sys, math, subprocess, os, wave
import numpy as np
from PIL import Image, ImageFilter

# les anciens scripts chargent au démarrage des images de conversations passées :
# on les remplace par une image vide, seules leurs fonctions servent ici
_open = Image.open
def _safe_open(p, *a, **k):
    if isinstance(p, str) and p.startswith('/mnt/user-data/') and not os.path.exists(p):
        return Image.new('RGB', (941, 1672))
    return _open(p, *a, **k)
Image.open = _safe_open
import montage as M
import fete as F
import court as C
Image.open = _open

W, H, FPS = M.W, M.H, M.FPS
SR = 44100
END = 19.8
END_T = 16.8                      # écran final
NOTICE_T = END_T + 0.6
NY = 1330
SUB_Y = 1420                      # sous-titres, au-dessus de la zone des boutons TikTok / Instagram

# ---------- voix : on raccourcit les silences trop longs (la voix elle-même n'est pas accélérée) ----------
# (début, fin, durée gardée) des silences de voix.wav, mesurés avec ffmpeg silencedetect (-35 dB)
VCUTS = [(5.8715, 6.7639, .35), (7.4678, 8.1307, .35), (8.4720, 9.2851, .40),
         (10.2319, 10.9966, .40), (14.5701, 15.1903, .35), (15.8759, 16.4702, .50)]
def _removed():
    out = []
    for s, e, keep in VCUTS:
        out.append((s + .15, e - (keep - .15)))           # on garde le début et la fin du silence
    return out
REMOVED = _removed()
def vmap(t):
    """Temps dans voix.wav -> temps dans la vidéo."""
    shift = 0.0
    for a, b in REMOVED:
        if t >= b: shift += b - a
        elif t > a: return a - shift
    return t - shift

# mots et début de chaque mot dans voix.wav (transcription Whisper, corrigée avec les silences mesurés)
WORDS = [("Hé,", .19), ("toi !", .38), ("Oui,", 1.0), ("toi !", 1.42), ("Ça", 2.24), ("t'est", 2.40), ("déjà", 2.56),
         ("arrivé", 2.84), ("de", 3.12), ("ne", 3.30), ("pas", 3.42), ("savoir", 3.58), ("quoi", 3.82), ("faire", 4.14),
         ("pour", 4.50), ("l'anniversaire", 4.68), ("de", 5.28), ("ton", 5.38), ("enfant ?", 5.50), ("Moi,", 6.76),
         ("oui.", 7.31), ("Tous", 8.13), ("les", 8.22), ("ans !", 8.34), ("Alors,", 9.29), ("regarde", 9.50),
         ("bien", 9.68), ("la", 9.88), ("suite…", 9.98), ("Une", 11.0), ("quête", 11.12), ("de", 11.42),
         ("chevalier", 11.58), ("au", 12.08), ("prénom", 12.32), ("de", 12.62), ("ton", 12.78), ("enfant,", 12.88),
         ("dans", 13.52), ("les", 13.80), ("rues", 13.96), ("de", 14.12), ("ta", 14.24), ("ville.", 14.32),
         ("Prête", 15.15), ("en", 15.34), ("deux", 15.46), ("minutes.", 15.60), ("Et", 16.47), ("moi ?", 16.55),
         ("Toujours", 17.17), ("pas", 17.44), ("payé.", 17.58)]
WORDS = [(w, vmap(t)) for w, t in WORDS]
GROUPS = [(0, 1), (2, 3), (4, 7), (8, 11), (12, 14), (15, 15), (16, 18), (19, 20), (21, 23), (24, 25), (26, 28),
          (29, 30), (31, 32), (33, 34), (35, 37), (38, 40), (41, 43), (44, 45), (46, 47), (48, 49), (50, 50), (51, 52)]

# ---------- plans ----------
# (début, fin, source, (z0, cx0, cy0), (z1, cx1, cy1)) ; coupes sur la grille de la musique (0,6 s)
SHOTS = [
    (0.0, 6.0, 'k1', (1.04, 470, 836), (1.22, 470, 760)),      # « Hé, toi ! »
    (6.0, 7.8, 'k2', (1.12, 470, 800), (1.04, 470, 836)),      # « Moi, oui. Tous les ans ! »
    (7.8, 9.0, 'k3', (1.06, 470, 800), (1.18, 470, 730)),      # « Alors, regarde bien la suite… »
    (9.0, 11.7, 'phone', (1.05, 470, 760), (1.20, 470, 730)),  # prénom tapé
    (11.7, 13.2, 'f7', (1.00, 470, 836), (1.16, 470, 800)),    # course dans les rues
    (13.2, 14.4, 'f8', (1.04, 470, 836), (1.18, 470, 800)),    # lettre dorée
    (14.4, END_T, 'bourse', (1.04, 470, 836), (1.16, 520, 820)),  # « Et moi ? Toujours pas payé. »
]
# clips : (fichier, décalage de départ en s, vitesse, aller-retour)
CLIPS = {'k1': ('ia/k1.mp4', 0.0, 0.85, True), 'k2': ('ia/k2.mp4', 0.1, 1.0, False),
         'k3': ('ia/k3.mp4', 0.0, 1.0, False), 'f7': ('ia/f7.mp4', 0.3, 1.0, False),
         'f8': ('ia/f8.mp4', 0.3, 1.0, False),
         'bourse': ('ia/p1.mp4', 0.0, 1.0, False)}             # le dragon pleure sur sa bourse vide (Wan 3.0, fal.ai)
STILLS = {'phone': 'img/phone.jpg', 'bourse': 'img/bourse-pleure.jpg'}
SRC = {}
_CF = {}
def clip_src(name, lt):
    path, off, rate, pingpong = CLIPS[name]
    if name not in _CF:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True).stdout
        w, h = 480, 832; n = len(raw) // (w * h * 3)
        _CF[name] = [Image.frombuffer('RGB', (w, h), raw[i * w * h * 3:(i + 1) * w * h * 3]) for i in range(n)]
    fr = _CF[name]; last = len(fr) - 1
    x = (lt * rate + off) * M.CLIP_FPS
    if pingpong:
        x = x % (2 * last); x = 2 * last - x if x > last else x
    x = min(last - .001, max(0, x))
    i = int(x); a = x - i
    im = Image.blend(fr[i], fr[i + 1], a) if a > .05 else fr[i]
    im = im.resize((M.SW, M.SH), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))

# ---------- éléments ----------
E = {}
SUB_SIZE = 90
def build():
    T, B_ = M.TITLE, M.BODY
    for k, p in STILLS.items(): SRC[k] = Image.open(p).convert('RGB')
    E['titre'] = M.text_img('Un message\ndu dragon.', T, 100, fill=[M.WHITE, M.GOLD], stroke=12, maxw=960)
    E['impaye'] = F.stamp('IMPAYÉ', 130)
    E['p1'] = M.text_img('Son prénom. Sa ville.\nSa quête.', B_, 80, fill=[M.WHITE, M.GOLD], stroke=10, maxw=1000)
    E['cta'] = M.banner('CRÉEZ SA QUÊTE\nLIEN EN BIO', 80)
    E['url'] = M.text_img('maquetelegendaire.fr', T, 78, stroke=10)
    bg = SRC['bourse'].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(14)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, 175)))
    E['endbg'] = bg
    # sous-titres : chaque mot pré-rendu en blanc et en or (le mot en cours est en or)
    f = M.font(T, SUB_SIZE)
    E['sp'] = f.getlength(' ') + 26          # les contours épais mangent l'espace
    E['words'] = [(M.text_img(w, T, SUB_SIZE, fill=M.WHITE, stroke=10, maxw=2000),
                   M.text_img(w, T, SUB_SIZE, fill=M.GOLD, stroke=10, maxw=2000), f.getlength(w)) for w, _ in WORDS]
    C.build()
    n = C.notice_base('AVIS DU ROYAUME', 'Envoie-la au parent qui', 'ne sait jamais quoi faire.', '(Le dragon, lui, a une idée.)')
    C.E['notice'] = n.resize((int(n.width * .9), int(n.height * .9)), Image.LANCZOS)

def subtitles(im, t):
    if t >= END_T: return
    for gi, (a, b) in enumerate(GROUPS):
        start = WORDS[a][1]
        nxt = WORDS[GROUPS[gi + 1][0]][1] if gi + 1 < len(GROUPS) else END_T
        stop = min(nxt, WORDS[b][1] + 1.0, END_T)
        if start <= t < stop: break
    else:
        return
    idx = list(range(a, b + 1))
    total = sum(E['words'][i][2] for i in idx) + E['sp'] * (len(idx) - 1)
    x = W / 2 - total / 2
    cur = max(i for i in idx if WORDS[i][1] <= t)
    for i in idx:
        wimg, gimg, wl = E['words'][i]
        if WORDS[i][1] <= t:
            M.paste(im, gimg if i == cur else wimg, x + wl / 2 + 4, SUB_Y, M.pop(t, WORDS[i][1], .14))
        x += wl + E['sp']

SPF = M.Sparkles(36, (80, 500, 1000, 1500), 17, rise=0.8, size=(8, 22))
SPE = M.Sparkles(40, (30, 160, 1050, 1750), 39, size=(6, 16))

def frame(t):
    if t >= END_T:
        return end_card(t - END_T, t)
    for (a, b, k, p0, p1) in SHOTS:
        if a <= t < b: break
    u = (t - a) / (b - a); e = M.ease(u) * 0.85 + u * 0.15
    z = M.lerp(p0[0], p1[0], e); cx = M.lerp(p0[1], p1[1], e); cy = M.lerp(p0[2], p1[2], e)
    lt = t - a
    z *= 1 + 0.05 * math.exp(-lt * 10) + 0.012 * math.exp(-(t % 0.6) * 12)   # coup de zoom à la coupe, pulsation au temps
    if k == 'f7': cy += 6 * abs(math.sin(lt * 9))                             # foulée
    if k == 'bourse' and t >= 15.85:                                          # secousse du tampon
        s = 16 * math.exp(-(t - 15.85) * 9); cx += s * math.sin(t * 70); cy += s * math.cos(t * 55)
    if k in CLIPS: src = clip_src(k, lt)
    else: src = SRC[k]
    if k == 'phone':
        src = src.copy(); ui = M.phone_ui(lt + 0.1); src.paste(ui, (M.SCR[0], M.SCR[1]), ui)
    im, v = M.shoot(src, z, cx, cy)
    P = M.paste
    if k == 'k1':
        P(im, E['titre'], W / 2, 270, M.pop(t, 0.05, .18))
    elif k == 'f8':
        gx, gy = M.to_screen(v, 470, 1180)
        P(im, M.GLOW, gx, gy, 1.0 + .15 * math.sin(lt * 5), alpha=min(1, .5 + lt))
        SPF.draw(im, lt, alpha=min(1, lt * 2))
    elif k == 'bourse':
        F.stamp_at(im, E['impaye'], t, 15.85, 300, 330, .8)
    if lt < 0.07 and a > 0:                                                   # éclair de coupe
        im.alpha_composite(Image.new('RGBA', (W, H), (255, 240, 200, int(90 * (1 - lt / 0.07)))))
    if t > END_T - 0.2:
        f = (t - (END_T - 0.2)) / 0.2
        im.alpha_composite(Image.new('RGBA', (W, H), (12, 16, 40, int(200 * f))))
    subtitles(im, t)
    return im

def end_card(lt, t):
    im = E['endbg'].copy(); SPE.draw(im, lt, 0.7)
    P = M.paste; pop = M.pop
    P(im, E['p1'], W / 2, 400, pop(lt, 0.0))
    P(im, E['cta'], W / 2, 720, pop(lt, 0.3) * (1 + 0.04 * math.exp(-(lt % 0.6) * 10)))
    P(im, E['url'], W / 2, 920, pop(lt, 0.45))
    C.draw_notice(im, t, NOTICE_T, W / 2, NY)
    return im

# ---------- son : voix raccourcie + musique baissée sous la voix ----------
def read_wav(p):
    with wave.open(p) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
def mix_audio(out='parle.wav'):
    v = read_wav('voix.wav')
    keep = np.ones(len(v), bool)
    for a, b in REMOVED: keep[int(a * SR):int(b * SR)] = False
    v = v[keep]; v = v / np.abs(v).max() * .89
    m = read_wav('son9.wav')
    n = int(END * SR); vo = np.zeros(n); vo[:len(v)] = v[:n]
    # baisse de la musique quand le dragon parle (enveloppe lissée sur 120 ms)
    k = int(.12 * SR); env = np.convolve(np.abs(vo), np.ones(k) / k, 'same')
    env = np.clip(env / .05, 0, 1)
    t = np.arange(n) / SR
    g = .30 - .12 * env
    g = np.where(t >= END_T, .75, np.where(t >= END_T - .3, .30 + (.75 - .30) * (t - END_T + .3) / .3, g))
    mo = np.zeros(n); mo[:min(n, len(m))] = m[:n]
    s = vo + mo * g
    s = s / max(1, np.abs(s).max() / .97)
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((s * 32767).astype(np.int16).tobytes())
    return out

def main():
    M.build(); build()
    args = sys.argv[1:]
    if '--preview' in args:
        for ts in args[args.index('--preview') + 1:]:
            frame(float(ts)).convert('RGB').save(f'parle_{ts}.jpg', quality=88)
        return
    out = args[0] if args else 'le-dragon-te-parle.mp4'
    snd = mix_audio()
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', snd,
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for f_ in range(n):
        p.stdin.write(frame(f_ / FPS).convert('RGB').tobytes())
        if f_ % 120 == 0: print(f_, '/', n, flush=True)
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
