# "Le jour où tu deviens chevalier": a series of short videos (from 22 Oct 2026) where every episode opens
# on a different image (generated with Z-Image Turbo on Hugging Face, saved in img/) and ends by announcing
# the next one. Voice: the app's recorded Grand Maître clips, exact words.
#   python3 dev/video/serie/serie.py [slug …]   -> out/<slug>.mp4 + out/<slug>.jpg
import asyncio, json, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "campagne"))
from build import build_audio, spans, VOIX, NOMS, REPO
from hook import time_words, chunk
from clean import clean

OUT = HERE / "out"
FPS = 24
PRO = VOIX / "prologue-dehors-m.mp3"
# Measured pauses of prologue-dehors-m (silencedetect): sentence and comma boundaries.
S_APPROCHE = (0.0, 0.76, "Approche.")
S_ANNIV = (21.24, 26.6, "Aujourd'hui, c'est ton anniversaire, et j'ai besoin d'un chevalier courageux.")
S_DEFIS = (30.42, 34.25, "Relève mes défis, et rapporte-moi les lettres.")
S_PRET = (34.87, 35.33, "Es-tu prêt ?")
# Recorded for the series (audio/video/rue.mp3, pauses shortened by court.line):
from court import line
S_RUE = (None, None, "Pour vous, une rue ordinaire. Pour votre enfant, le jour de son anniversaire : une vraie aventure de chevalier.", line("rue"))
TAIL = 4.2


def end_card(q, nxt):
    return (f'<div id="brand">Ma Quête Légendaire</div><div class="q">{q}</div>'
            '<ul><li><i></i><span>Votre enfant appelé <b>par son prénom</b></span></li>'
            '<li><i></i><span>7 à 10 ans · prête en <b>2 minutes</b></span></li>'
            '<li><i></i><span>Il pleut ? Elle se joue <b>à la maison</b></span></li></ul>'
            '<div class="link"><div><b>maquetelegendaire.fr</b><small>Lien dans la bio</small></div></div>'
            '<div class="deal">Offerte aux familles testeuses · écrivez CHEVALIER</div>'
            f'<div class="next"><b>Demain, épisode suivant</b>{nxt}</div>')


def voice(seq, name="leo", label="Léo,"):
    """seq: list of ("name",) | (gap,) | (a, b, text). Returns audio pieces, words, end of voice."""
    audio, words, t = [(None, 0, 0.3)], [], 0.3
    for it in seq:
        if it == "name":
            sp = spans(NOMS / f"{name}.mp3"); a, b = 0, sp[-1][1] + 0.05
            audio.append((NOMS / f"{name}.mp3", a, b))
            words.append({"w": label, "t0": t, "t1": t + b - a + 0.2, "name": True}); t += b - a
        elif len(it) == 1:
            audio.append((None, 0, it[0])); t += it[0]
        else:
            a, b, text = it[:3]; f = it[3] if len(it) > 3 else PRO
            if a is None: sp = spans(f); a, b = sp[0][0] + 0.03, sp[-1][1]
            audio.append((f, a - 0.03, b + 0.06))
            inner = [(x, y) for x, y in spans(f) if y > a and x < b]
            inner = [(max(x, a), min(y, b)) for x, y in inner]
            words += time_words(text, inner, t + 0.03); t += b - a + 0.09
    names = [w for w in words if w.get("name")]
    rest = chunk([w for w in words if not w.get("name")])
    for w in names: w["chunk"] = 0
    for w in rest: w["chunk"] += 1
    return audio, names + rest, t


