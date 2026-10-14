# Static copies of what the browser draws, for robots that do not run JavaScript
# (the AI assistants' crawlers: GPTBot, ClaudeBot, PerplexityBot...).
#   python3 dev/snapshot.py      after any change to the home screen
# Needs Python Playwright (local only; the deploy reuses the committed file):
#   dev/home.static.html   the home screen, put inside <div id="app"> by build.py
import hashlib, http.server, re, socketserver, subprocess, threading
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright

d = Path(__file__).parent
root = d.parent
subprocess.run(["python3", str(d / "build.py")], check=True)

handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(root / "site"))  # the paid build
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}/"


with sync_playwright() as p:
    b = p.chromium.launch()
    # Home screen, as a first-time visitor sees it in light mode.
    page = b.new_page(viewport={"width": 390, "height": 844}, color_scheme="light")
    page.goto(base, wait_until="networkidle")
    page.wait_for_timeout(500)
    html = page.eval_on_selector("#app", "e => e.innerHTML")
    # Buttons only work once the script runs: in the copy, they are plain text holders.
    html = re.sub(r'<p class="note" role="status"></p>|<p class="words"></p>', "", html)
    src = (d / "app.template.html").read_text(encoding="utf-8")
    tag = hashlib.sha256(re.search(r"\nconst FAQ=.*?\nfunction setupScreen", src, re.S).group(0).encode()).hexdigest()[:12]
    (d / "home.static.html").write_text(f"<!--home {tag}-->" + html.strip() + "\n", encoding="utf-8")
    b.close()
srv.shutdown()
subprocess.run(["python3", str(d / "build.py")], check=True)
print("dev/home.static.html mis à jour")
