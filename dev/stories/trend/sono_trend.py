"""Réel « sono sur l'épaule » (tendance « Quand t'as un commerce et que t'essaye de te faire connaître »).
Codes repris de la tendance (TikTok, novembre 2026) :
- décor : capture du vrai profil Instagram de la marque, fixe, en mode clair
- personnage détouré (fond vert) qui danse avec une enceinte, posé en bas de l'écran, coupé par le bas,
  en un seul plan continu (deux clips enchaînés, le second part de la dernière image du premier)
- texte en haut, gras italique noir à contour blanc, présent toute la vidéo
- ~12 s, son de la tendance ajouté dans l'application (Gonna Make You Sweat)
Fichiers : profil.jpg (capture du profil), dragon-vert.mp4 (Wan 2.2 sur Hugging Face, fond vert),
           dragon-vert-2.mp4 (suite, Wan 3.0 sur fal.ai, quota Hugging Face épuisé)
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

# enchaînés sans retour en arrière ni répétition ; fal.ai a recadré l'image de départ en 9:16 (468 px de large au centre),
# on remet donc le clip 2 à cette échelle et on complète de vert pour que le raccord tombe pile
CLIPS = [('dragon-vert.mp4', 'fps=16,scale=480:832'),
         ('dragon-vert-2.mp4', 'fps=16,scale=468:832,pad=480:832:6:0:color=0x00FF00')]
CX, BOT, HH = 560, 2010, 1180                            # centre x, bas du personnage, hauteur du personnage

def background():
    im = Image.open(os.path.join(HERE, 'profil.jpg')).convert('RGB')
    im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    return im.crop((0, 0, W, H)).convert('RGBA')

def load_frames():
    raws = []
    for j, (c, vf) in enumerate(CLIPS):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, c), '-vf', vf,
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        n = len(raw) // (480 * 832 * 3)
        raws += [raw[i * 480 * 832 * 3:(i + 1) * 480 * 832 * 3] for i in range(1 if j else 0, n)]   # la 1re image du clip 2 = la dernière du clip 1
    w, h = 480, 832; out = []
    for chunk in raws:
        i = 0; raw = chunk
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
    big = [f.resize((int(f.width * HH / f.height), HH), Image.LANCZOS) for f in frames]
    speed = last / (END * cfps)                                      # tout le mouvement étalé sur 12 s, en un seul plan
    for k in range(int(END * FPS)):
        t = k / FPS
        x = min(last - .001, t * speed * cfps); i = int(x); a = x - i
        d = Image.blend(big[i], big[i + 1], a) if a > .05 else big[i]   # images intermédiaires : mouvement fluide
        im = bg.copy()
        im.alpha_composite(d, (int(CX - d.width / 2), int(BOT - d.height)))
        im.alpha_composite(cap, (0, 360))
        p.stdin.write(im.convert('RGB').tobytes())
        if k == int(10.5 * FPS): im.convert('RGB').save(os.path.join(HERE, '..', 'sortie', 'reel-sono-epaule-apercu.jpg'), quality=90)
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
