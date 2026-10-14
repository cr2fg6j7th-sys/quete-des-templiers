# Builds the app from dev/: python3 dev/build.py
#   index.html          free demo for GitHub Pages: everything runs in the phone, unlock is free
#   site/index.html     paid app for Cloudflare: places chosen by the server, unlock after payment
#   legal/, site/legal/ sales terms, legal notice, privacy, filled from dev/legal/identite.json
#   *.html guides       pages for Google and Pinterest, from dev/pages/, at the site root
#   dist/worker.js      Cloudflare server: geo.js + engine.js + worker.js
#   sw.js               keeps a bought quest playable without network (both builds)
#   og.png, icons       link preview image and icons (dev/static/, made by dev/video/og.py)
#   robots.txt, sitemap.xml   for search engines (paid site only; the demo is marked noindex)
#   home.static.html    the home screen copied into the page for robots without JavaScript (dev/snapshot.py)
# The audio folder is copied into site/ by the deploy workflow (or with --audio).
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
d = Path(__file__).parent
root = d.parent
read = lambda n: (d / n).read_text(encoding="utf-8")
t, geo, eng, voice, worker = read("app.template.html"), read("geo.js"), read("engine.js"), read("voice.js"), read("worker.js")

# The paid site: its address goes in the link previews and for Google; the demo reads its copy of
# the places of France (CORS allowed on /places/). To change when the domain name is bought.
SITE = PLACES_SITE = "https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev"
# Changes when the voice clips change, so phones drop the old copy kept for playing without network.
audio_files = [root / "audio" / "manifest.json", root / "audio" / "noms.json"]
VOICE_VERSION = hashlib.sha256(b"".join(f.read_bytes() for f in audio_files if f.exists())).hexdigest()[:10]

# For robots that do not run JavaScript (the AI assistants' crawlers): the home screen as drawn
# (dev/home.static.html, made by dev/snapshot.py) and the FAQ as structured data.
home_static = (d / "home.static.html").read_text(encoding="utf-8").strip() if (d / "home.static.html").exists() else ""
faq = json.loads(re.search(r"const FAQ=(\[.*?\n\]);", t, re.S).group(1))
faq_ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}, ensure_ascii=False) + "</script>"

def page(engine_part, paid):
    return (t.replace("/*GEO*/", geo).replace("/*ENGINE*/", engine_part).replace("/*VOICE*/", voice)
             .replace("const PAID=/*PAID*/false;", f"const PAID={'true' if paid else 'false'};")
             .replace("/*PLACES_SITE*/", "" if paid else PLACES_SITE)
             .replace("{{SITE}}", SITE).replace("/*VOICE_VERSION*/", VOICE_VERSION)
             .replace("<!--ROBOTS-->", "" if paid else '<meta name="robots" content="noindex">')
             .replace("<!--FAQ-->", faq_ld).replace("/*HOME*/", home_static))
sw = read("sw.js").replace("/*VOICE_VERSION*/", VOICE_VERSION)

(root / "index.html").write_text(page(eng, False), encoding="utf-8")
(root / "sw.js").write_text(sw, encoding="utf-8")
for f in (d / "static").iterdir():
    shutil.copy(f, root / f.name)

# Legal pages: one identity file (dev/legal/identite.json) fills every page.
STYLE = """<style>
@font-face{font-family:"Alegreya Sans";src:url(../fonts/AlegreyaSans-Regular.woff) format("woff");font-weight:400;font-display:swap}
@font-face{font-family:"Alegreya Sans";src:url(../fonts/AlegreyaSans-Bold.woff) format("woff");font-weight:700;font-display:swap}
@font-face{font-family:"UnifrakturMaguntia";src:url(../fonts/UnifrakturMaguntia-Book.woff) format("woff");font-display:swap}
:root{--stone:#eef0f5;--card:#fff;--ink:#1b2547;--muted:#5b6482;--rose:#b8505c;--rose-soft:#f6e3e5;--or:#a87a1f;--on-rose:#fff;color-scheme:light}
@media (prefers-color-scheme: dark){:root{--stone:#11152a;--card:#1a2038;--ink:#ebe9f4;--muted:#a3a8c3;--rose:#e58b95;--rose-soft:#3a2230;--or:#e0b55a;--on-rose:#11152a;color-scheme:dark}}
body{margin:0;background:var(--stone);color:var(--ink);font-family:"Alegreya Sans",system-ui,sans-serif;font-size:17px;line-height:1.55}
main{max-width:640px;margin:0 auto;padding:20px 16px 48px}
h1{font-family:"UnifrakturMaguntia",Georgia,serif;font-weight:400;font-size:2rem;line-height:1.15;margin:.4em 0 .2em}
h2{font-size:1.1rem;color:var(--rose);margin:1.6em 0 .3em}
p,li{margin:.4em 0}a{color:var(--rose)}.maj,.back{color:var(--muted);font-size:.9rem}
.todo{background:#fff3c4;color:#5a4300;padding:0 4px;border-radius:4px}
</style>"""
ident = json.loads((d / "legal" / "identite.json").read_text(encoding="utf-8"))
todo = lambda label: f'<span class="todo">[à compléter : {label}]</span>'
med = ident.get("mediateur") or ""
if med and ident.get("mediateur_site"):
    med = f'{med} (<a href="{ident["mediateur_site"]}" rel="noopener">{ident["mediateur_site"]}</a>)'
