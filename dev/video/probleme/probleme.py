# « Le problème des parents, puis notre solution » (23 Oct 2026, Nathan : « des vidéos qui mettent en avant un problème
# que les parents rencontrent : organiser l'anniversaire de leur enfant… et ensuite notre solution »).
# The ALERTE hook, the party to-do list piling up (with a heartbeat), the seal crushing it, then the solution:
# the first name typed on the real site, the Grand Maître calling the child, the quest in town, the end card.
#   python3 dev/video/probleme/probleme.py [slug]   -> marketing/videos-probleme/<slug>.mp4 + .jpg
import asyncio, json, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
REPO = HERE.parents[2]
sys.path[:0] = [str(HERE.parent / "campagne"), str(HERE.parent / "accroche"), str(HERE.parent)]
from build import build_audio, VOIX, NOMS
from accroche import make as with_hook
from plan import alerte
FPS = 30
SONS = HERE.parent / "accroche/sons"
OUT = REPO / "marketing/videos-probleme"
IMG = HERE.parent / "serie/img"
PHONE = HERE.parent / "campagne/img/phone"

VIDEOS = {
    "anniversaire-casse-tete": dict(
        name="Léo", name_clip="leo",
        hook=alerte("Samedi : 10 enfants.", "Et rien de prêt ?"),
        items=["Inviter les copains", "Trouver une activité (sans écrans)", "Imprimer et cacher les indices",
               "Écrire les énigmes", "Les occuper 2 heures", "Et s'il pleut ?"],
        t=dict(items=[0.4, 1.0, 1.6, 2.2, 2.8, 3.4], sigh=3.9, seal=4.8, strike=5.0, phone=6.3, type=6.6, tap=7.15,
               ville=9.8, tags=[10.1, 10.6, 11.1], step=11.8, end=14.0),
        voice=[(7.3, "name", None, None), (8.15, "prologue-dehors-m", 0.0, 5.69), (14.4, "nomme-m", 5.92, 8.21)],
        caps=[(7.3, 8.1, '<span class="n">Léo</span>,'), (8.15, 9.45, "Approche."),
              (9.52, 13.95, "Je suis le Grand Maître de l'Ordre des Gardiens du Temple."), (14.4, 16.75, "Joyeux anniversaire !")],
        total=17.2),
}


def sfx(c):
    T = c["t"]; ev = []
    beats = [0.3, 1.0, 1.6, 2.1, 2.6, 3.0, 3.4, 3.75, 4.1, 4.4]
    ev += [(b, "heart", 0.45 + 0.5 * i / len(beats)) for i, b in enumerate(beats)]
    ev += [(x, "tock", 0.7) for x in T["items"]]
    ev += [(T["seal"] - 0.03, "thud", 1.0)] + [(T["strike"] + i * 0.15 + 0.05, "tick", 0.55) for i in range(len(c["items"]))]
    ev += [(T["phone"] - 0.05, "whoosh", 0.7), (T["ville"] - 0.05, "whoosh", 0.6), (T["end"] - 0.05, "whoosh", 0.6)]
    ev += [(T["type"] + i * 0.14, "tick", 0.45) for i in range(len(c["name"]))] + [(T["tap"], "tock", 0.6)]
    return ev


def audio(c, tmp):
    parts, t = [], 0.0
    for at, key, a, b in c["voice"]:
        f = NOMS / f"{c['name_clip']}.mp3" if key == "name" else VOIX / f"{key}.mp3"
        if a is None: a, b = 0.0, 0.8
        if at > t: parts.append((None, 0, at - t)); t = at
        parts.append((f, a, b)); t += b - a
    if c["total"] > t: parts.append((None, 0, c["total"] - t))
    base = build_audio(parts, c["total"], tmp)             # voice + the soft music of the site
    ev = sfx(c); ins, fl = ["-i", str(base)], ["[0:a]aresample=44100,aformat=channel_layouts=mono[b]"]
    for i, (at, s, g) in enumerate(ev):
        ins += ["-i", str(SONS / f"{s}.wav")]
        fl.append(f"[{i + 1}:a]aresample=44100,adelay={int(at * 1000)}:all=1,volume={g}[e{i}]")
    fl.append("[b]" + "".join(f"[e{i}]" for i in range(len(ev))) + f"amix=inputs={len(ev) + 1}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    out = tmp / "mix.m4a"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    return out


async def frames(c, tmp):
    page = HERE / "_probleme.html"
    bord = (REPO / "dev/flyers/svg/sceau-bord.txt").read_text().strip()
    h = (HERE / "probleme.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/").replace('d="BORD"', f'd="{bord}"')
    for k, f in {"IMG_WIDE": PHONE / "wide.jpg", "IMG_CLOSE": PHONE / "close.jpg", "IMG_HOME": PHONE / "home.jpg", "IMG_VILLE": IMG / "ville.jpg"}.items():
        h = h.replace(k, f.as_uri())
    page.write_text(h)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
        await pg.evaluate(f"setup({json.dumps(c, ensure_ascii=False)})"); await pg.wait_for_timeout(600)
        n = int(round(c["total"] * FPS))
        for i in range(n):
            await pg.evaluate(f"frame({i / FPS})")
            await pg.screenshot(path=str(tmp / f"f{i:04d}.jpg"), type="jpeg", quality=90)
        await b.close()
    page.unlink()
    return n


def render(slug):
    c = VIDEOS[slug]
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        n = asyncio.run(frames(c, tmp))
        a = audio(c, tmp)
        body = tmp / "body.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.jpg"), "-i", str(a),
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-t", f"{n / FPS:.3f}", str(body)], check=True)
        out = OUT / f"{slug}.mp4"
        with_hook(body, out, c["hook"])
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.0", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(OUT / f"{slug}.jpg")], check=True)
    print(slug, out)


if __name__ == "__main__":
    for s in sys.argv[1:] or list(VIDEOS):
        render(s)
