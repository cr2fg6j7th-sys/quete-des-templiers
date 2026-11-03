"""Deux réels tendance faits uniquement avec des images déjà générées (aucun coût IA) :
1. « Pump It » : les étapes de fabrication qui défilent en rythme, chacune avec un petit titre
   en italique et des étoiles (codes vus sur TikTok, oct. 2026 : « the tools », « the markers »…)
   -> la préparation d'une quête, du prénom tapé jusqu'au salaire du dragon.
2. « Vlog 9 photos » : 9 photos qui se posent en grille sur le rythme, chacune avec son heure
   -> une journée de travail du dragon.
Sans son : ajouter le son de la tendance (ou un son de la bibliothèque commerciale) dans l'application.
Usage : python3 libres.py  ->  ../sortie/reel-pump-it.mp4, ../sortie/reel-journee-du-dragon.mp4"""
import os, sys, math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DEV = os.path.abspath(os.path.join(HERE, '..', '..'))
DRAGON = os.path.join(DEV, 'video', 'dragon')
SERIE = os.path.join(DEV, 'video', 'serie', 'img')
STO = os.path.join(DEV, 'stories')
OUT = os.path.join(STO, 'sortie')
W, H, FPS = 1080, 1920, 30
ITAL = os.path.join(HERE, 'FreeSerifItalic.ttf')
BOLD = os.path.join(HERE, 'LiberationSans-Bold.ttf')

# l'écran de téléphone de montage.py (prénom et ville tapés)
sys.path.insert(0, DRAGON)
_open = Image.open
Image.open = lambda p, *a, **k: Image.new('RGB', (941, 1672)) if isinstance(p, str) and p.startswith('/mnt/user-data/') and not os.path.exists(p) else _open(p, *a, **k)
import montage as M
Image.open = _open
for k in ('TITLE', 'BODY', 'SEMI'):
    setattr(M, k, os.path.join(DRAGON, getattr(M, k)))

def cover(im, w=W, h=H):
    im = im.convert('RGB'); s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

def fit_on_blur(im):
    """Image entière (ex. le diplôme) sur un fond flou de la même image."""
    bg = cover(im).filter(ImageFilter.GaussianBlur(30))
    s = min(W * .92 / im.width, H * .8 / im.height); fg = im.convert('RGB').resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2)); return bg

def phone(t):
    src = Image.open(os.path.join(DRAGON, 'img', 'phone.jpg')).convert('RGB')
    ui = M.phone_ui(t); src.paste(ui, (M.SCR[0], M.SCR[1]), ui); return src

