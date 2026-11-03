"""Réel tendance « It's time » (1er novembre : on passe d'un coup d'Halloween à Noël).
Codes repris de la tendance (TikTok, 1er-3 novembre 2026) :
- texte blanc simple en haut, présent toute la vidéo (« ma femme chaque année le 1er novembre »)
- scène calme et ordinaire, puis coupe sèche au cri « It's tiiime » : tout est déjà en mode Noël, le
  personnage déboule, surexcité
- ~8 s, son de la tendance ajouté dans l'application
Fichiers : calme.mp4, noel.mp4 (Wan 3.0 sur fal.ai, depuis calme.png / noel.png de Nano Banana 2.1)
Usage : python3 itstime.py  ->  ../sortie/reel-its-time.mp4"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
CUT, END = 3.8, 8.0                     # la coupe tombe sur le cri « It's tiiime »
FONT = os.path.join(HERE, 'LiberationSans-Bold.ttf')
TXT = ['Le dragon, chaque année,', 'le 1er novembre']

def frames(name):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, name), '-vf', f'fps={FPS},scale={W}:{H}',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    n = len(raw) // (W * H * 3)
    return [raw[i * W * H * 3:(i + 1) * W * H * 3] for i in range(n)]

def caption():
    f = ImageFont.truetype(FONT, 64)
    im = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(TXT):
        d.text((W / 2, 70 + i * 80), l, font=f, fill=(255, 255, 255), anchor='mm')
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').point(lambda a: int(a * .6)))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.alpha_composite(sh, (2, 3)); out.alpha_composite(im)
    return out

def main():
    a, b = frames('calme.mp4'), frames('noel.mp4'); cap = caption()
    out = os.path.join(HERE, '..', 'sortie', 'reel-its-time.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
                          '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for k in range(int(END * FPS)):
        t = k / FPS
        if t < CUT:
            im = Image.frombuffer('RGB', (W, H), a[min(k, len(a) - 1)]).convert('RGBA')
        else:
            j = k - int(CUT * FPS)
            im = Image.frombuffer('RGB', (W, H), b[min(j, len(b) - 1)]).convert('RGBA')
            if j < 4:                                                    # éclair blanc sur le cri
                im.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - j / 4)))))
        im.alpha_composite(cap, (0, 230))
        p.stdin.write(im.convert('RGB').tobytes())
        if abs(t - 5.0) < 1e-6: im.convert('RGB').save(os.path.join(HERE, '..', 'sortie', 'reel-its-time-couverture.jpg'), quality=92)
    p.stdin.close(); p.wait(); print('ok', out)

if __name__ == '__main__':
    main()
