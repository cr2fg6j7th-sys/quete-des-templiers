# "Parchemin" version of the two flyers (16/10/2026, Nathan): aged parchment, sepia ink, a keep guarded
# by two knights in silhouette, the Grand Master's red wax seal hanging from the QR card like on a charter.
#   python3 dev/flyers/parchemin.py
#   -> marketing/flyers/flyer-a6-comptoir-parchemin.pdf (A6 recto)
#   -> marketing/flyers/flyer-a5-restaurant-parchemin.pdf (A5 recto verso)
# The paper is a 300 dpi picture (parchemin_texture.py); text, drawings and QR codes stay vector.
import asyncio, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
import make as M
from parchemin_texture import parchment

H, ROOT, OUT, PREV, BLEED = M.H, M.ROOT, M.OUT, M.PREV, M.BLEED
INK, WAX, PAPER = "#3a2212", "#8f2a24", "#f2e4c2"

def qr(url):
    return M.qr(url).replace('fill="#fff"', 'fill="#fbf5e6"').replace('fill="#10142a"', f'fill="#24140a"')

# ---------- silhouettes (holes are real holes: fill-rule evenodd shows the paper) ----------
KNIGHT = f"""<g fill="{INK}" fill-rule="evenodd">
 <path d="M24 7Q35 1 46 7L47 31H23Z M27 15h16v2.4H27Z M34 17.4h2v9h-2Z"/>
 <path d="M30 31h10v3H30Z"/>
 <path d="M19 34Q35 31 51 34Q56 36 57 42L59 72Q57 75 54 73L52 50 53 98Q35 103 17 98L18 50 16 73Q13 75 11 72L13 42Q14 36 19 34Z M36 44h4v6h6v4h-6v12h-4v-12h-6v-4h6Z"/>
 <path d="M22 97h10l-1 38h-9Z M38 97h10v38h-9Z M17 135h15v5H16Z M38 135h15l1 5H38Z"/>
 <path d="M58.6 75h2.8v54l-1.4 7-1.4-7Z M52.5 71h14a1.4 1.4 0 0 1 0 2.8h-14a1.4 1.4 0 0 1 0-2.8Z M58.8 61h2.4v10h-2.4Z"/><circle cx="60" cy="59" r="2.6"/>
</g>
<path d="M36 3Q39-6 48-3Q41-1 39 5Z" fill="{WAX}"/>
<path d="M3 43Q15 38 28 43V62Q26 82 15.5 97Q5 82 3 62Z M14 47h3v13h7v3h-7v20h-3v-20H7v-3h7Z" fill="#6e2a1c" fill-rule="evenodd"/>"""

def knight(cls, flip=False):
    t = ' transform="translate(70 0) scale(-1 1)"' if flip else ""
    return f'<svg class="{cls}" viewBox="0 -8 70 150" aria-hidden="true"><g{t}>{KNIGHT}</g></svg>'

def keep_path():
    holes = []
    holes += [f"M{x} 42h3v4h-3Z" for x in range(29, 92, 6)]                       # machicolations
    holes += ["M58 62h4v15h-4Z", "M44 94h3v12h-3Z", "M73 94h3v12h-3Z",              # arrow slits
              "M58.5 116h3v6h4v3h-4v8h-3v-8h-4v-3h4Z",                              # cross loophole
              "M52 160V147a8 8 0 0 1 16 0V160Z"]                                    # door
    merlons = "".join(f"M{x} 24h6v12h-6Z" for x in range(26, 94, 10))
    walls = ("M0 160V120h4v-6h5v6h5v-6h5v6h5v-6h6V160Z M90 160V114h6v6h5v-6h5v6h5v-6h5v6h4V160Z")
    return (f'<path fill="{INK}" fill-rule="evenodd" d="M30 160V46H90V160Z M26 36H94V46H26Z {merlons} M68 24V7H82V24Z M66 7 75-12 84 7Z '
            f'{" ".join(holes)}"/><path fill="{INK}" d="{walls}"/>'
            f'<path d="M75-12V-23" stroke="{INK}" stroke-width="1.4"/><path d="M75-23l13 3.6-13 3.6Z" fill="{WAX}"/>')

def keep(cls):
    return f'<svg class="{cls}" viewBox="0 -26 120 186" aria-hidden="true">{keep_path()}</svg>'

