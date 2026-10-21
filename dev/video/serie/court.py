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
from boucle import boucle

OUT = HERE / "out"
FPS = 24
IMG = HERE / "img"
PHONE = HERE.parent / "campagne/img/phone"
PRO = VOIX / "prologue-dehors-m.mp3"
END = 2.3   # end card length (short: a long end card reads as an ad)
TTS = REPO / "audio/video"   # lines recorded for these videos (manifest keys video/…)


def line(key):
    """A recorded line with its long pauses shortened and a slightly quicker pace (out/voix/<key>.mp3)."""
    out = OUT / "voix" / f"{key}.mp3"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(TTS / f"{key}.mp3"), "-af",
                        "silenceremove=stop_periods=-1:stop_duration=0.15:stop_threshold=-40dB,atempo=1.22", str(out)], check=True)
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
    t = seq.at(end_at + 0.55, name_clip(name))
    seq.at(t + 0.08, PRO, 0.0, 0.8)


def base(bg, total, end_at, top, name, beats, **kw):
    return dict(bg=bg.as_uri(), lin=(PHONE / "close.jpg").as_uri(), shot=(PHONE / "home.jpg").as_uri(),
                total=total, endAt=end_at, end=dict(top=top, name=name), beats=beats, **kw)


def hook(html, t0=0, t1=None, top=150):
    return dict(cls="hook", html=html, t0=t0, t1=t1, style=f"top:{top}px", din=0.01)


def defi(bg, riddle, answer, why, name, gender="m", key="herse"):
    seq = Seq(); seq.at(0.25, line("defi-intro"))      # « Parents, voici l'une de mes énigmes. Votre enfant trouvera-t-il avant la fin ? »
    c0, rv = 1.4, 4.4
    rep_end = seq.at(rv + 0.15, line(f"defi-{key}"))               # « La herse ! Des énigmes comme celle-là attendent votre enfant, dans les rues de votre ville. »
    end_at = rep_end + 0.25; total = end_at + END
    beats = [hook('<span class="eb">Défi du Grand Maître</span>Votre enfant trouve en <b>3 secondes</b> ?', 0, rv),
             dict(cls="parch", html=f'<div class="q">{riddle}</div>', t0=0.45, t1=rv, anim="up", style="top:640px"),
             dict(cls="pill", html="<div>Réponse en commentaire avant la fin !</div>", t0=1.1, t1=rv, anim="pop", style="top:1150px")]
    for k in range(3):
        beats.append(dict(cls="seal", html=str(3 - k), t0=c0 + k, t1=c0 + k + 0.92, anim="pop", din=0.18, style="top:1330px"))
    beats += [dict(cls="big", html=answer, t0=rv, anim="slam", din=0.22, style="top:700px"),
              dict(cls="mid", html=why, t0=rv + 0.35, anim="up", style="top:960px"),
              dict(cls="box", html="Une énigme comme ça <b>à chaque étape</b> de la quête", t0=rv + 0.9, anim="up", style="top:1300px")]
    end_voice(seq, end_at, name)
    cfg = base(bg, total, end_at, "Tapez son prénom :<br><b>le Grand Maître l'appelle</b>", name.capitalize(), beats,
               cam=[[0, 1.18, 560, 900], [total, 1.02, 540, 960]], dim=0.42, flashes=[rv])
    return cfg, seq.p


def roulette(bg, names, labels, final, final_label, gender):
    seq = Seq(); beats = [hook("<b>Arrêtez la vidéo</b> sur le prénom de votre enfant", 0, None),
                         dict(cls="mid", html="Le Grand Maître connaît <b>1 500 prénoms</b>", t0=0.3, anim="up", style="top:1300px")]
    t = 0.45
    for n, lab in zip(names, labels):
        a = t; t = seq.at(t, name_clip(n)) + 0.05
        beats.append(dict(cls="name", html=lab, t0=a, t1=t - 0.02, anim="slam", din=0.12, style="top:760px"))
    beats.append(dict(cls="big", html="Pas <b>le sien</b> ?", t0=t, t1=t + 1.2, anim="pop", style="top:780px"))
    v_end = seq.at(t + 0.1, line("roulette-fin"))    # « Le prénom de votre enfant n'est pas passé ? Tapez-le sur le site : je l'appellerai. »
    end_at = t + 1.2; total = max(end_at + END, v_end + 0.3)
    cfg = base(bg, total, end_at, "Tapez-le :<br><b>il l'appelle par son prénom</b>", final_label, beats,
               cam=[[0, 1.1, 540, 900], [total, 1.0, 540, 960]], dim=0.5)
    return cfg, seq.p


