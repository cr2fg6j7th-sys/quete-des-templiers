# The "phone on the family table" art direction (Nathan, 21 Oct 2026): overhead descent onto an iPhone,
# the home page, the TikTok video playing on the phone, the site's address, then the camera rises.
# The hook card is on screen from the first frame (retention); the descent is kept short.
#   python3 dev/video/campagne/phone.py [slug …]   (needs out/hook/<slug>.mp4)  -> out/phone/<slug>.mp4
import asyncio, json, os, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clean import clean
HERE = Path(__file__).parent
REPO = HERE.parents[2]
OUT = HERE / "out" / "phone"
FPS = 24
MUSIC = REPO / "audio/musique/accueil.mp3"

def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))

async def render(slug, hook):
    src = HERE / "out" / "hook" / f"{slug}.mp4"
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); (tmp / "vf").mkdir(); (tmp / "f").mkdir()
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vf", f"fps={FPS},scale=720:1280", "-q:v", "3", str(tmp / "vf/f%04d.jpg")], check=True)
        nvf = len(list((tmp / "vf").glob("*.jpg")))
        S = {"down": 1.6, "hold": 0.7, "vid": nvf / FPS, "site": 1.3, "up": 2.0, "hook": hook}
        total = S["down"] + S["hold"] + S["vid"] + S["site"] + S["up"]
        t_vid = S["down"] + S["hold"]
        page = HERE / f"_phone_{os.getpid()}.html"
        page.write_text((HERE / "phone.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/"))
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"setup({json.dumps(S, ensure_ascii=False)})"); await pg.wait_for_timeout(300)
            for i in range(int(total * FPS)):
                t = i / FPS
                k = min(max(int((t - t_vid) * FPS) + 1, 1), nvf)
                await pg.evaluate(f"frame({t}, {json.dumps((tmp / 'vf' / f'f{k:04d}.jpg').as_uri())})")
                await pg.screenshot(path=str(tmp / "f" / f"f{i:04d}.jpg"), type="jpeg", quality=90)
            await b.close()
        page.unlink()
        a = tmp / "a.m4a"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-stream_loop", "-1", "-i", str(MUSIC), "-filter_complex",
            f"[0:a]adelay={int(t_vid*1000)}|{int(t_vid*1000)},apad,atrim=0:{total:.3f}[v];"
            f"[1:a]volume='if(lt(t,{t_vid}),0.28,0.10)':eval=frame,atrim=0:{total:.3f},afade=t=out:st={total-1.5:.3f}:d=1.5[m];"
            "[v][m]amix=inputs=2:duration=first:normalize=0[o]", "-map", "[o]", "-c:a", "aac", "-b:a", "160k", str(a)], check=True)
        out = OUT / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f/f%04d.jpg"), "-i", str(a),
            "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "27", "-preset", "slow", "-c:a", "copy", "-shortest",
            "-movflags", "+faststart", str(out)], check=True)
        clean(out)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "0.3", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(OUT / f"{slug}.jpg")], check=True)
    print(slug, f"{total:.1f} s", flush=True)

if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    from videos_hook import VIDEOS
    for k in sys.argv[1:] or list(VIDEOS):
        asyncio.run(render(k, VIDEOS[k]["hook"]))