def hill(cls):
    return (f'<svg class="{cls}" viewBox="0 0 300 30" preserveAspectRatio="none" aria-hidden="true">'
            f'<path d="M0 30V22Q40 12 90 14T170 10T240 14T300 20V30Z" fill="{INK}"/>'
            f'<path d="M14 24q30-9 70-8M200 15q40-2 80 6" stroke="{PAPER}" stroke-opacity=".35" stroke-width=".8" fill="none"/></svg>')

def seal(cls, text=None):
    s = M.SEAL_PATH
    inner = ('<circle r="17" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.2"/>'
             '<path d="M-1.6-1.6-5-12H5L1.6-1.6 12-5V5L1.6 1.6 5 12H-5L-1.6 1.6-12 5V-5Z" fill="#f6e3c0" fill-opacity=".9"/>') if not text else \
            '<circle r="21.5" fill="none" stroke="#f6e3c0" stroke-opacity=".55" stroke-width=".9" stroke-dasharray="2 1.6"/>'
    tails = (f'<path d="M-9 14 -16 44 -11 40 -7 46 -2 16Z" fill="{WAX}"/><path d="M9 14 16 44 11 40 7 46 2 16Z" fill="#7a221d"/>')
    svg = (f'<svg viewBox="-30 -30 60 78" aria-hidden="true">{tails}'
           f'<path d="{s}" transform="translate(1.2 1.6)" fill="#4a1410"/><path d="{s}" fill="{WAX}"/>{inner}</svg>')
    txt = f'<div class="stxt">{text}</div>' if text else ""
    return f'<div class="{cls}">{svg}{txt}</div>'

BASE = """
:root{--ink:#3a2212;--wax:#8f2a24;--paper:#f2e4c2;--sepia:#6b4a2b}
*{box-sizing:border-box;margin:0}
html,body{width:@PWmm;height:@PHmm;overflow:hidden;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{position:relative;font-family:"Alegreya Sans",sans-serif;color:var(--ink)}
@page{size:@PWmm @PHmm;margin:0}
.paperbg{position:absolute;inset:0;width:100%;height:100%}
.trim{position:absolute;left:3mm;top:3mm;width:@TWmm;height:@THmm}
.rule{position:absolute;border:.35mm solid rgba(58,34,18,.75)}
.rule::after{content:"";position:absolute;inset:.8mm;border:.15mm solid rgba(58,34,18,.55)}
.dia{position:absolute;width:2.2mm;height:2.2mm;background:var(--ink);transform:translate(-50%,-50%) rotate(45deg)}
.center{position:absolute;left:0;right:0;display:flex;flex-direction:column;align-items:center;text-align:center}
.brand{font-family:"UnifrakturMaguntia",serif;color:var(--wax);line-height:1}
.oyez{font-style:italic;color:var(--sepia);line-height:1}
.ribbon{position:relative;z-index:0;display:inline-block;background:var(--wax);color:#f8ead0;font-family:"Alegreya Sans SC",sans-serif;font-weight:700;letter-spacing:.05em;line-height:1;white-space:nowrap}
.ribbon::before,.ribbon::after{content:"";position:absolute;top:22%;bottom:-22%;width:2.4mm;background:#5e1a16;z-index:-1}
.ribbon::before{clip-path:polygon(0 0,100% 0,100% 100%,0 100%,45% 50%)}
.ribbon::after{clip-path:polygon(0 0,100% 0,55% 50%,100% 100%,0 100%)}
h1{font-family:"UnifrakturMaguntia",serif;font-weight:400;line-height:1.02;color:var(--ink)}
h1 .ini{color:var(--wax)}
.sub{font-style:italic;color:var(--ink)}
.knight,.keep,.hill{position:absolute;display:block}
.card{position:absolute;display:flex;align-items:center;background:rgba(251,243,223,.78);border:.4mm solid var(--ink);color:var(--ink)}
.card::after{content:"";position:absolute;inset:.8mm;border:.15mm solid rgba(58,34,18,.6);pointer-events:none}
.card .qr{flex:none;display:block;position:relative;z-index:1}
.card .kick{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;letter-spacing:.1em;color:var(--wax);line-height:1}
.card .say{font-weight:800;line-height:1.1}
.card .url{font-weight:900;line-height:1}
.seal{position:absolute;z-index:2}
.seal svg{display:block;width:100%;height:100%}
.seal .stxt{position:absolute;left:0;right:0;top:0;aspect-ratio:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fbefd6;line-height:1}
.facts{position:absolute;left:0;right:0;text-align:center;color:var(--ink);line-height:1.25}
"""

