# QR code printed on the diplomas, pointing to the site (?ref=diplome, counted in the weekly report):
#   python3 dev/video/qr.py  -> dev/qr-diplome.json, inlined in the page by build.py
# To run again whenever the site's address changes (build.py refuses a QR code that points elsewhere).
# Made with OpenCV (already installed), and read back to be sure it scans.
import json, re
from pathlib import Path
import cv2
import numpy as np

DEV = Path(__file__).resolve().parents[1]
SITE = re.search(r'^SITE = PLACES_SITE = "([^"]+)"', (DEV / "build.py").read_text(encoding="utf-8"), re.M).group(1)
URL = SITE + "/?ref=diplome"

p = cv2.QRCodeEncoder.Params()
p.correction_level = cv2.QRCODE_ENCODER_CORRECT_LEVEL_M   # survives a fold or a smudge on paper
m = cv2.QRCodeEncoder.create(p).encode(URL)
dark = m < 128
ys, xs = np.where(dark)
dark = dark[ys.min():ys.max() + 1, xs.min():xs.max() + 1]   # without the white margin: the page draws its own
size = dark.shape[0]

# one path: a rectangle per run of dark modules in a row
d = []
for y, row in enumerate(dark):
    x = 0
    while x < size:
        if row[x]:
            n = 1
            while x + n < size and row[x + n]:
                n += 1
            d.append(f"M{x} {y}h{n}v1h-{n}z")
            x += n
        else:
            x += 1

# read it back from a drawing of the path's modules
img = np.full(((size + 8) * 10, (size + 8) * 10), 255, np.uint8)
for y, x in zip(*np.where(dark)):
    img[(y + 4) * 10:(y + 5) * 10, (x + 4) * 10:(x + 5) * 10] = 0
assert cv2.QRCodeDetector().detectAndDecode(img)[0] == URL, "QR code illisible"

(DEV / "qr-diplome.json").write_text(json.dumps({"url": URL, "size": size, "d": "".join(d)}), encoding="utf-8")
print(f"dev/qr-diplome.json : {URL} ({size}x{size} modules)")
