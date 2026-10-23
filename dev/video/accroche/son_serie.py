# The series videos published from 21 Oct 2026 lost their sound: the loop step (serie/boucle.py) dropped it.
# Their picture is fine, so the sound is rebuilt from the same scripts (same timeline, same voice clips and
# music), looped the same way (the first 0.3 s cut, the last 0.3 s cross-faded into the head) and put back.
#   python3 dev/video/accroche/son_serie.py SLUG SILENT.mp4 OUT.mp4
import subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).parent
sys.path[:0] = [str(HERE.parent / "serie"), str(HERE.parent), str(HERE.parent / "campagne")]
import court, serie, ecran
from build import build_audio

L = 0.3


def parts_of(slug):
    if slug in court.VIDEOS:
        cfg, parts = court.VIDEOS[slug]()
    elif slug in serie.VIDEOS:
        cfg, parts, _ = serie.VIDEOS[slug]()
    else:
        cfg, parts = ecran.VIDEOS[slug]()
    return cfg["total"], parts or [(None, 0, 0.1)]


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


def put_sound(slug, silent, out):
    total, parts = parts_of(slug)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        a = build_audio(parts, total, tmp)
        T = total
        fc = (f"[0:a]apad=whole_dur={T:.3f},atrim={L}:{T:.3f},asetpts=PTS-STARTPTS[am];"
              f"[1:a]atrim=0:{L},asetpts=PTS-STARTPTS[ah];[am][ah]acrossfade=d={L}:c1=tri:c2=tri[au]")
        looped = tmp / "looped.m4a"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(a), "-i", str(a), "-filter_complex", fc, "-map", "[au]",
                        "-c:a", "aac", "-b:a", "160k", str(looped)], check=True)
        V = dur(silent)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(looped), "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-af", f"apad=whole_dur={V:.3f}", "-c:a", "aac", "-b:a", "160k", "-t", f"{V:.3f}",
                        "-movflags", "+faststart", str(out)], check=True)
    return out


if __name__ == "__main__":
    put_sound(sys.argv[1], sys.argv[2], sys.argv[3])
