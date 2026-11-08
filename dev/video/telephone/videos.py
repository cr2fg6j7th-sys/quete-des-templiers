# Short phone videos for the website: the real quest pages (captured by capt.py at 390 px, 2x),
# stacked and scrolled slowly and continuously, then a crossfade back to the top so the loop is seamless.
import subprocess, sys
from pathlib import Path
from PIL import Image

D = Path(__file__).parent
E = D / 'ecrans'; OUT = D / 'out'; OUT.mkdir(exist_ok=True)
W2, H2 = 780, 1688            # the phone screen in the captures (390 x 844 CSS at 2x)
W, H = 540, 1168              # video size (about 2x the phone drawn on the site)
FPS = 30
GAP = 14                      # thin band between two pages (2x px)
BAND = (222, 208, 172)

VIDEOS = {
    'quete-apercu':   ([('01-apercu', 4080)], 220),
    'quete-depart':   ([('03-debut', None), ('04-etape', None)], 200),
    'quete-defis':    ([('05-recit', None), ('06-enigme', None), ('07-lettre', None)], 260),
    'quete-tresor':   ([('09-mot-secret', None), ('10-tresor', 2040)], 220),
}
HOLD0, HOLD1, FADE, RAMP = 1.0, 1.0, 0.6, 0.7

def strip(pages):
    ims = []
    for name, cut in pages:
        im = Image.open(E / f'{name}.png').convert('RGB')
        if cut: im = im.crop((0, 0, W2, cut))
        ims.append(im)
    h = sum(i.height for i in ims) + GAP * (len(ims) - 1)
    s = Image.new('RGB', (W2, h), BAND); y = 0
    for i in ims: s.paste(i, (0, y)); y += i.height + GAP
    return s.resize((W, round(h * W / W2)), Image.LANCZOS)

def pos(t, dist, v):
    """Scroll offset: still at the top, smooth start, constant speed, smooth stop, still at the bottom."""
    T = dist / v + RAMP              # scroll time with a ramp at each end (same distance)
    u = t - HOLD0
    if u <= 0: return 0.0
    if u >= T: return float(dist)
    vmax = dist / (T - RAMP)
    if u < RAMP: return vmax * u * u / (2 * RAMP)
    if u > T - RAMP: w = T - u; return dist - vmax * w * w / (2 * RAMP)
    return vmax * RAMP / 2 + vmax * (u - RAMP)

for name, (pages, v2) in VIDEOS.items():
    s = strip(pages); dist = s.height - H; v = v2 * W / W2
    T = HOLD0 + dist / v + RAMP + HOLD1 + FADE
    n = round(T * FPS); first = s.crop((0, 0, W, H))
    tmp = OUT / f'{name}.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'slow', '-crf', '25', '-pix_fmt', 'yuv420p', '-g', '60', '-an',
                          '-movflags', '+faststart', str(tmp)], stdin=subprocess.PIPE)
    for k in range(n):
        t = k / FPS
        y = round(pos(t, dist, v))
        fr = s.crop((0, y, W, y + H))
        tf = t - (T - FADE)
        if tf > 0: fr = Image.blend(fr, first, min(1, tf / FADE))
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0:
        tmp.rename(OUT / f'{name}.mp4')
        first.save(OUT / f'{name}.jpg', quality=82)
        print(name, f'{T:.1f} s', (OUT / f'{name}.mp4').stat().st_size // 1024, 'Ko')
