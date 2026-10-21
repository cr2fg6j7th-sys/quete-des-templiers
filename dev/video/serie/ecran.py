# Short videos made of the real site's screens (captured by captures.py): the 2-minute set-up, what the
# adult sees on the day, the invitation and diploma, and "type the name, hear the Grand Maître".
# Invented place names are blurred; story texts and riddle answers are not shown in full.
#   python3 dev/video/serie/ecran.py [slug …]   -> out/<slug>.mp4 + .jpg
import asyncio, json, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "campagne"))
from build import build_audio, VOIX, NOMS, REPO
from clean import clean
from court import Seq, line

OUT = HERE / "out"
EC = OUT / "ecrans"
FPS = 24
LIN = (HERE.parent / "campagne/img/phone/close.jpg").as_uri()
u = lambda n: (EC / f"{n}.png").as_uri()
K = 700 / 1170              # screenshot px -> screen px
SCR_TOP = 350               # page y of the top of the screen (phone top + bezel)


def phone_y(y):             # page y of a point at screenshot y (no scroll)
    return SCR_TOP + y * K


def speedrun():
    seq = Seq(); seq.at(5.6, line("faq-preparer"))     # « Rien à imprimer, rien à cacher… je m'occupe du reste. »
    end = 10.9
    return dict(hook="Un anniversaire de chevalier,<br><b>prêt en 2 minutes</b>", chrono=[0.3, end - 0.4, 0, 112], endAt=end, total=end + 1.8,
        screens=[dict(img=u("01-accueil"), t0=0, t1=1.6, taps=[[585, 2111, 1.1]]),
                 dict(img=u("02-formulaire"), t0=1.6, t1=3.4, typed=dict(x=112, y=828, w=440, h=105, fs=46, text="Léo", t=1.9)),
                 dict(img=u("04-adresse"), t0=3.4, t1=5.4, blur=[[90, 2390, 1080, 2525]], taps=[[585, 1936, 4.8]]),
                 dict(img=u("05-apercu-long"), t0=5.4, t1=99, blur=[[300, 500, 900, 720]], scroll=0, scrollTo=900, sd=1.2, sl=1.6)],
        caps=[dict(html="1. <b>Son prénom</b>", t0=1.7, t1=3.35), dict(html="2. <b>Votre adresse</b>", t0=3.5, t1=5.35),
              dict(html="3. <b>Le parcours est prêt</b>", t0=5.6, t1=end)],
        cam=[[0, 1.0, 540, 1000], [end, 1.03, 540, 1000]]), seq.p


def jourj():
    seq = Seq(); seq.at(0.4, VOIX / "intro-dehors-m.mp3", 0.0, 4.55)   # « Chevalier de l'Ordre, la quête commence ! À chaque lieu, tu gagneras une lettre. »
    end = 10.2
    return dict(hook="Le jour de la fête,<br><b>sur votre téléphone</b> :", endAt=end, total=end + 1.8,
        screens=[dict(img=u("08-debut"), t0=0, t1=2.0, taps=[[585, 1365, 1.6]]),
                 dict(img=u("09-etape"), t0=2.0, t1=4.2, blur=[[80, 1455, 800, 1530]], taps=[[853, 2233, 3.8]]),
                 dict(img=u("10-recit"), t0=4.2, t1=6.2, blur=[[60, 760, 1110, 1200]]),
                 dict(img=u("11-enigme"), t0=6.2, t1=8.2, blur=[[80, 980, 1090, 1630]]),
                 dict(img=u("12-lettre"), t0=8.2, t1=99)],
        caps=[dict(html="Le Grand Maître <b>lance la quête</b>", t0=0.2, t1=1.95), dict(html="Un <b>indice</b> mène au lieu", t0=2.1, t1=4.15),
              dict(html="Un <b>récit</b>, puis un <b>défi</b>", t0=4.3, t1=6.15), dict(html="Une <b>énigme</b>…", t0=6.3, t1=8.15),
              dict(html="… et une <b>lettre gagnée</b> !", t0=8.3, t1=end)],
        cam=[[0, 1.0, 540, 1000], [end, 1.04, 540, 1000]]), seq.p


def offerts():
    seq = Seq(); seq.at(4.4, VOIX / "nomme-m.mp3", 5.90, 8.21)        # « Joyeux anniversaire ! »
    end = 7.9
    return dict(hook="Avec chaque quête,<br><b>c'est offert</b> :", endAt=end, total=end + 1.8,
        screens=[dict(img=u("07-invitation"), card=True, w=951, t0=0, t1=3.9),
                 dict(img=u("15-diplome"), card=True, w=951, t0=3.9, t1=99, blur=[[505, 785, 735, 842]])],
        caps=[dict(html="L'<b>invitation</b> pour les copains", t0=0.3, t1=3.85), dict(html="Un <b>diplôme</b> à son prénom", t0=4.0, t1=end)],
        cam=[[0, 1.0, 540, 1000], [end, 1.06, 540, 1000]]), seq.p


def ecouter():
    seq = Seq()
    t = seq.at(1.75, NOMS / "leo.mp3")
    seq.at(t + 0.1, VOIX / "prologue-dehors-m.mp3", 0.0, 5.7)       # « Approche. Je suis le Grand Maître de l'Ordre des Gardiens du Temple. »
    end = t + 0.1 + 5.7 + 0.3
    cy = phone_y(1600)
    return dict(hook="Tapez son prénom…<br><b>et écoutez.</b>", endAt=end, total=end + 1.8,
        screens=[dict(img=u("01-accueil"), t0=0, t1=99, typed=dict(x=105, y=1398, w=950, h=100, fs=46, text="Léo", t=0.5), taps=[[585, 1843, 1.5]])],
        caps=[dict(html="Gratuit, <b>sur le site</b>", t0=2.4, t1=end)],
        cam=[[0, 1.0, 540, 1000], [0.4, 1.0, 540, 1000], [1.3, 1.45, 540, cy], [end - 0.5, 1.5, 540, cy], [end, 1.0, 540, 1000]]), seq.p


VIDEOS = {"ecran-2-minutes": speedrun, "ecran-jour-j": jourj, "ecran-offerts": offerts, "ecran-ecouter": ecouter}


async def render(slug):
    cfg, parts = VIDEOS[slug]()
    cfg["lin"] = LIN
    page = HERE / f"_e_{slug}.html"
    page.write_text((HERE / "ecran.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/"))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = build_audio(parts or [(None, 0, 0.1)], cfg["total"], tmp)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"setup({json.dumps(cfg, ensure_ascii=False)})"); await pg.wait_for_timeout(800)
            for i in range(int(cfg["total"] * FPS)):
                await pg.evaluate(f"frame({i / FPS})")
                await pg.screenshot(path=str(tmp / f"f{i:04d}.jpg"), type="jpeg", quality=90)
            await pg.evaluate("frame(2.0)"); await pg.screenshot(path=str(OUT / f"{slug}.jpg"), type="jpeg", quality=88)
            await b.close()
        out = OUT / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.jpg"), "-i", str(a),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-c:a", "copy",
                        "-t", f"{cfg['total']:.3f}", "-movflags", "+faststart", str(out)], check=True)
        clean(out)
    page.unlink()
    print(slug, f"{cfg['total']:.1f} s", flush=True)


if __name__ == "__main__":
    for k in sys.argv[1:] or list(VIDEOS):
        asyncio.run(render(k))
