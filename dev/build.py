# Builds the app from dev/: python3 dev/build.py
#   index.html          free demo for GitHub Pages: everything runs in the phone, unlock is free
#   site/index.html     paid app for Cloudflare: places chosen by the server, unlock after payment
#   legal/, site/legal/ sales terms, legal notice, privacy, filled from dev/legal/identite.json
#   *.html guides       pages for Google and Pinterest, from dev/pages/, at the site root
#   dist/worker.js      Cloudflare server: geo.js + engine.js + worker.js
# The audio folder is copied into site/ by the deploy workflow (or with --audio).
import json, shutil, subprocess, sys
from pathlib import Path
d = Path(__file__).parent
root = d.parent
read = lambda n: (d / n).read_text(encoding="utf-8")
t, geo, eng, voice, worker = read("app.template.html"), read("geo.js"), read("engine.js"), read("voice.js"), read("worker.js")

def page(engine_part, paid):
    return (t.replace("/*GEO*/", geo).replace("/*ENGINE*/", engine_part).replace("/*VOICE*/", voice)
             .replace("const PAID=/*PAID*/false;", f"const PAID={'true' if paid else 'false'};"))

(root / "index.html").write_text(page(eng, False), encoding="utf-8")

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
    "{{STYLE}}": STYLE, "{{DATE}}": "13 octobre 2026",
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
# Guides for Google and Pinterest (dev/pages/), served at the site root.
guide_pages = {f.name: fill(f.read_text(encoding="utf-8")) for f in sorted((d / "pages").glob("*.html"))}
for name, html in guide_pages.items():
    (root / name).write_text(html, encoding="utf-8")
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
if "--audio" in sys.argv:
    shutil.copytree(root / "audio", site / "audio", ignore=shutil.ignore_patterns("manifest.json", "rapport-noms.json", "test"))

(root / "dist").mkdir(exist_ok=True)
(root / "dist" / "worker.js").write_text(geo + "\n" + eng + "\n" + worker, encoding="utf-8")
print("index.html, site/ et dist/worker.js reconstruits")
