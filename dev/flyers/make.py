# Flyers to print (16/10/2026, Nathan): one model per format, made to be seen on a counter.
#   A6 (105 x 148 mm), recto only, for every counter       -> marketing/flyers/flyer-a6-comptoir.pdf
#   A5 (148 x 210 mm), recto + kids' games on the verso,   -> marketing/flyers/flyer-a5-restaurant.pdf
#   for restaurants (turn over on the long edge)
# Each file has 3 mm of bleed on every side; text and QR codes stay vector, fonts are embedded.
#   python3 dev/flyers/make.py           (Playwright's Chromium + pypdf + OpenCV)
# Previews (PNG) go to dist/flyers/. The QR codes are read back before anything is written.
import asyncio, re, subprocess
from pathlib import Path
import cv2
import numpy as np
from playwright.async_api import async_playwright
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
OUT, PREV = ROOT / "marketing" / "flyers", ROOT / "dist" / "flyers"
SITE = "https://maquetelegendaire.fr"
BLEED = 3

# ---------- QR codes (vector path, read back) ----------
def qr(url):
    p = cv2.QRCodeEncoder.Params()
    p.correction_level = cv2.QRCODE_ENCODER_CORRECT_LEVEL_M
    m = cv2.QRCodeEncoder.create(p).encode(url)
    dark = m < 128
    ys, xs = np.where(dark)
    dark = dark[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    n = dark.shape[0]
    d = []
    for y, row in enumerate(dark):
        x = 0
        while x < n:
            if row[x]:
                k = 1
                while x + k < n and row[x + k]: k += 1
                d.append(f"M{x} {y}h{k}v1h-{k}z"); x += k
            else: x += 1
    img = np.full(((n + 8) * 10, (n + 8) * 10), 255, np.uint8)
    for y, x in zip(*np.where(dark)): img[(y + 4) * 10:(y + 5) * 10, (x + 4) * 10:(x + 5) * 10] = 0
    assert cv2.QRCodeDetector().detectAndDecode(img)[0] == url, "QR code illisible : " + url
    return (f'<svg class="qr" viewBox="-2 -2 {n + 4} {n + 4}" shape-rendering="crispEdges" role="img" aria-label="QR code">'
            f'<rect x="-2" y="-2" width="{n + 4}" height="{n + 4}" fill="#fff"/><path d="{"".join(d)}" fill="#10142a"/></svg>')

# ---------- drawings ----------
SEAL_PATH = (H / "svg" / "sceau-bord.txt").read_text().strip()
def seal(cls="seal"):
    return (f'<svg class="{cls}" viewBox="-30 -30 60 60" aria-hidden="true">'
            f'<path d="{SEAL_PATH}" transform="translate(1.2 1.6)" fill="#5e1f2a"/>'
            f'<path d="{SEAL_PATH}" fill="#b8505c"/>'
            '<circle r="17" fill="none" stroke="#fff" stroke-opacity=".38" stroke-width="1.2"/>'
            '<path d="M-1.6-1.6-5-12H5L1.6-1.6 12-5V5L1.6 1.6 5 12H-5L-1.6 1.6-12 5V-5Z" fill="#fff" fill-opacity=".92"/></svg>')

# one sword, point up, in a 24 x 130 box; two of them are crossed behind the seal
SWORD = ('<g><path d="M12 0 16.5 10V88H7.5V10Z" fill="url(#blade)" stroke="#8a6418" stroke-width=".8"/>'
         '<path d="M12 8V86" stroke="#8a6418" stroke-width=".9" opacity=".7"/>'
         '<path d="M0 88h24a2.5 2.5 0 0 1 0 5H0a2.5 2.5 0 0 1 0-5z" fill="#e3b95c" stroke="#8a6418" stroke-width=".8"/>'
         '<rect x="9.2" y="93" width="5.6" height="24" rx="2" fill="#7a2a33" stroke="#4d1720" stroke-width=".7"/>'
         '<circle cx="12" cy="121.5" r="5" fill="#e3b95c" stroke="#8a6418" stroke-width=".8"/></g>')
def emblem(cls="emblem"):
    return (f'<div class="{cls}"><svg class="swords" viewBox="-70 -70 140 140" aria-hidden="true">'
            '<defs><linearGradient id="blade" x1="0" x2="1"><stop offset="0" stop-color="#fff4d6"/><stop offset=".5" stop-color="#f0d38c"/><stop offset="1" stop-color="#c99a3a"/></linearGradient></defs>'
            f'<g transform="rotate(-38) translate(-12 -68)">{SWORD}</g><g transform="rotate(38) translate(-12 -68)">{SWORD}</g></svg>'
            f'{seal()}</div>')

# a castle at night, lit windows; drawn on a 300 x 80 box, ground at y = 80
CASTLE = ('<svg class="castle" viewBox="0 0 300 80" preserveAspectRatio="xMidYMax meet" aria-hidden="true"><g fill="#0b0e20">'
  # left tower, roof and flag
  '<path d="M30 80V30h28v50z"/><path d="M26 31 44 4 62 31z"/><path d="M44 4V-8" stroke="#0b0e20" stroke-width="1.6"/>'
  # left wall with merlons
  '<path d="M58 80V48h6v-5h6v5h6v-5h6v5h6v-5h6v5h6v-5h6v5h6v-5h6v5h4v32z"/>'
  # keep
  '<path d="M112 80V22h8v-7h8v7h8v-7h8v7h8v-7h8v7h8v-7h8v7h8v58z"/>'
  # right wall
  '<path d="M188 80V48h4v-5h6v5h6v-5h6v5h6v-5h6v5h6v-5h6v5h6v-5h6v5h4v32z"/>'
  # right tower, roof and flag
  '<path d="M242 80V30h28v50z"/><path d="M238 31 256 4 274 31z"/><path d="M256 4V-8" stroke="#0b0e20" stroke-width="1.6"/>'
  # little towers at both ends and the ground
  '<path d="M0 80V56h14v-4h4v4h4v-4h4v4h4v28zM270 80V56h4v-4h4v4h4v-4h4v4h14v24z"/><rect x="-20" y="78" width="340" height="40"/></g>'
  # pennants
  '<path d="M44 -8l13 4-13 4z" fill="#b8505c"/><path d="M256 -8l13 4-13 4z" fill="#b8505c"/>'
  # gate (arched, slightly lighter) and lit windows
  '<path d="M140 80V62a10 10 0 0 1 20 0v18z" fill="#1d2448"/>'
  '<g fill="#f0c766"><path d="M41 44h6v-5a3 3 0 0 0-6 0zM253 44h6v-5a3 3 0 0 0-6 0zM126 42h6v-6a3 3 0 0 0-6 0zM168 42h6v-6a3 3 0 0 0-6 0zM147 38h6v-7a3 3 0 0 0-6 0z"/>'
  '<path d="M41 62h6v-4a3 3 0 0 0-6 0zM253 62h6v-4a3 3 0 0 0-6 0z" opacity=".75"/></g></svg>')

def stars(spec):
    # spec: list of (left %, top mm, size mm, opacity)
    out = []
    for l, t, s, o in spec:
        out.append(f'<svg class="star" style="left:{l}%;top:{t}mm;width:{s}mm;height:{s}mm;opacity:{o}" viewBox="-10 -10 20 20" aria-hidden="true">'
                   '<path d="M0-10 2.2-2.2 10 0 2.2 2.2 0 10-2.2 2.2-10 0-2.2-2.2z" fill="#f3d27e"/></svg>')
    return "".join(out)

def font(name, file, weight, style="normal"):
    return f'@font-face{{font-family:"{name}";src:url("{file}");font-weight:{weight};font-style:{style}}}'

F = (ROOT / "fonts").as_uri(); FF = (H / "fonts").as_uri()
FONTS = "".join([
    font("UnifrakturMaguntia", f"{F}/UnifrakturMaguntia-Book.woff", 400),
    font("Alegreya Sans", f"{F}/AlegreyaSans-Regular.woff", 400), font("Alegreya Sans", f"{F}/AlegreyaSans-Italic.woff", 400, "italic"),
    font("Alegreya Sans", f"{F}/AlegreyaSans-Medium.woff", 500), font("Alegreya Sans", f"{F}/AlegreyaSans-Bold.woff", 700),
    font("Alegreya Sans", f"{FF}/AlegreyaSans-ExtraBold.ttf", 800), font("Alegreya Sans", f"{FF}/AlegreyaSans-Black.ttf", 900),
    font("Alegreya Sans", f"{FF}/AlegreyaSans-BlackItalic.ttf", 900, "italic"),
    font("Alegreya Sans SC", f"{F}/AlegreyaSansSC-Bold.woff", 700), font("Alegreya Sans SC", f"{F}/AlegreyaSansSC-Medium.woff", 500)])

BASE = """
:root{--night:#10142a;--gold:#e3b95c;--gold-d:#a87a1f;--cream:#f8f1e1;--wax:#b8505c;--wax-l:#e58b95;--ink:#1b2547;--muted:#4a516f}
*{box-sizing:border-box;margin:0}
html,body{width:@PWmm;height:@PHmm;overflow:hidden;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{position:relative;font-family:"Alegreya Sans",sans-serif;color:var(--cream)}
@page{size:@PWmm @PHmm;margin:0}
.bleed{position:absolute;inset:0}
.trim{position:absolute;left:3mm;top:3mm;width:@TWmm;height:@THmm}
.night{background:radial-gradient(120% 75% at 50% 30%,#2b3570 0%,#1a2150 38%,#10142a 72%,#0b0e20 100%)}
.glow{position:absolute;left:0;right:0;background:radial-gradient(60% 100% at 50% 100%,rgba(229,139,149,.38),rgba(229,139,149,0) 70%)}
.frame{position:absolute;border:.45mm solid var(--gold);border-radius:1.5mm}
.frame::after{content:"";position:absolute;inset:.9mm;border:.18mm solid rgba(227,185,92,.65);border-radius:1mm}
.corner{position:absolute;width:2.6mm;height:2.6mm;background:var(--gold);transform:translate(-50%,-50%) rotate(45deg)}
.star{position:absolute;transform:translate(-50%,-50%)}
.center{position:absolute;left:0;right:0;display:flex;flex-direction:column;align-items:center;text-align:center}
.brand{font-family:"UnifrakturMaguntia",serif;color:var(--cream);line-height:1}
.ribbon{position:relative;z-index:0;display:inline-block;background:var(--wax);color:#fff;font-family:"Alegreya Sans SC",sans-serif;font-weight:700;letter-spacing:.12em;line-height:1}
.ribbon::before,.ribbon::after{content:"";position:absolute;top:22%;bottom:-22%;width:2.4mm;background:#8f3a45;z-index:-1}
h1{font-weight:900;line-height:1;letter-spacing:-.01em;color:var(--cream)}
h1 em{font-style:normal;color:var(--gold)}
.sub{font-style:italic;color:#f3e6c6}
.emblem{position:absolute;left:50%;transform:translateX(-50%)}
.emblem .swords{position:absolute;inset:0;width:100%;height:100%}
.emblem .seal{position:absolute;left:21%;top:21%;width:58%;height:58%}
.castle{position:absolute;left:0;width:100%;display:block;overflow:visible}
.ground{position:absolute;left:-3mm;right:-3mm;bottom:-3mm;background:#0b0e20}
.card{position:absolute;background:var(--cream);color:var(--ink);display:flex;align-items:center;border:.4mm solid var(--gold)}
.card .qr{flex:none;display:block}
.card .kick{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;letter-spacing:.1em;color:var(--wax);line-height:1}
.card .say{font-weight:800;line-height:1.08}
.card .url{font-weight:900;color:var(--ink);letter-spacing:-.005em;line-height:1}
.facts{position:absolute;left:0;right:0;text-align:center;color:#e9dfc6;line-height:1.25}
"""

def page(w, h, css, body, bg="night"):
    css0 = BASE.replace("@PW", str(w + 2 * BLEED)).replace("@PH", str(h + 2 * BLEED)).replace("@TW", str(w)).replace("@TH", str(h))
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{FONTS}{css0}{css}</style></head>'
            f'<body><div class="bleed {bg}"></div>{body}</body></html>')