def budget():
    seq = Seq()
    rows = [("Trampoline park", "≈ 250 €"), ("Animateur, 2 h", "≈ 200 €"), ("Bowling + goûter", "≈ 180 €")]
    rc = '<h3>Anniversaire · 10 enfants</h3>' + "".join(f'<div class="row"><span>{a}</span><span>{b}</span><i></i></div>' for a, b in rows)
    beats = [hook("Anniversaire de 10 enfants :<br><b>le budget</b>…", 0, None),
             dict(cls="rcpt", html=rc, t0=0.3, t1=3.2, anim="up", strike=[1.1, 1.7, 2.3], style="top:620px"),
             dict(cls="big", html="Ce que j'ai fait <b>à la place</b>", t0=3.2, anim="pop", style="top:600px;font-size:96px"),
             dict(cls="box", html="Une <b>quête de chevaliers</b> dans les rues du village", t0=4.0, anim="up", style="top:900px"),
             dict(cls="box", html="<b>24,90 €</b> · rien à préparer,<br>rien à imprimer", t0=4.8, anim="up", style="top:1230px")]
    v_end = seq.at(3.3, line("budget"))     # « Pas besoin d'une fortune. Donnez-moi une adresse : je transforme votre quartier en quête de chevaliers. »
    end_at = v_end + 0.25; total = end_at + END
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
                          t0=0.7 + 1.15 * k, anim="up", style=f"top:{520 + 215 * k}px"))
    beats.append(dict(cls="pill", html="<div>Vous êtes lequel ? Répondez en commentaire</div>", t0=4.9, anim="pop", style="top:1420px"))
    v_end = seq.at(4.2, line("parents"))   # « Soyez ce parent-là : un prénom, une adresse, et je m'occupe du reste. »
    end_at = v_end + 0.25; total = end_at + END
    end_voice(seq, end_at, "zoe")
    cfg = base(IMG / "ville.jpg", total, end_at, "Devenez le <b>n° 4</b> :<br>tapez son prénom", "Zoé", beats,
               cam=[[0, 1.1, 560, 1000], [total, 1.0, 540, 960]], dim=0.55)
    return cfg, seq.p


def rue():
    seq = Seq(); sw = 2.3      # the voice says « Pour vous, une rue ordinaire. » before the switch
    plain = [(150, 1450, "Boulangerie"), (640, 1220, "Arrêt de bus"), (640, 990, "Église")]
    gold = [(150, 1450, "<b>1</b> · La source enchantée"), (560, 1220, "<b>2</b> · Le repaire du dragon"), (420, 990, "<b>3</b> · Le clocher secret")]
    beats = [hook("Pour vous, c'est<br><b>la rue de la boulangerie</b>.", 0, sw),
             hook("Pour votre enfant, <b>le jour<br>de son anniversaire</b>…", sw, None)]
    for k, (x, y, s) in enumerate(plain):
        beats.append(dict(cls="tag plain", html=s, inScene=True, t0=0.5 + 0.5 * k, t1=sw, anim="pop", style=f"left:{x}px;top:{y}px"))
    for k, (x, y, s) in enumerate(gold):
        beats.append(dict(cls="tag gold", html=s, inScene=True, t0=sw + 0.9 + 1.4 * k, anim="pop", style=f"left:{x}px;top:{y}px"))
    v_end = seq.at(0.3, line("rue"))   # « Pour vous, une rue ordinaire. Pour votre enfant, le jour de son anniversaire : une vraie aventure de chevalier. »
    end_at = v_end + 0.25; total = end_at + END
    end_voice(seq, end_at, "hugo")
    cfg = base(IMG / "ville.jpg", total, end_at, "La quête se crée avec<br><b>les vrais lieux</b> autour de chez vous", "Hugo", beats,
               cam=[[0, 1.12, 540, 1150], [sw, 1.12, 540, 1150], [sw + 1.5, 1.0, 540, 960], [total, 1.0, 540, 960]],
               grayUntil=sw, flashes=[sw], veilK=[[0, 0.15], [sw, 0.15], [sw + 0.01, 0.0], [total, 0.0]],
               path=dict(pts=[[540, 1760], [542, 1483], [552, 1300], [571, 1128], [576, 1040], [700, 960], [770, 760], [660, 640]], t0=sw + 0.5, t1=end_at - 0.6))
    return cfg, seq.p



def faq(key, bg, hook_html, items, end_top, name, name_label, dim=0.45, cam=None, **kw):
    """Parents' question videos: the question as a big hook from frame 0, the Grand Maître answers at once
    (audio/video/faq-<key>.mp3), the answer's points appear while he speaks, then the site end card."""
    seq = Seq(); f = line(f"faq-{key}")
    v0 = 0.35; v = length(f); seq.at(v0, f)
    beats = [hook(hook_html, 0, None)]
    for it in items:
        it = dict(it); fr = it.pop("at"); it.setdefault("anim", "up"); it["t0"] = round(v0 + fr * v, 2)
        beats.append(it)
    end_at = v0 + v + 0.25; total = end_at + END
    end_voice(seq, end_at, name)
    cfg = base(bg, total, end_at, end_top, name_label, beats, cam=cam or [[0, 1.15, 540, 960], [total, 1.0, 540, 960]], dim=dim, **kw)
    return cfg, seq.p


