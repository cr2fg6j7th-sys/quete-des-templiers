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
from plan import alerte, question
FPS = 30
SONS = HERE.parent / "accroche/sons"
OUT = REPO / "marketing/videos-probleme"
IMG = HERE.parent / "serie/img"
PHONE = HERE.parent / "campagne/img/phone"

VIDEOS = {
    "anniversaire-casse-tete": dict(
        name="Léo", name_clip="leo",
        hook=question("Ton enfant a bientôt <em>son anniversaire</em> ?", "Et rien de prêt ?", "Idée anniversaire enfant · jeu de piste"),
        items=["Inviter les copains", "Trouver une activité (sans écrans)", "Imprimer et cacher les indices",
               "Écrire les énigmes", "Les occuper 2 heures", "Et s'il pleut ?"],
        # slow enough to read every line (Nathan, 23/10 16:13), with a heartbeat that speeds up until the seal falls
        t=dict(items=[0.7, 1.6, 2.5, 3.4, 4.3, 5.2], sigh=6.1, seal=7.7, strike=7.9, phone=10.2, type=10.6, tap=11.45,
               ville=14.9, tags=[15.3, 16.0, 16.7], step=17.5, end=20.2),
        beats=[0.25, 1.15, 1.95, 2.7, 3.35, 3.95, 4.5, 5.0, 5.45, 5.85, 6.2, 6.5, 6.78, 7.03, 7.26, 7.47],
        voice=[(11.65, "name", None, None), (12.5, "prologue-dehors-m", 0.0, 5.69), (20.7, "nomme-m", 5.92, 8.21)],
        caps=[(11.65, 12.45, '<span class="n">Léo</span>,'), (12.5, 13.8, "Approche."),
              (13.87, 18.3, "Je suis le Grand Maître de l'Ordre des Gardiens du Temple."), (20.7, 23.05, "Joyeux anniversaire !")],
        total=24.0),

    # 23 Oct, 16:25 (Nathan: « glisse quelques vidéos de ce genre dans l'artefact des publications à la main »):
    # four more parents' problems, same build. Only recorded lines are used (no new voice).
    "anniversaire-budget": dict(
        name="Jade", name_clip="jade", bg1=IMG / "gateau.jpg",
        hook=question("Un anniversaire <em>qui coûte une fortune</em> ?", "Il y a plus simple.", "Idée anniversaire petit budget",
                      cal="Budget", labels=["50 €", "100 €", "150 €", "200 €", "250 €"]),
        txt=dict(kw1="Idée anniversaire petit budget", head1="Le budget d'un anniversaire <em>de 10 enfants</em>…",
                 ntitle="Anniversaire de Jade<small>10 copains, et le budget ?</small>", sigh="Le budget explose.",
                 turn="Et si c'était <em>beaucoup plus simple</em> ?", head3="Il crée la quête <em>dans votre quartier</em>.",
                 st="<b>24,90 €</b> pour 4 à 15 enfants,<br><b>rien à préparer</b>"),
        items=["Trampoline park · ≈ 250 €", "Animateur, 2 h · ≈ 200 €", "Bowling + goûter · ≈ 180 €",
               "Sachets cadeaux · ≈ 40 €", "Déco, ballons · ≈ 30 €", "Et le gâteau ?"],
        t=dict(items=[0.7, 1.6, 2.5, 3.4, 4.3, 5.2], sigh=6.1, seal=7.7, strike=7.9, phone=10.2, type=10.6, tap=11.45,
               ville=13.6, tags=[14.0, 14.6, 15.2], step=16.4, end=23.1),
        beats=[0.25, 1.15, 1.95, 2.7, 3.35, 3.95, 4.5, 5.0, 5.45, 5.85, 6.2, 6.5, 6.78, 7.03, 7.26, 7.47],
        voice=[(11.65, "name", None, None), (12.6, "prologue-dehors-f", 0.0, 0.63), (13.9, "video/budget", 0.0, 2.1),
               (16.3, "video/budget", 2.53, 8.88), (23.6, "nomme-f", 6.14, 9.65)],
        caps=[(11.65, 12.55, '<span class="n">Jade</span>,'), (12.6, 13.4, "Approche."), (13.9, 16.1, "Pas besoin d'une fortune."),
              (16.3, 22.7, "Donnez-moi une adresse : je transforme votre quartier en quête de chevaliers."),
              (23.6, 27.1, "Joyeux anniversaire !")],
        total=27.7),
    "anniversaire-pas-le-temps": dict(
        name="Hugo", name_clip="hugo", bg1=IMG / "lettre.jpg", bg3=IMG / "village.jpg",
        hook=question("Pas le temps de <em>tout préparer</em> ?", "Regarde ça.", "Idée jeu de piste d'anniversaire",
                      cal="Préparation", labels=["1 h", "2 h", "3 h", "4 h", "5 h"]),
        txt=dict(kw1="Idée jeu de piste d'anniversaire", head1="Préparer un jeu de piste <em>soi-même</em>…",
                 ntitle="Anniversaire d'Hugo<small>samedi, 14 h</small>", sigh="5 heures de travail. Pour 1 heure de jeu.",
                 turn="Et si c'était prêt <em>en 2 minutes</em> ?", kw3="Jeu de piste dans votre village",
                 head3="Il crée la quête <em>dans votre village</em>.",
                 st="<b>Prête en 2 minutes</b> : un prénom,<br>une adresse, <b>rien à imprimer</b>"),
        items=["Écrire 10 énigmes · 2 h", "Repérer le parcours · 1 h", "Imprimer, découper · 30 min",
               "Cacher les indices · 1 h", "Prévoir un plan B · 30 min", "La veille, à minuit…"],
        t=dict(items=[0.7, 1.6, 2.5, 3.4, 4.3, 5.2], sigh=6.1, seal=7.7, strike=7.9, phone=10.2, type=10.6, tap=11.45,
               ville=14.9, tags=[15.3, 16.0, 16.7], step=17.5, end=20.2),
        beats=[0.25, 1.15, 1.95, 2.7, 3.35, 3.95, 4.5, 5.0, 5.45, 5.85, 6.2, 6.5, 6.78, 7.03, 7.26, 7.47],
        voice=[(11.65, "name", None, None), (12.5, "prologue-dehors-m", 0.0, 5.69), (20.7, "nomme-m", 5.92, 8.21)],
        caps=[(11.65, 12.45, '<span class="n">Hugo</span>,'), (12.5, 13.8, "Approche."),
              (13.87, 18.3, "Je suis le Grand Maître de l'Ordre des Gardiens du Temple."), (20.7, 23.05, "Joyeux anniversaire !")],
        total=24.0),
    "anniversaire-ennui": dict(
        name="Gabriel", name_clip="gabriel", bg1=IMG / "gateau.jpg",
        hook=question("10 enfants, 2 heures. <em>Tu tiens</em> ?", "Pas sûr…", "Idée jeu de piste d'anniversaire",
                      cal="Samedi", labels=["14 h", "14 h 10", "14 h 20", "14 h 30", "14 h 40"]),
        txt=dict(kw1="Grand jeu chevalier enfant", head1="Un anniversaire <em>à la maison</em>…",
                 ntitle="Anniversaire de Gabriel<small>samedi, 14 h – 16 h</small>", sigh="Les 2 heures les plus longues de l'année.",
                 turn="Et si le Grand Maître <em>les occupait</em> ?",
                 st="<b>1 heure</b> de quête en équipe,<br>un diplôme pour chaque enfant"),
        items=["14 h · Ils arrivent", "14 h 10 · Gâteau englouti", "14 h 20 · Bataille de coussins",
               "14 h 30 · « On s'ennuie ! »", "14 h 40 · Quelqu'un pleure", "14 h 45 · Encore 1 h 15…"],
        t=dict(items=[0.7, 1.6, 2.5, 3.4, 4.3, 5.2], sigh=6.1, seal=7.7, strike=7.9, phone=10.2, type=10.45, tap=11.8,
               ville=15.6, tags=[16.0, 16.7, 17.4], step=18.2, end=20.9),
        beats=[0.25, 1.15, 1.95, 2.7, 3.35, 3.95, 4.5, 5.0, 5.45, 5.85, 6.2, 6.5, 6.78, 7.03, 7.26, 7.47],
        voice=[(12.0, "name", None, None), (13.3, "prologue-dehors-m", 0.0, 5.69), (21.4, "nomme-m", 5.92, 8.21)],
        caps=[(12.0, 13.2, '<span class="n">Gabriel</span>,'), (13.3, 14.6, "Approche."),
              (14.67, 19.1, "Je suis le Grand Maître de l'Ordre des Gardiens du Temple."), (21.4, 23.75, "Joyeux anniversaire !")],
        total=24.7),
    "anniversaire-pluie": dict(
        name="Inès", name_clip="ines", bg1=IMG / "pluie.jpg", bg3=PHONE / "wide.jpg",
        hook=question("Il pleut <em>le jour de la fête</em> ?", "Pas de panique.", "Anniversaire chevalier à la maison"),
        txt=dict(kw1="Anniversaire chevalier à la maison", head1="Il pleut <em>le jour J</em>…",
                 ntitle="Anniversaire d'Inès<small>samedi… sous la pluie</small>", sigh="Le cauchemar des parents.",
                 turn="Et si la quête <em>venait à la maison</em> ?", kw3="Anniversaire chevalier à la maison",
                 head3="La quête se joue <em>à la maison</em>.",
                 g1="<b>1</b> · Sous le canapé", g2="<b>2</b> · Dans le frigo", g3="<b>3</b> · Le mot secret",
                 st="<b>Mode maison</b> : 6 cartes à cacher,<br><b>5 minutes</b> de préparation"),
        items=["Le parc ? Annulé.", "10 enfants dans le salon", "Le canapé devient trampoline",
               "Les écrans, encore ?", "Les voisins du dessous…", "Et 2 heures à tenir"],
        t=dict(items=[0.7, 1.6, 2.5, 3.4, 4.3, 5.2], sigh=6.1, seal=7.7, strike=7.9, phone=10.2, type=10.6, tap=11.45,
               ville=13.6, tags=[14.4, 15.4, 16.4], step=17.2, end=19.9),
        beats=[0.25, 1.15, 1.95, 2.7, 3.35, 3.95, 4.5, 5.0, 5.45, 5.85, 6.2, 6.5, 6.78, 7.03, 7.26, 7.47],
        voice=[(11.65, "name", None, None), (12.6, "prologue-dehors-f", 0.0, 0.63), (14.0, "prologue-maison-f", 19.78, 24.75),
               (20.4, "nomme-f", 6.14, 9.65)],
        caps=[(11.65, 12.55, '<span class="n">Inès</span>,'), (12.6, 13.4, "Approche."),
              (14.0, 19.0, "Cette nuit, ses lettres sont apparues, cachées dans ta maison !"), (20.4, 23.9, "Joyeux anniversaire !")],
        total=24.5),
}