def frame(inset, w, h):
    c = "".join(f'<div class="corner" style="left:{x}mm;top:{y}mm"></div>' for x in (inset, w - inset) for y in (inset, h - inset))
    return f'<div class="frame" style="left:{inset}mm;top:{inset}mm;right:{inset}mm;bottom:{inset}mm"></div>{c}'

# ---------- A6, recto only ----------
def a6():
    w, h = 105, 148
    css = """
.brand{font-size:15pt}
.ribbon{font-size:7.2pt;padding:1.5mm 3.4mm 1.3mm}
.ribbon::before{left:-1.9mm;clip-path:polygon(0 0,100% 0,100% 100%,0 100%,45% 50%)}
.ribbon::after{right:-1.9mm;clip-path:polygon(0 0,100% 0,55% 50%,100% 100%,0 100%)}
h1{font-size:27pt}
.sub{font-size:11pt;margin-top:1.6mm}
.emblem{top:54mm;width:39mm;height:39mm}
.castle{top:76mm;height:28mm}
.ground{top:103.6mm}
.glow{top:62mm;height:42mm}
.card{left:7mm;right:7mm;top:107mm;height:29mm;border-radius:2.4mm;padding:2.2mm;gap:3mm}
.card .qr{width:24.6mm;height:24.6mm}
.card .kick{font-size:7pt}
.card .say{font-size:9.6pt;margin-top:1.3mm}
.card .url{font-size:10.4pt;margin-top:1.8mm}
.facts{top:137.6mm;font-size:6.6pt}
"""
    body = f"""<div class="trim">
{stars([(14,22,2.6,.9),(86,26,2.2,.8),(9,47,1.6,.6),(91,52,2.8,.85),(22,63,1.8,.7),(79,66,1.6,.6),(30,10.5,1.4,.5),(70,11,1.4,.5)])}
<div class="glow"></div>
{emblem()}
<div class="ground"></div>
{CASTLE}
{frame(4, w, h)}
<div class="center" style="top:8.6mm"><div class="brand">Ma Quête Légendaire</div></div>
<div class="center" style="top:16.4mm"><span class="ribbon">Anniversaire · 7 à 10 ans</span></div>
<div class="center" style="top:24mm"><h1>Une vraie quête<br><em>de chevaliers</em></h1><div class="sub">dans les rues de votre ville</div></div>
<div class="card"><QR/><div>
  <div class="kick">Aperçu gratuit</div>
  <div class="say">Scannez, tapez son prénom&#8239;: le Grand Maître l'appelle&#8239;!</div>
  <div class="url">maquetelegendaire.fr</div></div></div>
<div class="facts">4 à 15 enfants · environ 1 h · 24,90&#8239;€ pour tout le groupe</div>
</div>"""
    return page(w, h, css, body.replace("<QR/>", qr(SITE + "/?ref=f-comptoir")))

