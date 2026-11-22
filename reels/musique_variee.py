#!/usr/bin/env python3
"""Une bande son différente pour chaque Reel (consigne de Nathan, 22/11/2026).

    python3 reels/musique_variee.py              # compose toutes les pistes du CATALOGUE absentes de reels/musique/
    python3 reels/musique_variee.py --liste      # pistes disponibles et Reels qui les ont déjà utilisées
    python3 reels/musique_variee.py --nouvelle   # compose une piste inédite (graine au hasard) et affiche son nom

Composées par programme (libres de droits) avec les instruments de musique.py : luth (corde pincée), flûte,
cloches, vièle, bourdon, tambour sur cadre et grelots. Chaque piste a sa tonalité, son mode, son tempo, sa grille
d'accords, sa mélodie (générée à partir d'une graine) et son orchestration. Durée : 16 mesures, boucle propre.
Dans script.json : "musique": "<nom>" (fichier reels/musique/<nom>.mp3). "defaut" = aventure.mp3.
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np
import musique as M

ICI = Path(__file__).resolve().parent
DOSSIER = ICI / "musique"
SR = M.SR
MODES = {"majeur": [0, 2, 4, 5, 7, 9, 11], "mineur": [0, 2, 3, 5, 7, 8, 10],
         "dorien": [0, 2, 3, 5, 7, 9, 10], "mixolydien": [0, 2, 4, 5, 7, 9, 10]}

# nom: tonique (MIDI de la basse), mode, bpm, grille (degrés 0-6, 16 mesures), graine, mélodie, accompagnement, percussions
CATALOGUE = {
    "marche-des-chevaliers": dict(tonique=43, mode="majeur", bpm=112, grille=[0, 3, 4, 0, 0, 3, 4, 4, 5, 3, 0, 4, 0, 3, 4, 0], graine=11, lead="flute", accomp="galop", perc="marche"),
    "ruelles-en-fete": dict(tonique=41, mode="majeur", bpm=120, grille=[0, 4, 5, 3, 0, 4, 3, 4, 0, 4, 5, 3, 1, 4, 4, 0], graine=23, lead="cloche", accomp="arpege", perc="fete"),
    "enigme-du-grand-maitre": dict(tonique=45, mode="dorien", bpm=94, grille=[0, 6, 0, 3, 0, 6, 3, 4, 0, 6, 0, 3, 5, 3, 4, 0], graine=37, lead="viele", accomp="arpege", perc="doux"),
    "chasse-au-tresor": dict(tonique=40, mode="mixolydien", bpm=104, grille=[0, 6, 3, 0, 0, 6, 3, 4, 0, 6, 3, 0, 3, 6, 4, 0], graine=51, lead="flute", accomp="accords", perc="marche"),
    "le-coffre-dore": dict(tonique=42, mode="mineur", bpm=98, grille=[0, 5, 2, 6, 0, 5, 6, 4, 0, 5, 2, 6, 3, 5, 4, 0], graine=67, lead="cloche", accomp="arpege", perc="doux"),
    "petits-heros": dict(tonique=44, mode="majeur", bpm=116, grille=[0, 5, 3, 4, 0, 5, 3, 4, 3, 4, 0, 5, 3, 4, 4, 0], graine=79, lead="viele", accomp="galop", perc="fete"),
}
RYTHMES = [[1, 1, 1, 1], [1, .5, .5, 1, 1], [1.5, .5, 2], [.5, .5, .5, .5, 1, 1], [2, 1, 1], [1, 1, 2], [.5, .5, 1, .5, .5, 1]]


def cloche(f, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.0 * t) + 0.2 * np.sin(2 * np.pi * f * 3.01 * t)
    return x * np.exp(-t / 0.45) * np.minimum(1, t / 0.003)


def viele(f, dur):
    t = np.arange(int(dur * SR)) / SR
    vib = 1 + 0.007 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.2)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = sum(np.sin(k * ph) / k ** 1.3 for k in range(1, 8))          # corde frottée (dents de scie adoucie)
    a = np.minimum(1, t / 0.07) * np.clip((dur - t) / 0.1, 0, 1)
    return x * a * 0.8


def melodie(cfg, gamme):
    """mélodie générée : notes d'accord sur les temps forts, mouvement conjoint ailleurs, cadences toutes les 4 mesures"""
    rng = np.random.default_rng(cfg["graine"])
    base = cfg["tonique"] + 24                                          # registre de la mélodie
    notes_gamme = [base + o * 12 + g for o in (0, 1) for g in gamme] + [base + 24]
    pos = 4                                                              # index dans notes_gamme
    out = []
    for b, deg in enumerate(cfg["grille"]):
        accord = {(deg + k) % 7 for k in (0, 2, 4)}
        fin_phrase = b % 4 == 3
        rythme = [3, 1] if fin_phrase else RYTHMES[rng.integers(len(RYTHMES))]
        temps = 0
        for j, d in enumerate(rythme):
            if fin_phrase and j == 1:
                out.append((None, d)); temps += d; continue
            fort = temps % 1 == 0 and (temps % 2 == 0 or rng.random() < 0.5)
            if fort or fin_phrase:
                cand = [i for i, n in enumerate(notes_gamme) if i % 7 in accord]
                if fin_phrase:
                    cand = [i for i in cand if i % 7 == deg % 7]
                pos = min(cand, key=lambda i: abs(i - pos) + rng.random() * 1.5)
            else:
                pos = int(np.clip(pos + rng.choice([-1, 1, 1, -2, 2]), 0, len(notes_gamme) - 1))
            out.append((notes_gamme[pos], d)); temps += d
        out.append(("|", 0))
    return out


