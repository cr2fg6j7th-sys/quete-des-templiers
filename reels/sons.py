#!/usr/bin/env python3
"""Bande son des Reels : bruitages synthétisés ici (libres, ne doivent rien à personne) + musique de fond propre aux Reels.

    python3 reels/sons.py            # (re)crée reels/sons/*.wav
    (le moteur appelle aussi bande_son() pour mixer chaque Reel)

Bruitages placés automatiquement d'après le minutage du gabarit (gabarit-reel.html) :
  whoosh  changement de scène          pop     apparition d'un sticker
  trait   sticker barré                tic/toc compte à rebours (chaque seconde)
  eclat   arrivée de la solution       ding    bouton du CTA
Musique : reels/musique/aventure.mp3 (composée par musique.py, différente de celle du site), en boucle, sous les bruitages, fondu final.
"""
import math, subprocess, wave
from pathlib import Path
import numpy as np

ICI = Path(__file__).resolve().parent
SONS = ICI / "sons"
MUSIQUE_DEFAUT = ICI / "musique/aventure.mp3"      # composée par musique.py (différente de celle du site)
SR = 44100
rng = np.random.default_rng(11)

# minutage du gabarit (garder en phase avec gabarit-reel.html)
STICKER_T0, STICKER_PAS, BARRE_AVANT_FIN, BARRE_ECART = 0.57, 0.5, 0.77, 0.17


def t(d): return np.arange(int(d * SR)) / SR


def passe_bas(x, fc):
    """filtre passe-bas (moyenne glissante en cascade, assez doux pour des bruitages)"""
    n = max(1, int(SR / fc / 2))
    k = np.ones(n) / n
    for _ in range(3):
        x = np.convolve(x, k, mode="same")
    return x


def env(n, a, r):            # attaque / déclin exponentiel
    tt = np.arange(n) / SR
    return np.minimum(1, tt / max(a, 1e-4)) * np.exp(-tt / r)


def ecrire(nom, x, crete=0.9):
    x = x / (np.abs(x).max() + 1e-9) * crete
    SONS.mkdir(exist_ok=True)
    with wave.open(str(SONS / f"{nom}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def fabriquer():
    # pop : petite bulle (sinus qui monte vite) + clic
    d = t(0.12); f = 380 + 900 * (1 - np.exp(-d / 0.02))
    pop = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(d), 0.002, 0.035)
    pop[:60] += rng.normal(0, 0.4, 60) * np.linspace(1, 0, 60)
    ecrire("pop", pop)
    # trait : feutre sur le papier (bruit filtré, enveloppe en arche)
    d = t(0.22); b = rng.normal(0, 1, len(d))
    trait = (passe_bas(b, 5000) - passe_bas(b, 900)) * np.sin(np.pi * d / d[-1]) ** 0.6
    ecrire("trait", trait, 0.7)
    # tic / toc : bois léger
    for nom, f0 in (("tic", 2400), ("toc", 1800)):
        d = t(0.05)
        x = np.sin(2 * np.pi * f0 * d) * env(len(d), 0.0005, 0.008) + rng.normal(0, 0.3, len(d)) * env(len(d), 0.0002, 0.003)
        ecrire(nom, x, 0.8)
    # whoosh : souffle qui monte puis retombe
    d = t(0.45); b = rng.normal(0, 1, len(d))
    w = passe_bas(b, 2500) - passe_bas(b, 250)
    ecrire("whoosh", w * np.sin(np.pi * (d / d[-1]) ** 0.7) ** 2, 0.8)
    # eclat : arpège de clochettes (do-mi-sol-do) + scintillement
    d = t(1.6); x = np.zeros(len(d))
    for k, f0 in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        s = int(k * 0.07 * SR); dd = d[: len(d) - s]
        x[s:] += (np.sin(2 * np.pi * f0 * dd) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * dd)) * env(len(dd), 0.003, 0.5) * (0.9 - 0.1 * k)
    x += passe_bas(rng.normal(0, 1, len(d)), 9000) * 0.05 * env(len(d), 0.01, 0.25)
    ecrire("eclat", x, 0.75)
    # ding : cloche douce pour le bouton
    d = t(1.0); f0 = 1567.98
    ding = (np.sin(2 * np.pi * f0 * d) + 0.4 * np.sin(2 * np.pi * f0 * 2.0 * d) + 0.2 * np.sin(2 * np.pi * f0 * 3.01 * d)) * env(len(d), 0.002, 0.35)
    ecrire("ding", ding, 0.7)


