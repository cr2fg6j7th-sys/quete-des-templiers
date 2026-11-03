"""Stories Instagram / TikTok de Ma Quête Légendaire (1080 x 1920), à poster au fil des jours.
- textes sur fond noir (le *mot* entre étoiles passe en or)
- stories illustrées avec le dragon (images IA dans img/)
- stories animées (mp4) : texte tapé à la machine, liste à cocher, sono levée
Zone sûre : rien d'important au-dessus de y = 260 ni sous y = 1600 (barres d'Instagram).
Usage : python3 stories.py  ->  sortie/"""
import os, sys, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DRAGON = os.path.join(HERE, '..', 'video', 'dragon')
FONTS = os.path.join(DRAGON, 'fonts')
TITLE = os.path.join(FONTS, 'luckiest-guy-latin-400-normal.ttf')
BODY = os.path.join(FONTS, 'alegreya-sans-latin-900-normal.ttf')
SEMI = os.path.join(FONTS, 'alegreya-sans-latin-800-normal.ttf')
REG = os.path.join(FONTS, 'alegreya-sans-latin-400-normal.ttf')
W, H, FPS = 1080, 1920, 30
GOLD = (255, 205, 70); WHITE = (255, 255, 255); GREY = (150, 150, 160); RED = (200, 30, 40)
OUT = os.path.join(HERE, 'sortie')
os.makedirs(OUT, exist_ok=True)

def font(p, s): return ImageFont.truetype(p, s)

# ---------- fonds ----------
def black_bg(seed=1):
    a = np.full((H, W, 3), 8, np.float32)
    rng = np.random.default_rng(seed)
    a += rng.normal(0, 4, (H, W, 1))                                  # léger grain, comme une photo de nuit
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')

def navy_bg():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([22, 30, 64]), np.array([8, 10, 24])
    a = (top * (1 - y) + bot * y) * np.ones((1, W, 1))
    return Image.fromarray(a.astype(np.uint8)).convert('RGBA')

def signature(im, y=1540, col=GREY):
    d = ImageDraw.Draw(im)
    d.text((W / 2, y), 'Ma Quête Légendaire  ·  maquetelegendaire.fr', font=font(SEMI, 34), fill=col, anchor='mm')

# ---------- texte riche : *mot* en or, retour à la ligne automatique ----------
def rich_lines(txt, f, maxw):
    lines = []
    for para in txt.split('\n'):
        words = []; gold = False
        for raw in para.split(' '):
            w = raw
            starts = w.startswith('*'); w = w.lstrip('*') if starts else w
            if starts: gold = True
            ends = w.endswith('*') or w.rstrip('.,:;!?»…').endswith('*')
            g = gold
            w = w.replace('*', '')
            if ends: gold = False
            words.append((w, g))
        cur = []; cw = 0; sp = f.getlength(' ')
        for w, g in words:
            wl = f.getlength(w)
            if cur and cw + sp + wl > maxw:
                lines.append(cur); cur = []; cw = 0
            cw += (sp if cur else 0) + wl; cur.append((w, g))
        lines.append(cur)
    return lines

def draw_rich(im, txt, path, size, x, y, maxw=900, lh=1.18, align='left', col=WHITE, gold=GOLD, upto=None):
    """Écrit le texte ; upto = nombre de caractères visibles (effet machine à écrire). Renvoie le bas du bloc."""
    f = font(path, size); d = ImageDraw.Draw(im); sp = f.getlength(' ')
    lines = rich_lines(txt, f, maxw); step = int(size * lh); n = 0
    for i, ln in enumerate(lines):
        lw = sum(f.getlength(w) for w, _ in ln) + sp * max(0, len(ln) - 1)
        cx = x if align == 'left' else x - lw / 2
        for w, g in ln:
            if upto is not None:
                if n >= upto: return y + i * step
                if n + len(w) > upto: w = w[:upto - n]
            d.text((cx, y + i * step), w, font=f, fill=gold if g else col)
            n += len(w) + 1
            cx += f.getlength(w) + sp
        n += 0
    return y + len(lines) * step

