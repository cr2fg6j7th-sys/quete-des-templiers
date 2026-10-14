/* ENGINE-START
   Quest generator: OpenStreetMap places around a start point -> a 4 to 6 step quest.
   Pure functions only (no DOM): runs on the server (Cloudflare), in Node for tests,
   and in the browser for the free demo build. */

const QuestEngine = (() => {
  const G = (typeof QuestGeo !== "undefined") ? QuestGeo : require("./geo.js");
  const { SEARCH_RADIUS, overpassQuery, dist, bearing } = G;
  const MAX_WALK = 1600;         // metres of walking for the whole quest
  const WALK_FACTOR = 1.3;       // straight line -> real walking distance
  const MIN_GAP = 60;            // two stops closer than this feel like one place

  // ---- 1. classify OSM elements into kid-friendly categories ----
  const BASE = { gate: 9, castle: 9, ruins: 8, tower: 8, church: 8, well: 8, fountain: 7, viewpoint: 6,
    townhall: 6, square: 6, park: 6, statue: 6, memorial: 5, artwork: 5, playground: 4 };

  function classify(el) {
    const t = el.tags || {};
    if (t.access === "private" || t.access === "no") return null;
    const lat = el.lat ?? el.center?.lat, lon = el.lon ?? el.center?.lon;
    if (lat == null || lon == null) return null;
    let cat = null;
    if (t.historic === "city_gate") cat = "gate";
    else if (["castle", "fort", "manor"].includes(t.historic)) cat = "castle";
    else if (t.historic === "ruins" || t.historic === "archaeological_site") cat = t.name ? "ruins" : null;
    else if (t.historic === "tower" || t.man_made === "tower") cat = "tower";
    else if (t.amenity === "place_of_worship") cat = (!t.religion || t.religion === "christian") ? "church" : null;
    else if (t.man_made === "water_well") cat = "well";
    else if (t.amenity === "fountain") cat = "fountain";
    else if (t.amenity === "townhall") cat = (!t.townhall || t.townhall === "city") ? "townhall" : null;
    else if (t.historic === "memorial") {
      const m = t.memorial || "";
      if (["plaque", "stolperstein", "blue_plaque", "bench", "stone"].includes(m)) cat = null;
      else if (m === "war_memorial" || /morts|guerre/i.test(t.name || "")) cat = "memorial";
      else if (m === "statue" || m === "bust") cat = "statue";
      else cat = t.name ? "statue" : null;
    }
    else if (t.historic === "monument") cat = "statue";
    else if (t.place === "square") cat = t.name ? "square" : null;
    else if (t.leisure === "park" || t.leisure === "garden") cat = (t.access === "private" || t.garden === "private") ? null : "park";
    else if (t.leisure === "playground") cat = "playground";
    else if (t.tourism === "viewpoint") cat = "viewpoint";
    else if (t.tourism === "artwork") cat = (t.artwork_type === "statue" || t.artwork_type === "sculpture") ? "statue" : (t.name ? "artwork" : null);
    if (!cat) return null;
    let score = BASE[cat] + (t.name ? 2 : 0) + (t.historic ? 1 : 0) + (t.wikidata || t.wikipedia ? 1 : 0);
    return { id: `${el.type}/${el.id}`, cat, lat, lon, name: t.name || "", score, tags: t };
  }

  // ---- 2. merge duplicates (church as a point and as a building, etc.) ----
  function dedupe(list) {
    const out = [];
    for (const p of list.sort((a, b) => b.score - a.score)) {
      const twin = out.find(q => dist(p, q) < (q.cat === p.cat ? 70 : 25));
      if (!twin) out.push(p);
    }
    return out;
  }

  // ---- 3. choose and order the stops ----
  const LIMIT = { church: 2, park: 2, fountain: 2, statue: 2, square: 1, playground: 1, memorial: 1,
    townhall: 1, gate: 2, tower: 2, castle: 1, ruins: 1, well: 1, artwork: 1, viewpoint: 1 };

  function pathLength(start, stops) {
    let d = 0, cur = start;
    for (const s of stops) { d += dist(cur, s); cur = s; }
    return d * WALK_FACTOR;
  }

  function greedyFrom(start, cands, first, n) {
    const chosen = [first], used = { [first.cat]: 1 };
    let cur = first;
    while (chosen.length < n) {
      let best = null, bestV = -Infinity;
      for (const c of cands) {
        if (chosen.includes(c)) continue;
        if ((used[c.cat] || 0) >= (LIMIT[c.cat] || 1)) continue;
        if (chosen.some(s => dist(s, c) < MIN_GAP)) continue;
        const v = c.score - 0.03 * dist(cur, c) - 2.5 * (used[c.cat] || 0);
        if (v > bestV) { bestV = v; best = c; }
      }
      if (!best) break;
      chosen.push(best); used[best.cat] = (used[best.cat] || 0) + 1; cur = best;
    }
    return chosen;
  }

  function twoOpt(start, stops) {
    let best = stops.slice(), improved = true;
    while (improved) {
      improved = false;
      for (let i = 0; i < best.length - 1; i++) {
        for (let k = i + 1; k < best.length; k++) {
          const cand = best.slice(0, i).concat(best.slice(i, k + 1).reverse(), best.slice(k + 1));
          if (pathLength(start, cand) + 1e-6 < pathLength(start, best)) { best = cand; improved = true; }
        }
      }
    }
    return best;
  }

  function choose(start, places, want = 6) {
    const cands = places.filter(p => dist(start, p) <= SEARCH_RADIUS + 50);
    let best = null, bestV = -Infinity;
    const firsts = cands.slice().sort((a, b) => (b.score - 0.02 * dist(start, b)) - (a.score - 0.02 * dist(start, a))).slice(0, 10);
    for (const f of firsts) {
      for (const n of [want, want - 1, want - 2]) {
        if (n < 4) continue;
        let stops = twoOpt(start, greedyFrom(start, cands, f, n));
        while (stops.length > 4 && pathLength(start, stops) > MAX_WALK) {
          // drop the stop whose removal saves the most walking
          let drop = 0, save = -1;
          stops.forEach((_, i) => { const s = pathLength(start, stops) - pathLength(start, stops.filter((__, j) => j !== i)); if (s > save) { save = s; drop = i; } });
          stops = twoOpt(start, stops.filter((_, j) => j !== drop));
        }
        if (stops.length < 4 || pathLength(start, stops) > MAX_WALK) continue;
        const last = stops[stops.length - 1];
        const endBonus = ["park", "square", "playground", "gate", "castle"].includes(last.cat) ? 3 : 0;
        const v = stops.reduce((s, p) => s + p.score, 0) + stops.length * 4 - 0.006 * pathLength(start, stops) + endBonus;
        if (v > bestV) { bestV = v; best = stops; }
      }
    }
    return best;
  }

  // ---- 4. words and texts ----
  const WORDS = {
    6: { word: "FIDELE", say: "FIDÈLE", hint: "[[un vrai chevalier|une vraie chevalière]] l'est toujours envers ses amis", meaning: "[[Un chevalier|Une chevalière]] est fidèle à ses amis et à sa parole." },
    5: { word: "BRAVE", say: "BRAVE", hint: "[[un chevalier|une chevalière]] n'a pas peur : [[il|elle]] est…", meaning: "[[Un chevalier|Une chevalière]] est brave : [[il|elle]] avance même quand c'est difficile." },
    4: { word: "EPEE", say: "ÉPÉE", hint: "c'est l'arme [[du chevalier|de la chevalière]]", meaning: "L'épée [[du chevalier|de la chevalière]] protège les plus faibles." }
  };

  function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
  function scramble(word, rand) {
    const idx = [...word].map((_, i) => i);
    for (let tries = 0; tries < 20; tries++) {
      for (let i = idx.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [idx[i], idx[j]] = [idx[j], idx[i]]; }
      const s = idx.map(i => word[i]).join("");
      if (s !== word) return s;
    }
    return word.split("").reverse().join("");
  }

  const T = {
    church: [{
      teaser: "Une tour où dorment des cloches.",
      generic: "l'église",
      clue: "Levez les yeux : cherchez un clocher qui dépasse des toits. La prochaine lettre s'y cache.",
      story: "Bravo, {N}. Te voici devant {P}. Au Moyen Âge, les chevaliers venaient prier avant de partir en voyage. Les cloches annonçaient les fêtes, les dangers et l'heure de la journée.",
      defi: "Restez à l'extérieur. En silence, comme des chevaliers en mission, comptez les fenêtres de la façade. Chacun murmure son nombre à l'oreille du Grand Maître.",
      defiIn: "Chaque chevalier fait sonner une cloche imaginaire : « Dong ! » Le Grand Maître choisit la cloche la plus grave et la plus rigolote.",
      q: "Comment s'appelle la tour d'une église où se trouvent les cloches ?", choices: ["Le clocher", "Le donjon", "La cheminée"], answer: 0,
      fact: "Le clocher abrite les cloches qui sonnent les heures et les fêtes.",
      hints: ["Elle « cloche »… elle sonne !", "Le mot ressemble à « cloche ».", "Le clocher."],
      adult: "Restez à l'extérieur. Si une cérémonie a lieu, parlez bas et faites le défi plus loin."
    }, {
      teaser: "Un lieu de pierre où l'on chuchote.",
      generic: "la chapelle",
      clue: "Cherchez un bâtiment surmonté d'une croix. Les chevaliers y venaient avant chaque grande aventure.",
      story: "Te voici devant {P}, {N}. Avant d'être nommé chevalier, un jeune écuyer passait toute une nuit à veiller dans une église ou une chapelle, sans dormir. On appelait cela la veillée d'armes.",
      defi: "La veillée d'armes : tout le monde ferme les yeux et reste parfaitement silencieux pendant quinze secondes, comme un écuyer qui veille.",
      defiIn: "La veillée d'armes : tout le monde ferme les yeux et reste parfaitement silencieux pendant quinze secondes, comme un écuyer qui veille.",
      timer: 15,
      q: "Comment s'appelait le jeune garçon qui aidait un chevalier avant d'en devenir un ?", choices: ["Un écuyer", "Un pompier", "Un pirate"], answer: 0,
      fact: "L'écuyer portait le bouclier du chevalier et s'occupait de son cheval.",
      hints: ["Il portait l'écu, c'est-à-dire le bouclier.", "Écu… écu…", "Un écuyer."],
      adult: "Restez à l'extérieur, à voix basse."
    }],
    gate: [{
      teaser: "Une porte qui gardait la ville.",
      generic: "la porte de la ville",
      clue: "Au Moyen Âge, les villes avaient des portes dans leurs murailles. Cherchez une tour sous laquelle on peut passer.",
      story: "Voici {P}. Ces portes étaient les gardiennes de la ville. Le soir, on les fermait, et des gardes surveillaient qui voulait entrer. Le Templier, lui, connaissait le mot de passe…",
      defi: "Devenez les gardes de la porte : tout le monde se tient droit comme une lance, sans bouger ni rire, pendant vingt secondes.",
      defiIn: "Devenez les gardes du château : tout le monde se tient droit comme une lance, sans bouger ni rire, pendant vingt secondes.",
      timer: 20,
      q: "À quoi servaient les portes d'une ville fortifiée ?", choices: ["À protéger la ville et surveiller qui entrait", "À faire joli pour les touristes", "À ranger les chevaux"], answer: 0,
      fact: "Le soir, on fermait les portes pour protéger les habitants.",
      hints: ["Pensez aux murailles autour de la ville.", "Les gardes n'étaient pas là pour décorer.", "Elles servaient à protéger."],
      adult: "Restez sur le trottoir : des voitures peuvent passer sous la porte."
    }, {
      teaser: "Une deuxième porte, gardée depuis des siècles.",
      generic: "la vieille porte",
      clue: "Une autre porte de l'ancienne muraille vous attend. Cherchez des pierres très anciennes au-dessus de la rue.",
      story: "Encore une porte, {N} ! {P} faisait partie des remparts. Les habitants payaient parfois une petite taxe pour faire entrer leurs marchandises en ville : on l'appelait l'octroi.",
      defi: "Le péage des chevaliers : pour passer, chaque chevalier doit donner au Grand Maître un mot qui commence par la première lettre de son prénom.",
      defiIn: "Le péage des chevaliers : pour passer, chaque chevalier doit donner au Grand Maître un mot qui commence par la première lettre de son prénom.",
      q: "Comment appelle-t-on le grand mur qui entourait une ville au Moyen Âge ?", choices: ["Les remparts", "La haie", "Le grillage"], answer: 0,
      fact: "Les remparts protégeaient la ville des attaques.",
      hints: ["On pouvait marcher dessus pour surveiller.", "Ça commence par « rem… ».", "Les remparts."],
      adult: "Restez sur le trottoir : des voitures peuvent passer sous la porte."
    }],
    tower: [{
      teaser: "Une tour d'où l'on voyait arriver les ennemis.",
      generic: "la tour",
      clue: "Cherchez une tour en pierre plus haute que les maisons autour. C'est un poste de guet parfait.",
      story: "Voici {P}, {N}. Du haut des tours, les guetteurs surveillaient l'horizon. S'ils voyaient arriver des ennemis, ils donnaient l'alerte.",
      defi: "Les guetteurs : chacun cherche autour de lui quelque chose de rouge, quelque chose de vert et un toit pointu. Le premier qui a trouvé les trois crie « Alerte ! ».",
      defiIn: "Les guetteurs : chacun cherche dans la pièce quelque chose de rouge, quelque chose de vert et un objet pointu. Le premier qui a trouvé les trois crie « Alerte ! ».",
      q: "Comment s'appelait le soldat qui surveillait l'horizon du haut d'une tour ?", choices: ["Le guetteur", "Le cuisinier", "Le jardinier"], answer: 0,
      fact: "Le guetteur faisait le guet, jour et nuit.",
      hints: ["Il faisait le « guet ».", "Ça commence par « guet… ».", "Le guetteur."],
      adult: "Restez sur le trottoir, groupe rassemblé."
    }],
    castle: [{
      teaser: "Une demeure de seigneur, solide comme un roc.",
      generic: "le château",
      clue: "Cherchez la demeure la plus fortifiée du coin : de gros murs, peut-être une tour. Un seigneur y vivait.",
      story: "Te voici devant {P}. Les seigneurs vivaient derrière d'épais murs de pierre. Les chevaliers les servaient et défendaient le château.",
      defi: "Le siège du château : la moitié de l'équipe forme un mur en se tenant par les bras, l'autre moitié doit trouver le mot magique pour passer. Le Grand Maître décide quand le mur s'ouvre.",
      defiIn: "Le siège du château : construisez en deux minutes une forteresse de coussins assez grande pour cacher toute l'équipe.",
      q: "Comment s'appelle la plus grande tour d'un château fort ?", choices: ["Le donjon", "Le grenier", "Le garage"], answer: 0,
      fact: "Le donjon était la tour la plus haute et la plus solide.",
      hints: ["C'était le dernier refuge en cas d'attaque.", "Ça commence par « don… ».", "Le donjon."],
      adult: "Restez à l'extérieur si le lieu est privé ou fermé."
    }],
    ruins: [{
      teaser: "Des pierres qui racontent une histoire très ancienne.",
      generic: "les ruines",
      clue: "Cherchez de vieilles pierres, des murs à moitié écroulés. Le temps a laissé un indice.",
      story: "Voici {P}. Ces pierres sont restées debout pendant des siècles. Les archéologues étudient ce genre de lieu pour comprendre comment on vivait autrefois.",
      defi: "Les archéologues : chacun cherche du regard, sans rien déplacer, la pierre la plus ancienne et la plus abîmée. Le Grand Maître choisit la gagnante.",
      defiIn: "Les archéologues : le Grand Maître cache une petite pièce dans la pièce, les chevaliers ont une minute pour la retrouver.",
      q: "Comment s'appelle le métier de ceux qui étudient les vestiges du passé ?", choices: ["Archéologue", "Astronaute", "Boulanger"], answer: 0,
      fact: "Les archéologues fouillent la terre avec beaucoup de patience.",
      hints: ["Ils fouillent la terre avec des pinceaux.", "Ça commence par « archéo… ».", "Archéologue."],
      adult: "Ne grimpez pas sur les ruines."
    }],
    well: [{
      teaser: "Un trou très profond qui cache un trésor liquide.",
      generic: "le puits",
      clue: "Avant l'eau du robinet, chaque quartier avait son point d'eau. Cherchez un puits en pierre.",
      story: "Bravo, {N}. Voici {P}. Avant l'eau du robinet, les habitants venaient y remplir leurs seaux, chaque jour, même en hiver.",
      defi: "Relais du puits : chaque chevalier mime à son tour de remonter un seau très lourd, puis le passe au suivant sans en renverser une goutte.",
      defiIn: "Relais du puits : faites passer un gobelet en plastique rempli d'eau de chevalier en chevalier, au-dessus d'une serviette, sans en renverser une goutte.",
      q: "À quoi servait un puits ?", choices: ["À puiser de l'eau sous la terre", "À cacher des trésors", "À faire peur aux voleurs"], answer: 0,
      fact: "L'eau était remontée avec un seau et une corde.",
      hints: ["On y descend un seau avec une corde.", "Ce qu'on boit tous les jours.", "À puiser de l'eau."],
      adult: "Personne ne monte sur le puits."
    }],
    fountain: [{
      teaser: "Un lieu où l'eau chante.",
      generic: "la fontaine",
      clue: "Tendez l'oreille : cherchez un endroit où l'eau coule ou jaillit.",
      story: "Te voici près de {P}, {N}. Avant l'eau du robinet, les fontaines servaient à tout le village : on y remplissait les cruches et on y faisait boire les chevaux.",
      defi: "Les porteurs d'eau : chaque chevalier mime de porter une cruche pleine sur sa tête, en marchant trois pas sans la faire tomber.",
      defiIn: "Les porteurs d'eau : chaque chevalier marche dix pas avec un livre posé sur la tête, sans le faire tomber.",
      q: "À quoi servaient les fontaines avant l'eau du robinet ?", choices: ["À remplir les cruches et faire boire les animaux", "À prendre son bain", "À rien du tout"], answer: 0,
      fact: "La fontaine était le point de rencontre du village.",
      hints: ["Les chevaux avaient soif aussi.", "On y venait avec des cruches.", "À remplir les cruches et abreuver les animaux."],
      adult: "On ne grimpe pas sur la fontaine."
    }, {
      teaser: "Une autre source d'eau, plus discrète.",
      generic: "la fontaine",
      clue: "Encore de l'eau ! Cherchez une deuxième fontaine, plus discrète que la première.",
      story: "Une deuxième fontaine, {N} ! Au Moyen Âge, on disait que certaines sources avaient des pouvoirs. Celle-ci garde une lettre du Templier.",
      defi: "Le vœu du chevalier : chacun fait un vœu en silence pour l'anniversaire de {N}, puis le Grand Maître compte jusqu'à trois et tout le monde crie « Joyeux anniversaire ! ».",
      defiIn: "Le vœu du chevalier : chacun fait un vœu en silence pour l'anniversaire de {N}, puis tout le monde crie « Joyeux anniversaire ! ».",
      q: "Que faut-il pour qu'une fontaine coule ?", choices: ["De l'eau qui arrive d'une source ou d'un tuyau", "Du vent", "Du soleil"], answer: 0,
      fact: "L'eau des fontaines vient souvent d'une source dans les collines.",
      hints: ["Ce n'est pas la météo.", "Elle arrive par un tuyau ou une source.", "De l'eau qui arrive d'une source."],
      adult: "On ne grimpe pas sur la fontaine."
    }],
    townhall: [{
      teaser: "La maison où l'on décide pour toute la ville.",
      generic: "la mairie",
      clue: "Cherchez le bâtiment avec un drapeau bleu, blanc, rouge. C'est là qu'on prend les décisions pour la ville.",
      story: "Voici {P}, {N}. C'est ici que se réunit le conseil de la ville pour prendre les décisions. Au Moyen Âge, certaines villes avaient déjà leur propre conseil.",
      defi: "Le conseil des chevaliers : formez un cercle, et chacun propose une loi rigolote pour la ville. L'équipe vote à main levée pour la meilleure.",
      defiIn: "Le conseil des chevaliers : formez un cercle, et chacun propose une loi rigolote pour la maison. L'équipe vote à main levée pour la meilleure.",
      q: "Qui dirige la mairie ?", choices: ["Le maire", "Le roi", "Le boulanger"], answer: 0,
      fact: "Le maire est élu par les habitants.",
      hints: ["On l'élit tous les six ans.", "Mairie… m…", "Le maire."],
      adult: "Restez sur le trottoir ou sur la place."
    }],
    memorial: [{
      teaser: "Un lieu où l'on se souvient.",
      generic: "le monument aux morts",
      clue: "Cherchez un monument de pierre avec beaucoup de noms gravés. C'est un lieu calme et important.",
      story: "Ici, {N}, on se souvient des habitants morts pendant les guerres. Les chevaliers respectaient toujours les lieux de mémoire.",
      defi: "Un chevalier sait être sérieux : toute l'équipe garde le silence pendant dix secondes, la main sur le cœur.",
      defiIn: "Un chevalier sait être sérieux : toute l'équipe garde le silence pendant dix secondes, la main sur le cœur.",
      timer: 10,
      q: "À quoi sert un monument aux morts ?", choices: ["À se souvenir des personnes mortes pendant les guerres", "À indiquer la route", "À jouer à cache-cache"], answer: 0,
      fact: "Chaque année, on y organise des cérémonies du souvenir.",
      hints: ["Il y a des noms gravés dessus.", "On y vient pour se souvenir.", "À se souvenir."],
      adult: "Lieu de mémoire : on ne grimpe pas, on parle doucement."
    }],
    statue: [{
      teaser: "Quelqu'un qui ne bouge jamais.",
      generic: "la statue",
      clue: "Cherchez quelqu'un qui reste parfaitement immobile, jour et nuit, beau temps mauvais temps.",
      story: "Voici {P}, {N}. Les statues sont faites pour qu'on n'oublie pas une personne ou une histoire. Le Templier aimait les gardiens immobiles.",
      defi: "Les statues de chevaliers : tout le monde se fige dans la pose la plus héroïque possible pendant quinze secondes. Celui qui bouge rit en premier !",
      defiIn: "Les statues de chevaliers : tout le monde se fige dans la pose la plus héroïque possible pendant quinze secondes.",
      timer: 15,
      q: "Comment appelle-t-on la personne qui fabrique des statues ?", choices: ["Un sculpteur", "Un boulanger", "Un plombier"], answer: 0,
      fact: "Le sculpteur taille la pierre ou fond le métal.",
      hints: ["Il sculpte.", "Ça commence par « sculp… ».", "Un sculpteur."],
      adult: "On ne grimpe pas sur le monument."
    }, {
      teaser: "Un deuxième gardien de pierre ou de métal.",
      generic: "le monument",
      clue: "Cherchez un autre monument, un autre gardien immobile qui veille sur la ville.",
      story: "Encore un gardien, {N} ! {P} veille ici depuis longtemps. Les chevaliers saluaient toujours ceux qui montent la garde.",
      defi: "Le salut des chevaliers : tout le monde salue le monument en posant le poing sur le cœur, puis fait une révérence.",
      defiIn: "Le salut des chevaliers : tout le monde salue le Grand Maître en posant le poing sur le cœur, puis fait une révérence.",
      q: "Quel geste faisait un chevalier devant un roi ?", choices: ["Il mettait un genou à terre", "Il tirait la langue", "Il sautait à cloche-pied"], answer: 0,
      fact: "Mettre un genou à terre montrait le respect.",
      hints: ["C'est un geste de respect.", "Le genou touche le sol.", "Un genou à terre."],
      adult: "On ne grimpe pas sur le monument."
    }],
    artwork: [{
      teaser: "Une œuvre qu'un artiste a laissée pour tout le monde.",
      generic: "l'œuvre d'art",
      clue: "Cherchez une œuvre d'art en plein air. Un artiste l'a placée là pour qu'on la regarde.",
      story: "Voici {P}, {N}. Au Moyen Âge, les artistes décoraient les églises et les châteaux. Aujourd'hui, ils décorent aussi les rues.",
      defi: "L'atelier des artistes : chacun invente le titre le plus rigolo possible pour cette œuvre. Le Grand Maître choisit le meilleur.",
      defiIn: "L'atelier des artistes : chacun dessine en une minute le blason de l'équipe sur une feuille.",
      q: "Comment appelle-t-on le dessin sur le bouclier d'un chevalier ?", choices: ["Un blason", "Une affiche", "Un tag"], answer: 0,
      fact: "Le blason permettait de reconnaître un chevalier sous son armure.",
      hints: ["On le voyait de loin, sur le bouclier.", "Ça commence par « bla… ».", "Un blason."],
      adult: "On regarde sans toucher."
    }],
    square: [{
      teaser: "Un grand espace où se tenaient les fêtes.",
      generic: "la place",
      clue: "Cherchez une grande place, là où les gens se retrouvent les jours de marché et de fête.",
      story: "Te voici sur {P}, {N}. Au Moyen Âge, les places accueillaient les marchés, les fêtes et les annonces importantes, criées à voix haute.",
      defi: "Le crieur public : chaque chevalier annonce à voix haute, comme un crieur d'autrefois : « Oyez, oyez ! Aujourd'hui, c'est l'anniversaire de {N} ! »",
      defiIn: "Le crieur public : chaque chevalier annonce à voix haute : « Oyez, oyez ! Aujourd'hui, c'est l'anniversaire de {N} ! »",
      q: "Que trouvait-on souvent sur la place d'un village au Moyen Âge ?", choices: ["Le marché", "Une piscine", "Un aéroport"], answer: 0,
      fact: "Le marché réunissait paysans, artisans et marchands.",
      hints: ["On y achetait à manger.", "Il a souvent lieu une fois par semaine.", "Le marché."],
      adult: "Gardez le groupe sur la place, loin des voitures."
    }],
    park: [{
      teaser: "Un coin de verdure pour s'entraîner.",
      generic: "le parc",
      clue: "Les chevaliers s'entraînaient en plein air. Cherchez de l'herbe et des arbres.",
      story: "Bravo, {N}. Te voici dans {P}. Les futurs chevaliers s'entraînaient chaque jour en plein air : course, équilibre et maniement de l'épée en bois.",
      defi: "L'entraînement : course au galop sur place pendant dix secondes, puis chacun tient en équilibre sur un pied en comptant jusqu'à dix.",
      defiIn: "L'entraînement : course au galop sur place pendant dix secondes, puis chacun tient en équilibre sur un pied en comptant jusqu'à dix.",
      q: "Au Moyen Âge, quel animal portait les chevaliers ?", choices: ["Le cheval", "La vache", "Le chien"], answer: 0,
      fact: "Le cheval d'un chevalier s'appelait souvent un destrier.",
      hints: ["Le mot « chevalier » vient de lui.", "Cheval… ier.", "Le cheval."],
      adult: "Restez dans le parc, tous les enfants à vue."
    }, {
      teaser: "Un jardin où se cache une lettre.",
      generic: "le jardin",
      clue: "Cherchez un autre coin de verdure, avec des arbres ou des fleurs.",
      story: "Un nouveau coin de verdure, {N}. Dans les châteaux, on cultivait des jardins de plantes médicinales pour soigner les blessés.",
      defi: "La cueillette : chaque chevalier trouve, sans rien arracher, trois feuilles différentes tombées au sol et les montre au Grand Maître.",
      defiIn: "La cueillette : chaque chevalier trouve dans la maison trois objets de couleurs différentes et les montre au Grand Maître.",
      q: "À quoi servaient certaines plantes dans les jardins du Moyen Âge ?", choices: ["À soigner les malades", "À fabriquer des téléphones", "À faire du plastique"], answer: 0,
      fact: "On les appelait les simples, les plantes qui soignent.",
      hints: ["Il n'y avait pas de pharmacie comme aujourd'hui.", "Pour les blessés…", "À soigner."],
      adult: "Restez dans le jardin, tous les enfants à vue."
    }],
    playground: [{
      teaser: "Un terrain d'entraînement pour jeunes écuyers.",
      generic: "l'aire de jeux",
      clue: "Cherchez un terrain d'entraînement idéal pour de jeunes écuyers : des toboggans, des balançoires…",
      story: "Te voici sur le terrain d'entraînement, {N} ! Les jeunes écuyers apprenaient l'agilité avant de monter à cheval.",
      defi: "Le parcours de l'écuyer : chacun traverse l'aire de jeux à sa façon, sans pousser personne, puis revient saluer le Grand Maître.",
      defiIn: "Le parcours de l'écuyer : passer sous une table, sauter par-dessus un coussin, et revenir saluer le Grand Maître.",
      q: "Comment s'appelle le combat à cheval avec des lances ?", choices: ["La joute", "Le foot", "La pêche"], answer: 0,
      fact: "Pendant les tournois, les chevaliers s'affrontaient lors de joutes.",
      hints: ["Ça se passait pendant les tournois.", "Ça rime avec « route ».", "La joute."],
      adult: "Laissez la place aux autres enfants qui jouent."
    }],
    viewpoint: [{
      teaser: "Un endroit d'où l'on voit loin.",
      generic: "le point de vue",
      clue: "Cherchez un endroit d'où l'on voit loin, au-dessus des toits.",
      story: "Regarde au loin, {N}. Les seigneurs construisaient leurs châteaux en hauteur pour voir arriver les visiteurs… et les ennemis.",
      defi: "Les guetteurs : chacun trouve au loin quelque chose de rouge, quelque chose de vert et un toit pointu.",
      defiIn: "Les guetteurs : chacun regarde par la fenêtre et trouve quelque chose de rouge, de vert et un toit pointu.",
      q: "Pourquoi construisait-on les châteaux en hauteur ?", choices: ["Pour voir arriver les ennemis", "Pour avoir moins froid", "Pour être près des nuages"], answer: 0,
      fact: "En hauteur, on voit loin et on se défend mieux.",
      hints: ["Pensez aux guetteurs.", "Pour surveiller.", "Pour voir arriver les ennemis."],
      adult: "Restez derrière les barrières."
    }]
  };


  // What the voice says instead of the place name (the exact name stays on the adult's screen).
  const HERE = { church: ["cette église", "ce lieu de prière"], gate: ["cette porte", "cette vieille porte"], tower: ["cette tour"],
    castle: ["ce château"], ruins: ["ces ruines"], well: ["ce puits"], fountain: ["cette fontaine", "cette fontaine"],
    townhall: ["cette mairie"], memorial: ["ce monument"], statue: ["cette statue", "ce monument"], artwork: ["cette œuvre"],
    square: ["cette place"], park: ["ce parc", "ce jardin"], playground: ["cette aire de jeux"], viewpoint: ["ce point de vue"] };

  // "Église Saint-Martin" -> "l'église Saint-Martin"; "Saint-Martin" (church) -> "l'église Saint-Martin"
  const NOUNS = [["hôtel de ville", "l'"], ["aire de jeux", "l'"], ["monument", "le "], ["église", "l'"], ["chapelle", "la "],
    ["cathédrale", "la "], ["basilique", "la "], ["temple", "le "], ["parc", "le "], ["jardin", "le "], ["square", "le "],
    ["place", "la "], ["fontaine", "la "], ["puits", "le "], ["porte", "la "], ["tour", "la "], ["château", "le "],
    ["fort", "le "], ["manoir", "le "], ["statue", "la "], ["mairie", "la "], ["maison", "la "], ["ruines", "les "],
    ["belvédère", "le "], ["calvaire", "le "], ["lavoir", "le "], ["stèle", "la "], ["buste", "le "]];
  function articleize(name, generic) {
    if (!name) return generic;
    const low = name.toLowerCase();
    for (const [noun, art] of NOUNS) {
      if (low.startsWith(noun + " ") || low === noun) return art + name.charAt(0).toLowerCase() + name.slice(1);
    }
    if (/^(le|la|les|l')\s?/i.test(name)) return name.charAt(0).toLowerCase() + name.slice(1);
    return `${generic} « ${name} »`.replace(/^(l'église|la chapelle) « (Saint[^»]*) »$/, "$1 $2");
  }

  // ---- 5. build the quest ----
  // The places chosen for a quest, in walking order. This is what a paid quest stores.
  function select(elements, start) {
    return selectPlaces(elements.map(classify).filter(Boolean), start);
  }
  // Same, from places already classified (the server's tiles: {id, cat, lat, lon, name, score}).
  function selectPlaces(classified, start) {
    const places = dedupe(classified.filter(p => dist(start, p) <= SEARCH_RADIUS + 120));
    const stops = choose(start, places, 6);
    if (!stops) return { ok: false, reason: "few", found: places.length };
    return { ok: true, stops: stops.map(s => ({ cat: s.cat, lat: s.lat, lon: s.lon, name: s.name, id: s.id })) };
  }

  // The quest at home works anywhere: same story, no map.
  const INDOOR = ["church", "gate", "well", "castle", "square", "park"];
  function indoorStops() { return INDOOR.map(cat => ({ cat })); }

  // Full quest (texts, letters, distances) from chosen stops. start is null for the quest at home.
  function assemble(start, stops) {
    const indoor = !start;
    const W = WORDS[stops.length];
    const scrambled = indoor ? "ELFIED" : scramble(W.word, rng(Math.round(start.lat * 1e5) ^ Math.round(start.lon * 1e5)));
    const seen = {};
    let prev = start;
    const steps = stops.map((s, i) => {
      const n = seen[s.cat] || 0; seen[s.cat] = n + 1;
      const v = indoor ? 0 : Math.min(n, T[s.cat].length - 1);
      const tpl = T[s.cat][v];
      const step = Object.assign({}, tpl, {
        cat: s.cat, v, letter: scrambled[i], name: s.name || "",
        lat: indoor ? null : s.lat, lon: indoor ? null : s.lon,
        P: indoor ? tpl.generic : articleize(s.name, tpl.generic),
        legM: indoor ? 0 : Math.round(dist(prev, s) * WALK_FACTOR / 10) * 10,
        dir: indoor ? "" : bearing(prev, s), osm: s.id || null
      });
      if (!indoor) prev = s;
      return step;
    });
    const q = { ok: true, start: start || null, steps, word: W.word, say: W.say, hint: W.hint, meaning: W.meaning, scrambled,
      walkM: indoor ? 0 : Math.round(pathLength(start, stops) / 10) * 10,
      minutes: indoor ? 60 : 10 + steps.length * 9 };
    if (indoor) q.indoorOnly = true;
    else q.centroid = { lat: stops.reduce((a, s) => a + s.lat, 0) / stops.length, lon: stops.reduce((a, s) => a + s.lon, 0) / stops.length };
    return q;
  }

  function build(elements, start) {
    const s = select(elements, start);
    return s.ok ? assemble(start, s.stops) : s;
  }

  // What anyone sees before paying: no place, no position, no answer.
  function preview(q) {
    return { ok: true, indoorOnly: !!q.indoorOnly, count: q.steps.length, walkM: q.walkM, minutes: q.minutes, teasers: q.steps.map(s => s.teaser) };
  }

  return { overpassQuery, classify, dedupe, choose, select, selectPlaces, assemble, indoorStops, build, preview, dist, bearing, articleize, T, HERE, WORDS, SEARCH_RADIUS, MAX_WALK };
})();
if (typeof module !== "undefined") module.exports = QuestEngine;
/* ENGINE-END */