def box(html, at, top, **k): return dict(cls="box", html=html, at=at, style=f"top:{top}px", **k)
def typ(n, html, at, top, win=False): return dict(cls="type" + (" win" if win else ""), html=f'<span class="n">{n}</span><span>{html}</span>', at=at, style=f"top:{top}px")
def tag(html, at, x, y): return dict(cls="tag gold", html=html, at=at, inScene=True, anim="pop", style=f"left:{x}px;top:{y}px")
def rcpt(title, rows, at, top, strike=None):
    h = f"<h3>{title}</h3>" + "".join(f'<div class="row"><span>{a}</span><span>{b}</span><i></i></div>' for a, b in rows)
    d = dict(cls="rcpt", html=h, at=at, style=f"top:{top}px")
    if strike: d["strike"] = strike
    return d


TOWN_PATH = [[540, 1760], [542, 1483], [552, 1300], [571, 1128], [576, 1040], [700, 960], [770, 760], [660, 640]]

FAQ = {
    "faq-presentation": lambda: faq("presentation", IMG / "ville.jpg", "Parents : <b>je m'occupe</b><br>de l'anniversaire.",
        [tag("<b>1</b> · Fontaine : une énigme", 0.25, 150, 1450), tag("<b>2</b> · Église : un défi", 0.45, 420, 990),
         tag("<b>3</b> · Le mot secret", 0.65, 420, 600),
         box("<b>1 prénom</b> + <b>1 adresse</b><br>= une quête de chevaliers", 0.8, 1560)],
        "Essayez avec <b>son prénom</b>", "louise", "Louise", dim=0.1,
        path=dict(pts=TOWN_PATH, t0=0.8, t1=5.5)),
    "faq-preparer": lambda: faq("preparer", PHONE / "wide.jpg", "Ce qu'il faut <b>préparer</b> :",
        [rcpt("À faire", [("Imprimer les indices", ""), ("Cacher les indices", ""), ("Écrire les énigmes", "")], 0.0, 560, strike=[1.3, 2.0, 2.7]),
         box("Un petit trésor dans votre sac.<br><b>C'est tout.</b>", 0.5, 1200)],
        "Prête en <b>2 minutes</b> :<br>tapez son prénom", "gabriel", "Gabriel", dim=0.15),
    "faq-pluie": lambda: faq("pluie", IMG / "pluie.jpg", "Il pleut <b>le jour J</b> ?",
        [box("<b>Mode maison</b> : 6 cartes à cacher", 0.2, 600), box("<b>5 minutes</b> de préparation", 0.45, 820),
         box("Énigmes et défis <b>faits pour l'intérieur</b>", 0.7, 1040)],
        "Dehors ou dedans :<br><b>tapez son prénom</b>", "jade", "Jade", dim=0.35),
    "faq-securite": lambda: faq("securite", IMG / "ville.jpg", "10 enfants dans la rue…<br><b>c'est prudent ?</b>",
        [typ(1, "À pied, autour du <b>point de départ</b>", 0.1, 560), typ(2, "Que des <b>lieux publics</b>, on n'entre nulle part", 0.35, 775),
         typ(3, "<b>1 adulte</b> pour 5 enfants environ", 0.6, 990), typ(4, "Défis sur une <b>place</b> ou dans un <b>parc</b>", 0.8, 1205, True)],
        "Un parcours <b>tout près</b><br>de chez vous", "arthur", "Arthur", dim=0.55),
    "faq-village": lambda: faq("village", IMG / "village.jpg", "Petit village ?<br><b>Ça marche aussi.</b>",
        [tag("<b>1</b> · Église", 0.15, 300, 640), tag("<b>2</b> · Fontaine", 0.3, 600, 1100), tag("<b>3</b> · Vieille maison", 0.45, 120, 1010),
         tag("<b>4</b> · Mairie", 0.6, 700, 1180), box("<b>Aperçu gratuit</b> : vous savez<br>avant de payer", 0.75, 1520)],
        "Testez <b>votre village</b><br>avec son prénom", "hugo", "Hugo", dim=0.1),
    "faq-prenom": lambda: faq("prenom", IMG / "gateau.jpg", "Prénom rare ?<br><b>Pas de souci.</b>",
        [dict(cls="name", html="Gabriel", at=0.0, t1=1.2, anim="slam", din=0.12, style="top:640px"),
         dict(cls="name", html="Inès", at=0.12, t1=2.4, anim="slam", din=0.12, style="top:640px"),
         dict(cls="big", html="+ de <b>1 000</b> prénoms", at=0.3, anim="pop", style="top:660px"),
         dict(cls="parch", html='<div class="q"><b>Diplôme de chevalier</b><br>décerné à</div><div style="font-family:UnifrakturMaguntia,serif;font-size:120px;line-height:1.1;color:#8e1f24">Kaïs</div>', at=0.6, style="top:960px")],
        "Tapez son prénom :<br><b>écoutez-le</b>", "ines", "Inès", dim=0.5),
    "faq-appli": lambda: faq("appli", PHONE / "wide.jpg", "<b>Pas d'appli</b><br>à installer.",
        [box("S'ouvre dans le <b>navigateur</b> du téléphone", 0.1, 560), box("Le lien se partage à <b>un autre adulte</b>", 0.35, 780),
         dict(cls="parch", html='<div class="q"><b>Oyez, oyez !</b><br>Léo t\'invite à sa quête de chevaliers<br>samedi à 14 h</div>', at=0.6, style="top:1020px")],
        "Préparez-la <b>dès ce soir</b>", "leo", "Léo", dim=0.2),
    "activite-vacances": lambda: faq("presentation", IMG / "ville.jpg", "Vacances de la Toussaint :<br><b>on fait quoi demain ?</b>",
        [tag("<b>1</b> · Fontaine : une énigme", 0.2, 150, 1450), tag("<b>2</b> · Église : un défi", 0.4, 420, 990),
         box("1 heure dehors, <b>sans écran</b>", 0.55, 1230),
         dict(cls="pill", html="<div>Quête <b>offerte</b> jusqu'au 6 novembre</div>", at=0.75, anim="pop", style="top:1560px")],
        "Offerte jusqu'au 6 novembre :<br><b>écrivez CHEVALIER</b>", "jules", "Jules", dim=0.1,
        path=dict(pts=TOWN_PATH, t0=0.8, t1=5.0)),
    "activite-mercredi": lambda: faq("presentation", IMG / "village.jpg", "Mercredi après-midi…<br><b>encore les écrans ?</b>",
        [tag("<b>1</b> · Église", 0.15, 300, 640), tag("<b>2</b> · Fontaine", 0.3, 600, 1100),
         box("Une quête de chevaliers<br><b>dans votre quartier</b>", 0.45, 1260),
         dict(cls="pill", html="<div>Quête <b>offerte</b> jusqu'au 6 novembre</div>", at=0.7, anim="pop", style="top:1560px")],
        "Offerte jusqu'au 6 novembre :<br><b>écrivez CHEVALIER</b>", "lina", "Lina", dim=0.1),
    "faq-prix": lambda: faq("prix", IMG / "cherche.jpg", "Combien ça coûte ?",
        [rcpt("Ma Quête Légendaire", [("Aperçu de la quête", "Gratuit"), ("Quête complète", "24,90 €"), ("Enfants", "4 à 15"), ("Durée", "≈ 1 h")], 0.05, 520),
         box("Anniversaire, fête, <b>mercredi entre copains</b>", 0.6, 1160)],
        "Commencez par<br><b>l'aperçu gratuit</b>", "emma", "Emma", dim=0.45),
}


