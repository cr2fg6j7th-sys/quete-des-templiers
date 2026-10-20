# Retention format for TikTok and Reels (from 21 Oct 2026). Why: the first videos stalled near 200 views
# with 0-3 s of average watch time; they opened on 2.6 s of silent card, then « Te voici devant… ».
# Here: the hook is on screen from the first frame, the Grand Maître speaks at once and only the facts
# are kept (12-18 s), big word-by-word captions, constant motion, a progress bar, the answer comes last,
# a short call to action, and the end loops into the hook.
#   python3 dev/video/campagne/hook.py [slug …]   -> out/hook/<slug>.mp4 + .jpg
import asyncio, json, re, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from build import spans, sentences, dur, build_audio, VOIX, NOMS, REPO
from clean import clean
from videos_toussaint import LINES_OF

HERE = Path(__file__).parent
OUT = HERE / "out" / "hook"
FPS = 20          # rendered frames per second (the file is 30 fps)
TAIL = 1.4        # call to action after the last word
GAP = 0.18        # between two kept pieces

CTA_TEST = {"text": "Quête offerte aux familles testeuses", "small": "écrivez CHEVALIER en commentaire"}
ASK = {"fact": "💬 Devinez en commentaire avant la fin !", "name": "💬 Le prénom de votre enfant en commentaire"}
CTA_OPEN = {"text": "Aperçu gratuit · lien en bio", "small": "maquetelegendaire.fr"}


def words_of(text):
    return text.split()


def align(clip):
    """Speech interval of each sentence of a clip: sentence ends are matched to pauses (dynamic programming,
    position estimated from the text length, longer pauses preferred)."""
    full = LINES_OF(clip)
    sent = sentences(full)
    sp = spans(VOIX / f"{clip}.mp3")
    L = sum(b - a for a, b in sp)
    def real(p):
        for a, b in sp:
            if p <= b - a: return a + p
            p -= b - a
        return sp[-1][1]
    lens = [len(x) for x in sent]; tot = sum(lens)
    est, acc = [], 0
    for n in lens[:-1]:
        acc += n; est.append(real(L * acc / tot))
    gaps = [((sp[k][1] + sp[k + 1][0]) / 2, sp[k + 1][0] - sp[k][1]) for k in range(len(sp) - 1)]
    nb, ng = len(est), len(gaps)
    INF = float("inf")
    cost = lambda j, k: ((est[j] - gaps[k][0]) / 1.5) ** 2 - 4 * gaps[k][1]
    best = [[INF] * ng for _ in range(nb)]; prev = [[-1] * ng for _ in range(nb)]
    for k in range(ng): best[0][k] = cost(0, k) if nb else 0
    for j in range(1, nb):
        run, arg = INF, -1
        for k in range(ng):
            if k > 0 and best[j - 1][k - 1] < run: run, arg = best[j - 1][k - 1], k - 1
            if run < INF: best[j][k] = run + cost(j, k); prev[j][k] = arg
    ks = []
    if nb:
        k = min(range(ng), key=lambda k: best[nb - 1][k])
        for j in range(nb - 1, -1, -1):
            ks.append(k); k = prev[j][k]
        ks.reverse()
    bounds = [sp[0][0]] + [x for k in ks for x in (sp[k][1], sp[k + 1][0])] + [sp[-1][1]]
    return sent, [(bounds[2 * i], bounds[2 * i + 1]) for i in range(len(sent))], sp


def locate(clip, piece):
    """Audio interval (a, b) of an exact piece of a clip's text, made of whole sentences."""
    full = LINES_OF(clip)
    i = full.find(piece)
    if i < 0: raise ValueError(f"{clip}: texte introuvable « {piece[:40]} »")
    sent, iv, sp = align(clip)
    pos, idx = 0, []
    for n, x in enumerate(sent):
        x = x.replace("\u00a0", " "); j = full.find(x, pos); pos = j + len(x)
        if j >= i - 2 and pos <= i + len(piece) + 3: idx.append(n)
    a, b = iv[idx[0]][0], iv[idx[-1]][1]
    return a, b, [(max(x, a), min(y, b)) for x, y in sp if y > a and x < b]


def time_words(piece, inner, offset):
    """Each word of a piece spread over its speech spans by length."""
    ws = words_of(piece)
    wt = [len(w) + 1.5 for w in ws]
    L, W = sum(y - x for x, y in inner), sum(wt)
    out, acc = [], 0.0
    def real(p):
        for x, y in inner:
            if p <= y - x + 1e-6: return x + p
            p -= y - x
        return inner[-1][1]
    a0 = inner[0][0]
    for w, k in zip(ws, wt):
        s, e = real(L * acc / W), real(L * (acc + k) / W)
        out.append({"w": w, "t0": round(offset + s - a0, 3), "t1": round(offset + e - a0, 3)})
        acc += k
    return out


