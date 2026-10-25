# Vidéos animées « idée à enregistrer » (25 Oct 2026). Après l'analyse de la niche (les vidéos qui marchent donnent une
# idée utile au parent), Nathan : « fais les vidéos que tu peux faire gratuitement ». Faites uniquement avec les fichiers
# du flyer (labyrinthe, mots cachés, blason), les voix déjà enregistrées, la musique du site et les bruitages maison :
# aucune dépense. La promesse est lisible dès la première image ; appel unique : « Écris CHEVALIER » = PDF offert.
#   python3 dev/video/anime/anime.py [slug …]   -> marketing/videos-anime/<slug>.mp4 + .jpg
import asyncio, json, re, subprocess, sys, tempfile, unicodedata
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
REPO = HERE.parents[2]
sys.path[:0] = [str(HERE.parent / "campagne"), str(HERE.parent)]
from build import build_audio, spans, VOIX
from clean import clean

FPS = 30
OUT = REPO / "marketing/videos-anime"
SONS = HERE.parent / "accroche/sons"
TTS = REPO / "audio/video"
FLY = REPO / "dev/flyers/svg"

CTA = "Écris <b>CHEVALIER</b> en commentaire :<br>les jeux en PDF te sont offerts"


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


def quick(src, name, tempo=1.15):
    """A recorded line with long pauses shortened and a slightly quicker pace."""
    out = HERE / "out/voix" / f"{name}.mp3"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-af",
                        f"silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=-1:stop_duration=0.2:stop_threshold=-40dB,atempo={tempo}",
                        str(out)], check=True)
    return out


# ---------- flyer material ----------
def maze():
    s = (FLY / "labyrinthe-1.svg").read_text()
    d = re.search(r'<path d="([^"]+)"', s).group(1)
    W = {(int(x), int(y), k) for x, y, k, _ in re.findall(r"M(\d+) (\d+)([hv])(\d+)", d)}
    def wall(r, c, dr, dc):
        x, y = c * 22, r * 22
        return {(-1, 0): (x, y, "h"), (1, 0): (x, y + 22, "h"), (0, -1): (x, y, "v"), (0, 1): (x + 22, y, "v")}[(dr, dc)] in W
    prev, q = {(0, 0): None}, [(0, 0)]
    while q:
        r, c = q.pop(0)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (r + dr, c + dc)
            if 0 <= n[0] < 9 and 0 <= n[1] < 9 and n not in prev and not wall(r, c, dr, dc):
                prev[n] = (r, c); q.append(n)
    p, n = [], (8, 8)
    while n: p.append(list(n)); n = prev[n]
    return s, p[::-1]


GRID = "DRTTRNEH ERSNACFU CBAJEPEE AAIGRVNO NUSTOURP EMDQBNER RGIOUJOO SNUMTEUI".split()
WORDS = ["ÉPÉE", "ROI", "CASQUE", "TOUR", "DRAGON"]


def word_pos():
    plain = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    out = []
    for w in WORDS:
        w = plain(w)
        hits = [[r, c, dr, dc, len(w)] for r in range(8) for c in range(8) for dr, dc in ((0, 1), (1, 0), (1, 1), (-1, 1))
                if all(0 <= r + dr * i < 8 and 0 <= c + dc * i < 8 and GRID[r + dr * i][c + dc * i] == ch for i, ch in enumerate(w))]
        assert len(hits) == 1, w
        out.append(hits[0])
    return out


def seal_svg():
    bord = (FLY / "sceau-bord.txt").read_text().strip()
    return (f'<svg viewBox="-30 -30 60 60"><path d="{bord}" fill="#a33f4b" stroke="#7d2a35" stroke-width=".6"/>'
            '<circle r="17.5" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.2"/></svg>')


# ---------- building blocks ----------
def T(cls, html, t0, top, t1=None, anim="up", **k):
    return dict(cls=cls, html=html, t0=t0, t1=t1, anim=anim, style=f"top:{top}px", **k)


def head(kw, title):
    return [T("kw", kw, 0, 96, anim=None, din=0.01), T("title", title, 0, 160, anim=None, din=0.01)]


def countdown(start, n, top):
    return [dict(type="seal", html=str(n - k), t0=start + k, t1=start + k + 0.92, style=f"top:{top}px", din=0.15) for k in range(n)]


def ticks(start, n):
    return [(start + k, "heartbig", 0.9 + 0.4 * k / n) for k in range(n)]


