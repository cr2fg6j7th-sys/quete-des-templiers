"""Couverture du réel « sono sur l'épaule » : le dragon brandit la sono à bout de bras, sur le profil Instagram.
Détourage local et gratuit avec rembg (modèle isnet-anime), nettoyé : on ne garde que le dragon et sa sono.
Usage : python3 couverture.py  ->  ../sortie/reel-sono-epaule-couverture.jpg"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
import sono_trend as T

HERE = os.path.dirname(os.path.abspath(__file__))

def cutout():
    from rembg import remove, new_session
    im = Image.open(os.path.join(HERE, '..', 'img', 'sono.png')).convert('RGB')
    a = np.array(remove(im, session=new_session('isnet-anime')))
    al = a[..., 3].astype(np.float32)
    lab, n = ndimage.label(al > 120)                                  # restes de décor : on garde le plus gros morceau
    if n:
        big = 1 + np.argmax(ndimage.sum(np.ones_like(al), lab, range(1, n + 1)))
        keep = ndimage.binary_dilation(lab == big, iterations=3)
        al = np.where(keep, al, 0)
    al = np.clip((al - 60) / 140, 0, 1) * 255                         # bords nets, sans voile
    a[..., 3] = al.astype(np.uint8)
    out = Image.fromarray(a, 'RGBA')
    return out.crop(out.getbbox())

def main():
    d = cutout()
    hh = 1250; d = d.resize((int(d.width * hh / d.height), hh), Image.LANCZOS)
    im = T.background()
    im.alpha_composite(d, (int(560 - d.width / 2), 1960 - d.height))
    im.alpha_composite(T.caption(), (0, 360))
    out = os.path.join(HERE, '..', 'sortie', 'reel-sono-epaule-couverture.jpg')
    im.convert('RGB').save(out, quality=93); print('ok', out)

if __name__ == '__main__':
    main()
