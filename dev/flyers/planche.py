# Usage : python3 dev/flyers/planche.py marketing/flyers/flyer-a6-comptoir-parchemin.pdf dist/flyers/flyers-A6-parchemin-4-par-feuille-A4.pdf
# 4 A6 flyers on one A4 sheet, for a home printer: each scaled to 96 mm wide (91.4 %), abutting (one cut in each
# direction), 2 mm of bleed on the outer sides, crop marks in the margins, a printing note at the bottom.
import sys, pikepdf
from pikepdf import Pdf, Page, Name, Dictionary, Array
SRC, OUT = sys.argv[1], sys.argv[2]
MM = 72 / 25.4
A4W, A4H = 210 * MM, 297 * MM
src = Pdf.open(SRC)
p0 = src.pages[0]
tx0, ty0, tx1, ty1 = [float(v) for v in p0.trimbox]
tw, th = tx1 - tx0, ty1 - ty0
W = 96 * MM; s = W / tw; H = th * s; B = 2 * MM
X0 = (A4W - 2 * W) / 2; Y0 = (A4H - 2 * H) / 2 + 3 * MM   # a little higher: room for the note at the bottom
out = Pdf.new()
form = out.copy_foreign(Page(p0).as_form_xobject())
font = Dictionary(Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica, Encoding=Name.WinAnsiEncoding)
ops = []
for col in (0, 1):
    for row in (0, 1):   # row 0 at the top
        x, y = X0 + col * W, Y0 + (1 - row) * H
        cx0 = x - (B if col == 0 else 0); cx1 = x + W + (B if col == 1 else 0)
        cy0 = y - (B if row == 1 else 0); cy1 = y + H + (B if row == 0 else 0)
        ops.append(f"q {cx0:.3f} {cy0:.3f} {cx1-cx0:.3f} {cy1-cy0:.3f} re W n {s:.6f} 0 0 {s:.6f} {x - tx0*s:.3f} {y - ty0*s:.3f} cm /F Do Q")
# crop marks: thin black lines in the margins, clear of the bleed
ops.append("q 0 G 0.4 w")
top, bot = Y0 + 2 * H, Y0
for xv in (X0, X0 + W, X0 + 2 * W):
    ops.append(f"{xv:.3f} {top + B + 1*MM:.3f} m {xv:.3f} {top + B + 7*MM:.3f} l S")
    ops.append(f"{xv:.3f} {bot - B - 1*MM:.3f} m {xv:.3f} {bot - B - 7*MM:.3f} l S")
for yv in (Y0, Y0 + H, Y0 + 2 * H):
    ops.append(f"{X0 - B - 0.8*MM:.3f} {yv:.3f} m {max(X0 - B - 6*MM, 1*MM):.3f} {yv:.3f} l S")
    ops.append(f"{X0 + 2*W + B + 0.8*MM:.3f} {yv:.3f} m {min(X0 + 2*W + B + 6*MM, A4W - 1*MM):.3f} {yv:.3f} l S")
ops.append("Q")
note = "Imprimer en taille r\xe9elle (100 %), recto seul, qualit\xe9 \xe9lev\xe9e. Couper sur les traits : 4 flyers de 96 x 135 mm."
ops.append(f"BT /H 7 Tf 0.3 g {X0:.3f} {bot - B - 11*MM:.3f} Td ({note}) Tj ET")
content = ("\n".join(ops)).encode("cp1252")
page = out.add_blank_page(page_size=(A4W, A4H))
page.obj.Resources = Dictionary(XObject=Dictionary(F=form), Font=Dictionary(H=out.make_indirect(font)))
page.obj.Contents = out.make_stream(content)
out.docinfo["/Title"] = "Ma Quête Légendaire - flyers A6 parchemin, 4 par feuille A4"
out.save(OUT)
print(f"scale {s:.4f}, flyer {W/MM:.1f} x {H/MM:.1f} mm, margins x {X0/MM:.1f} mm, y {Y0/MM:.1f} / {(A4H-Y0-2*H)/MM:.1f} mm")