def clip_frame(path, t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1', '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                    '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.split(','))
    return Image.frombuffer('RGB', (w, h), raw[:w * h * 3])

def clip_frames(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'fps={FPS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True).stdout
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                    '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.split(','))
    return [Image.frombuffer('RGB', (w, h), raw[i * w * h * 3:(i + 1) * w * h * 3]) for i in range(len(raw) // (w * h * 3))]

def star(d, x, y, r, col=(255, 255, 255, 255)):
    d.polygon([(x, y - r), (x + r * .25, y - r * .25), (x + r, y), (x + r * .25, y + r * .25),
               (x, y + r), (x - r * .25, y + r * .25), (x - r, y), (x - r * .25, y - r * .25)], fill=col)

def pump_label(txt):
    """Petit titre italique blanc, halo doux, deux étoiles (style « the tools »)."""
    f = ImageFont.truetype(ITAL, 112)
    w = int(f.getlength(txt)) + 260; im = Image.new('RGBA', (w, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((w / 2, 110), txt, font=f, fill=(255, 255, 255, 255), anchor='mm', stroke_width=1, stroke_fill=(255, 255, 255, 255))
    star(d, 60, 70, 26); star(d, 98, 128, 14); star(d, w - 60, 150, 26); star(d, w - 100, 82, 14)
    glow = Image.new('RGBA', im.size, (255, 120, 190, 0)); glow.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * .8)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(5)).point(lambda a: int(a * .5)))
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 0)); out.alpha_composite(glow); out.alpha_composite(im)
    return out

def encode(name, n, fr):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
                          '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(OUT, name)], stdin=subprocess.PIPE)
    for k in range(n): p.stdin.write(fr(k / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', name)

# ---------------- 1. Pump It ----------------
BEAT = 0.78                                    # deux temps par plan, coupes sèches
def pump_it():
    f7 = clip_frames(os.path.join(DRAGON, 'ia', 'f7.mp4')); f8 = clip_frames(os.path.join(DRAGON, 'ia', 'f8.mp4'))
    shots = [('le prénom', lambda t: phone(0.95)),
             ('la ville', lambda t: phone(1.75)),
             ('le parcours', lambda t: Image.open(os.path.join(SERIE, 'ville.jpg'))),
             ('les énigmes', lambda t: Image.open(os.path.join(SERIE, 'lettre.jpg'))),
             ('la troupe', lambda t: f7[min(len(f7) - 1, int((t + .3) * FPS))]),
             ("la lettre d'or", lambda t: f8[min(len(f8) - 1, int((t + .3) * FPS))]),
             ('le gâteau', lambda t: Image.open(os.path.join(SERIE, 'gateau.jpg'))),
             ('le diplôme', None),
             ('le salaire du dragon', lambda t: Image.open(os.path.join(DRAGON, 'img', 'bourse-pleure.jpg')))]
    dip = fit_on_blur(Image.open(os.path.join(DEV, 'video', 'campagne', 'img', 'diplome-rose.png')))
    labels = [pump_label(s[0]) for s in shots]
    durs = [BEAT] * 8 + [2.2]                  # le dernier plan tient : la chute
    starts = [sum(durs[:i]) for i in range(len(durs))]; end = sum(durs)
    cache = {}
    def fr(t):
        i = max(j for j in range(len(starts)) if starts[j] <= t); lt = t - starts[i]
        name, src = shots[i]
        if name == 'le diplôme': base = dip
        elif name in ('la troupe', "la lettre d'or"): base = cover(src(lt))
        else:
            if i not in cache: cache[i] = cover(src(0))
            base = cache[i]
        z = 1.0 + .06 * lt / durs[i] + .05 * math.exp(-lt * 12)          # petit coup de zoom à la coupe, puis avance lente
        w, h = int(W * z), int(H * z)
        im = base.resize((w, h), Image.BICUBIC).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H)).convert('RGBA')
        lab = labels[i]; im.alpha_composite(lab, ((W - lab.width) // 2, 280))   # au-dessus de l'écran du téléphone
        return im
    encode('reel-pump-it.mp4', int(end * FPS), fr)

# ---------------- 2. Vlog 9 photos ----------------
def journee():
    cafe = clip_frame(os.path.join(STO, 'img', 'cafe.mp4'), 1.0)
    k1 = clip_frame(os.path.join(DRAGON, 'ia', 'k1.mp4'), 0.4)
    pics = [('07:02', cafe), ('08:30', Image.open(os.path.join(STO, 'itstime', 'calme.png'))),
            ('10:00', Image.open(os.path.join(STO, 'img', 'sono.png'))), ('11:15', k1),
            ('14:00', Image.open(os.path.join(DRAGON, 'img', 'course.jpg'))), ('15:30', Image.open(os.path.join(DRAGON, 'img', 'lettre.jpg'))),
            ('16:30', Image.open(os.path.join(SERIE, 'gateau.jpg'))), ('17:00', Image.open(os.path.join(DRAGON, 'img', 'bourse-pleure.jpg'))),
            ('21:00', Image.open(os.path.join(STO, 'img', 'fete-epuise.png')))]
    cw, ch, gap = 320, 426, 14
    gx = (W - 3 * cw - 2 * gap) // 2; gy = 560
    ft = ImageFont.truetype(BOLD, 40)
    cells = []
    for hh, im in pics:
        c = cover(im, cw, ch).convert('RGBA'); d = ImageDraw.Draw(c)
        d.text((16, ch - 16), hh, font=ft, fill=(255, 255, 255), anchor='ld', stroke_width=3, stroke_fill=(0, 0, 0))
        cells.append(c)
    bg = cover(pics[2][1]).filter(ImageFilter.GaussianBlur(40)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA', (W, H), (10, 10, 20, 150)))
    tf = ImageFont.truetype(BOLD, 66); title = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(title)
    for i, l in enumerate(['Une journée de travail', 'du dragon']):
        d.text((W / 2, 60 + i * 80), l, font=tf, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
    STEP, END = 0.52, 7.5                       # une photo par temps, puis la grille complète tient
    def fr(t):
        im = bg.copy(); im.alpha_composite(title, (0, 300))
        for i, c in enumerate(cells):
            t0 = .4 + i * STEP
            if t < t0: break
            s = M.pop(t, t0, .16)
            x = gx + (i % 3) * (cw + gap) + cw // 2; y = gy + (i // 3) * (ch + gap) + ch // 2
            M.paste(im, c, x, y, s)
        return im
    encode('reel-journee-du-dragon.mp4', int(END * FPS), fr)

if __name__ == '__main__':
    pump_it(); journee()