# ---------- A5, recto ----------
def a5_recto():
    w, h = 148, 210
    css = """
.brand{font-size:21pt}
.ribbon{font-size:10pt;padding:2.1mm 4.8mm 1.8mm}
.ribbon::before{left:-2.2mm;width:3.2mm;clip-path:polygon(0 0,100% 0,100% 100%,0 100%,45% 50%)}
.ribbon::after{right:-2.2mm;width:3.2mm;clip-path:polygon(0 0,100% 0,55% 50%,100% 100%,0 100%)}
h1{font-size:38pt}
.sub{font-size:15pt;margin-top:2.2mm}
.emblem{top:69.5mm;width:56mm;height:56mm}
.castle{top:100mm;height:39.5mm}
.ground{top:139mm}
.glow{top:80mm;height:60mm}
.badge{position:absolute;right:5.5mm;top:60mm;width:31mm;height:31mm;transform:rotate(-11deg)}
.badge svg{position:absolute;inset:0;width:100%;height:100%}
.badge div{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fff;line-height:1}
.badge .b1{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:7.6pt;letter-spacing:.08em}
.badge .b2{font-weight:900;font-size:13.5pt;margin:.6mm 0 .4mm}
.badge .b3{font-size:7.2pt;font-style:italic}
.points{position:absolute;left:10mm;right:10mm;top:143.5mm;display:flex;justify-content:center;gap:3mm}
.points span{border:.3mm solid rgba(227,185,92,.85);border-radius:5mm;padding:1.3mm 3mm 1.1mm;font-size:8.6pt;font-weight:700;color:#f3e6c6;white-space:nowrap}
.card{left:9.5mm;right:9.5mm;top:154.5mm;height:37mm;border-radius:3mm;padding:3mm;gap:4.5mm}
.card .qr{width:32mm;height:32mm}
.card .kick{font-size:9pt}
.card .say{font-size:12.6pt;margin-top:1.6mm}
.card .url{font-size:14pt;margin-top:2.4mm}
.facts{top:195.6mm;font-size:8.4pt}
"""
    badge = ('<div class="badge"><svg viewBox="-30 -30 60 60" aria-hidden="true">'
             f'<path d="{SEAL_PATH}" transform="translate(1.2 1.6)" fill="#5e1f2a"/><path d="{SEAL_PATH}" fill="#b8505c"/>'
             '<circle r="21.5" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width=".9" stroke-dasharray="2 1.6"/></svg>'
             '<div><span class="b1">Les enfants&#8239;:</span><span class="b2">jeux au dos</span><span class="b3">retourne-moi&#8239;!</span></div></div>')
    body = f"""<div class="trim">
{stars([(13,30,3.6,.9),(87,34,3,.8),(8,64,2.2,.6),(20,88,2.4,.7),(30,14.5,1.9,.5),(70,15,1.9,.5),(92,100,2,.6)])}
<div class="glow"></div>
{emblem()}
<div class="ground"></div>
{CASTLE}
{frame(5, w, h)}
<div class="center" style="top:11.5mm"><div class="brand">Ma Quête Légendaire</div></div>
<div class="center" style="top:22.5mm"><span class="ribbon">Anniversaire · 7 à 10 ans</span></div>
<div class="center" style="top:33mm"><h1>Une vraie quête<br><em>de chevaliers</em></h1><div class="sub">dans les rues de votre ville</div></div>
{badge}
<div class="points"><span>Au prénom de l'enfant</span><span>Prête en 2 minutes</span><span>Il pleut&#8239;? À la maison</span></div>
<div class="card"><QR/><div>
  <div class="kick">Aperçu gratuit</div>
  <div class="say">Scannez, tapez le prénom de votre enfant&#8239;: le Grand Maître l'appelle&#8239;!</div>
  <div class="url">maquetelegendaire.fr</div></div></div>
<div class="facts">4 à 15 enfants · environ 1 h · 24,90&#8239;€ pour tout le groupe, sans animateur</div>
</div>"""
    return page(w, h, css, body.replace("<QR/>", qr(SITE + "/?ref=f-restaurant")))