def lire_wav(p):
    with wave.open(str(p)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32767


def lire_audio(p, duree, debut=0.0):
    """décode n'importe quel fichier audio en mono 44,1 kHz, en boucle si besoin"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", str(debut), "-i", str(p), "-t", str(duree),
                          "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<i2").astype(float) / 32767


def evenements(script):
    """liste (instant, bruitage, gain) déduite du script, au même minutage que l'animation"""
    sc = script["scenes"]
    ev = []
    sol = next((s["debut"] for s in sc if s["type"] != "probleme"), sc[-1]["fin"])
    for s in sc[1:]:
        ev.append((s["debut"] - 0.12, "whoosh", 0.35))
    for k in range(int(math.ceil(sol))):                       # une graine par seconde affichée
        if k + 0.02 < sol - 0.1:
            ev.append((k + 0.02, "tic" if k % 2 == 0 else "toc", 0.22))
    for s in sc:
        st = s.get("stickers") or []
        if not st:
            continue
        barre = None if s.get("barrer") is False else s.get("barrer_a", s["fin"] - BARRE_AVANT_FIN)
        fin_pop = (barre if barre is not None else s["fin"]) - 0.35
        pas = min(STICKER_PAS, (fin_pop - s["debut"] - STICKER_T0) / max(1, len(st) - 1)) if len(st) > 1 else 0
        for k in range(len(st)):
            ev.append((s["debut"] + STICKER_T0 + k * pas, "pop", 0.5))
        if barre is not None:
            for k in range((len(st) + 1) // 2):
                ev.append((barre + k * BARRE_ECART, "trait", 0.45))
    ev.append((sol + 0.05, "eclat", 0.5))
    cta = next((s for s in sc if s["type"] == "cta"), None)
    if cta:
        ev.append((cta["debut"] + 0.3, "ding", 0.35))
    for s in sc:                                               # CTA de chaque slide
        if s.get("cta") and s["type"] != "cta":
            ev.append((s["debut"] + 0.9, "pop", 0.3))
    return ev


def bande_son(script, duree, sortie: Path, base: Path):
    """mixe musique + bruitages → WAV stéréo ; renvoie le chemin"""
    if not (SONS / "eclat.wav").exists():
        fabriquer()
    n = int(duree * SR)
    mix = np.zeros(n)
    m = script.get("musique", "defaut")
    if m:
        p = MUSIQUE_DEFAUT if m == "defaut" else (base / m).resolve()
        mus = lire_audio(p, duree, script.get("musique_debut", 0))[:n]
        mus = np.pad(mus, (0, n - len(mus)))
        tt = np.arange(n) / SR
        fondu = np.minimum(1, tt / 0.5) * np.clip((duree - tt) / 1.5, 0, 1)
        mix += mus * fondu * 10 ** (script.get("musique_db", -12) / 20)
    if script.get("bruitages", True):
        cache = {}
        for t0, nom, g in evenements(script):
            x = cache.setdefault(nom, lire_wav(SONS / f"{nom}.wav"))
            i = int(max(0, t0) * SR)
            if i < n:
                seg = x[: n - i]
                mix[i:i + len(seg)] += seg * g
    crete = np.abs(mix).max()
    if crete > 0.95:
        mix *= 0.95 / crete
    st = np.repeat(mix[:, None], 2, axis=1)
    with wave.open(str(sortie), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    return sortie


if __name__ == "__main__":
    fabriquer()
    print("Bruitages :", ", ".join(sorted(p.stem for p in SONS.glob("*.wav"))))