def page(w, h, css, body, paper_img):
    css0 = BASE.replace("@PW", str(w + 2 * BLEED)).replace("@PH", str(h + 2 * BLEED)).replace("@TW", str(w)).replace("@TH", str(h))
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{M.FONTS}{css0}{css}</style></head>'
            f'<body><img class="paperbg" src="{Path(paper_img).as_uri()}" alt="">{body}</body></html>')

def rule(inset, w, h):
    d = "".join(f'<div class="dia" style="left:{x}mm;top:{y}mm"></div>' for x in (inset, w - inset) for y in (inset, h - inset))
    return f'<div class="rule" style="left:{inset}mm;top:{inset}mm;right:{inset}mm;bottom:{inset}mm"></div>{d}'

HEAD = """<div class="center" style="top:{b}mm"><div class="brand">Ma Quête Légendaire</div></div>
<div class="center" style="top:{o}mm"><div class="oyez">Oyez, oyez, jeunes chevaliers&#8239;!</div></div>
<div class="center" style="top:{r}mm"><span class="ribbon">Pour des fêtes d'enfants réussies · de 7 à 10 ans</span></div>
<div class="center" style="top:{t}mm"><h1><span class="ini">U</span>ne vraie quête<br>de chevaliers</h1><div class="sub">dans les rues de votre ville</div></div>"""

def a6(paper):
    w, h = 105, 148
    css = """
.brand{font-size:13.5pt}.oyez{font-size:9.6pt}
.ribbon{font-size:6.9pt;padding:1.5mm 3mm 1.3mm}.ribbon::before{left:-1.9mm}.ribbon::after{right:-1.9mm}
h1{font-size:27pt}h1 .ini{font-size:33pt}.sub{font-size:10.6pt;margin-top:1.4mm}
.keep{left:35.5mm;top:56mm;width:34mm;height:52.7mm}
.knight{top:71.5mm;width:17.5mm;height:37.5mm}.k1{left:12mm}.k2{right:12mm}
.hill{left:7.5mm;right:7.5mm;width:90mm;top:103.5mm;height:6mm}
.card{left:9mm;right:9mm;top:110mm;height:25.4mm;padding:1.8mm 2.4mm;gap:2.8mm}
.card .qr{width:21.8mm;height:21.8mm}
.card .kick{font-size:6.8pt}.card .say{font-size:8.8pt;margin-top:1.1mm;padding-right:9mm}.card .url{font-size:9.8pt;margin-top:1.6mm}
.seal{right:5.5mm;top:103mm;width:14mm;height:18.2mm}
.facts{top:136.3mm;font-size:6.5pt}
"""
    body = f"""<div class="trim">
{rule(7, w, h)}
{HEAD.format(b=10.2, o=16.6, r=20.6, t=27.6)}
{keep("keep")}{knight("knight k1")}{knight("knight k2", flip=True)}{hill("hill")}
<div class="card">{qr(M.SITE + "/?ref=f-comptoir")}<div>
  <div class="kick">Aperçu gratuit</div>
  <div class="say">Scannez, tapez son prénom&#8239;: le Grand Maître l'appelle&#8239;!</div>
  <div class="url">maquetelegendaire.fr</div></div></div>
{seal("seal")}
<div class="facts">4 à 15 enfants · environ 1 h · 24,90&#8239;€ pour tout le groupe</div>
</div>"""
    return page(w, h, css, body, paper)

