# Short viral formats (from 22 Oct 2026), built on what spreads in the niche: challenges (a riddle and a
# 5-second countdown), a first-name roulette (pause on your child's name), parents' relatable struggles
# (the party budget, the 4 kinds of parents), and the "your street, quest version" demo. 9-13 s each,
# almost no speech, a new visual every ~2 s, and one action at the end: type the child's first name on
# the site and hear the Grand Maître call it (the end card types a name and plays that name's real clip).
#   python3 dev/video/serie/court.py [slug …]   -> out/<slug>.mp4 + out/<slug>.jpg
import asyncio, json, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "campagne"))
from build import build_audio, spans, VOIX, NOMS, REPO
from clean import clean

OUT = HERE / "out"
FPS = 24
IMG = HERE / "img"
PHONE = HERE.parent / "campagne/img/phone"
PRO = VOIX / "prologue-dehors-m.mp3"
END = 3.6   # end card length
TTS = REPO / "audio/video"   # lines recorded for these videos (manifest keys video/…)


def line(key):
    """A recorded line with its long pauses shortened and a slightly quicker pace (out/voix/<key>.mp3)."""
    out = OUT / "voix" / f"{key}.mp3"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(TTS / f"{key}.mp3"), "-af",
                        "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-40dB,atempo=1.1", str(out)], check=True)
    return out


