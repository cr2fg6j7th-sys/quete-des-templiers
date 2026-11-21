#!/usr/bin/env python3
"""Rendu d'un Reel 9:16 « problème de parent → solution » pour Ma Quête Légendaire.

    python3 reels/render_reel_probleme.py sorties/<dossier>/script.json sorties/<dossier>/reel.mp4 [--force] [--apercu 3.2,9,20]

- Vérifie le script (lignes ≤ 22 caractères, scènes contiguës, images présentes, durée 20-25 s).
- Anime reels/gabarit-reel.html image par image dans Chromium (Playwright, 1080×1920, 30 i/s).
- Contrôle les zones protégées (Instagram/TikTok) au milieu de chaque scène : s'arrête en cas d'erreur, sauf --force.
- Bande son (sons.py) : musique de fond (« musique » : "defaut" = musique du site, un chemin, ou null) + bruitages
  calés sur l'animation (« bruitages » : false pour les couper) ; assemble en H.264 + AAC avec ffmpeg.
- --apercu : n'écrit que des images fixes aux instants donnés (pour régler vite), sans vidéo.
"""
import argparse, json, math, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from sons import bande_son

ICI = Path(__file__).resolve().parent
FPS, W, H = 30, 1080, 1920
MAX_CAR = 22


def charger(script_path: Path):
    s = json.loads(script_path.read_text(encoding="utf-8"))
    base = script_path.parent
    err = []
    scenes = s["scenes"]
    for i, sc in enumerate(scenes):
        for k in ("l1", "l2"):
            if len(sc.get(k, "").replace("**", "")) > MAX_CAR:
                err.append(f"scène {i+1} : {k} « {sc[k]} » fait {len(sc[k])} caractères (max {MAX_CAR})")
        if i and abs(sc["debut"] - scenes[i-1]["fin"]) > 1e-6:
            err.append(f"scène {i+1} : commence à {sc['debut']} au lieu de {scenes[i-1]['fin']}")
        img = (base / sc["image"]).resolve()
        if not img.exists():
            err.append(f"scène {i+1} : image introuvable {img}")
        sc["image"] = img.as_uri()
        if sc["type"] in ("solution", "benefice") and not sc.get("cta"):
            err.append(f"scène {i+1} : CTA de slide manquant (champ « cta »)")
    if scenes[-1]["type"] != "cta":
        err.append("la dernière scène doit être de type « cta »")
    duree = scenes[-1]["fin"]
    if not 20 <= duree <= 25:
        err.append(f"durée {duree} s hors de 20-25 s")
    return s, err


def page_html(s):
    tpl = (ICI / "gabarit-reel.html").read_text(encoding="utf-8")
    return tpl.replace("__FONTS__", (ICI / "fonts").as_uri()).replace("__DATA__", json.dumps(s, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("sortie")
    ap.add_argument("--force", action="store_true", help="rendre malgré les erreurs de contrôle")
    ap.add_argument("--apercu", help="instants (s) séparés par des virgules : images fixes seulement")
    a = ap.parse_args()

    script_path = Path(a.script).resolve()
    sortie = Path(a.sortie).resolve()
    s, err = charger(script_path)
    if err and not a.force:
        sys.exit("Script refusé :\n- " + "\n- ".join(err))

    tmp_html = script_path.parent / "_reel.html"
    tmp_html.write_text(page_html(s), encoding="utf-8")
    duree = s["scenes"][-1]["fin"]
    n = int(round(duree * FPS))

    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(tmp_html.as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_function("[...document.images].every(i => i.complete && i.naturalWidth > 0)")
        page.evaluate("ajuster()")

        # contrôle des zones protégées au milieu (et juste après l'apparition des stickers) de chaque scène
        problemes = []
        for i, sc in enumerate(s["scenes"]):
            for t in sorted({(sc["debut"] + sc["fin"]) / 2, sc["fin"] - 0.4}):
                page.evaluate(f"render({t})")
                problemes += [f"scène {i+1} ({t:.1f} s) : {e}" for e in page.evaluate("controle()")]
        if problemes:
            print("Contrôle des zones :\n- " + "\n- ".join(dict.fromkeys(problemes)))
            if not a.force:
                nav.close(); tmp_html.unlink(missing_ok=True)
                sys.exit("Rendu arrêté (corriger le script, ou --force).")
        else:
            print("Contrôle des zones : OK (rien dans les zones protégées, aucun texte coupé)")

        if a.apercu:
            sortie.parent.mkdir(parents=True, exist_ok=True)
            for t in [float(x) for x in a.apercu.split(",")]:
                page.evaluate(f"render({t})")
                f = sortie.with_name(f"{sortie.stem}_{t:05.2f}s.jpg")
                page.screenshot(path=str(f), type="jpeg", quality=92); print(f)
            nav.close(); tmp_html.unlink(missing_ok=True); return

        audio_wav = sortie.with_suffix(".tmp.wav")
        bande_son(s, duree, audio_wav, script_path.parent)
        audio, afilt = ["-i", str(audio_wav)], ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100"]
        sortie.parent.mkdir(parents=True, exist_ok=True)
        tmp_mp4 = sortie.with_suffix(".tmp.mp4")
        ff = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
             *audio, "-map", "0:v", "-map", "1:a", *afilt,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "160k", "-t", f"{duree:.3f}", "-movflags", "+faststart", str(tmp_mp4)],
            stdin=subprocess.PIPE)
        for k in range(n):
            page.evaluate(f"render({k / FPS})")
            ff.stdin.write(page.screenshot(type="jpeg", quality=94))
            if k % 60 == 0:
                print(f"  image {k}/{n}", flush=True)
        ff.stdin.close()
        if ff.wait():
            sys.exit("ffmpeg a échoué")
        nav.close()
    tmp_mp4.replace(sortie)
    audio_wav.unlink(missing_ok=True)
    tmp_html.unlink(missing_ok=True)
    print(f"Vidéo : {sortie} ({duree:.1f} s, {n} images)")


if __name__ == "__main__":
    main()
