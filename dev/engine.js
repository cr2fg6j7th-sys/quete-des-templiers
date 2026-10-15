/* ENGINE-START
   Quest generator: OpenStreetMap places around a start point -> a 4 to 6 step quest.
   Pure functions only (no DOM): runs on the server (Cloudflare), in Node for tests,
   and in the browser for the free demo build. */

const QuestEngine = (() => {
  const G = (typeof QuestGeo !== "undefined") ? QuestGeo : require("./geo.js");
  const { SEARCH_RADIUS, overpassQuery, dist, bearing } = G;
  const MAX_WALK = 1800;         // metres of walking for the whole quest
  const WALK_FACTOR = 1.3;       // straight line -> real walking distance
  const MIN_GAP = 60;            // two stops of the same kind closer than this feel like one place
  const MIN_GAP_OTHER = 35;      // a church and the war memorial in front of it are two stops (villages)
  const tooClose = (a, b) => dist(a, b) < (a.cat === b.cat ? MIN_GAP : MIN_GAP_OTHER);

  // ---- 1. classify OSM elements into kid-friendly categories ----
  // From the most to the least interesting stop for a child (Nathan's ranking, 15/10/2026): churches,
  // remarkable buildings, mills, lavoirs, crosses and calvaries first; the post box last. A name adds 2,
  // a historic tag 1 and a Wikipedia article 1. The village places (mill to post box) let small
  // communes have a quest too.
  const RANK = [
    ["church", 10],                                                     // églises, chapelles
    ["castle", 9.5], ["gate", 9.5], ["tower", 9], ["ruins", 9],         // bâtiments remarquables
    ["mill", 8.5], ["lavoir", 8.5],                                     // moulins, lavoirs
    ["cross", 8],                                                       // calvaires, croix de chemin
    ["fountain", 7.5], ["well", 7.5],                                   // fontaines, puits
    ["house", 7], ["tree", 7],                                          // vieilles maisons, arbres remarquables
    ["watertower", 6.5], ["statue", 6.5],                               // châteaux d'eau, statues
    ["memorial", 6], ["townhall", 6],                                   // monuments aux morts, mairies
    ["fire", 5.5], ["square", 5.5], ["viewpoint", 5.5],                 // casernes de pompiers, places, points de vue
    ["artwork", 5], ["park", 5],                                        // œuvres d'art, parcs
    ["library", 4.5], ["playground", 4],                                // bibliothèques, aires de jeux
    ["school", 3.5], ["sport", 3],                                      // écoles, terrains de sport
    ["postbox", 1.5]];                                                  // boîtes aux lettres
  const BASE = Object.fromEntries(RANK);
  const PITCH = /^(soccer|multi|basketball|rugby|rugby_union|team_handball|volleyball|football)\b/;

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
    else if (t.historic === "wayside_chapel" || (t.building === "chapel" && t.name)) cat = "church";
    else if (t.amenity === "watering_place" || t.historic === "fountain") cat = "fountain";
    else if (t.historic === "wayside_cross" || t.man_made === "cross") cat = "cross";
    else if (t.man_made === "water_tower") cat = "watertower";
    else if (t.amenity === "lavoir") cat = "lavoir";
    else if (t.man_made === "watermill" || t.man_made === "windmill" || t.historic === "mill") cat = "mill";
    else if (t.natural === "tree") cat = (t.name || t.denotation === "natural_monument" || t.denotation === "landmark") ? "tree" : null;
    else if (["building", "house", "farm"].includes(t.historic) || (t.heritage && t.building && t.building !== "no")) cat = t.name ? "house" : null;
    else if (t.amenity === "fire_station") cat = "fire";
    else if (t.amenity === "library") cat = "library";
    else if (t.amenity === "school") cat = t.name ? "school" : null;
    else if (t.leisure === "stadium" || (t.leisure === "pitch" && PITCH.test(t.sport || ""))) cat = "sport";
    else if (t.amenity === "post_box") cat = "postbox";
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
    townhall: 1, gate: 2, tower: 2, castle: 1, ruins: 1, well: 1, artwork: 1, viewpoint: 1, cross: 2 };

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
        if (chosen.some(s => tooClose(s, c))) continue;
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
      story: "Bravo, {N}. Te voici devant {P}. Au Moyen Âge, les chevaliers venaient prier avant de partir en voyage. Les cloches annonçaient les fêtes, les dangers et l'heure de la journée. Certaines sont énormes : le gros bourdon de Notre-Dame de Paris pèse environ treize tonnes, plus lourd que deux éléphants !",
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
      story: "Te voici devant {P}, {N}. Avant d'être nommé chevalier, un jeune écuyer passait toute une nuit à veiller dans une église ou une chapelle, sans dormir. On appelait cela la veillée d'armes. Le lendemain, le nouveau chevalier recevait parfois une bonne tape sur la nuque, la colée, pour ne jamais oublier ce grand jour !",
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
      story: "Voici {P}. Ces portes étaient les gardiennes de la ville. Le soir, on les fermait, et des gardes surveillaient qui voulait entrer. En cas d'attaque, une lourde grille, la herse, tombait d'un coup devant l'entrée, comme une mâchoire géante ! Le Templier, lui, connaissait le mot de passe…",
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
      story: "Encore une porte, {N} ! {P} faisait partie des remparts. Les habitants payaient parfois une petite taxe pour faire entrer leurs marchandises en ville : on l'appelait l'octroi. On payait pour un tonneau de vin, pour un sac de farine… et même pour un cochon !",
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
      story: "Voici {P}, {N}. Du haut des tours, les guetteurs surveillaient l'horizon. S'ils voyaient arriver des ennemis, ils donnaient l'alerte en soufflant de toutes leurs forces dans une grande corne : « Tuuut ! »",
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
      story: "Te voici devant {P}. Les seigneurs vivaient derrière d'épais murs de pierre. Les chevaliers les servaient et défendaient le château. Et les toilettes ? C'était un petit coin accroché au mur, avec un trou qui donnait directement… dans le vide, au-dessus du fossé !",
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
      story: "Voici {P}. Ces pierres sont restées debout pendant des siècles. Les archéologues étudient ce genre de lieu pour comprendre comment on vivait autrefois. En grattant la terre avec de petits pinceaux, ils retrouvent parfois des pièces, des jouets d'enfants… et même des dés pour jouer !",
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
      story: "Bravo, {N}. Voici {P}. Avant l'eau du robinet, les habitants venaient y remplir leurs seaux, chaque jour, même en hiver. Un seau plein d'eau pèse aussi lourd qu'un petit chien : les enfants aidaient souvent à les porter !",
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
      story: "Te voici près de {P}, {N}. Avant l'eau du robinet, les fontaines servaient à tout le village : on y remplissait les cruches et on y faisait boire les chevaux. Un cheval boit une trentaine de litres d'eau par jour : ça en fait, des allers et retours !",
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
      story: "Une deuxième fontaine, {N} ! Au Moyen Âge, on disait que certaines sources avaient des pouvoirs. Aujourd'hui encore, à Rome, les visiteurs jettent des pièces dans une fontaine en faisant un vœu : plus d'un million d'euros chaque année, offerts ensuite aux plus pauvres ! Celle-ci garde une lettre du Templier.",
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
      story: "Voici {P}, {N}. C'est ici que se réunit le conseil de la ville pour prendre les décisions. Au Moyen Âge, certaines villes avaient déjà leur propre conseil. Le soir, une cloche sonnait le couvre-feu : l'heure d'éteindre les feux et d'aller se coucher !",
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
      story: "Ici, {N}, on se souvient des habitants morts pendant les guerres. Les chevaliers respectaient toujours les lieux de mémoire. Le 11 novembre, on y dépose des fleurs, et beaucoup de gens portent un bleuet, la petite fleur bleue du souvenir.",
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
      story: "Voici {P}, {N}. Les statues sont faites pour qu'on n'oublie pas une personne ou une histoire. Le Templier aimait les gardiens immobiles. Le savais-tu ? La statue de la Liberté, à New York, a été imaginée par un sculpteur né à Colmar, en Alsace : Auguste Bartholdi !",
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
      story: "Encore un gardien, {N} ! {P} veille ici depuis longtemps. Les chevaliers saluaient toujours ceux qui montent la garde. Avec le temps et la pluie, le métal des statues change parfois de couleur : la statue de la Liberté était couleur cuivre, et elle est devenue toute verte !",
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
      story: "Voici {P}, {N}. Au Moyen Âge, les artistes décoraient les églises et les châteaux. Aujourd'hui, ils décorent aussi les rues. Pour peindre, les artistes du Moyen Âge mélangeaient leurs couleurs avec… du jaune d'œuf !",
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
      story: "Te voici sur {P}, {N}. Au Moyen Âge, les places accueillaient les marchés, les fêtes et les annonces importantes, criées à voix haute. Les jours de marché, on y croisait des poules, des oies… et même des cochons qui se promenaient en liberté !",
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
      story: "Bravo, {N}. Te voici dans {P}. Les futurs chevaliers s'entraînaient chaque jour en plein air : course, équilibre et maniement de l'épée en bois. À cheval, ils frappaient un mannequin qui tournait sur lui-même : celui qui allait trop lentement recevait un coup de sac de sable dans le dos !",
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
      story: "Un nouveau coin de verdure, {N}. Dans les châteaux, on cultivait des jardins de plantes médicinales pour soigner les blessés. Et contre les puces, on glissait dans les lits des herbes qui sentent fort, comme la lavande !",
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
      story: "Te voici sur le terrain d'entraînement, {N} ! Les jeunes écuyers apprenaient l'agilité avant de monter à cheval. Les enfants du Moyen Âge jouaient déjà à la toupie, aux billes, à saute-mouton et à colin-maillard !",
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
      story: "Regarde au loin, {N}. Les seigneurs construisaient leurs châteaux en hauteur pour voir arriver les visiteurs… et les ennemis. Par beau temps, on voit parfois à des dizaines de kilomètres : un cavalier mettait presque une journée pour aller aussi loin !",
      defi: "Les guetteurs : chacun trouve au loin quelque chose de rouge, quelque chose de vert et un toit pointu.",
      defiIn: "Les guetteurs : chacun regarde par la fenêtre et trouve quelque chose de rouge, de vert et un toit pointu.",
      q: "Pourquoi construisait-on les châteaux en hauteur ?", choices: ["Pour voir arriver les ennemis", "Pour avoir moins froid", "Pour être près des nuages"], answer: 0,
      fact: "En hauteur, on voit loin et on se défend mieux.",
      hints: ["Pensez aux guetteurs.", "Pour surveiller.", "Pour voir arriver les ennemis."],
      adult: "Restez derrière les barrières."
    }],
    // ---- what every village has (added 15/10/2026) ----
    cross: [{
      teaser: "Une croix qui veille au bord du chemin.",
      generic: "la croix",
      clue: "Autrefois, on plantait des croix au bord des chemins pour guider les voyageurs. Cherchez-en une, en pierre ou en bois.",
      story: "Te voici devant {P}, {N}. Les voyageurs et les pèlerins s'arrêtaient devant ces croix pour se reposer et se donner du courage avant de reprendre la route. Les chevaliers du Temple, eux, protégeaient ces voyageurs sur les chemins. Certains pèlerins marchaient des mois jusqu'à Saint-Jacques-de-Compostelle, en Espagne, avec une coquille accrochée à leur chapeau !",
      defi: "Le serment du chevalier : chacun promet à voix haute une bonne action qu'il fera aujourd'hui, la main posée sur le cœur.",
      defiIn: "Le serment du chevalier : chacun promet à voix haute une bonne action qu'il fera aujourd'hui, la main posée sur le cœur.",
      q: "Comment appelait-on les voyageurs qui marchaient très loin pour rejoindre un lieu saint ?", choices: ["Des pèlerins", "Des pirates", "Des astronautes"], answer: 0,
      fact: "Les Templiers ont été créés pour protéger les pèlerins sur les routes.",
      hints: ["Ils faisaient un pèlerinage.", "Ça commence par « pèle… ».", "Des pèlerins."],
      adult: "Lieu de recueillement : on parle doucement et on ne grimpe pas."
    }, {
      teaser: "Un signe dressé là où les chemins se croisent.",
      generic: "le calvaire",
      clue: "Une autre croix vous attend, souvent là où deux chemins se croisent. Ouvrez l'œil aux carrefours.",
      story: "Encore une croix, {N} ! On en dressait souvent aux carrefours : quand on hésitait entre deux chemins, on s'y arrêtait pour réfléchir. Un bon chevalier prend toujours le temps de choisir le bon chemin. Autrefois, il n'y avait ni panneaux ni GPS : ces croix servaient aussi de repères pour ne pas se perdre !",
      defi: "Le carrefour : le Grand Maître montre deux directions. Chaque chevalier choisit la sienne en sautant à pieds joints, puis tout le monde se rassemble en criant : « Pour l'Ordre ! »",
      defiIn: "Le carrefour : le Grand Maître montre deux coins de la pièce. Chaque chevalier choisit le sien en sautant à pieds joints, puis tout le monde se rassemble au centre en criant : « Pour l'Ordre ! »",
      q: "Comment appelle-t-on l'endroit où deux routes se croisent ?", choices: ["Un carrefour", "Un plafond", "Un pont-levis"], answer: 0,
      fact: "Au carrefour, il faut choisir sa route.",
      hints: ["Les routes s'y « croisent ».", "Ça commence par « carre… ».", "Un carrefour."],
      adult: "Restez sur le bas-côté : ces croix sont souvent au bord des routes."
    }],
    watertower: [{
      teaser: "Un château qui ne garde pas de trésor… mais de l'eau.",
      generic: "le château d'eau",
      clue: "Cherchez un château très étrange : une grande tour ronde, souvent en hauteur, sans fenêtre ni chevalier.",
      story: "Voici {P}, {N} ! Ce château-là ne protège pas un seigneur : il garde l'eau de tout le village, tout là-haut. Grâce à lui, l'eau descend toute seule jusqu'aux robinets des maisons. Il contient autant d'eau que des milliers de baignoires !",
      defi: "La chaîne de l'eau : tout le monde se met en file et fait passer de main en main un seau imaginaire très lourd, sans en renverser une goutte. Le dernier crie « Plouf ! ».",
      defiIn: "La chaîne de l'eau : en file, faites passer de main en main un gobelet en plastique rempli d'eau, au-dessus d'une serviette, sans en renverser une goutte.",
      q: "Pourquoi garde-t-on l'eau tout en haut d'un château d'eau ?", choices: ["Pour qu'elle descende toute seule jusqu'aux robinets", "Pour que les oiseaux puissent boire", "Pour qu'elle soit plus près du soleil"], answer: 0,
      fact: "L'eau descend toute seule : c'est la pesanteur qui la pousse.",
      hints: ["L'eau aime descendre.", "Pense aux robinets des maisons.", "Pour qu'elle descende toute seule jusqu'aux robinets."],
      adult: "On reste en dehors des clôtures."
    }],
    lavoir: [{
      teaser: "Un bassin où l'on faisait la grande lessive.",
      generic: "le lavoir",
      clue: "Avant les machines à laver, on lavait le linge dans un bassin couvert, rempli d'eau. Cherchez ce bassin.",
      story: "Te voici devant {P}, {N}. Autrefois, les lavandières venaient ici laver le linge à la main. Elles le frottaient, le tapaient avec un battoir et le rinçaient dans l'eau froide, en se racontant les nouvelles du village. Et pour que le linge soit bien blanc, on le faisait tremper… dans de l'eau mélangée à de la cendre de bois !",
      defi: "Les lavandières : par deux, tenez un drap imaginaire. Frottez, tapez, essorez, puis secouez-le très fort en comptant jusqu'à trois.",
      defiIn: "Les lavandières : par deux, prenez une serviette. Faites semblant de la frotter, de la taper, de l'essorer, puis pliez-la le plus vite possible.",
      q: "Avant les machines à laver, où lavait-on le linge ?", choices: ["Au lavoir", "Au four à pain", "Au grenier"], answer: 0,
      fact: "Faire la lessive pouvait prendre toute une journée.",
      hints: ["Le mot ressemble à « laver ».", "C'est un bassin rempli d'eau.", "Au lavoir."],
      adult: "On ne marche pas sur le bord du bassin."
    }],
    mill: [{
      teaser: "Une grande roue qui travaillait jour et nuit.",
      generic: "le moulin",
      clue: "Cherchez un vieux bâtiment près de l'eau, ou une grande roue : c'est là qu'on fabriquait la farine du pain.",
      story: "Voici {P}, {N}. Ici, la force de l'eau ou du vent faisait tourner une grande roue, qui faisait tourner deux énormes pierres. Entre elles, le blé était écrasé pour devenir de la farine. Le soir, le meunier était tout blanc de farine, des cheveux jusqu'aux sourcils, comme un fantôme !",
      defi: "La roue du moulin : tout le monde se tient par la main en cercle et tourne lentement, puis de plus en plus vite. Au signal « Stop ! », tout le monde s'arrête net, sans tomber.",
      defiIn: "La roue du moulin : tout le monde se tient par la main en cercle et tourne lentement, puis de plus en plus vite. Au signal « Stop ! », tout le monde s'arrête net, sans tomber.",
      q: "Que fabriquait-on dans un moulin ?", choices: ["De la farine", "Des chaussures", "Du chocolat"], answer: 0,
      fact: "Le meunier transformait le blé en farine, et le boulanger la farine en pain.",
      hints: ["On en a besoin pour faire du pain.", "C'est une poudre blanche.", "De la farine."],
      adult: "Moulin souvent privé : on regarde depuis la rue, loin de l'eau."
    }],
    tree: [{
      teaser: "Un géant très vieux, qui ne bouge jamais.",
      generic: "le vieil arbre",
      clue: "Cherchez un arbre pas comme les autres : très vieux, très grand, ou planté là pour qu'on s'en souvienne.",
      story: "Te voici devant {P}, {N}. Certains arbres vivent plusieurs centaines d'années. Celui-ci a peut-être vu passer des cavaliers, des marchés et des fêtes. Autrefois, on se réunissait parfois à l'ombre d'un grand arbre pour rendre la justice. En France, certains arbres ont plus de mille ans : ils étaient déjà là au temps des chevaliers !",
      defi: "La ronde de l'arbre : en vous tenant la main, combien de chevaliers faut-il pour faire le tour du tronc ? Si vous ne pouvez pas l'approcher, devinez-le !",
      defiIn: "La forêt des chevaliers : chacun se transforme en arbre, les bras en branches, et tient en équilibre sur un pied pendant que le Grand Maître souffle comme le vent.",
      q: "Comment connaître l'âge d'un arbre coupé ?", choices: ["En comptant les cercles de son tronc", "En comptant ses feuilles", "En mesurant son ombre"], answer: 0,
      fact: "Chaque année, le tronc grandit d'un nouveau cercle.",
      hints: ["Regarde l'intérieur d'un tronc coupé.", "Un cercle par année.", "En comptant les cercles de son tronc."],
      adult: "On ne grimpe pas et on n'arrache rien."
    }],
    house: [{
      teaser: "Une maison qui a traversé les siècles.",
      generic: "la vieille maison",
      clue: "Cherchez une maison très ancienne, peut-être avec des poutres de bois dessinées sur sa façade.",
      story: "Voici {P}, {N}. Elle a traversé les siècles ! Autrefois, on construisait avec ce que l'on trouvait autour de soi : du bois pour les poutres, de la terre et de la paille pour boucher les trous entre elles. Dans certaines fermes, les animaux vivaient juste en dessous de la chambre : leur chaleur montait et réchauffait la famille… avec l'odeur en prime !",
      defi: "Les bâtisseurs : construisez une maison avec vos corps ! Deux chevaliers font le toit en joignant leurs mains au-dessus de leur tête, les autres font les murs. Tenez dix secondes sans que la maison s'écroule.",
      defiIn: "Les bâtisseurs : construisez une maison avec vos corps ! Deux chevaliers font le toit en joignant leurs mains au-dessus de leur tête, les autres font les murs. Tenez dix secondes sans que la maison s'écroule.",
      timer: 10,
      q: "Comment appelle-t-on les maisons aux poutres de bois apparentes ?", choices: ["Les maisons à colombages", "Les maisons en chocolat", "Les igloos"], answer: 0,
      fact: "Il y a beaucoup de maisons à colombages en Alsace et en Normandie.",
      hints: ["Le mot fait penser à un oiseau blanc, la colombe.", "Colom…", "Les maisons à colombages."],
      adult: "Maison habitée : on reste sur le trottoir, sans bruit."
    }],
    fire: [{
      teaser: "La maison des chevaliers d'aujourd'hui.",
      generic: "la caserne des pompiers",
      clue: "Cherchez la maison des héros d'aujourd'hui : un bâtiment avec de grandes portes, d'où partent des camions rouges.",
      story: "Voici {P}, {N}. Ici veillent les pompiers, les chevaliers d'aujourd'hui. Comme les chevaliers d'autrefois, ils sont courageux et prêts à partir à tout moment pour aider les autres. Autrefois, quand un feu éclatait, tout le village faisait la chaîne pour se passer des seaux d'eau, de main en main !",
      defi: "L'alerte : au signal « Alerte ! » du Grand Maître, tout le monde se met en rang le plus vite possible, au garde-à-vous. Puis on recommence, encore plus vite !",
      defiIn: "L'alerte : au signal « Alerte ! » du Grand Maître, tout le monde se met en rang le plus vite possible, au garde-à-vous. Puis on recommence, encore plus vite !",
      q: "Quel numéro faut-il appeler pour joindre les pompiers ?", choices: ["Le 18", "Le 10", "Le 42"], answer: 0,
      fact: "Le 18 et le 112 servent à appeler les secours en cas d'urgence.",
      hints: ["C'est un nombre plus petit que 20.", "Huit plus dix.", "Le 18."],
      adult: "Ne vous placez jamais devant les portes de sortie des camions."
    }],
    library: [{
      teaser: "Un trésor de mots et d'histoires.",
      generic: "la bibliothèque",
      clue: "Cherchez la maison des livres, là où dorment des milliers d'histoires.",
      story: "Te voici devant {P}, {N}. Au Moyen Âge, il n'y avait pas d'imprimerie : des moines copiaient les livres à la main, lettre après lettre. Un seul livre pouvait demander des mois de travail ! Les livres étaient si précieux qu'on les attachait parfois avec des chaînes, pour que personne ne les emporte.",
      defi: "Les copistes : chacun trace dans l'air, avec son doigt, la première lettre de son prénom, la plus grande et la plus belle possible. Les autres doivent la deviner.",
      defiIn: "Les copistes : chacun trace dans l'air, avec son doigt, la première lettre de son prénom, la plus grande et la plus belle possible. Les autres doivent la deviner.",
      q: "Comment appelait-on ceux qui recopiaient les livres à la main ?", choices: ["Des copistes", "Des imprimantes", "Des cuisiniers"], answer: 0,
      fact: "Les copistes décoraient la première lettre de chaque page avec de l'or et des couleurs.",
      hints: ["Ils faisaient des copies.", "Ça commence par « copi… ».", "Des copistes."],
      adult: "Restez dehors et parlez doucement : on lit à l'intérieur."
    }],
    school: [{
      teaser: "Un lieu où l'on apprend à lire et à compter.",
      generic: "l'école",
      clue: "Cherchez le bâtiment où les enfants apprennent à lire, à écrire et à compter.",
      story: "Voici {P}, {N}. Les jeunes écuyers aussi apprenaient beaucoup de choses : lire, compter, monter à cheval, et surtout les bonnes manières d'un chevalier. Pour écrire, les élèves utilisaient de petites tablettes recouvertes de cire : pour effacer, il suffisait de lisser la cire !",
      defi: "La dictée des chevaliers : chacun à son tour dit une lettre du mot « chevalier », dans l'ordre, sans se tromper. Une erreur ? On recommence depuis le début !",
      defiIn: "La dictée des chevaliers : chacun à son tour dit une lettre du mot « chevalier », dans l'ordre, sans se tromper. Une erreur ? On recommence depuis le début !",
      q: "Sur quoi les écoliers écrivaient-ils autrefois ?", choices: ["Sur une ardoise, avec une craie", "Sur une tablette tactile", "Sur un nuage"], answer: 0,
      fact: "L'ardoise s'effaçait avec un chiffon, et on recommençait.",
      hints: ["C'est une pierre noire et plate.", "On écrit dessus avec une craie.", "Sur une ardoise."],
      adult: "On reste devant l'école, sans entrer dans la cour."
    }],
    sport: [{
      teaser: "Un champ parfait pour un tournoi.",
      generic: "le terrain de sport",
      clue: "Les chevaliers s'entraînaient sur un grand terrain plat. Cherchez un terrain de sport, avec des buts ou des lignes tracées au sol.",
      story: "Te voici au bord du terrain, {N}. Autrefois, les chevaliers s'affrontaient lors de grands tournois, devant tout le village qui les encourageait. Ce terrain ferait un parfait champ de tournoi ! Une armure pouvait peser plus de vingt kilos, autant qu'un enfant de six ans : et pourtant, les chevaliers arrivaient à courir avec !",
      defi: "La course des destriers : chacun galope comme un cheval jusqu'à un repère choisi par le Grand Maître, en imitant le bruit des sabots, puis revient au trot.",
      defiIn: "La course des destriers : à quatre pattes, chaque chevalier fait le tour de la pièce comme un cheval, puis revient au trot.",
      q: "Comment s'appelait la grande fête où les chevaliers s'affrontaient devant le public ?", choices: ["Le tournoi", "Le carnaval", "Le marché"], answer: 0,
      fact: "Les tournois servaient aussi d'entraînement aux chevaliers.",
      hints: ["Ça ressemble à « tourner ».", "Tour… tour…", "Le tournoi."],
      adult: "Si une équipe joue, restez au bord du terrain."
    }],
    postbox: [{
      teaser: "Une petite maison jaune pour les messages.",
      generic: "la boîte aux lettres",
      clue: "Cherchez une petite boîte jaune où l'on glisse les lettres. Le Templier y a laissé un message.",
      story: "Voici {P}, {N}. Au temps des chevaliers, les messages voyageaient à cheval, portés par des messagers. Aujourd'hui, on glisse sa lettre ici, et elle peut partir tout autour du monde ! Le Père Noël a même son adresse en France : chaque année, il reçoit plus d'un million de lettres d'enfants, et il répond à chacune !",
      defi: "Le message secret : le Grand Maître murmure une phrase à l'oreille d'un chevalier, qui la répète à son voisin, et ainsi de suite. Le dernier la dit à voix haute : est-ce toujours la même ?",
      defiIn: "Le message secret : le Grand Maître murmure une phrase à l'oreille d'un chevalier, qui la répète à son voisin, et ainsi de suite. Le dernier la dit à voix haute : est-ce toujours la même ?",
      q: "Avant la Poste, comment voyageaient les messages des seigneurs ?", choices: ["Portés par des messagers à cheval", "Par Internet", "Par la pensée"], answer: 0,
      fact: "Les messagers changeaient de cheval en route pour aller plus vite.",
      hints: ["Il n'y avait ni téléphone ni Internet.", "Un cavalier…", "Portés par des messagers à cheval."],
      adult: "Boîte souvent au bord de la rue : restez sur le trottoir."
    }]
  };


  // What the voice says instead of the place name (the exact name stays on the adult's screen).
  const HERE = { church: ["cette église", "ce lieu de prière"], gate: ["cette porte", "cette vieille porte"], tower: ["cette tour"],
    castle: ["ce château"], ruins: ["ces ruines"], well: ["ce puits"], fountain: ["cette fontaine", "cette fontaine"],
    townhall: ["cette mairie"], memorial: ["ce monument"], statue: ["cette statue", "ce monument"], artwork: ["cette œuvre"],
    square: ["cette place"], park: ["ce parc", "ce jardin"], playground: ["cette aire de jeux"], viewpoint: ["ce point de vue"],
    cross: ["cette croix", "ce calvaire"], watertower: ["ce château d'eau"], lavoir: ["ce lavoir"], mill: ["ce moulin"], tree: ["cet arbre"],
    house: ["cette vieille maison"], fire: ["cette caserne"], library: ["cette bibliothèque"], school: ["cette école"], sport: ["ce terrain"],
    postbox: ["cette boîte aux lettres"] };

  // "Église Saint-Martin" -> "l'église Saint-Martin"; "Saint-Martin" (church) -> "l'église Saint-Martin"
  const NOUNS = [["hôtel de ville", "l'"], ["aire de jeux", "l'"], ["monument", "le "], ["église", "l'"], ["chapelle", "la "],
    ["cathédrale", "la "], ["basilique", "la "], ["temple", "le "], ["parc", "le "], ["jardin", "le "], ["square", "le "],
    ["place", "la "], ["fontaine", "la "], ["puits", "le "], ["porte", "la "], ["tour", "la "], ["château", "le "],
    ["fort", "le "], ["manoir", "le "], ["statue", "la "], ["mairie", "la "], ["maison", "la "], ["ruines", "les "],
    ["belvédère", "le "], ["calvaire", "le "], ["lavoir", "le "], ["stèle", "la "], ["buste", "le "],
    ["château d'eau", "le "], ["croix", "la "], ["moulin", "le "], ["arbre", "l'"], ["tilleul", "le "], ["chêne", "le "],
    ["caserne", "la "], ["centre de secours", "le "], ["centre d'incendie", "le "], ["bibliothèque", "la "], ["médiathèque", "la "],
    ["école", "l'"], ["groupe scolaire", "le "], ["collège", "le "], ["stade", "le "], ["terrain", "le "], ["complexe sportif", "le "],
    ["ferme", "la "], ["oratoire", "l'"], ["presbytère", "le "], ["auberge", "l'"], ["hôtel", "l'"]];
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
  // At home, the Templar hid each letter in the house: the adult hides the cards before the party (5 minutes),
  // the children find each one from the Grand Master's riddle. Places every home has, in this order.
  // Each hiding place has its own story, challenge and question, about that object in the time of the
  // knights (15/10/2026: the stories of the outdoor places made no sense at home).
  const CACHES = [
    { id: "chaussure", where: "dans une chaussure, dans l'entrée", title: "La chaussure du chevalier",
      teaser: "Une cachette qui suit tes pas.",
      clue: "Le Templier a caché cette lettre dans une cachette qui t'accompagne partout, mais toujours à tes pieds ! Cherche bien, et pince-toi le nez.",
      story: "Bravo, {N}, tu l'as trouvée ! Sais-tu que les chevaliers aussi protégeaient leurs pieds ? Sur leur armure, ils portaient des chaussures de métal, faites de petites plaques qui bougeaient comme des écailles. Un jour, la mode fut aux chaussures très pointues, les poulaines. On raconte que des chevaliers devaient couper le bout de leurs chaussures pour pouvoir courir !",
      defi: "La marche de l'armure : chaque chevalier traverse la pièce comme s'il portait une armure très lourde, raide comme un robot, sans plier les genoux. Le Grand Maître choisit l'armure la plus rigolote.",
      q: "Comment s'appelaient les chaussures très pointues à la mode au Moyen Âge ?", choices: ["Les poulaines", "Les baskets", "Les palmes"], answer: 0,
      fact: "Plus on était important, plus la pointe de ses poulaines avait le droit d'être longue.",
      hints: ["Le mot ressemble au nom d'un animal de la ferme…", "Pou… comme une poule !", "Les poulaines."] },
    { id: "frigo", where: "dans le réfrigérateur, sur une étagère du bas ou collée sur la porte", title: "Le garde-manger du château",
      teaser: "Un coffre où il fait toujours froid.",
      clue: "Cette lettre-ci est cachée dans un coffre magique où il fait toujours froid, même en plein été. Quand on l'ouvre, une petite lumière s'allume !",
      story: "Bravo, {N}, tu l'as trouvée ! Au temps des chevaliers, il n'y avait pas de réfrigérateur. Pour garder la viande, on la salait, ou on la fumait au-dessus du feu, et les provisions restaient au frais dans les caves du château. Et pendant les grands banquets, on servait parfois un paon rôti, recouvert de ses propres plumes, comme s'il était encore vivant !",
      defi: "Les statues de glace : les chevaliers marchent dans la pièce. Quand le Grand Maître crie « Glace ! », tout le monde se fige. Celui qui bouge le premier devient le prochain à crier. Trois manches !",
      q: "Sans réfrigérateur, comment gardait-on la viande au Moyen Âge ?", choices: ["En la salant ou en la fumant", "En la laissant au soleil", "En la cachant sous son lit"], answer: 0,
      fact: "Le sel était si précieux qu'on l'appelait parfois l'or blanc.",
      hints: ["Pense à ce qu'on met sur les frites…", "On en trouve dans l'eau de la mer.", "En la salant ou en la fumant."] },
    { id: "oreiller", where: "sous l'oreiller du lit de l'enfant", title: "La nuit du chevalier",
      teaser: "Une cachette où l'on fait de beaux rêves.",
      clue: "Cette lettre dort là où tu poses ta tête chaque soir, pour rêver de dragons et de chevaliers.",
      story: "Bravo, {N}, tu l'as trouvée ! En voyage, les chevaliers dormaient souvent par terre, enroulés dans leur manteau, la tête posée sur leur selle de cheval. Et dans les auberges, il y avait si peu de lits qu'on devait parfois partager le sien avec des voyageurs inconnus… qui ronflaient peut-être très fort !",
      defi: "Le dragon endormi : un chevalier fait le dragon, assis les yeux fermés, un coussin à ses pieds : c'est son trésor. Les autres s'approchent sans bruit pour le prendre. Si le dragon entend quelqu'un, il le montre du doigt, et ce chevalier retourne au départ.",
      q: "Sur quoi les chevaliers en voyage posaient-ils souvent leur tête pour dormir ?", choices: ["Sur leur selle de cheval", "Sur un oreiller en plumes de dragon", "Sur leur casque rempli d'eau"], answer: 0,
      fact: "Chez les seigneurs, les lits avaient des rideaux tout autour, pour garder la chaleur.",
      hints: ["Ils voyageaient à cheval…", "On s'assoit dessus pour monter à cheval.", "Sur leur selle de cheval."] },
    { id: "livre", where: "entre les pages d'un livre, sur une étagère", title: "Le grimoire du moine",
      teaser: "Une cachette pleine d'histoires.",
      clue: "Cette lettre se cache entre les pages d'un grimoire, là où dorment les histoires. Cherche parmi les livres !",
      story: "Bravo, {N}, tu l'as trouvée ! Au Moyen Âge, chaque livre était écrit à la main par des moines, avec une plume d'oie et de l'encre. Ils travaillaient en silence pendant des mois. Et dans le bord des pages, certains dessinaient des choses très rigolotes : des escargots géants qui se battent contre des chevaliers, ou des lapins armés d'une épée !",
      defi: "Le silence des moines : pendant trente secondes, plus personne ne parle ni ne rit… même si le Grand Maître fait des grimaces !",
      timer: 30,
      q: "Avec quoi les moines écrivaient-ils les livres ?", choices: ["Avec une plume d'oiseau et de l'encre", "Avec un stylo à bille", "Avec un ordinateur"], answer: 0,
      fact: "Un seul livre pouvait demander des mois, et parfois des années de travail.",
      hints: ["Ça vient d'un oiseau…", "Une oie en a plein sur le dos.", "Avec une plume d'oiseau et de l'encre."] },
    { id: "canape", where: "sous un coussin du canapé", title: "La grande salle du château",
      teaser: "Un nuage tout doux où l'on s'assoit.",
      clue: "Cette lettre est cachée sous un nuage tout doux, là où toute la famille s'assoit le soir.",
      story: "Bravo, {N}, tu l'as trouvée ! Au château, il n'y avait pas de canapé. Le soir, tout le monde se retrouvait dans la grande salle, près de la cheminée, assis sur des bancs ou sur des coffres. Seul le seigneur avait une vraie chaise, avec un dossier : c'était un honneur ! Pour amuser tout le monde, des musiciens chantaient des histoires de chevaliers, et des montreurs faisaient parfois danser… un ours !",
      defi: "Le troubadour : chaque chevalier, à son tour, ajoute une phrase à une aventure du Templier. Le Grand Maître commence : « Il était une fois un chevalier qui avait perdu son cheval… »",
      q: "Dans la grande salle du château, qui avait le droit de s'asseoir sur une vraie chaise ?", choices: ["Le seigneur", "Les chiens", "Tout le monde"], answer: 0,
      fact: "Les autres s'asseyaient sur des bancs, des tabourets ou des coffres.",
      hints: ["C'était un honneur…", "La personne la plus importante du château.", "Le seigneur."] },
    { id: "table", where: "collée sous la table du repas, avec un morceau de ruban adhésif", title: "Le banquet des chevaliers",
      teaser: "Une cachette sous le grand banquet.",
      clue: "Cette lettre attend sous la grande table où les chevaliers prennent leur repas. Regarde bien, même par en dessous !",
      story: "Bravo, {N}, tu l'as trouvée ! Pendant les banquets du Moyen Âge, on mangeait avec ses doigts et son couteau : la fourchette était encore très rare. Et pas d'assiette ! On posait la nourriture sur une grosse tranche de pain, le tranchoir. À la fin du repas, ce pain plein de sauce était donné aux pauvres… ou aux chiens !",
      defi: "Le banquet mimé : chaque chevalier, à son tour, mime un plat du banquet sans parler : une cuisse de poulet géante, une soupe brûlante, une grappe de raisin… Les autres devinent.",
      q: "Dans la légende, pourquoi le roi Arthur avait-il choisi une table ronde ?", choices: ["Pour que tous ses chevaliers soient égaux", "Pour pouvoir la faire rouler", "Parce qu'il avait peur des coins"], answer: 0,
      fact: "Autour d'une table ronde, personne n'est en bout de table : chacun a la même place.",
      hints: ["Personne n'était plus important que les autres…", "Autour d'un rond, il n'y a pas de bout.", "Pour que tous ses chevaliers soient égaux."] }
  ];
  // What the step at home shows instead of the outdoor place (also when an outdoor quest is played at home).
  const homeOf = c => ({ title: c.title, story: c.story, defi: c.defi, timer: c.timer || 0, q: c.q, choices: c.choices, answer: c.answer, fact: c.fact, hints: c.hints });

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
      const tpl = T[s.cat][v], c = CACHES[i % CACHES.length];
      const step = Object.assign({}, tpl, {
        cat: s.cat, v, letter: scrambled[i], name: s.name || "",
        lat: indoor ? null : s.lat, lon: indoor ? null : s.lon,
        P: indoor ? c.title : articleize(s.name, tpl.generic),
        legM: indoor ? 0 : Math.round(dist(prev, s) * WALK_FACTOR / 10) * 10,
        dir: indoor ? "" : bearing(prev, s), osm: s.id || null,
        // where the letter card is hidden when the quest is played at home (also after a rainy switch),
        // and the story, challenge and question that go with that hiding place
        hideId: c.id, hide: c.where, hideClue: c.clue, home: homeOf(c)
      });
      if (indoor) step.teaser = c.teaser;
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

  return { overpassQuery, classify, dedupe, choose, select, selectPlaces, assemble, indoorStops, build, preview, dist, bearing, articleize, T, HERE, WORDS, CACHES, RANK, SEARCH_RADIUS, MAX_WALK };
})();
if (typeof module !== "undefined") module.exports = QuestEngine;
/* ENGINE-END */