def text_height(txt, path, size, maxw=900, lh=1.18):
    return len(rich_lines(txt, font(path, size), maxw)) * int(size * lh)

def outlined(im, txt, path, size, cx, cy, fill=WHITE, stroke=10, maxw=980):
    """Texte centré à contour noir (pour poser sur une illustration)."""
    f = font(path, size); d = ImageDraw.Draw(im)
    lines = [l for l in (' '.join(w for w, _ in ln) for ln in rich_lines(txt, f, maxw))]
    step = int(size * 1.08); top = cy - step * len(lines) / 2
    for i, l in enumerate(lines):
        col = fill[i] if isinstance(fill, list) else fill
        d.text((cx, top + i * step + step / 2), l, font=f, fill=col, anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0))

def cover(path):
    im = Image.open(path).convert('RGB')
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x0, y0, x0 + W, y0 + H)).convert('RGBA')

def shade(im, top=True, bottom=True):
    """Dégradés sombres en haut / en bas pour que le texte reste lisible."""
    a = np.zeros((H, W), np.float32); y = np.arange(H)[:, None]
    if top: a = np.maximum(a, np.clip(1 - y / 700, 0, 1) * 170)
    if bottom: a = np.maximum(a, np.clip((y - 1250) / 670, 0, 1) * 190)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(Image.fromarray(a.astype(np.uint8) * np.ones((1, W), np.uint8)))
    im.alpha_composite(sh); return im

def save(im, name):
    p = os.path.join(OUT, name); im.convert('RGB').save(p, quality=93); print('ok', name); return p

# ---------- stories fixes sur fond noir ----------
X0 = 90
def s_noir(name, blocks, seed=1, sign=True):
    """blocks : liste de (texte, police, taille, espace_après)."""
    im = black_bg(seed)
    total = sum(text_height(t, p, s) + gap for t, p, s, gap in blocks)
    y = max(300, (H - total) / 2 - 60)
    for t, p, s, gap in blocks:
        y = draw_rich(im, t, p, s, X0, y) + gap
    if sign: signature(im)
    return save(im, name)

def static_stories():
    s_noir('01-personne.jpg', [
        ('Personne :', SEMI, 62, 20),
        ('Absolument personne :', SEMI, 62, 70),
        ("Moi, à 23 h, la veille de l'anniversaire :", SEMI, 62, 30),
        ('« idée anniversaire enfant *DEMAIN* »', BODY, 78, 0)], seed=2)
    s_noir('02-souvenir.jpg', [
        ('Ton enfant ne se souviendra pas du gâteau.', BODY, 80, 70),
        ('Il se souviendra du jour où il est devenu *chevalier.*', BODY, 80, 0)], seed=3)
    s_noir('03-trois-etapes.jpg', [
        ('Un anniversaire réussi en 3 étapes :', BODY, 70, 70),
        ('1.  Taper *son prénom.*', SEMI, 64, 30),
        ('2.  Taper *ta ville.*', SEMI, 64, 30),
        ('3.  Le regarder courir dans la rue en criant « *À L\'ATTAQUE !* »', SEMI, 64, 0)], seed=4)
    s_noir('04-pov-adoube.jpg', [
        ('POV :', BODY, 70, 30),
        ("tu as dit à ton fils de 8 ans qu'il serait *adoubé* samedi.", BODY, 74, 70),
        ('Il dort avec son épée en bois depuis mardi.', SEMI, 62, 0)], seed=5)
    # sondage et questions : place laissée vide pour le sticker d'Instagram
    im = black_bg(6); y = draw_rich(im, "Ton enfant, c'est plutôt…", BODY, 84, X0, 420)
    draw_rich(im, 'chevalier, chevalière… ou *petit dragon* ?', SEMI, 62, X0, y + 30)
    signature(im); save(im, '05-sondage.jpg')
    im = black_bg(7); y = draw_rich(im, 'Une question pour le *Grand Maître* ?', BODY, 84, X0, 420)
    draw_rich(im, 'Âge, ville, durée, météo… il répond à tout. Même aux dragons.', SEMI, 56, X0, y + 30, col=(210, 210, 215))
    signature(im); save(im, '06-question.jpg')
    s_noir('07-ceci-ou-cela.jpg', [
        ('Pour son anniversaire, tu choisis quoi ?', BODY, 76, 80),
        ('A.  Le château gonflable dans le salon', SEMI, 64, 30),
        ('B.  Une *quête de chevalier* dans les rues de ta ville', SEMI, 64, 70),
        ('Réponds en message, le dragon compte les voix.', SEMI, 48, 0)], seed=8)
    # rappel « aperçu gratuit » aux couleurs de la marque
    im = navy_bg(); d = ImageDraw.Draw(im)
    outlined(im, 'PETIT RAPPEL', TITLE, 96, W / 2, 470, fill=GOLD, stroke=0)
    y = draw_rich(im, "L'aperçu de la quête est *gratuit.*", BODY, 80, W / 2, 620, align='center', maxw=900)
    y = draw_rich(im, 'Tu vois les étapes, la distance et la durée avant de payer.', SEMI, 58, W / 2, y + 40, align='center', maxw=880, col=(220, 220, 230))
    d.rounded_rectangle([200, y + 90, 880, y + 230], 70, fill=RED, outline=GOLD, width=6)
    d.text((W / 2, y + 162), 'LIEN EN BIO', font=font(TITLE, 70), fill=WHITE, anchor='mm')
    signature(im, col=(180, 180, 200)); save(im, '08-apercu-gratuit.jpg')