VIDEOS = {
    "defi-herse": lambda: defi(IMG / "ville.jpg", "J'ai des <b>dents</b>, mais je ne mords jamais. Je garde la porte du château. <b>Qui suis-je&nbsp;?</b>",
                               "La <b>herse</b> !", "La grille à dents qui fermait la porte du château", "lucas"),
    "defi-trou": lambda: defi(IMG / "cherche.jpg", "Plus on m'en <b>enlève</b>, plus je deviens <b>grand</b>. <b>Qui suis-je&nbsp;?</b>",
                              "Un <b>trou</b> !", "Comme les douves creusées autour du château", "ines", "f", "trou"),
    "prenoms-garcons": lambda: roulette(IMG / "gateau.jpg", ["gabriel", "leo", "louis", "arthur", "jules", "mael"],
                                        ["Gabriel", "Léo", "Louis", "Arthur", "Jules", "Maël"], "noah", "Noah", "m"),
    "prenoms-filles": lambda: roulette(IMG / "ville.jpg", ["jade", "louise", "ambre", "emma", "rose", "alice"],
                                       ["Jade", "Louise", "Ambre", "Emma", "Rose", "Alice"], "lina", "Lina", "f"),
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
        boucle(out); clean(out)   # seamless loop
    page.unlink()
    print(slug, f"{cfg['total']:.1f} s", flush=True)


VIDEOS.update(FAQ)

if __name__ == "__main__":
    for k in sys.argv[1:] or list(VIDEOS):
        asyncio.run(render(k))
