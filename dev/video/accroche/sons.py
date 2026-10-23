# Sound effects for the hook intros (23 Oct 2026), synthesised here so they are free and owe nothing to anyone:
# the seal hitting the screen (a low thud with a wax crack), clock ticks, a whoosh, a heartbeat.
# The Grand Maître's own « Tuuut ! » comes from the recorded tower line (audio/voix/recit-tower-0.mp3).
#   python3 dev/video/accroche/sons.py   -> dev/video/accroche/sons/*.wav
import subprocess, wave
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "sons"
REPO = HERE.parents[2]
SR = 44100
rng = np.random.default_rng(7)


def t(d): return np.arange(int(d * SR)) / SR


def save(name, x, peak=0.89):
    x = x / (np.abs(x).max() + 1e-9) * peak
    OUT.mkdir(exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def lowpass(x, a):            # one-pole low-pass, a in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def thud():
    """The seal stamped on the glass: a falling low tone, a dull knock and a short crackle of wax."""
    d = 0.55; tt = t(d)
    f = 95 * np.exp(-tt * 9) + 42                       # pitch falls from ~137 Hz to 42 Hz
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7.5)
    knock = lowpass(rng.normal(0, 1, len(tt)), 0.18) * np.exp(-tt * 55) * 1.6
    crack = np.zeros_like(tt)
    for k in range(14):                                # little clicks of breaking wax, in the first 120 ms
        i = int(rng.uniform(0.004, 0.12) * SR); n = int(0.004 * SR)
        crack[i:i + n] += rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.0012 * SR)) * rng.uniform(0.3, 0.9)
    crack = crack - lowpass(crack, 0.25)               # keep the bright part only
    return body * 1.0 + knock + crack * 0.55


def tick(high=True):
    d = 0.05; tt = t(d)
    f = 2300 if high else 1650
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 140) + rng.normal(0, 0.15, len(tt)) * np.exp(-tt * 400)


def whoosh(d=0.45):
    tt = t(d); n = rng.normal(0, 1, len(tt))
    out = np.zeros_like(tt); acc = 0.0
    for i, v in enumerate(n):                           # band rising with time
        a = 0.02 + 0.5 * (i / len(n)) ** 2
        acc += a * (v - acc); out[i] = acc
    env = np.sin(np.pi * tt / d) ** 2
    return out * env


def heart():
    d = 0.5; tt = t(d); x = np.zeros_like(tt)
    for st, amp in ((0.0, 1.0), (0.17, 0.7)):
        i = int(st * SR); tl = tt[: len(tt) - i]
        x[i:] += np.sin(2 * np.pi * (60 * np.exp(-tl * 6) + 38) * tl) * np.exp(-tl * 14) * amp
    return x


def heart_big():
    """A heavier heartbeat for urgency: lower, longer, with a soft knock on each beat."""
    d = 0.62; tt = t(d); x = np.zeros_like(tt)
    for st, amp in ((0.0, 1.0), (0.2, 0.8)):
        i = int(st * SR); tl = tt[: len(tt) - i]
        x[i:] += (np.sin(2 * np.pi * (48 * np.exp(-tl * 5) + 34) * tl) * np.exp(-tl * 9) * amp
                  + lowpass(rng.normal(0, 1, len(tl)), 0.08) * np.exp(-tl * 40) * amp * 0.8)
    return x


def tuuut():
    src = REPO / "audio/voix/recit-tower-0.mp3"
    out = OUT / "tuuut.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "16.55", "-t", "1.35", "-i", str(src), "-af",
                    f"aresample={SR},aformat=channel_layouts=mono,afade=t=out:st=1.05:d=0.3,volume=2.2,alimiter=limit=0.9",
                    str(out)], check=True)


if __name__ == "__main__":
    save("thud", thud()); save("tick", tick(), 0.5); save("tock", tick(False), 0.45)
    save("whoosh", whoosh(), 0.6); save("heart", heart(), 0.85); tuuut()
    save("heartbig", heart_big(), 0.97)
    print(sorted(p.name for p in OUT.iterdir()))