# ---------- A5, verso: the knight's trials ----------
GRID = "DRTTRNEH ERSNACFU CBAJEPEE AAIGRVNO NUSTOURP EMDQBNER RGIOUJOO SNUMTEUI".split()
WORDS = ["ÉPÉE", "ROI", "CASQUE", "TOUR", "DRAGON"]

def check_grid():
    import unicodedata
    plain = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    for w in WORDS:
        w = plain(w)
        hits = [1 for r in range(8) for c in range(8) for dr, dc in ((0, 1), (1, 0), (1, 1), (-1, 1))
                if all(0 <= r + dr * i < 8 and 0 <= c + dc * i < 8 and GRID[r + dr * i][c + dc * i] == ch for i, ch in enumerate(w))]
        assert len(hits) == 1, f"mot caché {w} : {len(hits)} fois"

def a5_verso():
    w, h = 148, 210
    css = """
.paper{background:#fffdf7}
.head{position:absolute;left:-3mm;right:-3mm;top:-3mm;height:35mm;background:radial-gradient(120% 140% at 50% 0%,#2b3570 0%,#1a2150 45%,#10142a 100%)}
.head::after{content:"";position:absolute;left:0;right:0;bottom:0;height:.8mm;background:var(--gold)}
h2{font-family:"UnifrakturMaguntia",serif;font-weight:400;font-size:27pt;line-height:1;color:var(--cream)}
.lead{font-size:10.4pt;color:#f3e6c6;margin-top:1.6mm}
.lead b{color:var(--gold)}
.grid{position:absolute;left:8mm;right:8mm;top:38mm;bottom:17mm;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:3.6mm}
.box{position:relative;border:.5mm solid var(--ink);border-radius:2.6mm;padding:7.2mm 3.4mm 3mm;display:flex;flex-direction:column;align-items:center;gap:1.6mm;color:var(--ink)}
.num{position:absolute;left:3mm;top:-3.3mm;background:var(--wax);color:#fff;font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:9.4pt;letter-spacing:.06em;padding:1.1mm 2.6mm .9mm;border-radius:1.4mm;white-space:nowrap}
.ask{font-size:9.6pt;line-height:1.3;align-self:stretch}
.ask i{color:var(--muted)}
.maze{width:64mm;height:49.8mm;margin-top:1.5mm}
.words{display:grid;grid-template-columns:repeat(8,5.6mm);border:.4mm solid var(--ink);font-weight:800;font-size:10.4pt;text-align:center;line-height:5.6mm}
.riddle{font-style:italic;font-size:10.2pt;line-height:1.32;align-self:stretch}
.blanks{font-size:15pt;font-weight:800;letter-spacing:2.2mm;align-self:stretch;margin:.6mm 0 1.2mm}
.sec{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:9.4pt;letter-spacing:.06em;color:var(--wax);align-self:stretch;border-top:.3mm dashed #b9ae95;padding-top:2mm}
.tiles{display:flex;gap:2mm;align-self:stretch}
.tiles span{width:8.6mm;height:10mm;border-radius:1.4mm;background:#f3ead6;border:.4mm solid var(--ink);display:flex;align-items:center;justify-content:center;font-family:"UnifrakturMaguntia",serif;font-size:16pt}
.tiles i{width:8.6mm;height:10mm;border-bottom:.5mm solid var(--ink)}
.shield{width:34mm;height:39mm}
.motto{align-self:stretch;border-bottom:.4mm dashed var(--ink);height:6mm;font-size:8pt;color:var(--muted);display:flex;align-items:flex-end}
.foot{position:absolute;left:8mm;right:8mm;bottom:5.5mm;display:flex;align-items:center;justify-content:space-between;color:var(--ink);font-size:8.6pt}
.foot .brand{color:var(--ink);font-size:12pt}
.foot .ans{transform:rotate(180deg);color:var(--muted);font-size:7.6pt}
"""
    maze = (H / "svg" / "labyrinthe-1.svg").read_text()
    maze = maze.replace("<svg ", '<svg class="maze" ', 1)
    shield = (H / "svg" / "blason.svg").read_text().replace("<svg ", '<svg class="shield" ', 1)
    letters = "".join(f"<span>{c}</span>" for row in GRID for c in row)
    body = f"""<div class="trim">
<div class="head"></div>
<div class="center" style="top:6.5mm"><h2>Les épreuves du chevalier</h2>
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
  <div class="box"><span class="num">4 · Ton blason</span><div class="ask">Colorie-le et invente ta devise.</div>{shield}<div class="motto">Ma devise&#8239;:</div></div>
</div>
<div class="foot"><div class="ans">Réponses&#8239;: le donjon · ÉPÉE</div><div><span class="brand">Ma Quête Légendaire</span> · maquetelegendaire.fr</div></div>
</div>"""
    return page(w, h, css, body, bg="paper")

