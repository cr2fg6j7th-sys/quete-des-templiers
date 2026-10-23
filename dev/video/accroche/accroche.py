# Hook intros (23 Oct 2026, Nathan: « un hook visuel, textuel et auditif très surprenant… curiosité, peur,
# peur de manquer quelque chose, des mots courts qui percutent »). A 1.4-1.6 s intro is put in front of each
# video: the red seal hits the screen (thud, cracks, flash), with a few words and one line of the keywords
# parents type in TikTok search. Five kinds, chosen by the kind of video:
#   roulette  first names flicker like a slot machine and stop on ONE      (first-name videos)
#   alerte    « ALERTE. » + the Grand Maître's « Tuuut ! »                   (parents' questions, the site, budget)
#   ans       « 7 ans. » … « Une seule fois. »                              (episodes, the day itself)
#   defi      « DÉFI PARENTS » : plus fort que votre enfant ? + a countdown (anecdotes, riddles)
#   village   a street map dives in, the seal falls on it: « Il y a une quête ici. »
#   python3 dev/video/accroche/accroche.py BASE.mp4 OUT.mp4 '<json cfg>'    (or import and call make())
import asyncio, json, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
REPO = HERE.parents[2]
SONS = HERE / "sons"
FPS = 30
SR = 44100


def ticks_roulette(land):
    out, acc, d = [], 0.0, 0.055
    while acc + d <= land - 0.15:
        acc += d; out.append(acc); d *= 1.17
    return out


def sound_events(c):
    """(time, sound, gain) for the intro, in step with what accroche.html draws."""
    k, ev = c["type"], []
    if k == "roulette":
        ev += [(x, "tick" if i % 2 else "tock", 0.9) for i, x in enumerate(ticks_roulette(c["land"]))]
        ev += [(c["land"] - 0.03, "thud", 1.0)]
    elif k == "alerte":
        ev += [(0.0, "tuuut", 0.6), (0.12, "thud", 0.7), (c["t1"], "tick", 0.6), (c["t2"], "tock", 0.6)]
    elif k == "ans":
        ev += [(0.02, "heart", 0.9), (c["t2"] - 0.03, "thud", 1.0)]
    elif k == "defi":
        ev += [(0.12, "thud", 1.0)] + [(0.45 + i * 0.3, "tick" if i % 2 else "tock", 0.7) for i in range(int((c["dur"] - 0.45) / 0.3) + 1)]
    elif k == "village":
        ev += [(0.0, "whoosh", 0.9), (c["land"] - 0.03, "thud", 1.0)]
    return ev


def intro_audio(c, out):
    ev = [e for e in sound_events(c) if e[0] < c["dur"]]
    ins, fl = [], []
    for i, (t, s, g) in enumerate(ev):
        ins += ["-i", str(SONS / f"{s}.wav")]
        fl.append(f"[{i}:a]aresample={SR},adelay={int(t * 1000)}:all=1,volume={g}[e{i}]")
    fl.append("".join(f"[e{i}]" for i in range(len(ev))) + f"amix=inputs={len(ev)}:normalize=0:duration=longest,"
              f"apad=whole_dur={c['dur']:.3f},atrim=0:{c['dur']:.3f},alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "[a]",
                    "-ac", "1", "-ar", str(SR), str(out)], check=True)


async def intro_frames(c, tmp):
    page = HERE / "_accroche.html"
    bord = (REPO / "dev/flyers/svg/sceau-bord.txt").read_text().strip()
    page.write_text((HERE / "accroche.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/").replace('"BORD"', json.dumps(bord)))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
        await pg.evaluate(f"setup({json.dumps(c, ensure_ascii=False)})"); await pg.wait_for_timeout(300)
        n = int(round(c["dur"] * FPS))
        for i in range(n):
            await pg.evaluate(f"frame({i / FPS})")
            await pg.screenshot(path=str(tmp / f"h{i:04d}.jpg"), type="jpeg", quality=92)
        await b.close()
    page.unlink()
    return n


def has_audio(f):
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(f)],
                               capture_output=True, text=True).stdout.strip())


def make(base, out, c):
    """Intro + base video, re-encoded once at 1080x1920, 30 fps, mono AAC; metadata stripped."""
    base, out = Path(base), Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        n = asyncio.run(intro_frames(c, tmp))
        intro_audio(c, tmp / "intro.wav")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "h%04d.jpg"), "-i", str(tmp / "intro.wav"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "1", "-t", f"{n / FPS:.3f}", str(tmp / "intro.mp4")], check=True)
        base_in = ["-i", str(base)]
        if not has_audio(base):    # silent base: give it a silent track so the two parts join
            base_in += ["-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono"]
            amap = "[2:a]"
        else:
            amap = "[1:a]"
        bdur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(base)]))
        fc = (f"[0:v]fps={FPS},scale=1080:1920,setsar=1,format=yuv420p[v0];[1:v]fps={FPS},scale=1080:1920,setsar=1,format=yuv420p[v1];"
              f"[0:a]aresample={SR},aformat=channel_layouts=mono[a0];"
              f"{amap}aresample={SR},aformat=channel_layouts=mono,apad=whole_dur={bdur:.3f},atrim=0:{bdur:.3f}[a1];"
              f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tmp / "intro.mp4"), *base_in, "-filter_complex", fc,
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "aac", "-b:a", "160k",
                        "-t", f"{n / FPS + bdur:.3f}", "-movflags", "+faststart", str(out)], check=True)
    sys.path.insert(0, str(HERE.parent))
    from clean import clean
    clean(out)
    return out


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]))