def lettre():
    audio, words, ve = voice(["name", (0.3,), S_APPROCHE, (0.35,), S_ANNIV, (0.45,), S_PRET])
    w = {x["w"]: x for x in words}
    anniv = [x for x in words if x["w"].startswith("anniversaire")][0]
    cour = [x for x in words if x["w"].startswith("courageux")][0]
    pret = [x for x in words if x["w"].startswith("prêt")][0]
    t_ap = [x for x in words if x["w"].startswith("Aujourd")][0]["t0"]
    total = ve + TAIL
    end_at = ve + 0.55
    return dict(
        imgA=(HERE / "img/lettre.jpg").as_uri(), total=total, endAt=end_at,
        hook="POV : tu as 8 ans, et ton <b>anniversaire</b> commence par cette lettre…",
        ep="Épisode 1 · La lettre",
        cam=[[0, 1.0, 540, 1150], [ve - 0.6, 1.14, 545, 1180], [ve + 0.3, 2.2, 693, 1397], [total, 2.3, 693, 1397]],
        letter=dict(name="Léo,", at=0.3, sig=pret["t1"] + 0.1, lines=[
            ["Aujourd'hui, c'est ton anniversaire.", t_ap, anniv["t1"]],
            ["J'ai besoin d'un chevalier courageux.", anniv["t1"] + 0.15, cour["t1"]],
            ["Es-tu prêt ?", pret["t0"] - 0.3, pret["t1"]],
        ]),
        end=end_card("Et si son anniversaire devenait <b>une vraie quête de chevaliers</b> ?",
                     "Le gâteau d'anniversaire qui cachait <b style='display:inline;font-family:inherit;letter-spacing:0;font-size:inherit;color:#f0c25e'>une carte</b>"),
    ), audio, None


def gateau():
    audio, words, ve = voice(["name", (0.25,), S_ANNIV, (0.4,), S_RUE])
    first_end = [x for x in words if x["w"].startswith("courageux")][0]["t1"]
    sw = first_end + 0.35
    total = ve + TAIL
    # path in the town image (1080 x 1920 space): fountain, parvis, church, belfry, top street
    P = [[540, 1640], [542, 1483], [552, 1300], [571, 1128], [576, 1040], [700, 960], [770, 760], [660, 640]]
    return dict(
        imgA=(HERE / "img/gateau.jpg").as_uri(), imgB=(HERE / "img/ville.jpg").as_uri(), total=total, endAt=ve + 0.55,
        hook="Ce gâteau d'anniversaire cache <b>une carte au trésor</b>",
        ep="Épisode 2 · La carte", switchAt=sw, words=words,
        cam=[[0, 1.0, 540, 900], [sw - 0.5, 1.35, 533, 816], [sw, 3.4, 518, 690], [sw + 0.001, 1.7, 560, 1100], [sw + 1.2, 1.0, 540, 960], [total, 1.04, 540, 960]],
        points=P, path=[sw + 0.6, ve - 0.5],
        stops=[dict(i=1, side="l", label="<b>Fontaine</b> · une énigme"), dict(i=4, side="l", label="<b>Église</b> · un défi"),
               dict(i=7, side="l", label="<b>Clocher</b> · le mot secret")],
        end=end_card("Une vraie quête de chevaliers, <b>dans les rues de votre ville</b>",
                     "Fête au château : trouve <b style='display:inline;font-family:inherit;letter-spacing:0;font-size:inherit;color:#f0c25e'>la clé dorée</b> cachée dans la foule"),
    ), audio, words


VIDEOS = {"ep1-lettre": lettre, "ep2-gateau": gateau}


async def render(slug):
    cfg, audio_parts, words = VIDEOS[slug]()
    if words is not None: cfg["words"] = words
    OUT.mkdir(parents=True, exist_ok=True)
    page = HERE / f"_p_{slug}.html"
    page.write_text((HERE / "serie.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/"))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = build_audio(audio_parts, cfg["total"], tmp)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"setup({json.dumps(cfg, ensure_ascii=False)})"); await pg.wait_for_timeout(500)
            n = int(cfg["total"] * FPS)
            for i in range(n):
                await pg.evaluate(f"frame({i / FPS})")
                await pg.screenshot(path=str(tmp / f"f{i:04d}.jpg"), type="jpeg", quality=90)
            await pg.evaluate("frame(0.9)"); await pg.screenshot(path=str(OUT / f"{slug}.jpg"), type="jpeg", quality=88)
            await b.close()
        out = OUT / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.jpg"), "-i", str(a),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "copy",
                        "-t", f"{cfg['total']:.3f}", "-movflags", "+faststart", str(out)], check=True)
        clean(out)
    page.unlink()
    print(slug, f"{cfg['total']:.1f} s", flush=True)


if __name__ == "__main__":
    for k in sys.argv[1:] or list(VIDEOS):
        asyncio.run(render(k))