# ---------- render ----------
async def render(pg, html, name):
    f = PREV / f"_{name}.html"; f.write_text(html, encoding="utf-8")
    await pg.goto(f.as_uri()); await pg.evaluate("document.fonts.ready")
    over = await pg.evaluate("""() => [...document.querySelectorAll('.trim *')].filter(e => {
        const t = document.querySelector('.trim').getBoundingClientRect(), r = e.getBoundingClientRect();
        return e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow === 'visible' && e.children.length === 0 && e.textContent.trim();
      }).map(e => e.textContent.trim().slice(0, 40))""")
    pdf = PREV / f"_{name}.pdf"
    await pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
    f.unlink()
    return pdf, over

async def main():
    check_grid()
    OUT.mkdir(parents=True, exist_ok=True); PREV.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        jobs = {"flyer-a6-comptoir": [("recto", a6())], "flyer-a5-restaurant": [("recto", a5_recto()), ("verso", a5_verso())]}
        for out, faces in jobs.items():
            w = PdfWriter()
            for face, html in faces:
                pdf, over = await render(pg, html, f"{out}-{face}")
                if over: print("  débordement possible :", over)
                for pp in PdfReader(str(pdf)).pages: w.add_page(pp)
                subprocess.run(["pdftoppm", "-r", "110", "-png", "-singlefile", str(pdf), str(PREV / f"{out}-{face}")], check=True)
                pdf.unlink()
            # exact sizes for the printer: MediaBox = trim + 3 mm bleed (Chromium rounds to whole pixels),
            # TrimBox = finished size, BleedBox = MediaBox; the top-left corner stays where it was drawn
            tw, th = (105, 148) if "a6" in out else (148, 210)
            mm = 72 / 25.4
            for pp in w.pages:
                top = float(pp.mediabox.top)
                W, Hh = (tw + 2 * BLEED) * mm, (th + 2 * BLEED) * mm
                box = RectangleObject([0, top - Hh, W, top])
                pp.mediabox = box; pp.cropbox = box; pp.bleedbox = box
                pp.trimbox = RectangleObject([BLEED * mm, top - Hh + BLEED * mm, W - BLEED * mm, top - BLEED * mm])
            fmt = "A6 recto" if "a6" in out else "A5 recto verso"
            w.add_metadata({"/Title": f"Ma Quête Légendaire — flyer {fmt}", "/Author": "Ma Quête Légendaire"})
            w.write(str(OUT / f"{out}.pdf")); print(out, len(w.pages), "page(s)")
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
