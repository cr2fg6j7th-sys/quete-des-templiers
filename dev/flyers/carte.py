# Usage : python3 dev/flyers/carte.py marketing/flyers/flyer-a6-comptoir-parchemin.pdf sortie.pdf 100 150 0.98  (largeur, hauteur en mm, échelle)
# The A6 flyer on a 100 x 150 mm card (Bristol), filling it edge to edge: scaled to 98 %, the trim box centred;
# the burned edge loses 1.45 mm left and right, the bleed covers the top and bottom.
import sys, pikepdf
from pikepdf import Pdf, Page, Name, Dictionary
SRC, OUT, CW, CH, S = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
MM = 72 / 25.4
src = Pdf.open(SRC); p0 = src.pages[0]
mx0, my0, mx1, my1 = [float(v) for v in p0.mediabox]
tx0, ty0, tx1, ty1 = [float(v) for v in p0.trimbox]
W, H = CW * MM, CH * MM
tw, th = (tx1 - tx0) * S, (ty1 - ty0) * S
x, y = (W - tw) / 2, (H - th) / 2           # where the trim box lands
# the bleed must cover the card
assert x - (tx0 - mx0) * S <= 0.01 and y - (ty0 - my0) * S <= 0.01, "bleed too small"
out = Pdf.new()
form = out.copy_foreign(Page(p0).as_form_xobject())
page = out.add_blank_page(page_size=(W, H))
page.obj.Resources = Dictionary(XObject=Dictionary(F=form))
page.obj.Contents = out.make_stream(f"q 0 0 {W:.3f} {H:.3f} re W n {S:.6f} 0 0 {S:.6f} {x - tx0*S:.3f} {y - ty0*S:.3f} cm /F Do Q".encode())
out.docinfo["/Title"] = f"Ma Quête Légendaire - flyer parchemin {CW:g} x {CH:g} mm"
out.save(OUT)
print(f"carte {CW:g} x {CH:g} mm, flyer à {S*100:.0f} % : {tw/MM:.1f} x {th/MM:.1f} mm, rogné de {max(0,-(x/MM)):.2f} mm de chaque côté")
