"""Réel « sono sur l'épaule » (tendance « Quand t'as un commerce et que t'essaye de te faire connaître »).
Codes repris de la tendance (TikTok, novembre 2026) :
- décor : capture du vrai profil Instagram de la marque, fixe, en mode clair
- personnage détouré (fond vert) qui danse avec une enceinte, posé en bas de l'écran, coupé par le bas,
  qui change de place à chaque coupe sèche
- texte en haut, gras italique noir à contour blanc, présent toute la vidéo
- ~12 s, son de la tendance ajouté dans l'application (Gonna Make You Sweat)
Fichiers : profil.jpg (capture du profil), dragon-vert.mp4 (Wan 2.2 sur Hugging Face, fond vert)
Usage : python3 sono_trend.py  ->  ../sortie/reel-sono-epaule.mp4"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
END = 12.0
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-BoldItalic.ttf'
if os.path.exists(os.path.join(HERE, 'DejaVuSerifCondensed-BoldItalic.ttf')):
    FONT = os.path.join(HERE, 'DejaVuSerifCondensed-BoldItalic.ttf')
TXT = ['Quand le dragon se donne', 'du mal à faire connaître', 'la marque']

# (début, fin, sens de lecture, vitesse, centre x, bas du personnage, hauteur du personnage) : coupes sèches
SEGS = [(0.0, 5.0, 1, 1.0, 560, 2010, 1180),
        (5.0, 8.6, -1, 1.35, 700, 2060, 1320),
        (8.6, 12.0, 1, 1.45, 430, 1990, 1120)]

def background():
    im = Image.open(os.path.join(HERE, 'profil.jpg')).convert('RGB')
    im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    return im.crop((0, 0, W, H)).convert('RGBA')

def load_frames():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'dragon-vert.mp4'), '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    w, h = 480, 832; n = len(raw) // (w * h * 3)
    out = []
    for i in range(n):
        a = np.frombuffer(raw[i * w * h * 3:(i + 1) * w * h * 3], np.uint8).reshape(h, w, 3).astype(np.float32)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        green = g - np.maximum(r, b)                                     # dominance du vert
        alpha = np.clip(1 - (green - 40) / 50, 0, 1)                     # fond vert -> transparent, bord adouci
        a[..., 1] = np.minimum(g, np.maximum(r, b) + 10)                 # retire le reflet vert sur les bords
        rgba = np.dstack([a, alpha * 255]).astype(np.uint8)
        out.append(Image.fromarray(rgba, 'RGBA'))
    return out, 16

def caption():
    size = 84
    while max(ImageFont.truetype(FONT, size).getlength(l) for l in TXT) > 960: size -= 2   # tient dans la largeur
    f = ImageFont.truetype(FONT, size); step = int(size * 1.22)
    im = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(TXT):
        d.text((W / 2, 60 + i * step), l, font=f, fill=(0, 0, 0), anchor='mm', stroke_width=7, stroke_fill=(255, 255, 255))
    return im

def main():
    bg = background(); cap = caption(); frames, cfps = load_frames(); last = len(frames) - 1
    out = os.path.join(HERE, '..', 'sortie', 'reel-sono-epaule.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
                          '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    cache = {}
    for k in range(int(END * FPS)):
        t = k / FPS
        for (a, b, sens, v, cx, bot, hh) in SEGS:
            if a <= t < b: break
        x = (t - a) * v * cfps
        x = min(last, x) if sens > 0 else max(0, last - x)
        fr = frames[int(round(x))]
        key = (id(fr), hh)
        if key not in cache:
            cache[key] = fr.resize((int(fr.width * hh / fr.height), hh), Image.LANCZOS)
        d = cache[key]
        im = bg.copy()
        im.alpha_composite(d, (int(cx - d.width / 2), int(bot - d.height)))
        im.alpha_composite(cap, (0, 360))
        p.stdin.write(im.convert('RGB').tobytes())
        if k == int(10.5 * FPS): im.convert('RGB').save(os.path.join(HERE, '..', 'sortie', 'reel-sono-epaule-apercu.jpg'), quality=90)
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
