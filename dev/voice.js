/* VOICE-START
   The Grand Master's recorded voice: every line is generated once (Gemini TTS, voice Algenib)
   and reused for every customer. A message is a list of clip keys played in a row;
   "@name" stands for the child's first-name clip ("Léa,"), or "Jeune chevalier," when the
   name is not in the library; "@name?" plays the name only when it is recorded. Place names are never spoken: they stay on the adult's screen. */

const QuestVoice = (() => {
  // The texts come from the engine. The paid app does not ship the engine: its build injects
  // QUEST_VOICE_KEYS, the list of recorded clips, instead.
  const E = (typeof QuestEngine !== "undefined") ? QuestEngine : (typeof require === "function" ? require("./engine.js") : null);
  const STYLE = "Un très vieil homme sage, Grand Maître d'un ordre de chevaliers, qui parle à un enfant. Voix grave, chaleureuse, un peu voilée par l'âge. Il parle lentement et doucement, avec de petites pauses, comme s'il confiait un secret au coin du feu. Français de France, sans accent.";
  const VOICE = "Algenib";
  const LETTERS = ["F", "I", "D", "E", "L", "B", "R", "A", "V", "P"];

  const gender = (t, g) => t.replace(/\[\[([^|\]]*)\|([^\]]*)\]\]/g, (m, a, b) => g === "f" ? b : a);
  const cap = s => s.replace(/(^|[.!?…]\s+|«\s)([a-zàâäéèêëîïôöùûüç])/g, (m, a, b) => a + b.toUpperCase());

  const LINES = {};
  function add(key, text) {
    if (/\[\[/.test(text)) { LINES[key + "-m"] = cap(gender(text, "m")); LINES[key + "-f"] = cap(gender(text, "f")); }
    else LINES[key] = cap(text);
  }
  function key(base, g) { return KEYS.has(base) ? base : `${base}-${g === "f" ? "f" : "m"}`; }

  // Story text without the child's name (the name clip plays first) and without the place name.
  function spokenStory(t, here) {
    return t.replace(/,\s*\{N\}/g, "").replace(/\{N\},\s*/g, "").replace(/\{N\}/g, "jeune [[chevalier|chevalière]]")
      .replaceAll("{P}", here).replace(/\s+/g, " ").trim();
  }

  if (E) {
    add("vocatif", "jeune [[chevalier|chevalière]],");
    add("prologue-dehors", "approche. Je suis le Grand Maître de l'Ordre des Gardiens du Temple. Il y a bien longtemps, un chevalier du Temple passa par ici. Avant de repartir, il cacha un sceau magique et dispersa les lettres du mot secret qui permet de l'ouvrir. Aujourd'hui, c'est ton anniversaire, et j'ai besoin d'[[un chevalier courageux|une chevalière courageuse]]. Avec tes compagnons, suis les indices, relève mes défis, et rapporte-moi les lettres. Es-tu [[prêt|prête]] ?");
    add("prologue-maison", "approche. Je suis le Grand Maître de l'Ordre des Gardiens du Temple. Il y a bien longtemps, un chevalier du Temple cacha un sceau magique et dispersa les lettres du mot secret qui permet de l'ouvrir. Cette nuit, ses lettres sont apparues, cachées dans ta maison ! Aujourd'hui, c'est ton anniversaire, et j'ai besoin d'[[un chevalier courageux|une chevalière courageuse]]. Avec tes compagnons, résous mes énigmes pour trouver chaque cachette, relève mes défis, et rapporte-moi les lettres. Es-tu [[prêt|prête]] ?");
    add("intro-dehors", "[[chevalier|chevalière]] de l'Ordre, la quête commence ! À chaque lieu, tu gagneras une lettre. Les lettres arrivent dans le désordre : à toi de retrouver le mot secret à la fin. Suis les indices, reste toujours près des adultes, et ouvre grand les yeux.");
    add("intro-maison", "[[chevalier|chevalière]] de l'Ordre, la chasse commence ! Chaque énigme te mène à une cachette de la maison. Quand tu trouves une lettre, apporte-la au Grand Maître, sans la montrer aux autres. Les lettres sont dans le désordre : à toi de retrouver le mot secret à la fin.");
    // at home: the riddle of each hiding place, and the moment the card is found, before the story of the Templar's journey
    for (const c of E.CACHES) add(`cachette-${c.id}`, "Écoute bien. " + c.clue);
    add("imagine", "bravo, tu l'as trouvée ! Maintenant, ferme les yeux, et imagine.");
    for (const [cat, list] of Object.entries(E.T)) list.forEach((t, v) => {
      add(`indice-${cat}-${v}`, "Écoute bien. " + t.clue);
      add(`recit-${cat}-${v}`, spokenStory(t.story, E.HERE[cat][v]));
    });
    for (const L of LETTERS) {
      add(`lettre-${L}`, `Bien joué ! Voici la lettre ${L}.`);
      add(`derniere-${L}`, `Et voici la dernière lettre : ${L}. Choisissez son gardien.`);
    }
    add("gardien", "Choisissez un gardien de la lettre, un chevalier qui ne l'a pas encore été. Il devra s'en souvenir jusqu'à la fin de la quête.");
    for (const W of Object.values(E.WORDS)) {
      add(`mot-${W.word}`, `Tu as maintenant toutes les lettres, mais elles sont dans le désordre. Retrouve le mot secret. Un indice : ${W.hint}${/…$/.test(W.hint) ? "" : "."}`);
      add(`fin-${W.word}`, `tu as retrouvé le mot secret : ${W.say}. ${W.meaning} Le Sceau du Temple est ouvert ! Grand Maître, remets le trésor aux chevaliers. Et toi,`);
    }
    add("nomme", "je te nomme [[Chevalier|Chevalière]] de l'Ordre des Gardiens du Temple. Joyeux anniversaire !");
  }
  const KEYS = (typeof QUEST_VOICE_KEYS !== "undefined") ? new Set(QUEST_VOICE_KEYS) : new Set(Object.keys(LINES));

  const slug = s => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  // Spelling variants that sound the same in French share one recording (Michael -> Mickaël, Lyna -> Lina).
  const sound = s => s.replace(/chael/g, "kael").replace(/sh/g, "ch").replace(/ck/g, "k").replace(/ph/g, "f").replace(/th/g, "t").replace(/rh/g, "r")
    .replace(/([aeiouy])h$/, "$1").replace(/(?!^)y/g, "i").replace(/([bcdfgklmnprtvz])\1/g, "$1");
  // Recorded clip for a typed first name, or null. names: the recorded slugs.
  function nameClip(name, names) {
    const s = slug(name);
    if (!s || !names) return null;
    if (names.has(s)) return s;
    if (!names._sound) { names._sound = new Map(); for (const n of names) if (!names._sound.has(sound(n))) names._sound.set(sound(n), n); }
    return names._sound.get(sound(s)) || null;
  }

  // Clip keys for one message. ctx: { g: "m"|"f", indoor, cat, v, letter, last, word }
  function message(kind, ctx) {
    const g = ctx.g, N = "@name", where = ctx.indoor ? "maison" : "dehors";
    switch (kind) {
      case "prologue": return [N, key(`prologue-${where}`, g)];
      case "intro": return ["@name?", key(`intro-${where}`, g)]; // no "Jeune chevalier, chevalier de l'Ordre"
      case "indice": return ctx.indoor && ctx.cache ? [`cachette-${ctx.cache}`] : [key(`indice-${ctx.cat}-${ctx.v}`, g)];
      case "recit": return ctx.indoor && ctx.cache ? [N, "imagine", key(`recit-${ctx.cat}-${ctx.v}`, g)] : [N, key(`recit-${ctx.cat}-${ctx.v}`, g)];
      case "lettre": return ctx.last ? [key(`derniere-${ctx.letter}`, g), key(`mot-${ctx.word}`, g)] : [key(`lettre-${ctx.letter}`, g), "gardien"];
      case "fin": return [N, key(`fin-${ctx.word}`, g), N, key("nomme", g)];
    }
    return [];
  }

  return { STYLE, VOICE, LINES, message, slug, key, sound, nameClip };
})();
if (typeof module !== "undefined") module.exports = QuestVoice;
/* VOICE-END */
