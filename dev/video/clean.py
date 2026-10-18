"""Strip every metadata field from finished videos, in place: container tags (encoder, dates,
handler names), chapters, and the H.264 SEI units where x264 writes its version and settings.
The picture is copied untouched; the sound is re-encoded once at a high rate, because FFmpeg's
AAC encoder writes its own name inside the sound stream.

    python3 dev/video/clean.py dist/videos/*.mp4
"""
import subprocess, sys
from pathlib import Path


def clean(path):
    path = Path(path)
    tmp = path.with_name(path.stem + ".clean" + path.suffix)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-map", "0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-map_metadata", "-1", "-map_chapters", "-1",
                    "-bsf:v", "filter_units=remove_types=6",
                    "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
                    "-metadata:s:v", "handler_name=", "-metadata:s:a", "handler_name=",
                    "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        clean(p)
        print("ok", p)