def sfx(c):
    T = c["t"]; ev = []
    beats = c["beats"]
    ev += [(b, "heartbig", 0.9 + 0.7 * i / len(beats)) for i, b in enumerate(beats)]
    ev += [(x, "tock", 0.7) for x in T["items"]]
    ev += [(T["seal"] - 0.03, "thud", 1.0)] + [(T["strike"] + i * 0.15 + 0.05, "tick", 0.55) for i in range(len(c["items"]))]
    ev += [(T["phone"] - 0.05, "whoosh", 0.7), (T["ville"] - 0.05, "whoosh", 0.6), (T["end"] - 0.05, "whoosh", 0.6)]
    ev += [(T["type"] + i * 0.18, "tick", 0.45) for i in range(len(c["name"]))] + [(T["tap"], "tock", 0.6)]
    return ev


def audio(c, tmp):
    parts, t = [], 0.0
    for at, key, a, b in c["voice"]:
        f = (NOMS / f"{c['name_clip']}.mp3" if key == "name" else
             REPO / "audio" / f"{key}.mp3" if key.startswith("video/") else VOIX / f"{key}.mp3")
        if a is None: a, b = 0.0, 0.8
        if at > t: parts.append((None, 0, at - t)); t = at
        parts.append((f, a, b)); t += b - a
    if c["total"] > t: parts.append((None, 0, c["total"] - t))
    base = build_audio(parts, c["total"], tmp)             # voice + the soft music of the site
    ev = sfx(c); ins, fl = ["-i", str(base)], ["[0:a]aresample=44100,aformat=channel_layouts=mono[b]"]
    for i, (at, s, g) in enumerate(ev):
        ins += ["-i", str(SONS / f"{s}.wav")]
        fl.append(f"[{i + 1}:a]aresample=44100,adelay={int(at * 1000)}:all=1,volume={g}[e{i}]")
    fl.append("[b]" + "".join(f"[e{i}]" for i in range(len(ev))) + f"amix=inputs={len(ev) + 1}:normalize=0:duration=first,alimiter=limit=0.85[a]")
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
        cc = {k: (v.as_uri() if isinstance(v, Path) else v) for k, v in c.items()}
        await pg.evaluate(f"setup({json.dumps(cc, ensure_ascii=False)})"); await pg.wait_for_timeout(600)
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
