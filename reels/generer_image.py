#!/usr/bin/env python3
"""Illustrations des Reels « problème de parent → solution » (Ma Quête Légendaire).

    # une image
    python3 reels/generer_image.py "prompt de la scène" sorties/<dossier>/img/s1.jpg
    # toutes les images manquantes d'un script (champ « prompt » de chaque scène)
    python3 reels/generer_image.py --script sorties/<dossier>/script.json [--refaire]

Ordre des fournisseurs :
  1. Hugging Face (huggingface_hub.InferenceClient, FLUX.1-schnell, jeton HF_TOKEN) — en priorité ;
  2. fal.ai (fal-ai/flux/schnell, clé FAL_KEY) — seulement si Hugging Face échoue.
Sans aucune clé, le script le dit et s'arrête (code 2) : l'agent peut alors passer par l'outil MCP
Hugging Face (Z-Image Turbo) puis copier l'image produite à l'emplacement attendu.

Le STYLE commun est ajouté devant chaque prompt pour garder la même direction artistique.
"""
import argparse, io, json, os, sys, urllib.request
from pathlib import Path

STYLE = ("Modern children's book illustration, soft flat colors, thin clean outlines, warm pastel palette of cream, "
         "terracotta, sage green and burgundy, golden warm light, cozy, kind and gently funny mood. ")
FIN = " No text, no letters, no words, no logos, no existing characters or brands."
W, H = 1152, 864           # paysage 4:3, recadré en ~980×755 dans la carte
HF_MODELE = os.environ.get("HF_MODELE", "black-forest-labs/FLUX.1-schnell")


def prompt_complet(p: str) -> str:
    return STYLE + p.strip() + FIN


def via_hf(prompt: str, seed=None):
    from huggingface_hub import InferenceClient
    tok = os.environ.get("HF_TOKEN")
    if not tok:
        raise RuntimeError("HF_TOKEN absent")
    cli = InferenceClient(token=tok)
    return cli.text_to_image(prompt, model=HF_MODELE, width=W, height=H, seed=seed)


def via_fal(prompt: str, seed=None):
    from PIL import Image
    key = os.environ.get("FAL_KEY")
    if not key:
        raise RuntimeError("FAL_KEY absent")
    corps = {"prompt": prompt, "image_size": {"width": W, "height": H}, "num_inference_steps": 4, "num_images": 1,
             "enable_safety_checker": True}
    if seed is not None:
        corps["seed"] = seed
    req = urllib.request.Request("https://fal.run/fal-ai/flux/schnell", data=json.dumps(corps).encode(),
                                 headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        url = json.load(r)["images"][0]["url"]
    with urllib.request.urlopen(url, timeout=120) as r:
        return Image.open(io.BytesIO(r.read()))


def generer(prompt: str, sortie: Path, seed=None):
    p = prompt_complet(prompt)
    erreurs = []
    for nom, f in (("Hugging Face", via_hf), ("fal.ai", via_fal)):
        try:
            img = f(p, seed)
            sortie.parent.mkdir(parents=True, exist_ok=True)
            img.convert("RGB").save(sortie, quality=92)
            print(f"{sortie}  ({nom})")
            return nom
        except Exception as e:  # on passe au fournisseur suivant
            erreurs.append(f"{nom} : {e}")
    print("Aucun fournisseur n'a fonctionné :\n- " + "\n- ".join(erreurs), file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?"); ap.add_argument("sortie", nargs="?")
    ap.add_argument("--script"); ap.add_argument("--refaire", action="store_true"); ap.add_argument("--seed", type=int)
    ap.add_argument("--montrer-prompt", action="store_true", help="affiche le prompt complet sans rien générer")
    a = ap.parse_args()
    if a.script:
        sp = Path(a.script)
        for i, sc in enumerate(json.loads(sp.read_text(encoding="utf-8"))["scenes"]):
            dest = sp.parent / sc["image"]
            if a.montrer_prompt:
                print(f"{dest}\n  {prompt_complet(sc['prompt'])}"); continue
            if dest.exists() and not a.refaire:
                print(f"{dest} existe déjà (--refaire pour la régénérer)"); continue
            generer(sc["prompt"], dest, a.seed)
    elif a.prompt and a.sortie:
        if a.montrer_prompt:
            print(prompt_complet(a.prompt)); return
        generer(a.prompt, Path(a.sortie), a.seed)
    else:
        ap.error("donner « prompt sortie » ou --script")


if __name__ == "__main__":
    main()