def a5_recto(paper):
    w, h = 148, 210
    css = """
.brand{font-size:19pt}.oyez{font-size:13.4pt}
.ribbon{font-size:9.6pt;padding:2mm 4.4mm 1.8mm}.ribbon::before{left:-2.4mm;width:3.2mm}.ribbon::after{right:-2.4mm;width:3.2mm}
h1{font-size:38pt}h1 .ini{font-size:46pt}.sub{font-size:14.6pt;margin-top:2mm}
.keep{left:50mm;top:80mm;width:48mm;height:74.4mm}
.knight{top:101mm;width:24.5mm;height:52.5mm}.k1{left:18mm}.k2{right:18mm}
.hill{left:10mm;right:10mm;width:128mm;top:147mm;height:8.5mm}
.points{position:absolute;left:0;right:0;top:156.6mm;text-align:center;font-style:italic;font-size:10pt;color:var(--ink)}
.points b{color:var(--wax);font-style:normal;margin:0 2.2mm}
.card{left:13mm;right:13mm;top:164mm;height:30.5mm;padding:2.4mm 3mm;gap:4mm}
.card .qr{width:25.5mm;height:25.5mm}
.card .kick{font-size:8.6pt}.card .say{font-size:11.4pt;margin-top:1.4mm;padding-right:16mm}.card .url{font-size:13pt;margin-top:2mm}
.seal{right:6mm;top:159.5mm;width:26mm;height:33.8mm;transform:rotate(-8deg)}
.seal .b1{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:7pt;letter-spacing:.08em}
.seal .b2{font-weight:900;font-size:12.4pt;margin:.6mm 0 .4mm}
.seal .b3{font-size:6.8pt;font-style:italic}
.facts{top:196.2mm;font-size:8.2pt}
"""
    body = f"""<div class="trim">
{rule(8.5, w, h)}
{HEAD.format(b=14.5, o=24.5, r=30.5, t=38.5)}
{keep("keep")}{knight("knight k1")}{knight("knight k2", flip=True)}{hill("hill")}
<div class="points">Au prénom de l'enfant<b>✦</b>Prête en 2 minutes<b>✦</b>Il pleut&#8239;? À la maison</div>
<div class="card">{qr(M.SITE + "/?ref=f-restaurant")}<div>
  <div class="kick">Aperçu gratuit</div>
  <div class="say">Scannez, tapez le prénom de votre enfant&#8239;: le Grand Maître l'appelle&#8239;!</div>
  <div class="url">maquetelegendaire.fr</div></div></div>
{seal("seal", '<span class="b1">Les enfants&#8239;:</span><span class="b2">jeux au dos</span><span class="b3">retourne-moi&#8239;!</span>')}
<div class="facts">4 à 15 enfants · environ 1 h · 24,90&#8239;€ pour tout le groupe, sans animateur</div>
</div>"""
    return page(w, h, css, body, paper)

def a5_verso(paper):
    w, h = 148, 210
    css = """
h2{font-family:"UnifrakturMaguntia",serif;font-weight:400;font-size:28pt;line-height:1;color:var(--ink)}
h2 .ini{color:var(--wax);font-size:34pt}
.lead{font-size:10.4pt;font-style:italic;margin-top:1.6mm}
.lead b{color:var(--wax);font-style:normal}
.grid{position:absolute;left:10mm;right:10mm;top:31mm;bottom:20mm;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:4mm}
.box{position:relative;border:.45mm solid var(--ink);border-radius:1.6mm;background:rgba(253,248,234,.62);padding:7mm 3.2mm 2.8mm;display:flex;flex-direction:column;align-items:center;gap:1.6mm}
.box::after{content:"";position:absolute;inset:.7mm;border:.15mm solid rgba(58,34,18,.5);border-radius:1.1mm;pointer-events:none}
.num{position:absolute;left:3mm;top:-3.3mm;z-index:1;background:var(--wax);color:#f8ead0;font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:9.2pt;letter-spacing:.06em;padding:1.1mm 2.6mm .9mm;border-radius:1mm;white-space:nowrap}
.ask{font-size:9.6pt;line-height:1.3;align-self:stretch}
.ask i{color:var(--sepia)}
.maze{width:62mm;height:48.2mm;margin-top:1mm}
.words{display:grid;grid-template-columns:repeat(8,5.6mm);border:.4mm solid var(--ink);font-weight:800;font-size:10.4pt;text-align:center;line-height:5.6mm;background:rgba(255,252,242,.6)}
.riddle{font-style:italic;font-size:10.2pt;line-height:1.32;align-self:stretch}
.blanks{font-size:15pt;font-weight:800;letter-spacing:2.2mm;align-self:stretch;margin:.6mm 0 1.2mm}
.sec{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:9.2pt;letter-spacing:.06em;color:var(--wax);align-self:stretch;border-top:.3mm dashed rgba(58,34,18,.5);padding-top:2mm}
.tiles{display:flex;gap:2mm;align-self:stretch}
.tiles span{width:10mm;height:11.6mm;border-radius:1mm;background:rgba(255,250,236,.85);border:.4mm solid var(--ink);display:flex;align-items:center;justify-content:center;font-family:"Alegreya Sans",sans-serif;font-weight:900;font-size:21pt;line-height:1;padding-top:.6mm}
.tiles i{width:10mm;height:10mm;border-bottom:.5mm solid var(--ink)}
.shield{flex:1 1 0;min-height:0;width:100%}
.foot{position:absolute;left:10mm;right:10mm;bottom:9mm;display:flex;align-items:center;justify-content:space-between;font-size:8.6pt}
.foot .brand{font-size:12pt}
.foot .ans{transform:rotate(180deg);color:var(--sepia);font-size:7.6pt}
"""
    maze = (H / "svg" / "labyrinthe-1.svg").read_text().replace("<svg ", '<svg class="maze" ', 1).replace("#1b2547", INK).replace("#b8505c", M.SEAL_PATH and WAX)
    shield = (H / "svg" / "armoiries.svg").read_text().replace("<svg ", '<svg class="shield" ', 1).replace("#1b2547", INK).replace('fill="#fff"', 'fill="#fdf7e8"')
    letters = "".join(f"<span>{c}</span>" for row in M.GRID for c in row)
    body = f"""<div class="trim">
<div class="center" style="top:10mm"><h2><span class="ini">L</span>es épreuves du chevalier</h2>
  <div class="lead">Réussis les <b>quatre épreuves</b>, puis montre ta feuille à un adulte&#8239;!</div></div>
<div class="grid">
  <div class="box"><span class="num">1 · Le labyrinthe</span><div class="ask">Guide le chevalier jusqu'au château.</div>{maze}</div>
  <div class="box"><span class="num">2 · Les mots cachés</span><div class="words">{letters}</div>
    <div class="ask">Trouve&#8239;: <b>ÉPÉE · ROI · CASQUE · TOUR · DRAGON</b> <i>(de gauche à droite, de haut en bas ou en biais)</i></div></div>
  <div class="box"><span class="num">3 · L'énigme du Grand Maître</span>
    <div class="riddle">«&#8239;Je suis la tour la plus haute et la plus solide du château. Qui suis-je&#8239;?&#8239;»</div>
    <div class="blanks">_ _ _ _ _ _</div>
    <div class="sec">Le mot secret</div>
    <div class="ask">Remets les lettres dans l'ordre&#8239;: c'est l'arme du chevalier.</div>
    <div class="tiles"><span>P</span><span>E</span><span>É</span><span>É</span></div>
    <div class="tiles"><i></i><i></i><i></i><i></i></div></div>
  <div class="box"><span class="num">4 · Ton blason</span><div class="ask">Colorie-le, puis écris ta devise sur la banderole.</div>{shield}</div>
</div>
<div class="foot"><div class="ans">Réponses&#8239;: le donjon · ÉPÉE</div><div><span class="brand">Ma Quête Légendaire</span> · maquetelegendaire.fr</div></div>
</div>"""
    return page(w, h, css, body, paper)

