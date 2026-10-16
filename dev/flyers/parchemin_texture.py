# Aged parchment backgrounds for the "parchemin" flyers, drawn at 300 dpi (raster background only:
# text, drawings and QR codes stay vector on top). Same seed = same paper every time.
#   from parchemin_texture import parchment; parchment(154, 216, "out.jpg", seed=3, light=False)
import numpy as np
from PIL import Image, ImageFilter

DPI = 300
MM = DPI / 25.4

def _noise(h, w, cell, rng):
    g = rng.random((max(2, int(h / cell) + 3), max(2, int(w / cell) + 3)))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w + int(2 * cell), h + int(2 * cell)), Image.BICUBIC)
    return np.asarray(im, float)[int(cell):int(cell) + h, int(cell):int(cell) + w] / 255

def _fibers(h, w, rng):
    # thin streaks along the sheet: noise stretched sideways, then thresholded softly
    g = rng.random((h // 5 + 2, w // 40 + 2))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    a = np.asarray(im, float) / 255
    return np.clip((a - .7) * 2.4, 0, 1) * (.4 + .6 * _noise(h, w, 25 * MM, rng))

def parchment(w_mm, h_mm, out, seed=1, light=False):
    rng = np.random.default_rng(seed)
    w, h = round(w_mm * MM), round(h_mm * MM)
    # mottling: three scales of noise
    n = .5 * _noise(h, w, 70 * MM / 10, rng) + .32 * _noise(h, w, 22 * MM / 10, rng) + .18 * _noise(h, w, 5 * MM / 10, rng)
    m = np.clip((n - .4) * (1.1 if light else 1.4), 0, 1)
    c0 = np.array([241, 226, 190]) if light else np.array([236, 219, 178])   # light paper
    c1 = np.array([218, 192, 142]) if light else np.array([208, 174, 116])   # darker mottling
    img = c0[None, None, :] * (1 - m[..., None]) + c1[None, None, :] * m[..., None]
    # fibers and speckles
    f = _fibers(h, w, rng)
    img -= f[..., None] * np.array([14, 18, 22]) * (.6 if light else 1)
    sp = rng.random((h, w)) > .9993
    spk = np.asarray(Image.fromarray((sp * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)), float) / 255
    img -= np.clip(spk * 3, 0, 1)[..., None] * np.array([70, 80, 90])
    # a few old stains: soft blotches and one or two rings
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(3 if light else 5):
        cx, cy = rng.uniform(.1, .9) * w, rng.uniform(.1, .9) * h
        r = rng.uniform(9, 22) * MM
        d = np.hypot(xx - cx, yy - cy) / r
        blot = np.clip(1 - d, 0, 1) ** 2 * rng.uniform(.10, .22) * (.6 if light else 1)
        img -= blot[..., None] * np.array([40, 52, 70])
    for _ in range(1 if light else 2):
        cx, cy = rng.uniform(.15, .85) * w, rng.uniform(.15, .85) * h
        r = rng.uniform(10, 16) * MM
        d = np.abs(np.hypot(xx - cx, yy - cy) - r) / (.9 * MM)
        ring = np.exp(-d ** 2) * (.5 + .5 * _noise(h, w, 4 * MM, rng)) * .16 * (.6 if light else 1)
        img -= ring[..., None] * np.array([50, 70, 95])
    # burnt edges: distance to the edge, made irregular by noise
    dist = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / MM            # in mm
    wobble = 7 * _noise(h, w, 12 * MM, rng) + 2.5 * _noise(h, w, 3 * MM, rng)
    edge = np.clip(1 - (dist - 1.5 - wobble) / (16 if not light else 12), 0, 1) ** 1.7
    img = img * (1 - .72 * edge[..., None]) + np.array([96, 54, 20])[None, None, :] * (.72 * edge[..., None])
    scorch = np.clip(1 - (dist - .5 - .6 * wobble) / 4.5, 0, 1) ** 2
    img = img * (1 - .8 * scorch[..., None]) + np.array([52, 28, 10])[None, None, :] * (.8 * scorch[..., None])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
    im.save(out, quality=90, dpi=(DPI, DPI))
    return out