# ---------- the videos ----------
def v_labyrinthe():
    svg, path = maze()
    cd, n = 1.6, 5
    ts, te = cd + n + 0.2, cd + n + 4.2
    els = head("Jeu d'anniversaire chevalier · à imprimer", "DÉFI : sors le chevalier <em>avant ton enfant</em>")
    els += [dict(type="maze", cls="parch", html=svg, t0=0, din=0.01, style="top:470px", path=path, ts=ts, te=te),
            T("bubble", "<div>Ton temps en commentaire !</div>", 0.7, 1290, t1=cd + n, anim="pop")]
    els += countdown(cd, n, 1420)
    els += [T("mid", "Le chemin <em>du chevalier</em>", ts, 1300, t1=te + 0.2, anim="pop"),
            T("box", "<div>Labyrinthe, mots cachés, blason :<br>le PDF à imprimer est <b>offert</b></div>", te + 0.3, 1330)]
    end = te + 2.4
    sfx = ticks(cd, n) + [(ts - 0.05, "whoosh", 0.8)] + [(ts + 0.25 * i, "tick", 0.35) for i in range(16)] + [(te, "tock", 0.8), (end - 0.05, "whoosh", 0.6)]
    return dict(els=els, beats=[cd + k for k in range(n)], flashes=[ts], end=dict(at=end, sub="Et le jour J, <em>une vraie quête</em> de chevaliers dans ta ville", cta=CTA),
                total=end + 3.0, voice=[], sfx=sfx, cover=0.6)


def v_mots_caches():
    pos = word_pos()
    v = quick(TTS / "defi-intro.mp3", "defi-intro")
    vd = dur(v); cd, n = 0.3 + vd + 0.2, 5
    rv = cd + n + 0.1
    times = [rv + 0.7 * i for i in range(5)]
    grid = '<div class="grid">' + "".join(f"<span>{c}</span>" for row in GRID for c in row) + "</div>"
    words = '<div class="words">' + " · ".join(f"<b>{w}</b>" for w in WORDS) + "</div>"
    els = head("Jeu d'anniversaire chevalier · mots cachés", "5 mots de chevalier cachés. <em>Tu les trouves&nbsp;?</em>")
    els += [dict(type="grid", cls="parch", html=grid + words, t0=0, din=0.01, style="top:450px", words=pos, times=times),
            T("bubble", "<div>Combien en commentaire&nbsp;?</div>", 0.7, 1450, t1=cd + n, anim="pop")]
    els += countdown(cd, n, 1580)
    els += [T("box", "<div>Une épreuve comme ça <b>à chaque étape</b><br>de la quête</div>", times[-1] + 0.6, 1470)]
    end = times[-1] + 2.6
    sfx = ticks(cd, n) + [(x, "tock", 0.7) for x in times] + [(rv - 0.05, "whoosh", 0.7), (end - 0.05, "whoosh", 0.6)]
    caps = [(0.3, 0.3 + vd * 0.45, "Parents, voici l'une de mes énigmes."), (0.3 + vd * 0.45, 0.3 + vd + 0.1, "Votre enfant trouvera-t-il avant la fin ?")]
    return dict(els=els, beats=[cd + k for k in range(n)], flashes=[rv], caps=caps,
                end=dict(at=end, sub="Une quête de chevaliers <em>au prénom de ton enfant</em>", cta=CTA),
                total=end + 3.0, voice=[(0.3, v)], sfx=sfx, cover=0.6)


def v_message_code():
    v = quick(TTS / "defi-intro.mp3", "defi-intro")
    vd = dur(v); cd, n = 0.3 + vd + 0.2, 5
    rv = cd + n + 0.1
    nums, word = [2, 18, 1, 22, 5], "BRAVE"
    times = [rv + 0.35 * i for i in range(5)]
    code = '<div class="code">' + "".join(f'<div class="c"><div class="n">{x}</div><div class="l"><span>{ch}</span></div></div>' for x, ch in zip(nums, word)) + "</div>"
    hint = '<div class="hint">Indice : <b>A = 1</b>, B = 2, C = 3…</div>'
    els = head("Énigme de chevalier pour enfants", "Le message secret du Grand Maître : <em>tu le décodes&nbsp;?</em>")
    els += [dict(type="code", cls="parch", html=code + hint, t0=0, din=0.01, style="top:520px", times=times),
            T("bubble", "<div>Ta réponse en commentaire !</div>", 0.7, 1150, t1=cd + n, anim="pop")]
    els += countdown(cd, n, 1290)
    els += [T("mid", "BRAVE : <em>le mot secret</em> des chevaliers", times[-1] + 0.4, 1150, anim="pop"),
            T("box", "<div>Une énigme comme ça <b>à chaque étape</b><br>de la quête</div>", times[-1] + 1.0, 1360)]
    end = times[-1] + 3.0
    sfx = ticks(cd, n) + [(x, "thud", 0.5) for x in times] + [(end - 0.05, "whoosh", 0.6)]
    caps = [(0.3, 0.3 + vd * 0.45, "Parents, voici l'une de mes énigmes."), (0.3 + vd * 0.45, 0.3 + vd + 0.1, "Votre enfant trouvera-t-il avant la fin ?")]
    return dict(els=els, beats=[cd + k for k in range(n)], flashes=[rv], caps=caps,
                end=dict(at=end, sub="Des énigmes, des défis, <em>un mot secret</em> à la fin", cta=CTA),
                total=end + 3.0, voice=[(0.3, v)], sfx=sfx, cover=0.6)