async def main():
    M.check_grid()
    OUT.mkdir(parents=True, exist_ok=True); PREV.mkdir(parents=True, exist_ok=True)
    tex = PREV / "_papier"; tex.mkdir(exist_ok=True)
    pa6 = parchment(111, 154, tex / "a6.jpg", seed=7)
    pa5 = parchment(154, 216, tex / "a5r.jpg", seed=5)
    pa5v = parchment(154, 216, tex / "a5v.jpg", seed=11, light=True)
    jobs = {"flyer-a6-comptoir-parchemin": [("recto", a6(pa6))],
            "flyer-a5-restaurant-parchemin": [("recto", a5_recto(pa5)), ("verso", a5_verso(pa5v))]}
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        for out, faces in jobs.items():
            w = PdfWriter()
            for face, html in faces:
                pdf, _ = await M.render(pg, html, f"{out}-{face}")
                for pp in PdfReader(str(pdf)).pages: w.add_page(pp)
                subprocess.run(["pdftoppm", "-r", "110", "-png", "-singlefile", str(pdf), str(PREV / f"{out}-{face}")], check=True)
                pdf.unlink()
            tw, th = (105, 148) if "a6" in out else (148, 210)
            mm = 72 / 25.4
            for pp in w.pages:
                top = float(pp.mediabox.top)
                W, Hh = (tw + 2 * BLEED) * mm, (th + 2 * BLEED) * mm
                box = RectangleObject([0, top - Hh, W, top])
                pp.mediabox = box; pp.cropbox = box; pp.bleedbox = box
                pp.trimbox = RectangleObject([BLEED * mm, top - Hh + BLEED * mm, W - BLEED * mm, top - BLEED * mm])
            w.compress_identical_objects()
            fmt = "A6 recto" if "a6" in out else "A5 recto verso"
            w.add_metadata({"/Title": f"Ma Quête Légendaire — flyer {fmt} (parchemin)", "/Author": "Ma Quête Légendaire"})
            w.write(str(OUT / f"{out}.pdf")); print(out, len(w.pages), "page(s)")
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