def length(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


class Seq:
    """Audio laid out on a timeline: pieces are placed at given times, silence fills the gaps."""
    def __init__(self): self.p, self.t = [], 0.0
    def at(self, t, f, a=None, b=None):
        if t > self.t: self.p.append((None, 0, t - self.t)); self.t = t
        if a is None:
            sp = spans(f); a, b = 0, sp[-1][1] + 0.04
        self.p.append((f, a, b)); self.t += b - a
        return self.t


def name_clip(n): return NOMS / f"{n}.mp3"


def end_voice(seq, end_at, name):
    """The end card types the name, then the Grand Maître says it: « <Name>… Approche. »"""
    t = seq.at(end_at + 1.35, name_clip(name))
    seq.at(t + 0.15, PRO, 0.0, 0.8)


def base(bg, total, end_at, top, name, beats, **kw):
    return dict(bg=bg.as_uri(), lin=(PHONE / "close.jpg").as_uri(), shot=(PHONE / "home.jpg").as_uri(),
                total=total, endAt=end_at, end=dict(top=top, name=name), beats=beats, **kw)


def hook(html, t0=0, t1=None, top=150):
    return dict(cls="hook", html=html, t0=t0, t1=t1, style=f"top:{top}px", din=0.01)


def defi(bg, riddle, answer, why, name, gender="m", key="herse"):
    seq = Seq(); seq.at(0.25, line(f"defi-intro-{gender}"))      # « Jeune chevalier, voici mon énigme. Trouveras-tu la réponse avant la fin ? »
    c0, rv = 2.2, 7.2
    rep_end = seq.at(rv + 0.15, line(f"defi-{key}"))               # « La herse ! Bien trouvé, jeune chevalier. »
    end_at = max(9.6, rep_end + 0.3); total = end_at + END
    beats = [hook('<span class="eb">Défi du Grand Maître</span>Ton enfant trouve en <b>5 secondes</b> ?', 0, rv),
             dict(cls="parch", html=f'<div class="q">{riddle}</div>', t0=0.45, t1=rv, anim="up", style="top:640px"),
             dict(cls="pill", html="<div>Réponse en commentaire avant la fin !</div>", t0=1.1, t1=rv, anim="pop", style="top:1150px")]
    for k in range(5):
        beats.append(dict(cls="seal", html=str(5 - k), t0=c0 + k, t1=c0 + k + 0.92, anim="pop", din=0.18, style="top:1330px"))
    beats += [dict(cls="big", html=answer, t0=rv, anim="slam", din=0.22, style="top:700px"),
              dict(cls="mid", html=why, t0=rv + 0.35, anim="up", style="top:960px"),
              dict(cls="box", html="Une énigme comme ça <b>à chaque étape</b> de la quête", t0=rv + 0.9, anim="up", style="top:1300px")]
    end_voice(seq, end_at, name)
    cfg = base(bg, total, end_at, "Tape son prénom :<br><b>le Grand Maître l'appelle</b>", name.capitalize(), beats,
               cam=[[0, 1.18, 560, 900], [total, 1.02, 540, 960]], dim=0.42, flashes=[rv])
    return cfg, seq.p


def roulette(bg, names, labels, final, final_label, gender):
    seq = Seq(); beats = [hook("<b>Arrête la vidéo</b> sur le prénom de ton enfant", 0, None),
                         dict(cls="mid", html="Le Grand Maître connaît <b>1 500 prénoms</b>", t0=0.3, anim="up", style="top:1300px")]
    t = 0.45
    for n, lab in zip(names, labels):
        a = t; t = seq.at(t, name_clip(n)) + 0.12
        beats.append(dict(cls="name", html=lab, t0=a, t1=t - 0.02, anim="slam", din=0.12, style="top:760px"))
    beats.append(dict(cls="big", html="Pas <b>le sien</b> ?", t0=t, t1=t + 1.6, anim="pop", style="top:780px"))
    v_end = seq.at(t + 0.1, line("roulette-fin"))    # « Ton prénom n'est pas passé ? Dis-le à tes parents : je t'appellerai, toi aussi. »
    end_at = t + 1.6; total = max(end_at + END, v_end + 0.5)
    cfg = base(bg, total, end_at, "Tape-le :<br><b>il l'appelle par son prénom</b>", final_label, beats,
               cam=[[0, 1.1, 540, 900], [total, 1.0, 540, 960]], dim=0.5)
    return cfg, seq.p


def budget():
    seq = Seq()
    rows = [("Trampoline park", "≈ 250 €"), ("Animateur, 2 h", "≈ 200 €"), ("Bowling + goûter", "≈ 180 €")]
    rc = '<h3>Anniversaire · 10 enfants</h3>' + "".join(f'<div class="row"><span>{a}</span><span>{b}</span><i></i></div>' for a, b in rows)
    beats = [hook("Anniversaire de 10 enfants :<br><b>le budget</b>…", 0, None),
             dict(cls="rcpt", html=rc, t0=0.35, t1=4.2, anim="up", strike=[1.6, 2.3, 3.0], style="top:620px"),
             dict(cls="big", html="Ce que j'ai fait <b>à la place</b>", t0=4.2, anim="pop", style="top:600px;font-size:96px"),
             dict(cls="box", html="Une <b>quête de chevaliers</b> dans les rues du village", t0=5.0, anim="up", style="top:900px"),
             dict(cls="box", html="<b>24,90 €</b> · rien à préparer,<br>rien à imprimer", t0=5.8, anim="up", style="top:1230px")]
    v_end = seq.at(4.4, line("budget"))     # « Pas besoin d'une fortune : pour un chevalier, toute sa ville devient une quête. »
    end_at = max(8.9, v_end + 0.3); total = end_at + END
    end_voice(seq, end_at, "jules")
    cfg = base(PHONE / "wide.jpg", total, end_at, "Essayez : <b>aperçu gratuit</b><br>avec son prénom", "Jules", beats,
               cam=[[0, 1.0, 540, 960], [total, 1.12, 540, 900]], dim=0.15)
    return cfg, seq.p


def parents():
    seq = Seq()
    T = ["Celui qui prépare depuis <b>3 semaines</b>", "Celui qui achète le gâteau <b>à 11 h</b>",
         "Celui qui cache les indices <b>à minuit</b> la veille", "Celui qui tape un prénom et une adresse… <b>et c'est prêt</b>"]
    beats = [hook("Les <b>4 types de parents</b><br>à un anniversaire", 0, None)]
    for k, s in enumerate(T):
        beats.append(dict(cls="type" + (" win" if k == 3 else ""), html=f'<span class="n">{k + 1}</span><span>{s}</span>',
                          t0=0.9 + 1.55 * k, anim="up", style=f"top:{520 + 215 * k}px"))
    beats.append(dict(cls="pill", html="<div>Tu es lequel ? Réponds en commentaire</div>", t0=6.4, anim="pop", style="top:1420px"))
    v_end = seq.at(5.6, line("parents"))   # « Et celui-là… je le nomme Chevalier de l'anniversaire ! »
    end_at = max(8.9, v_end + 0.3); total = end_at + END
    end_voice(seq, end_at, "zoe")
    cfg = base(IMG / "ville.jpg", total, end_at, "Deviens le <b>n° 4</b> :<br>tape son prénom", "Zoé", beats,
               cam=[[0, 1.1, 560, 1000], [total, 1.0, 540, 960]], dim=0.55)
    return cfg, seq.p


def rue():
    seq = Seq(); sw = 3.4
    plain = [(150, 1450, "Boulangerie"), (640, 1220, "Arrêt de bus"), (640, 990, "Église")]
    gold = [(150, 1450, "<b>1</b> · La source enchantée"), (560, 1220, "<b>2</b> · Le repaire du dragon"), (420, 990, "<b>3</b> · Le clocher secret")]
    beats = [hook("Pour toi, c'est<br><b>la rue de la boulangerie</b>.", 0, sw),
             hook("Pour lui, <b>le jour de<br>son anniversaire</b>…", sw, None)]
    for k, (x, y, s) in enumerate(plain):
        beats.append(dict(cls="tag plain", html=s, inScene=True, t0=0.5 + 0.5 * k, t1=sw, anim="pop", style=f"left:{x}px;top:{y}px"))
    for k, (x, y, s) in enumerate(gold):
        beats.append(dict(cls="tag gold", html=s, inScene=True, t0=sw + 0.9 + 1.4 * k, anim="pop", style=f"left:{x}px;top:{y}px"))
    v_end = seq.at(sw + 0.4, line("rue"))   # « Pour un chevalier, chaque rue cache une aventure. Suis le chemin doré ! »
    end_at = v_end + 0.4; total = end_at + END
    end_voice(seq, end_at, "hugo")
    cfg = base(IMG / "ville.jpg", total, end_at, "La quête se crée avec<br><b>les vrais lieux</b> autour de chez vous", "Hugo", beats,
               cam=[[0, 1.12, 540, 1150], [sw, 1.12, 540, 1150], [sw + 1.5, 1.0, 540, 960], [total, 1.0, 540, 960]],
               grayUntil=sw, flashes=[sw], veilK=[[0, 0.15], [sw, 0.15], [sw + 0.01, 0.0], [total, 0.0]],
               path=dict(pts=[[540, 1760], [542, 1483], [552, 1300], [571, 1128], [576, 1040], [700, 960], [770, 760], [660, 640]], t0=sw + 0.5, t1=end_at - 0.6))
    return cfg, seq.p


VIDEOS = {
    "defi-herse": lambda: defi(IMG / "ville.jpg", "J'ai des <b>dents</b>, mais je ne mords jamais. Je garde la porte du château. <b>Qui suis-je&nbsp;?</b>",
                               "La <b>herse</b> !", "La grille à dents qui fermait la porte du château", "lucas"),
    "defi-trou": lambda: defi(IMG / "cherche.jpg", "Plus on m'en <b>enlève</b>, plus je deviens <b>grand</b>. <b>Qui suis-je&nbsp;?</b>",
                              "Un <b>trou</b> !", "Comme les douves creusées autour du château", "ines", "f", "trou"),
    "prenoms-garcons": lambda: roulette(IMG / "gateau.jpg", ["gabriel", "leo", "raphael", "louis", "arthur", "jules", "adam", "mael"],
                                        ["Gabriel", "Léo", "Raphaël", "Louis", "Arthur", "Jules", "Adam", "Maël"], "noah", "Noah", "m"),
    "prenoms-filles": lambda: roulette(IMG / "ville.jpg", ["jade", "louise", "ambre", "alba", "emma", "rose", "alice", "romy"],
                                       ["Jade", "Louise", "Ambre", "Alba", "Emma", "Rose", "Alice", "Romy"], "lina", "Lina", "f"),
    "budget": budget,
    "parents": parents,
    "rue": rue,
}


async def render(slug):
    cfg, parts = VIDEOS[slug]()
    OUT.mkdir(parents=True, exist_ok=True)
    page = HERE / f"_c_{slug}.html"
    page.write_text((HERE / "court.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/"))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = build_audio(parts, cfg["total"], tmp)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"setup({json.dumps(cfg, ensure_ascii=False)})"); await pg.wait_for_timeout(500)
            for i in range(int(cfg["total"] * FPS)):
                await pg.evaluate(f"frame({i / FPS})")
                await pg.screenshot(path=str(tmp / f"f{i:04d}.jpg"), type="jpeg", quality=90)
            await pg.evaluate("frame(1.6)"); await pg.screenshot(path=str(OUT / f"{slug}.jpg"), type="jpeg", quality=88)
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
