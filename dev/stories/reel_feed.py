"""Réel « Je te vois tout le temps dans mon feed » (tendance Instagram) avec le dragon qui boit son café.
Texte blanc fin, à empattements, centré, en deux temps, comme la tendance d'origine.
Fichiers : img/cafe.mp4 (clip Wan 3.0 de fal.ai), fonts/LiberationSerif-Regular.ttf
Usage : python3 reel_feed.py  ->  sortie/reel-mon-feed.mp4 (sans son : ajouter le son de la tendance dans l'application)"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
END = 7.0
SPEED = 0.72                       # le clip de 5 s étiré à ~7 s, geste plus nonchalant
SERIF = os.path.join(HERE, 'fonts', 'LiberationSerif-Regular.ttf')
L1 = '« Je vois tout le temps\nton dragon dans mon feed »'
L2 = "C'est marrant, je ne te vois\njamais dans mes\nnotifications…"
T1, T2 = 0.35, 2.5                 # apparition sèche de chaque phrase, sans fondu

def load_clip(p):
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                    'stream=width,height', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.split(','))
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return [Image.frombuffer('RGB', (w, h), raw[i * w * h * 3:(i + 1) * w * h * 3]).resize((W, H), Image.LANCZOS) for i in range(n)], FPS

def text_layer(txt, size=104, squeeze=0.84, lead=0.92):
    """Texte serif blanc, resserré horizontalement, interligne serré, petite ombre douce (style « Classique » d'Instagram)."""
    f = ImageFont.truetype(SERIF, size)
    lines = txt.split('\n'); step = int(size * lead)
    wide = int(max(f.getlength(l) for l in lines)) + 40
    im = Image.new('RGBA', (wide, step * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((wide / 2, 20 + i * step), l, font=f, fill=(255, 255, 255, 255), anchor='ma',
               stroke_width=1, stroke_fill=(255, 255, 255, 255))            # un peu plus gras, comme la police d'Instagram
    im = im.resize((int(im.width * squeeze), im.height), Image.LANCZOS)
    a = im.getchannel('A')
    halo = Image.new('RGBA', im.size, (0, 0, 0, 0)); halo.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .45)))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * .8)))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new('RGBA', (im.width + 8, im.height + 8), (0, 0, 0, 0))
    out.alpha_composite(halo, (2, 4)); out.alpha_composite(sh, (3, 5)); out.alpha_composite(im, (0, 0))   # ombre douce + halo pour rester lisible sur fond clair
    return out

def main():
    frames, fps = load_clip(os.path.join(HERE, 'img', 'cafe.mp4'))
    t1, t2 = text_layer(L1), text_layer(L2)
    gap = 70; total = t1.height + gap + t2.height
    y1 = int(H * 0.665 - total / 2)                 # sur le ventre, sous le visage et la tasse
    y2 = y1 + t1.height + gap
    out = os.path.join(HERE, 'sortie', 'reel-mon-feed.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
                          '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    last = len(frames) - 1
    for k in range(int(END * FPS)):
        t = k / FPS
        x = min(last - .001, t * SPEED * fps); i = int(x); a = x - i
        im = Image.blend(frames[i], frames[i + 1], a).convert('RGBA') if a > .05 else frames[i].convert('RGBA')
        if t >= T1: im.alpha_composite(t1, ((W - t1.width) // 2, y1))
        if t >= T2: im.alpha_composite(t2, ((W - t2.width) // 2, y2))
        p.stdin.write(im.convert('RGB').tobytes())
        if k == int(4 * FPS): im.convert('RGB').save(os.path.join(HERE, 'sortie', 'reel-mon-feed-couverture.jpg'), quality=92)
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