# ---------- stories illustrées ----------
def illustrated():
    im = shade(cover(os.path.join(DRAGON, 'img', 'bourse-pleure.jpg')))
    outlined(im, 'Le dragon quand il lit sa fiche de paie :', BODY, 76, W / 2, 400, maxw=940)
    outlined(im, '0 PIÈCE.', TITLE, 130, W / 2, 1450, fill=GOLD, stroke=12)
    save(im, '09-fiche-de-paie.jpg')
    p = os.path.join(HERE, 'img', 'fete-epuise.png')
    if os.path.exists(p):
        im = shade(cover(p))
        outlined(im, "Moi après 3 h d'anniversaire sans aucun programme :", BODY, 72, W / 2, 400, maxw=940)
        outlined(im, 'La prochaine fois : une quête.', BODY, 66, W / 2, 1460, fill=GOLD, maxw=900)
        save(im, '10-fete-epuise.jpg')

# ---------- stories animées ----------
def encode(frames_fn, n, name):
    p = os.path.join(OUT, name)
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', p], stdin=subprocess.PIPE)
    for i in range(n): pr.stdin.write(frames_fn(i / FPS).convert('RGB').tobytes())
    pr.stdin.close(); pr.wait(); print('ok', name)

def a_sono():
    """La sono levée : léger zoom avant et petit rebond au rythme (pose un son tendance par-dessus)."""
    p = os.path.join(HERE, 'img', 'sono.png')
    if not os.path.exists(p): return
    base = shade(cover(p), top=True, bottom=False)
    big = base.resize((int(W * 1.12), int(H * 1.12)), Image.LANCZOS)
    def fr(t):
        z = 1 + .08 * t / 8 + .012 * math.exp(-((t % .5) * 10))       # zoom lent + rebond tous les 0,5 s (120 bpm)
        w, h = int(W * z), int(H * z)
        im = big.resize((w, h), Image.BICUBIC).crop(((w - W) // 2, (h - H) // 2 + int(20 * (z - 1) * 10), (w - W) // 2 + W, (h - H) // 2 + H + int(20 * (z - 1) * 10)))
        im = im.convert('RGBA')
        outlined(im, 'Moi quand j\'essaie de faire connaître ma petite marque :', BODY, 78, W / 2, 400, maxw=960)
        return im
    fr(0).convert('RGB').save(os.path.join(OUT, '11-sono.jpg'), quality=93)
    encode(fr, 8 * FPS, '11-sono.mp4')

def a_machine():
    """Texte tapé à la machine sur fond noir, puis la chute en or."""
    bg = black_bg(9)
    l1 = 'Mon enfant : « on fait quoi pour mon anniversaire ? »'
    l2 = 'Moi, 2 minutes plus tard :'
    l3 = 'une *quête de chevalier* à son prénom, dans les rues de notre ville.'
    def fr(t):
        im = bg.copy()
        c1 = int(max(0, t - .3) * 26); y = draw_rich(im, l1, BODY, 76, X0, 420, upto=c1)
        if t > 3.0:
            y = draw_rich(im, l2, SEMI, 62, X0, y + 80, col=(200, 200, 205), upto=int((t - 3.0) * 26))
        if t > 4.6:
            draw_rich(im, l3, BODY, 76, X0, y + 50, upto=int((t - 4.6) * 24))
        if int(t * 2) % 2 == 0 and t < 7.5:                                 # curseur qui clignote
            ImageDraw.Draw(im).rectangle([X0, 1400, X0 + 34, 1408], fill=GOLD)
        if t > 7.6: signature(im, col=GOLD)
        return im
    encode(fr, 10 * FPS, '12-machine-a-ecrire.mp4')

def a_liste():
    """Liste à cocher de l'anniversaire de samedi, la dernière case se coche en or."""
    bg = black_bg(10)
    items = ['Gâteau', 'Bougies', 'Invitations', 'Copains (6, dont 2 qui ne se connaissent pas)', "Une activité qui les occupe 2 heures"]
    def box(d, x, y, state, col):
        d.rounded_rectangle([x, y, x + 64, y + 64], 12, outline=col, width=6)
        if state:
            d.line([(x + 12, y + 34), (x + 28, y + 50), (x + 54, y + 14)], fill=col, width=9)
    def fr(t):
        im = bg.copy(); d = ImageDraw.Draw(im)
        draw_rich(im, 'Anniversaire de samedi :', BODY, 84, X0, 340)
        y = 520
        for i, it in enumerate(items):
            last = i == len(items) - 1
            t_on = .6 + i * .8 + (1.4 if last else 0)
            col = GOLD if last and t > t_on else WHITE
            box(d, X0, y, t > t_on, col)
            yb = draw_rich(im, it, SEMI, 58, X0 + 100, y - 2, maxw=800, col=WHITE)
            y = max(yb, y + 80) + 40
        if t > 6.0:
            draw_rich(im, '…grâce à une *quête de chevalier* dans les rues de ta ville.', BODY, 66, X0, y + 50, upto=int((t - 6.0) * 30))
        if t > 8.4: signature(im, col=GOLD)
        return im
    encode(fr, 10 * FPS, '13-liste-a-cocher.mp4')

def planche():
    """Aperçu de toutes les stories sur une seule image."""
    files = sorted(f for f in os.listdir(OUT) if f.endswith('.jpg') and not f.startswith('apercu'))
    vids = sorted(f for f in os.listdir(OUT) if f.endswith('.mp4') and f.replace('.mp4', '.jpg') not in files)
    thumbs = []
    for f in files: thumbs.append((f, Image.open(os.path.join(OUT, f))))
    for v in vids:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-sseof', '-1', '-i', os.path.join(OUT, v), '-frames:v', '1',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        thumbs.append((v, Image.frombuffer('RGB', (W, H), raw[:W * H * 3])))
    tw, th, cols = 270, 480, 5
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new('RGB', (tw * cols, (th + 40) * rows), (30, 30, 36)); d = ImageDraw.Draw(sheet)
    for i, (f, im) in enumerate(thumbs):
        x, y = (i % cols) * tw, (i // cols) * (th + 40)
        sheet.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x + tw / 2, y + th + 20), f, font=font(SEMI, 22), fill=WHITE, anchor='mm')
    sheet.save(os.path.join(OUT, 'apercu-des-stories.jpg'), quality=88); print('ok planche')

if __name__ == '__main__':
    static_stories(); illustrated(); a_sono(); a_machine(); a_liste(); planche()