def chunk(words):
    """Groups of 1-3 words, cut after punctuation, at most ~15 letters."""
    k, n, letters = 0, 0, 0
    for i, w in enumerate(words):
        if n and (n >= 3 or letters + len(w["w"]) > 15):
            k += 1; n = 0; letters = 0
        w["chunk"] = k; n += 1; letters += len(w["w"])
        if re.search(r"[.!?…:;,]$", w["w"]) and i + 1 < len(words):
            k += 1; n = 0; letters = 0
    return words


def plan(v):
    audio, words, t = [(None, 0, 0.05)], [], 0.05
    pieces = []
    if v["kind"] == "name":
        f = NOMS / f"{v['slug']}.mp3"; sp = spans(f)
        a, b = max(sp[0][0] - 0.02, 0), sp[-1][1] + 0.05
        audio.append((f, a, b))
        words.append({"w": v["label"] + ",", "t0": t, "t1": t + (b - a) + 0.25, "name": True}); t += (b - a) + 0.25
        audio.append((None, 0, 0.25))
        clip = f"prologue-dehors-{v['g']}"
        sp = spans(VOIX / f"{clip}.mp3")
        for (i, j), text in v["parts"]:
            pieces.append((clip, sp[i][0], sp[j][1], [(x, y) for x, y in sp[i:j + 1]], text))
    else:
        for piece in v["keep"]:
            a, b, inner = locate(v["clip"], piece)
            pieces.append((v["clip"], a, b, inner, piece))
    for n, (clip, a, b, inner, text) in enumerate(pieces):
        a, b = max(a - 0.03, 0), b + 0.06
        audio.append((VOIX / f"{clip}.mp3", a, b))
        ws = time_words(text, inner, t + 0.03)
        if n == len(pieces) - 1 and v["kind"] != "name":
            # the reveal: after the last « … » or « : » of the last piece, else its last clause
            cut = [i for i, w in enumerate(ws[:-1]) if re.search(r"(…|:)$", w["w"])] or \
                  [i for i, w in enumerate(ws[:-1]) if w["w"].endswith(",") and i >= len(ws) // 2]
            for w in ws[cut[-1] + 1 if cut else 0:]: w["payoff"] = True
        words += ws; t += b - a
        if n < len(pieces) - 1: audio.append((None, 0, GAP)); t += GAP
    voice_end = t
    total = voice_end + TAIL
    audio.append((None, 0, TAIL))
    names = [w for w in words if w.get("name")]
    rest = chunk([w for w in words if not w.get("name")])
    for w in names: w["chunk"] = 0
    for w in rest: w["chunk"] += 1 if names else 0
    # the answer starts on its own chunk
    words = names + rest
    starts = {}
    for w in words: starts.setdefault(w["chunk"], w["t0"])
    chunks = [starts[k] for k in sorted(starts)]
    cta = dict(v.get("cta", CTA_TEST), at=round(voice_end + 0.1, 3))
    return audio, {"ask": v.get("ask", ASK[v["kind"]]), "hook": v["hook"], "total": round(total, 3), "words": words, "chunks": chunks, "cta": cta}


async def render(slug, v):
    OUT.mkdir(parents=True, exist_ok=True)
    audio_parts, cfg = plan(v)
    html = (HERE / "hook.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/")
    page = HERE / ("_hook_"+str(__import__("os").getpid())+".html"); page.write_text(html)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        audio = build_audio(audio_parts, cfg["total"], tmp)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto(page.as_uri())
            await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"setup({json.dumps(cfg, ensure_ascii=False)})")
            n = int(cfg["total"] * FPS) + 1
            for i in range(n):
                await pg.evaluate(f"frame({i / FPS})")
                await pg.screenshot(path=str(tmp / f"f{i:04d}.jpg"), type="jpeg", quality=92)
            # cover: the hook with the answer's first words
            await pg.evaluate(f"frame({v.get('cover', 0.6)})")
            await pg.screenshot(path=str(OUT / f"{slug}.jpg"), type="jpeg", quality=88)
            await b.close()
        out = OUT / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.jpg"), "-i", str(audio),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "copy",
                        "-t", f"{cfg['total']:.3f}", "-movflags", "+faststart", str(out)], check=True)
        clean(out)
    print(slug, f"{cfg['total']:.1f} s")


if __name__ == "__main__":
    from videos_hook import VIDEOS
    want = sys.argv[1:] or list(VIDEOS)
    for k in want:
        asyncio.run(render(k, VIDEOS[k]))