fields = {
    "{{STYLE}}": STYLE, "{{DATE}}": "14 octobre 2026",
    "{{NOM}}": ident.get("nom") or todo("nom et prénom"),
    "{{SIRET}}": ident.get("siret") or todo("numéro SIRET"),
    "{{ADRESSE}}": ident.get("adresse") or todo("adresse"),
    "{{EMAIL}}": (f'<a href="mailto:{ident["email"]}">{ident["email"]}</a>' if ident.get("email") else todo("e-mail de contact")),
    "{{MEDIATEUR}}": med or todo("médiateur de la consommation"),
}
def fill(html):
    for k, v in fields.items():
        html = html.replace(k, v)
    return html
# Guides for Google and Pinterest (dev/pages/), served at the site root. Google is told the paid
# site holds the original (canonical); the demo copies are not to be indexed.
guide_pages = {f.name: fill(f.read_text(encoding="utf-8")).replace("</head>", f'<link rel="canonical" href="{SITE}/{f.name}">\n</head>', 1)
               for f in sorted((d / "pages").glob("*.html"))}
for name, html in guide_pages.items():
    (root / name).write_text(html.replace("</head>", '<meta name="robots" content="noindex">\n</head>', 1), encoding="utf-8")
legal_pages = {}
for f in sorted((d / "legal").glob("*.html")):
    html = f.read_text(encoding="utf-8")
    for k, v in fields.items():
        html = html.replace(k, v)
    legal_pages[f.name] = html
(root / "legal").mkdir(exist_ok=True)
for name, html in legal_pages.items():
    (root / "legal" / name).write_text(html, encoding="utf-8")

# The paid page does not ship the engine: only the list of recorded voice clips.
keys = json.loads(subprocess.check_output(["node", "-e", "console.log(JSON.stringify(Object.keys(require('./voice.js').LINES)))"], cwd=d))
site = root / "site"
if site.exists():
    shutil.rmtree(site)
(site / "legal").mkdir(parents=True)
(site / "index.html").write_text(page("const QUEST_VOICE_KEYS=" + json.dumps(keys) + ";", True), encoding="utf-8")
for name, html in legal_pages.items():
    (site / "legal" / name).write_text(html, encoding="utf-8")
for name, html in guide_pages.items():
    (site / name).write_text(html, encoding="utf-8")
shutil.copytree(root / "fonts", site / "fonts")
(site / "sw.js").write_text(sw, encoding="utf-8")
for f in (d / "static").iterdir():
    shutil.copy(f, site / f.name)
(site / "robots.txt").write_text(f"User-agent: *\nDisallow: /api/\nDisallow: /places/\nDisallow: /audio/\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
urls = [SITE + "/"] + [f"{SITE}/{n}" for n in guide_pages]
(site / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
# Headers of the static files (Cloudflare): the demo may read the place tiles from another site.
(site / "_headers").write_text("/places/*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=86400\n"
    "/sw.js\n  Cache-Control: no-cache\n", encoding="utf-8")
if "--audio" in sys.argv:
    shutil.copytree(root / "audio", site / "audio", ignore=shutil.ignore_patterns("manifest.json", "rapport-noms.json", "test"))

(root / "dist").mkdir(exist_ok=True)
# The worker is one ES module: drop the Node-only require/module.exports fallbacks, which the
# Cloudflare bundler would try to resolve.
def for_worker(code):
    code = re.sub(r'\(typeof (\w+) !== "undefined"\) \? \1 : require\("[^"]+"\)', r"\1", code)
    return re.sub(r'^if \(typeof module !== "undefined"\) module\.exports = \w+;\n', "", code, flags=re.M)
bundle = for_worker(geo + "\n" + eng) + "\n" + worker
assert "require(" not in bundle and "module.exports" not in bundle, "worker bundle still has Node code"
(root / "dist" / "worker.js").write_text(bundle, encoding="utf-8")
print("index.html, site/ et dist/worker.js reconstruits")
