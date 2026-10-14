# Invented signature of the Grand Master ("Aldéran"), printed above "Le Grand Maître" on the diplomas:
#   python3 dev/video/signature.py -> dev/signature.json, inlined in the page by build.py
# Cursive letters from point templates, slanted, sampled along smooth curves and inked like a broad pen
# (thick downstrokes, thin hairlines), then written as one filled path.
import math, json
XH, BASE, SLANT = 10.5, 58, 0.32
L = {  # x from 0 to width, y up: baseline 0, x-height 1, ascender ~2.2
 "A": ([(-0.3,0.15),(0.3,0.9),(0.9,2.2),(1.25,2.95),(1.38,2.6),(1.35,1.6),(1.45,0.5),(1.6,0.05),(1.75,0.15),
        (1.5,0.6),(0.9,0.85),(0.45,1.0),(0.6,1.25),(1.3,1.15),(1.9,0.9),(2.05,0.4)], 2.05),
 "l": ([(0,0.4),(0.35,1.5),(0.6,2.2),(0.5,2.4),(0.3,2.05),(0.25,1.2),(0.3,0.3),(0.5,0.0),(0.75,0.15)], 0.75),
 "d": ([(0.85,0.75),(0.55,1.0),(0.2,0.8),(0.05,0.35),(0.3,0.0),(0.65,0.25),(0.85,0.8),(1.05,2.25),(1.0,1.2),(0.95,0.35),(1.1,0.0),(1.35,0.15)], 1.35),
 "e": ([(0,0.15),(0.45,0.45),(0.6,0.8),(0.45,1.0),(0.2,0.75),(0.15,0.25),(0.4,0.0),(0.75,0.15)], 0.75),
 "r": ([(0,0.2),(0.2,0.85),(0.3,1.0),(0.42,0.75),(0.6,0.95),(0.72,0.8),(0.7,0.35),(0.82,0.05),(1.0,0.15)], 1.0),
 "a": ([(0.75,0.85),(0.45,1.0),(0.12,0.7),(0.12,0.2),(0.42,0.02),(0.72,0.5),(0.8,1.0),(0.72,0.35),(0.85,0.0),(1.05,0.15)], 1.05),
 "n": ([(0,0.15),(0.12,0.8),(0.22,1.0),(0.32,0.7),(0.3,0.0),(0.4,0.6),(0.58,1.0),(0.72,0.75),(0.7,0.2),(0.82,0.0),(1.0,0.12)], 1.0),
}
def place(word):
    pts, x = [], 0.0
    for i, ch in enumerate(word):
        p, w = L[ch]
        q = [(x + a, b) for a, b in p]
        pts += q if not pts else q[1:] if abs(q[0][0] - pts[-1][0]) < 0.05 else q
        x += w
    return pts, x
def to_svg(p):  # slant + scale, svg y down
    return (20 + (p[0] + SLANT * p[1]) * XH, BASE - p[1] * XH)
word, width = place("Aldéran".replace("é", "e"))
# final flourish: up, loop, and a long swash under the name back to the start
fl = [(width + 0.45, 0.55), (width + 1.1, 1.15), (width + 1.35, 1.0), (width + 0.9, 0.0),
      (width - 1.2, -0.7), (width - 4.5, -0.95), (1.0, -0.7), (-0.4, -0.2), (0.2, 0.15)]
main = [to_svg(p) for p in word + fl]
acute = [to_svg(p) for p in [(3.25, 1.3), (3.55, 1.65)]]            # accent on the é (4th letter)
def bez(pts):  # Catmull-Rom -> dense samples
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]; p1, p2 = pts[i], pts[i + 1]; p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        for k in range(7):
            t = k / 7; u = 1 - t
            out.append((u**3*p1[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3*p2[0], u**3*p1[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3*p2[1]))
    out.append(pts[-1]); return out
NIB = math.radians(35)
def ink(pts, wmin=0.45, wmax=1.9):
    s = bez(pts); n = len(s); left, right = [], []
    for i in range(n):
        a, b = s[max(i - 1, 0)], s[min(i + 1, n - 1)]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        taper = min(1, i / 5, (n - 1 - i) / 7)                        # thin at both ends
        hw = (wmin + (wmax - wmin) * abs(math.sin(ang - NIB))) * (0.35 + 0.65 * taper) / 2
        nx, ny = -math.sin(ang), math.cos(ang)
        left.append((s[i][0] + nx * hw, s[i][1] + ny * hw)); right.append((s[i][0] - nx * hw, s[i][1] - ny * hw))
    poly = left + right[::-1]
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + "Z"
d = ink(main) + ink(acute, 0.5, 1.2)
xs = [p[0] for p in main]; ys = [p[1] for p in main]
from pathlib import Path
out = Path(__file__).resolve().parents[1] / "signature.json"
out.write_text(json.dumps({"d": d, "box": [round(min(xs)) - 4, round(min(ys)) - 4, round(max(xs) - min(xs)) + 8, round(max(ys) - min(ys)) + 8]}), encoding="utf-8")
print("dev/signature.json")
