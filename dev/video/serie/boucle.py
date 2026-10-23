# Seamless loop for the short videos (21 Oct 2026): TikTok and Reels replay a video as soon as it ends, and
# a replay counts. The first L seconds are cut, and the last L seconds cross-fade (picture and sound) into
# them, so the last frame flows into the first one and the music and voice never jump.
#   python3 dev/video/serie/boucle.py out/a.mp4 out/b.mp4 …   (in place)
import subprocess, sys
from pathlib import Path

L = 0.3


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


def has_audio(f):
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(f)],
                               capture_output=True, text=True).stdout.strip())


def boucle(path, l=L):
    """The input is read twice (no split/asplit: acrossfade on two branches of one asplit never got its frames,
    and the sound was silently dropped until 23 Oct 2026). The sound is padded to the picture's length first."""
    path = Path(path)
    T = dur(path)
    tmp = path.with_name(path.stem + ".boucle" + path.suffix)
    fc = (f"[0:v]trim={l}:{T},setpts=PTS-STARTPTS[main];[1:v]trim=0:{l},setpts=PTS-STARTPTS[head];"
          f"[main][head]xfade=transition=fade:duration={l}:offset={T - 2 * l:.3f},format=yuv420p[v]")
    maps = ["-map", "[v]"]
    if has_audio(path):
        fc += (f";[0:a]apad=whole_dur={T:.3f},atrim={l}:{T:.3f},asetpts=PTS-STARTPTS[am];"
               f"[1:a]atrim=0:{l},asetpts=PTS-STARTPTS[ah];[am][ah]acrossfade=d={l}:c1=tri:c2=tri[au]")
        maps += ["-map", "[au]", "-c:a", "aac", "-b:a", "160k"]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-i", str(path), "-filter_complex", fc, *maps,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                    "-map_metadata", "-1", "-movflags", "+faststart", str(tmp)], check=True)
    if has_audio(path) and not has_audio(tmp):
        raise RuntimeError(f"boucle: sound lost in {path}")
    tmp.replace(path)
    return T - l


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f, f"{boucle(f):.1f} s")
