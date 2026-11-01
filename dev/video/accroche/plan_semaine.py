# Weekly review of 1 Nov 2026: the « question » intro (2.7 s, roulette of first names) in front of the four
# first-name videos of hook.py (free-preview end card), for the hand posts of 21-30 Nov. The file without the
# intro is kept too, for Instagram, until the Instagram test of 28 Oct - 6 Nov says which version to keep.
#   python3 dev/video/accroche/plan_semaine.py   (after: python3 dev/video/campagne/hook.py mael ambre nolan juliette)
import shutil, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from plan import q_roulette, BOYS, GIRLS

REPO = HERE.parents[2]
SRC = REPO / "dev/video/campagne/out/hook"
OUT = REPO / "marketing/videos"
PLAN = {
    "2026-11-21-mael": ("mael", q_roulette("Maël", "Ton fils s'appelle <em>comment</em> ?", "Monte le son.", BOYS)),
    "2026-11-23-ambre": ("ambre", q_roulette("Ambre", "Il connaît le prénom de <em>ta fille</em> ?", "Écoute.", GIRLS)),
    "2026-11-26-nolan": ("nolan", q_roulette("Nolan", "Et si un chevalier appelait <em>ton fils</em> ?", "Par son prénom.", BOYS + ["Nolan"])),
    "2026-11-29-juliette": ("juliette", q_roulette("Juliette", "Ta fille s'appelle <em>comment</em> ?", "Monte le son.", GIRLS + ["Juliette"])),
}

if __name__ == "__main__":
    from accroche import make
    for out, (slug, cfg) in PLAN.items():
        if sys.argv[1:] and out not in sys.argv[1:]: continue
        make(SRC / f"{slug}.mp4", OUT / f"{out}.mp4", cfg)
        shutil.copy(SRC / f"{slug}.mp4", OUT / f"{out}-sans-accroche.mp4")
        print("ok", out, flush=True)
