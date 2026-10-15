# Builds the 15 vertical videos of the "familles testeuses" campaign (16-30 Oct 2026)
# from the app's recorded voice, its fonts and its home music. Output: out/<slug>.mp4 + out/<slug>.jpg (cover).
import asyncio, json, re, subprocess, sys, tempfile
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path("/home/claude/quete-des-templiers")
HERE = Path(__file__).parent
OUT = HERE / "out"
VOIX, NOMS = REPO / "audio/voix", REPO / "audio/noms"
MUSIC = REPO / "audio/musique/accueil.mp3"
SR = 44100

def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))

def spans(f):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    total, out, cur = dur(f), [], 0.0
    for s, e in zip(st, en + [total]):
        if s - cur > 0.15: out.append((cur, s))
        cur = e
    if total - cur > 0.15: out.append((cur, total))
    return out

def sentences(text):
    return [s.strip() for s in re.findall(r"[^.!?…]+(?:[.!?…]+|$)", text) if s.strip()]

def timed_captions(f, text):
    """(start, end) of each sentence inside the clip, start = first speech."""
    sp, sent = spans(f), sentences(text)
    s0, s1 = sp[0][0], sp[-1][1]
    if len(sp) == len(sent):
        return [(a - s0, b - s0, t) for (a, b), t in zip(sp, sent)], s0, s1
    total, n = s1 - s0, sum(len(t) for t in sent)
    out, t = [], 0.0
    for x in sent:
        d = total * len(x) / n
        out.append((t, t + d, x)); t += d
    return out, s0, s1

# A video = list of parts. ("card", slide, seconds) | ("voice", clip, slide, text) | ("name", slug, label, slide)
def plan_parts(parts):
    """Returns audio pieces [(file|None, a, b)] and slides [(slide, t0, t1)]."""
    audio, slides, t = [], [], 0.0
    for p in parts:
        if p[0] == "card":
            _, slide, d = p
            audio.append((None, 0, d)); slides.append((slide, t, t + d)); t += d
        elif p[0] == "name":
            _, slug, label, slide = p
            f = NOMS / f"{slug}.mp3"; sp = spans(f); a, b = max(sp[0][0] - 0.03, 0), sp[-1][1] + 0.08
            audio.append((f, a, b)); slides.append((dict(slide, kind="voice", name=label + ","), t, t + (b - a) + 0.2))
            audio.append((None, 0, 0.2)); t += (b - a) + 0.2
        elif p[0] == "voice":
            _, clip, slide, text, *rng = p
            f = VOIX / f"{clip}.mp3"
            if rng:   # only the first spoken spans of the clip, one sentence each
                sp = spans(f)[:rng[0]]; sent = sentences(text)[:rng[0]]
                s0, s1 = sp[0][0], sp[-1][1]
                caps = [(a - s0, b2 - s0, x) for (a, b2), x in zip(sp, sent)]
            else:
                caps, s0, s1 = timed_captions(f, text)
            a, b = max(s0 - 0.03, 0), s1 + 0.1
            audio.append((f, a, b))
            for i, (c0, c1, line) in enumerate(caps):
                end = caps[i + 1][0] if i + 1 < len(caps) else (b - a)
                slides.append((dict(slide, kind="voice", line=line), t + c0 + (0.03 if i else 0), t + end))
            if slides and caps: slides[-len(caps)] = (slides[-len(caps)][0], t, slides[-len(caps)][2])
            t += b - a
            audio.append((None, 0, 0.35)); t += 0.35
    return audio, slides, t

def build_audio(pieces, total, tmp, music=True):
    inputs, filters, labels = [], [], []
    for i, (f, a, b) in enumerate(pieces):
        if f is None:
            filters.append(f"anullsrc=r={SR}:cl=mono,atrim=0:{b - a:.3f}[p{i}]")
        else:
            inputs += ["-i", str(f)]
            k = len(inputs) // 2 - 1
            filters.append(f"[{k}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=mono,loudnorm=I=-16:TP=-1.5[p{i}]")
        labels.append(f"[p{i}]")
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[voice]")
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(MUSIC)]
        k = len(inputs) // 2 - 1 if False else None
    out = tmp / "audio.m4a"
    if music:
        mi = sum(1 for x in inputs if x == "-i") - 1
        filters.append(f"[{mi}:a]aresample={SR},aformat=channel_layouts=mono,volume=0.10,atrim=0:{total:.3f},afade=t=out:st={max(total - 1.2, 0):.3f}:d=1.2[m]")
        filters.append("[voice][m]amix=inputs=2:duration=first:normalize=0[out]")
    else:
        filters.append("[voice]anull[out]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
                    "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    return out

async def render(slug, parts, cover_index=0):
    OUT.mkdir(exist_ok=True)
    pieces, slides, total = plan_parts(parts)
    html = (HERE / "slides.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/")
    page_file = HERE / "_slides.html"; page_file.write_text(html)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        audio = build_audio(pieces, total, tmp)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto(page_file.as_uri())
            await pg.evaluate("document.fonts.ready")
            lst = []
            for i, (s, t0, t1) in enumerate(slides):
                await pg.evaluate(f"show({json.dumps(s, ensure_ascii=False)})")
                await pg.evaluate("document.fonts.ready")
                png = tmp / f"s{i:03d}.png"; await pg.screenshot(path=str(png)); lst.append((png, t0, t1))
            await b.close()
        # concat list with exact durations (gaps filled by extending the previous slide)
        lines = []
        for i, (png, t0, t1) in enumerate(lst):
            nxt = lst[i + 1][1] if i + 1 < len(lst) else total
            lines += [f"file '{png}'", f"duration {max(nxt - t0, 0.04):.3f}"]
        lines.append(f"file '{lst[-1][0]}'")
        (tmp / "list.txt").write_text("\n".join(lines))
        out = OUT / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-i", str(audio),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "copy",
                        "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(lst[cover_index][0]), "-q:v", "3", str(OUT / f"{slug}.jpg")], check=True)
    print(slug, f"{total:.1f} s, {len(slides)} plans")

if __name__ == "__main__":
    from videos import VIDEOS
    want = sys.argv[1:] or list(VIDEOS)
    for k in want:
        asyncio.run(render(k, *VIDEOS[k]))