CLUES = {
    "oreiller": ("Cette lettre dort là où tu poses ta tête chaque soir, pour rêver de dragons et de chevaliers.", "Sous l'oreiller !"),
    "canape": ("Cette lettre est cachée sous un nuage tout doux, là où toute la famille s'assoit le soir.", "Sous un coussin<br>du canapé !"),
}


def v_cachette(key):
    clue, ans = CLUES[key]
    v = quick(VOIX / f"cachette-{key}.mp3", f"cachette-{key}", tempo=1.1)
    vd = dur(v); cd, n = 0.4 + vd + 0.2, 3
    rv = cd + n + 0.05
    card = f'<div class="riddle"><span class="eb">L\'énigme du Grand Maître</span>« {clue} »</div>'
    els = head("Anniversaire chevalier à la maison", "Où est cachée la lettre&nbsp;? <em>Devine avant la fin</em>")
    els += [T("parch", card, 0, 560, anim=None, din=0.01),
            T("bubble", "<div>Ta réponse en commentaire !</div>", 0.7, 1150, t1=cd + n, anim="pop")]
    els += countdown(cd, n, 1300)
    els += [T("answer", ans, rv, 1150, anim="slam"),
            T("box", "<div><b>6 cachettes</b> comme ça dans la <b>quête à la maison</b></div>", rv + 0.9, 1480)]
    end = rv + 3.2
    sfx = ticks(cd, n) + [(rv - 0.03, "thud", 1.0), (end - 0.05, "whoosh", 0.6)]
    return dict(els=els, beats=[cd + k for k in range(n)], flashes=[rv], caps=[],
                end=dict(at=end, sub="Il pleut ? <em>La quête se joue à la maison</em>", cta=CTA),
                total=end + 3.0, voice=[(0.4, v)], sfx=sfx, cover=0.6)


def v_blason():
    svg = (FLY / "armoiries.svg").read_text()
    ts, te = 0.9, 9.0
    colors = ["#c0392b", "#e0b23c", "#2f5fa8", "#2e8b57", "#e0b23c", "#c0392b", "#d9dde3", "#2f5fa8"]
    els = head("Atelier blason · anniversaire chevalier", "Le blason de chevalier <em>à colorier</em>")
    els += [dict(type="blason", cls="parch", html=svg, t0=0, din=0.01, style="top:400px;left:120px;right:120px", ts=ts, te=te, colors=colors),
            T("bubble", "<div>Écris CHEVALIER : je t'envoie le PDF</div>", 0.8, 1500, t1=te, anim="pop"),
            T("box", "<div>Les couleurs des chevaliers :<br><b>or, gueules, azur, sinople</b></div>", te + 0.2, 1480)]
    end = te + 2.8
    sfx = [(ts + 0.45 * i, "tick", 0.3) for i in range(int((te - ts) / 0.45))] + [(te, "tock", 0.8), (end - 0.05, "whoosh", 0.6)]
    return dict(els=els, beats=[], flashes=[], caps=[], end=dict(at=end, sub="Un atelier blason, puis <em>une vraie quête</em> de chevaliers", cta=CTA),
                total=end + 3.0, voice=[], sfx=sfx, cover=4.0)


