# Knight on a rearing horse, facing left (towards the keep), for the right side of the parchment flyers
# (16/10/2026, Nathan). Smooth silhouettes; the helm slit and the cross on the shield are real holes.
#   from cavalier import rider_svg; rider_svg(cls="rider")   -> inline <svg>, hooves on the bottom edge
import math
INK, WAX, RED = "#3a2212", "#8f2a24", "#6e2a1c"

def smooth(pts, closed=True, t=.5):
    # Catmull-Rom through the points -> cubic Bezier path
    n = len(pts); P = pts
    rng = range(n) if closed else range(n - 1)
    d = f"M{P[0][0]:.2f} {P[0][1]:.2f}"
    for i in rng:
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        d += f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + ("Z" if closed else "")

def limb(pts, widths):
    # tapered limb along a polyline: offset both sides, then smooth the outline
    L, R = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; k = math.hypot(dx, dy)
        nx, ny = -dy / k, dx / k; w = widths[i] / 2
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    return smooth(L + R[::-1])

def hoof(prev, end, top=4.6, bot=6, h=4.4):
    # hoof growing out of the end of a leg, along the leg's direction
    dx, dy = end[0] - prev[0], end[1] - prev[1]; k = math.hypot(dx, dy); dx, dy = dx / k, dy / k
    nx, ny = -dy, dx
    q = [(end[0] + nx * top / 2 - dx, end[1] + ny * top / 2 - dy), (end[0] - nx * top / 2 - dx, end[1] - ny * top / 2 - dy),
         (end[0] - nx * bot / 2 + dx * h, end[1] - ny * bot / 2 + dy * h), (end[0] + nx * bot / 2 + dx * h, end[1] + ny * bot / 2 + dy * h)]
    return "M" + " L".join(f"{a:.2f} {b:.2f}" for a, b in q) + "Z"

def leg(pts, widths):
    return [limb(pts, widths), hoof(pts[-2], pts[-1], top=widths[-1] * 1.05, bot=widths[-1] * 1.35)]

BODY = [(16, 27), (19, 22), (27, 17), (37, 12.5), (46, 11), (51, 13.5), (55.5, 20.5), (59.5, 31), (64.5, 43), (70, 53),
        (78, 61), (86, 69), (94, 77), (100, 86), (104, 97), (103.5, 108), (98, 115), (88, 114), (76, 106), (64, 97),
        (56, 89), (50, 82), (46, 74), (44, 64), (42, 52), (41, 42), (40.5, 35), (37, 32.5), (29, 32.5), (21.5, 31.5), (17.5, 30.5)]
MANE = [(49, 12), (55, 13), (57.5, 17), (61, 20), (59, 23), (63.5, 28), (61.5, 31), (66.5, 37), (64.5, 40), (69.5, 46), (67.5, 49), (72.5, 54), (69, 56)]

def rider_svg(cls="rider"):
    legs = (leg([(50, 77), (31, 69), (28.5, 79), (27.5, 83.5)], [9, 5.8, 4.6, 4.3])
            + leg([(55, 85), (37.5, 82.5), (36, 92), (35.5, 96.5)], [9, 5.8, 4.6, 4.3])
            + leg([(92, 104), (97, 117), (99.5, 125), (96.5, 132), (95, 137)], [20, 10, 6.6, 5, 4.6])
            + leg([(77, 103), (82, 117), (84.5, 125), (81.5, 132), (80, 137)], [17, 9, 6.2, 4.8, 4.4]))
    horse = (f'<g fill="{INK}"><path d="{smooth(BODY)}"/><path d="{smooth(MANE, t=.3)}"/>'
             f'<path d="M42 13 43.5 3 47.5 12Z M46.5 13 50 4 51.5 14Z"/>'
             + "".join(f'<path d="{d}"/>' for d in legs) +
             '<path d="M99 88C111 89 120 100 120 113C120 122 122 128 126 133C115 131 108 122 107 112C106 105 103 100 97 97Z"/></g>'
             f'<path d="M69 54 21 30" stroke="{INK}" stroke-width=".9" fill="none"/>')
    rider = f"""<g fill="{INK}" fill-rule="evenodd">
 <path d="M73 27Q80 23 87 27L88 42H72Z M74.5 32h11v1.8h-11Z M79.2 33.8h1.6v6h-1.6Z"/>
 <path d="M71 43Q80 40 90 43L91 67Q82 71 72 67Z"/>
 <path d="M87 45 93 30 97 31 92 47Z"/>
 <path d="M93.6 29.5 84 1 86.2 0.2 96 28.6Z M89.5 30.5 100.5 26.5 101.3 28.5 90.3 32.5Z"/>
</g>
<path d="M80 25Q82 16 91 18Q85 20 83 26Z" fill="{WAX}"/>
<path d="M64 45Q72 42 80 45V57Q78 68 72 75Q66 68 64 57Z M70.8 48h2.4v8h5v2.4h-5v11h-2.4v-11h-5V56h5Z" fill="{RED}" fill-rule="evenodd"/>"""
    return f'<svg class="{cls}" viewBox="12 -4 116 146" aria-hidden="true">{horse}{rider}</svg>'
