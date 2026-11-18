#!/usr/bin/env python3
"""Musique de fond des Reels, composée ici par programme (libre de droits, différente de la musique du site).

    python3 reels/musique.py      -> reels/musique/aventure.mp3 (≈ 39 s, boucle propre)

Petite aventure médiévale joyeuse en ré dorien, 100 bpm : luth en arpèges (corde pincée Karplus-Strong),
bourdon doux, flûte à bec (mélodie avec vibrato), tambour sur cadre et grelots. 16 mesures.
"""
import subprocess, wave
from pathlib import Path
import numpy as np

ICI = Path(__file__).resolve().parent
SR = 44100
BPM = 100
TEMPS = 60 / BPM                      # une noire
MESURE = 4 * TEMPS
rng = np.random.default_rng(3)

def hz(n): return 440 * 2 ** ((n - 69) / 12)        # numéro MIDI -> Hz

# grille (accords en MIDI, basse en premier) : Dm C Bb C | Dm F C Dm, deux fois avec fin variée
DM, C, BB, F, AM = [50, 57, 62, 65, 69], [48, 55, 60, 64, 67], [46, 53, 58, 62, 65], [41, 53, 60, 65, 69], [45, 52, 57, 60, 64]
GRILLE = [DM, C, BB, C, DM, F, C, DM, DM, C, BB, AM, F, C, BB, DM]
# mélodie (MIDI, durée en temps) ; None = silence
M = [
    [(74, 1), (76, 0.5), (77, 0.5), (76, 1), (74, 1)],
    [(72, 1.5), (74, 0.5), (76, 2)],
    [(77, 1), (76, 0.5), (74, 0.5), (72, 1), (70, 1)],
    [(72, 3), (None, 1)],
    [(74, 0.5), (76, 0.5), (77, 1), (79, 1), (81, 1)],
    [(81, 1), (79, 0.5), (77, 0.5), (76, 2)],
    [(79, 1), (77, 0.5), (76, 0.5), (74, 1), (72, 1)],
    [(74, 3), (None, 1)],
    [(81, 1), (79, 0.5), (81, 0.5), (77, 1), (76, 1)],
    [(74, 0.5), (76, 0.5), (79, 1), (76, 2)],
    [(77, 1), (79, 0.5), (77, 0.5), (74, 2)],
    [(76, 1), (72, 1), (69, 2)],
    [(72, 0.5), (74, 0.5), (77, 1), (81, 2)],
    [(79, 1), (76, 1), (74, 0.5), (72, 0.5), (76, 1)],
    [(77, 1), (76, 0.5), (74, 0.5), (74, 1), (72, 1)],
    [(74, 4)],
]


def corde(f, dur, clair=0.5, amorti=0.996):
    """corde pincée (Karplus-Strong), calcul par blocs de la longueur d'onde"""
    n, N = int(dur * SR), max(2, int(SR / f))
    buf = rng.uniform(-1, 1, N)
    buf = clair * buf + (1 - clair) * np.convolve(buf, [0.5, 0.5], "same")
    out = np.empty(n + N); out[:N] = buf
    i = N
    while i < n + N:
        j = min(i + N, n + N)
        prev = out[i - N:j - N]; prev2 = out[i - N - 1:j - N - 1] if i - N - 1 >= 0 else np.concatenate([[0], out[i - N:j - N - 1]])
        out[i:j] = amorti * 0.5 * (prev + prev2)
        i = j
    return out[N:]


def flute(f, dur):
    t = np.arange(int(dur * SR)) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.25)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    x += rng.normal(0, 0.02, len(t))                                   # souffle
    a = np.minimum(1, t / 0.04) * np.minimum(1, (dur - t) / 0.08).clip(0)
    return x * a


def bourdon(notes, dur):
    t = np.arange(int(dur * SR)) / SR
    x = sum(np.sin(2 * np.pi * hz(n) * t) * 0.5 + 0.15 * np.sin(4 * np.pi * hz(n) * t) for n in notes)
    return x * np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.3).clip(0)


def tambour(dur=0.35, f0=95):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * (1 + 0.6 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) + rng.normal(0, 0.15, len(t)) * np.exp(-t / 0.01)


def grelots(dur=0.12):
    t = np.arange(int(dur * SR)) / SR
    b = rng.normal(0, 1, len(t)); b = b - np.convolve(b, np.ones(6) / 6, "same")    # passe-haut grossier
    return b * np.exp(-t / 0.04)


def composer():
    total = len(GRILLE) * MESURE
    n = int(total * SR) + SR
    piste = {k: np.zeros(n) for k in ("luth", "flute", "bourdon", "perc")}
    def poser(nom, x, t0, g=1.0):
        i = int(t0 * SR); x = x[: n - i]; piste[nom][i:i + len(x)] += x * g
    for b, acc in enumerate(GRILLE):
        t0 = b * MESURE
        poser("bourdon", bourdon([acc[0] - 12, acc[0] - 5], MESURE + 0.3), t0, 0.5)
        motif = [0, 2, 3, 4, 3, 2, 1, 2]                                # arpège en croches
        for k, idx in enumerate(motif):
            poser("luth", corde(hz(acc[idx]), 1.2, clair=0.7), t0 + k * TEMPS / 2, 0.9 if k % 2 == 0 else 0.6)
        for k in range(4):                                              # tambour 1 et 3, grelots sur les contretemps
            if k in (0, 2):
                poser("perc", tambour(), t0 + k * TEMPS, 1.0 if k == 0 else 0.7)
            poser("perc", grelots(), t0 + k * TEMPS + TEMPS / 2, 0.25)
        if b >= 0:
            tt = t0
            for note, d in M[b]:
                if note:
                    poser("flute", flute(hz(note), d * TEMPS * 0.95), tt, 1.0)
                tt += d * TEMPS
    norm = lambda x: x / (np.abs(x).max() + 1e-9)
    mix = 0.55 * norm(piste["luth"]) + 0.42 * norm(piste["flute"]) + 0.22 * norm(piste["bourdon"]) + 0.35 * norm(piste["perc"])
    # petite réverbération (échos décroissants)
    rev = mix.copy()
    for d, g in ((0.031, 0.28), (0.047, 0.22), (0.073, 0.16), (0.11, 0.1)):
        k = int(d * SR); rev[k:] += mix[:-k] * g
    rev = rev[: int(total * SR)]
    # boucle propre : la queue de fin est ajoutée au début
    queue = (mix[int(total * SR):] if len(mix) > int(total * SR) else np.zeros(0))
    rev[: len(queue)] += queue * 0.8
    rev = rev / np.abs(rev).max() * 0.9
    st = np.stack([rev, np.roll(rev, int(0.012 * SR))], axis=1)          # léger élargissement stéréo
    out = ICI / "musique" / "aventure.mp3"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "libmp3lame", "-q:a", "3", str(out)], input=(st * 32767).astype("<i2").tobytes(), check=True)
    print(f"{out} ({total:.1f} s)")


if __name__ == "__main__":
    composer()
