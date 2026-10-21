# Seamless loop for the short videos (21 Oct 2026): TikTok and Reels replay a video as soon as it ends, and
# a replay counts. The first L seconds are cut, and the last L seconds cross-fade (picture and sound) into
# them, so the last frame flows into the first one and the music and voice never jump.
#   python3 dev/video/serie/boucle.py out/a.mp4 out/b.mp4 …   (in place)
import subprocess, sys
from pathlib import Path

L = 0.3


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


def boucle(path, l=L):
    path = Path(path)
    T = dur(path)
    tmp = path.with_name(path.stem + ".boucle" + path.suffix)
    fc = (f"[0:v]split[a][b];[a]trim={l}:{T},setpts=PTS-STARTPTS[main];[b]trim=0:{l},setpts=PTS-STARTPTS[head];"
          f"[main][head]xfade=transition=fade:duration={l}:offset={T - 2 * l:.3f},format=yuv420p[v];"
          f"[0:a]asplit[c][d];[c]atrim={l}:{T},asetpts=PTS-STARTPTS[am];[d]atrim=0:{l},asetpts=PTS-STARTPTS[ah];"
          f"[am][ah]acrossfade=d={l}:c1=tri:c2=tri[au]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-filter_complex", fc, "-map", "[v]", "-map", "[au]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
                    "-map_metadata", "-1", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(path)
    return T - l


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f, f"{boucle(f):.1f} s")