def v_jeux_pluie():
    items = [("Le dragon endormi", "Yeux bandés, il garde le trésor. Approchez sans bruit !"),
             ("Le pont-levis", "Une écharpe tendue qui descend à chaque tour."),
             ("Le siège du château", "Une tour de gobelets, des chaussettes en boule."),
             ("La joute aux ballons", "À genoux sur un coussin, ballon contre ballon."),
             ("La chasse aux lettres", "6 cartes cachées dans la maison, un mot secret à former.")]
    els = head("Anniversaire chevalier à la maison", "Il pleut le jour J&nbsp;? <em>5 jeux de chevaliers</em>")
    tt = [0.0] + [1.2 + 1.7 * i for i in range(4)]
    for i, ((h, p), t0) in enumerate(zip(items, tt)):
        els.append(T("item", f'<span class="n">{i + 1}</span><div><h4>{h}</h4><p>{p}</p></div>', t0, 470 + 225 * i, din=0.01 if i == 0 else None))
    els.append(T("save", "<div>Enregistre pour l'anniversaire</div>", 0.4, 1620, anim="pop"))
    end = tt[-1] + 3.2
    sfx = [(x, "tock", 0.7) for x in tt] + [(end - 0.05, "whoosh", 0.6)]
    return dict(els=els, beats=[], flashes=[], caps=[], end=dict(at=end, sub="Et la chasse aux lettres ? <em>Le Grand Maître donne les énigmes</em>", cta=CTA),
                total=end + 3.0, voice=[], sfx=sfx, cover=0.6)


VIDEOS = {"defi-labyrinthe": v_labyrinthe, "defi-mots-caches": v_mots_caches, "message-code": v_message_code,
          "devine-oreiller": lambda: v_cachette("oreiller"), "devine-canape": lambda: v_cachette("canape"),
          "blason-a-colorier": v_blason, "jeux-pluie": v_jeux_pluie}


# ---------- render ----------
def audio(c, tmp):
    parts, t = [], 0.0
    for at, f in c["voice"]:
        if at > t: parts.append((None, 0, at - t)); t = at
        d = dur(f); parts.append((f, 0, d)); t += d
    if c["total"] > t: parts.append((None, 0, c["total"] - t))
    base = build_audio(parts, c["total"], tmp)
    ev = c["sfx"]; boost = 1.0 if c["voice"] else 6.0      # no voice: the soft music of the site carries the video
    ins, fl = ["-i", str(base)], [f"[0:a]aresample=44100,aformat=channel_layouts=mono,volume={boost}[b]"]
    for i, (at, s, g) in enumerate(ev):
        ins += ["-i", str(SONS / f"{s}.wav")]
        fl.append(f"[{i + 1}:a]aresample=44100,adelay={int(at * 1000)}:all=1,volume={g}[e{i}]")
    fl.append("[b]" + "".join(f"[e{i}]" for i in range(len(ev))) + f"amix=inputs={len(ev) + 1}:normalize=0:duration=first,alimiter=limit=0.85[a]")
    out = tmp / "mix.m4a"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    return out


async def frames(c, tmp, only=None):
    page = HERE / "_anime.html"
    h = (HERE / "anime.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/").replace("SEALSVG", seal_svg())
    page.write_text(h)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
        cc = {k: v for k, v in c.items() if k not in ("voice", "sfx")}
        await pg.evaluate(f"setup({json.dumps(cc, ensure_ascii=False)})"); await pg.wait_for_timeout(400)
        ts = only if only is not None else [i / FPS for i in range(int(round(c["total"] * FPS)))]
        for i, t in enumerate(ts):
            await pg.evaluate(f"frame({t})")
            await pg.screenshot(path=str(tmp / f"f{i:04d}.jpg"), type="jpeg", quality=90)
        await b.close()
    page.unlink()
    return len(ts)


def render(slug):
    c = VIDEOS[slug]()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        n = asyncio.run(frames(c, tmp))
        a = audio(c, tmp)
        out = OUT / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.jpg"), "-i", str(a),
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-t", f"{n / FPS:.3f}", "-movflags", "+faststart", str(out)], check=True)
        clean(out)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(c["cover"]), "-i", str(out), "-frames:v", "1", "-q:v", "3", str(OUT / f"{slug}.jpg")], check=True)
    print(slug, f"{c['total']:.1f} s", out)


def preview(slug, times):
    """Stills at given times (for checking the layout without rendering the whole video)."""
    c = VIDEOS[slug]()
    d = HERE / "out/preview"; d.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); asyncio.run(frames(c, tmp, only=times))
        for i, t in enumerate(times):
            (tmp / f"f{i:04d}.jpg").rename(d / f"{slug}-{t:05.1f}.jpg")
    return d


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--preview"]:
        slug, times = args[1], [float(x) for x in args[2:]]
        print(preview(slug, times))
    elif args[:1] == ["--audio"]:      # remake only the sound track of already rendered videos
        for slug in args[1:]:
            c = VIDEOS[slug](); out = OUT / f"{slug}.mp4"
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td); a = audio(c, tmp); v = tmp / "v.mp4"
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-i", str(a), "-map", "0:v", "-map", "1:a",
                                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(v)], check=True)
                v.replace(out); clean(out)
            print(slug, "son refait")
    else:
        for s in args or list(VIDEOS):
            render(s)
