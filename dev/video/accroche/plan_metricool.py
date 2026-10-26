# The « question » hook (model of 23 Oct) put in front of the videos already scheduled in Metricool (26 Oct 2026,
# Nathan: « mettre à jour les publications… mettre que celles avec des nouveaux hooks »). Those videos were made on
# 19-20 Oct, before the hooks. Same intros as the hand-posting page; the Metricool posts keep their date and caption,
# only the first caption line takes the hook's question.
#   python3 dev/video/accroche/plan_metricool.py [slug …]   -> marketing/videos-metricool/<slug>.mp4 + .jpg
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from plan import question, q_roulette, q_defi, q_village, q_ans, BOYS, KIDS, KW_PISTE, KW_TRESOR, KW_KID, KW_ENIGME

M = REPO / "marketing"
OUT = M / "videos-metricool"

# slug: (source, hook, first caption line)
PLAN = {
    "10-27-1745-couvre-feu": (M / "videos-hook/couvre-feu.mp4",
        q_defi("DÉFI PARENTS", "D'où vient <em>« couvre-feu »</em> ?", "Presque personne ne sait.", KW_ENIGME),
        "D'où vient le mot « couvre-feu » ? Presque personne ne le sait 🔔"),
    "10-30-1745-hugo": (M / "videos-hook/hugo.mp4",
        q_roulette("Hugo", "Ton fils s'appelle <em>comment</em> ?", "Monte le son.", BOYS),
        "Ton fils s'appelle comment ? Si c'est Hugo, monte le son 🔊"),
    "11-07-0942-ouverture": (M / "videos-ouverture/ouverture.mp4",
        question("L'anniversaire approche, <em>rien de prêt</em> ?", "C'est ouvert.", KW_TRESOR),
        "L'anniversaire approche et rien n'est prêt ? C'est le grand jour : la quête est ouverte ⚔️"),
    "11-07-1817-comment-ca-marche": (M / "videos-ouverture/comment-ca-marche-2.mp4",
        question("Un anniversaire <em>sans rien préparer</em> ?", "Voici comment.", KW_PISTE),
        "Un anniversaire de chevalier sans rien préparer ? Voici comment ça se passe 🗺️"),
    "11-08-1036-prenoms": (M / "videos-ouverture/prenoms.mp4",
        q_roulette("Ton enfant ?", "Il connaît <em>le prénom</em> de ton enfant ?", "1 500 prénoms.", KIDS, KW_KID),
        "Il connaît le prénom de ton enfant ? Jules, Inès, Noah, Mia, Tom, Zoé… 👑"),
    "11-10-1808-maison-novembre": (M / "videos-ouverture/maison-novembre.mp4",
        question("Il pleut <em>samedi</em> ?", "Et l'anniversaire ?", "Anniversaire chevalier à la maison", cal="Samedi"),
        "Il pleut samedi, il fait nuit à 17 h… et l'anniversaire ? 🌧️"),
    "11-12-1221-diplomes": (M / "videos-ouverture/diplomes.mp4",
        q_ans("Ton enfant grandit <em>trop vite</em> ?", 8),
        "Ton enfant grandit trop vite ? 8 ans, une seule fois. Le mot secret est trouvé, l'adoubement peut commencer ⚔️"),
    "11-14-1053-mot-fidele": (M / "videos-ouverture/mot-fidele.mp4",
        q_defi("DÉFI PARENTS", "Tu trouves <em>le mot secret</em> ?", "Avant ton enfant ?"),
        "Tu trouves le mot secret avant ton enfant ? L, E, D, I, F, E… 🔤"),
    "11-17-1834-prix": (M / "videos-ouverture/prix.mp4",
        question("Budget serré pour <em>l'anniversaire</em> ?", "Fais le calcul.", "Idée anniversaire petit budget",
                 cal="Budget", labels=["50 €", "100 €", "150 €", "200 €", "250 €"]),
        "Budget serré pour l'anniversaire ? Le calcul des parents : 8 enfants, 3,11 € par enfant 🧮"),
    "11-20-1746-votre-ville": (M / "videos-ouverture/votre-ville.mp4",
        q_village("Tu habites <em>un petit village</em> ?", "Ça marche aussi."),
        "Tu habites un petit village ? Ça marche aussi : Obernai, Molsheim, Mutzig, Ottrott… et le tien ? 📍"),
    "11-25-1412-devinez-le-lieu": (M / "videos-ouverture/devinez-le-lieu.mp4",
        q_defi("DÉFI DU MERCREDI", "Tu trouves <em>les 3 lieux</em> ?", "Avant ton enfant ?", KW_PISTE),
        "Défi du mercredi : tu trouves les trois lieux avant ton enfant ? 🧩"),
    "11-27-1823-prenoms-hiver": (M / "videos-ouverture/prenoms-hiver.mp4",
        q_roulette("Ton enfant ?", "Un anniversaire <em>en décembre</em> ?", "Il connaît son prénom.", KIDS, KW_KID),
        "Un anniversaire en décembre ? Hugo, Lina, Sacha, Manon, Ethan, Camille… ❄️"),
    "11-28-1047-maison-hiver": (M / "videos-ouverture/maison-hiver.mp4",
        question("Nuit à 17 h, <em>et la fête</em> ?", "Elle se joue à la maison.", "Anniversaire chevalier à la maison", cal="Décembre"),
        "Nuit à 17 h, et la fête ? Elle se joue à la maison ☁️"),
    "11-30-1805-mot-epee": (M / "videos-ouverture/mot-epee.mp4",
        q_defi("DÉFI PARENTS", "4 lettres, <em>un mot</em>. Facile ?", "Tu as 5 secondes.", seconds=5),
        "4 lettres, un mot de chevalier. Facile ? E, E, P, E… ⚔️"),
}

if __name__ == "__main__":
    from accroche import make
    OUT.mkdir(parents=True, exist_ok=True)
    for slug in sys.argv[1:] or list(PLAN):
        src, hook, _ = PLAN[slug]
        out = OUT / f"{slug}.mp4"
        make(src, out, hook)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "0.5", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(OUT / f"{slug}.jpg")], check=True)
        print("ok", slug, flush=True)