def composer(nom, cfg):
    gamme = MODES[cfg["mode"]]
    temps_s = 60 / cfg["bpm"]; mesure = 4 * temps_s
    total = len(cfg["grille"]) * mesure
    n = int(total * SR) + 2 * SR
    p = {k: np.zeros(n) for k in ("acc", "lead", "bourdon", "perc")}
    rng = np.random.default_rng(cfg["graine"] + 1)

    def poser(piste, x, t0, g=1.0):
        i = int(t0 * SR); x = x[: n - i]; p[piste][i:i + len(x)] += x * g

    def note(deg, octave=0):
        return cfg["tonique"] + 12 * (octave + deg // 7) + gamme[deg % 7]

    for b, deg in enumerate(cfg["grille"]):
        t0 = b * mesure
        r, tierce, quinte = note(deg), note(deg + 2), note(deg + 4)
        poser("bourdon", M.bourdon([r - 12 if r > 45 else r, quinte - 12 if quinte > 50 else quinte], mesure + 0.3), t0, 0.45)
        if cfg["accomp"] == "arpege":
            motif = [r, quinte, r + 12, tierce + 12, quinte + 12, tierce + 12, r + 12, quinte]
            for k, m in enumerate(motif):
                poser("acc", M.corde(M.hz(m), 1.2, clair=0.7), t0 + k * temps_s / 2, 0.9 if k % 2 == 0 else 0.6)
        elif cfg["accomp"] == "galop":                                     # croche-double-double
            for k in range(4):
                for dt, m, g in ((0, r + 12, 0.9), (0.5, quinte + 12, 0.55), (0.75, tierce + 12, 0.55)):
                    poser("acc", M.corde(M.hz(m), 0.9, clair=0.75), t0 + (k + dt) * temps_s, g)
        else:                                                              # accords plaqués sur 1 et 3, égrenés
            for k in (0, 2):
                for j, m in enumerate((r, quinte, r + 12, tierce + 12)):
                    poser("acc", M.corde(M.hz(m), 1.6, clair=0.6), t0 + k * temps_s + j * 0.025, 0.7)
        for k in range(4):
            if cfg["perc"] == "marche":
                poser("perc", M.tambour(f0=90), t0 + k * temps_s, 1.0 if k in (0, 2) else 0.55)
                if k == 3: poser("perc", M.tambour(f0=110, dur=0.2), t0 + (k + 0.5) * temps_s, 0.5)
            elif cfg["perc"] == "fete":
                if k in (0, 2): poser("perc", M.tambour(f0=95), t0 + k * temps_s, 1.0)
                for dt in (0.5, 0.75) if k % 2 else (0.5,):
                    poser("perc", M.grelots(), t0 + (k + dt) * temps_s, 0.3)
            else:
                if k == 0: poser("perc", M.tambour(f0=85, dur=0.45), t0, 0.8)
                poser("perc", M.grelots(0.08), t0 + (k + 0.5) * temps_s, 0.15)
    tt, b = 0.0, 0
    instr = {"flute": M.flute, "cloche": cloche, "viele": viele}[cfg["lead"]]
    for m, d in melodie(cfg, gamme):
        if m == "|":
            b += 1; tt = b * mesure; continue
        if m is not None:
            poser("lead", instr(M.hz(m), d * temps_s * (0.98 if cfg["lead"] == "cloche" else 0.93) + (0.4 if cfg["lead"] == "cloche" else 0)), tt)
        tt += d * temps_s
    norm = lambda x: x / (np.abs(x).max() + 1e-9)
    mix = 0.5 * norm(p["acc"]) + 0.42 * norm(p["lead"]) + 0.2 * norm(p["bourdon"]) + 0.33 * norm(p["perc"])
    rev = mix.copy()
    for d, g in ((0.029, 0.27), (0.043, 0.21), (0.071, 0.15), (0.12, 0.09)):
        k = int(d * SR); rev[k:] += mix[:-k] * g
    fin = int(total * SR)
    queue = rev[fin:]; rev = rev[:fin]; rev[: len(queue)] += queue * 0.8   # boucle propre
    rev = rev / np.abs(rev).max() * 0.9
    st = np.stack([rev, np.roll(rev, int(0.012 * SR))], axis=1)
    DOSSIER.mkdir(exist_ok=True)
    out = DOSSIER / f"{nom}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "libmp3lame", "-q:a", "3", str(out)], input=(st * 32767).astype("<i2").tobytes(), check=True)
    print(f"{out} ({total:.1f} s, {cfg['mode']}, {cfg['bpm']} bpm, {cfg['lead']})")
    return out


def utilisations():
    """piste -> dossiers de Reels qui l'utilisent (d'après les script.json)"""
    u = {}
    for sp in sorted((ICI / "sorties").glob("*/script.json")):
        m = json.loads(sp.read_text(encoding="utf-8")).get("musique", "defaut")
        u.setdefault("aventure" if m in ("defaut", None) else Path(str(m)).stem, []).append(sp.parent.name)
    return u


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--liste", action="store_true"); ap.add_argument("--nouvelle", action="store_true")
    a = ap.parse_args()
    if a.liste:
        u = utilisations()
        for f in sorted(DOSSIER.glob("*.mp3")):
            print(f"{f.stem:24} {', '.join(u.get(f.stem, [])) or 'jamais utilisée'}")
    elif a.nouvelle:
        g = int(np.random.default_rng().integers(1000, 99999))
        r = np.random.default_rng(g)
        cfg = dict(tonique=int(r.integers(40, 46)), mode=str(r.choice(list(MODES))), bpm=int(r.integers(92, 124)),
                   grille=[0] + [int(x) for x in r.choice([0, 3, 4, 5, 1, 6], 14)] + [0], graine=g,
                   lead=str(r.choice(["flute", "cloche", "viele"])), accomp=str(r.choice(["arpege", "galop", "accords"])),
                   perc=str(r.choice(["marche", "fete", "doux"])))
        composer(f"piste-{g}", cfg)
    else:
        for nom, cfg in CATALOGUE.items():
            if not (DOSSIER / f"{nom}.mp3").exists():
                composer(nom, cfg)
