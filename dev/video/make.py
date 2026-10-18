# Short vertical videos "Le Grand Maître appelle…" for TikTok, Instagram Reels and YouTube Shorts.
# Uses only the recorded voice of the app (no music, no paid generation).
#   python3 dev/video/make.py gabriel:m:Gabriel jade:f:Jade …   -> dist/videos/<slug>.mp4
import asyncio, json, re, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).parent))
from clean import clean

ROOT = Path(__file__).resolve().parents[1].parent
AUDIO = ROOT / "audio"
OUT = ROOT / "dist" / "videos"
FPS = 30
TYPE_START, TYPE_END, PRESS = 0.5, 1.6, 2.1   # the parent types, then taps "Écouter"
VOICE_AT = PRESS + 0.3                        # the voice starts
GAP, PAUSE, TAIL = 0.22, 0.45, 3.4            # name -> sentence, between parts, end card

def duration(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))

def speech(f):
    """Spoken spans of a clip, from its pauses."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    total, spans, cur = duration(f), [], 0.0
    for s, e in zip(starts, ends + [total]):
        if s - cur > 0.15: spans.append((cur, s))
        cur = e
    if total - cur > 0.15: spans.append((cur, total))
    return spans

# The two parts of the prologue used, as (first span, last span) indexes, with their words.
PARTS = {
    "m": [((0, 1), ["Approche.", "Je suis le Grand Maître de l'Ordre des Gardiens du Temple."]),
          ((5, 5), ["Aujourd'hui, c'est ton anniversaire, et j'ai besoin d'un chevalier courageux."])],
    "f": [((0, 1), ["Approche.", "Je suis le Grand Maître de l'Ordre des Gardiens du Temple."]),
          ((5, 6), ["Aujourd'hui, c'est ton anniversaire, et j'ai besoin d'une chevalière courageuse."])],
}

def build_audio(slug, g, tmp):
    name_clip = AUDIO / "noms" / f"{slug}.mp3"
    prologue = AUDIO / "voix" / f"prologue-dehors-{g}.mp3"
    spans = speech(prologue)
    pieces, captions, t = [], [], VOICE_AT
    nd = duration(name_clip)
    pieces.append((name_clip, 0, nd)); t += nd + GAP
    for (a, b), texts in PARTS[g]:
        part = spans[a:b + 1]
        if len(texts) == len(part):          # one caption per spoken span
            for (s, e), text in zip(part, texts):
                captions.append({"t0": round(t + (s - part[0][0]), 3), "t1": round(t + (e - part[0][0]), 3), "text": text})
        else:
            captions.append({"t0": round(t, 3), "t1": round(t + part[-1][1] - part[0][0], 3), "text": " ".join(texts)})
        s0, e1 = max(part[0][0] - 0.05, 0), part[-1][1] + 0.12
        pieces.append((prologue, s0, e1)); t += (e1 - s0) + PAUSE
    voice_end = t - PAUSE
    # silence before the voice, the pieces with gaps, silence under the end card
    filters, inputs, labels = [], [], []
    for i, (f, s, e) in enumerate(pieces):
        inputs += ["-i", str(f)]
        filters.append(f"[{i}:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=mono[p{i}]")
    sil = lambda d, k: filters.append(f"anullsrc=r=44100:cl=mono,atrim=0:{d:.3f}[s{k}]") or f"[s{k}]"
    seq = [sil(VOICE_AT, 0), "[p0]", sil(GAP, 1)]
    for i in range(1, len(pieces)):
        seq.append(f"[p{i}]")
        seq.append(sil(PAUSE if i < len(pieces) - 1 else TAIL, i + 1))
    filters.append("".join(seq) + f"concat=n={len(seq)}:v=0:a=1[out]")
    out = tmp / "audio.m4a"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", "128k", str(out)], check=True)
    return out, captions, voice_end, duration(out)

async def render(slug, g, label):
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        audio, captions, voice_end, total = build_audio(slug, g, tmp)
        cfg = {"name": label, "typeStart": TYPE_START, "typeEnd": TYPE_END, "press": PRESS, "captions": captions,
               "endAt": voice_end + 0.3, "total": total}
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto((Path(__file__).parent / "frame.html").as_uri())
            await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"setup({json.dumps(cfg)})")
            n = int(total * FPS)
            for i in range(n):
                await pg.evaluate(f"frame({i / FPS})")
                await pg.screenshot(path=str(tmp / f"f{i:04d}.png"))
            await b.close()
        out = OUT / f"grand-maitre-{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"), "-i", str(audio),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-c:a", "copy", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
        clean(out)
        print(out.name, f"{total:.1f} s")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        slug, g, label = arg.split(":")
        asyncio.run(render(slug, g, label))
