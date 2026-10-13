# Rebuild index.html from the template and the quest engine: python3 dev/build.py
from pathlib import Path
d = Path(__file__).parent
t = (d / "app.template.html").read_text(encoding="utf-8")
e = (d / "engine.js").read_text(encoding="utf-8")
(d.parent / "index.html").write_text(t.replace("/*ENGINE*/", e), encoding="utf-8")
print("index.html reconstruit")
