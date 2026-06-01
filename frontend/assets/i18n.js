/* Synapse i18n — web bilingüe ES/EN sin framework.
 *
 * Cómo funciona: traduce por NODOS DE TEXTO y ATRIBUTOS usando un diccionario
 * ES→EN (la clave es el texto exacto en español). Guarda el original de cada
 * nodo para poder alternar idioma, inyecta el selector ES/EN en la .topbar y,
 * con un MutationObserver, traduce también el contenido que el JS pinta después
 * (simulador, exploradores, informes…). Basta con incluir este script.
 *
 * Idioma: localStorage('synapse_lang') → si no, idioma del navegador (EN si
 * empieza por 'en') → si no, español. El idioma elegido se recuerda.
 *
 * Para textos NUEVOS solo hay que añadir la entrada ES→EN en DICT.
 */
(function () {
  "use strict";
  var STORE = "synapse_lang";
  var ATTRS = ["placeholder", "title", "aria-label", "alt"];

  // ───────────────────────── Diccionario ES → EN ─────────────────────────
  // Clave = texto EXACTO en español (sin espacios sobrantes).
  var DICT = {
    // Navegación / chrome
    "Coaching": "Coaching",
    "Estadísticas": "Stats",
    "Meta": "Meta",
    "Lab": "Lab",
    "Perfil": "Profile",
    "Saltar al contenido": "Skip to content",
    "Secciones": "Sections",
    "Juego": "Game",
    "Idioma / Language": "Language",
    "Marca propia, no afiliada a los titulares de los juegos.":
      "Own brand, not affiliated with the games' owners.",
    "Arquetipos, objetos y runas genéricos en la maqueta. Marca propia, no afiliada a los titulares de los juegos.":
      "Generic archetypes, items and runes in this mockup. Own brand, not affiliated with the games' owners.",

    // ───────── Perfil (GPI) ─────────
    "Synapse — Perfil": "Synapse — Profile",
    "Tu perfil": "Your profile",
    "Tu rendimiento · TFT": "Your performance · TFT",
    "Tu rendimiento · LoL": "Your performance · LoL",
    "Tu nivel de un vistazo: un perfil de habilidades que te dice en qué eres fuerte y dónde mejorar, comparado con la media de tu rango.":
      "Your level at a glance: a skill profile that tells you where you are strong and where to improve, compared with your rank average.",
    "Perfil de habilidades": "Skill profile",
    "Dónde mejoras más rápido": "Where you improve fastest",
    "Tú": "You",
    "Media de tu rango": "Your rank average",
    "Evolución": "Trend",
    // KPIs / benchmarks
    "Colocación media": "Average placement",
    "Top 4": "Top 4",
    "Top 1": "Top 1",
    "Partidas": "Games",
    "Winrate": "Win rate",
    "KDA medio": "Average KDA",
    "Media: 50%": "Avg: 50%",
    "Media: 12.5%": "Avg: 12.5%",
    "Últimos 30 días": "Last 30 days",
    "Objetivo: 2.5": "Target: 2.5",
    "Objetivo: 6.5": "Target: 6.5",
    // Ejes GPI
    "Economía": "Economy",
    "Posición": "Position",
    "Nivel": "Level",
    "Augments": "Augments",
    "Flexib.": "Flex.",
    "Consist.": "Consist.",
    "Farmeo": "Farming",
    "Lucha": "Fighting",
    "Visión": "Vision",
    "Objetivos": "Objectives",
    "Supervi.": "Survival",
    // Insights
    "Tu punto débil: posicionamiento (55)": "Your weak point: positioning (55)",
    "Por debajo de la media de tu rango. Trabajarlo es tu mayor salto de LP.":
      "Below your rank average. Working on it is your biggest LP jump.",
    "Tu fuerte: flexibilidad (80)": "Your strength: flexibility (80)",
    "Lees bien lo que te dan y pivotas. Mantenlo.":
      "You read your options well and pivot. Keep it up.",
    "Tu punto débil: objetivos (52) y visión (48)":
      "Your weak point: objectives (52) and vision (48)",
    "El control de mapa es lo que te frena. Prioriza drakes/heraldo y pon más visión.":
      "Map control is what holds you back. Prioritize drakes/herald and place more vision.",
    "Tu fuerte: farmeo (74)": "Your strength: farming (74)",
    "Tu CS temprano es sólido. Tu problema es macro, no mecánica.":
      "Your early CS is solid. Your issue is macro, not mechanics.",
    // Evolución / tablas
    "Colocación por semana (menor es mejor)": "Placement per week (lower is better)",
    "Winrate por semana": "Win rate per week",
    "Comps más jugadas": "Most played comps",
    "Campeones más jugados": "Most played champions",
    "Comp": "Comp",
    "Coloc.": "Place.",
    "Campeón": "Champion",

    // ───────── Build de campeón (LoL) ─────────
    "Synapse — Build de campeón": "Synapse — Champion build",
    "Build de campeón": "Champion build",
    "Campeones": "Champions",
    "Build recomendada": "Recommended build",
    "Orden de objetos (core)": "Item order (core)",
    "Notas": "Notes",
    "Adapta botas y situacionales al rival": "Adapt boots and situationals to the enemy",
    "Runas": "Runes",
    "Primaria": "Primary",
    "Secundaria": "Secondary",
    "Habilidades": "Abilities",
    "Hechizos de invocador": "Summoner spells",
    "Counters": "Counters",
    "Fuerte contra": "Strong against",
    "Débil contra": "Weak against",
    "Power spikes": "Power spikes",
    "La barra indica la fuerza relativa del campeón en cada fase de la partida.":
      "The bar shows the champion's relative strength in each phase of the game.",
    "Cómo jugarlo": "How to play it",
    "Juega tu fase fuerte (la de mayor power spike) buscando ventaja; cede espacio en tus fases débiles. Guarda tu control para frenar el acceso de los campeones contra los que eres débil.":
      "Play your strong phase (your biggest power spike) to build a lead; give up space in your weak phases. Save your crowd control to stop the engage of champions you are weak against.",
    "Pick": "Pick",
    "Ban": "Ban",
    "Ver build completa →": "View full build →",
    "Rol:": "Role:",
    "Dificultad:": "Difficulty:",
    // Roles y dificultad (datos comunes)
    "Mid": "Mid",
    "Top": "Top",
    "Jungla": "Jungle",
    "Soporte": "Support",
    "Media": "Medium",
    "Alta": "High",
    "Baja": "Low",

    // ───────── Términos comunes / acciones ─────────
    "Cargando…": "Loading…",
    "Cargando...": "Loading...",
    "Reintentar": "Retry",
    "Buscar": "Search",
    "Unidades": "Units",
    "Ítems": "Items",
    "Objetos": "Items",
    "Recetas": "Recipes",
    "Simulador": "Simulator",
    "Vaciar": "Clear",
    "Compartir": "Share",
    "Coste": "Cost",
    "Uso": "Usage",
    "Rango": "Rank",
    "Región": "Region",
    "Parche": "Patch",
    "Cola": "Queue",
    "Todos": "All"
  };

  // ───────────────────────── Estado de idioma ─────────────────────────
  var saved = null;
  try { saved = localStorage.getItem(STORE); } catch (e) {}
  var nav = (navigator.language || navigator.userLanguage || "es").toLowerCase();
  var lang = saved || (nav.indexOf("en") === 0 ? "en" : "es");

  var textOrig = new WeakMap();  // nodo de texto → original ES
  var attrOrig = new WeakMap();  // elemento → { atributo: original ES }
  var observer = null;

  function tr(s) {
    if (s == null) return s;
    var key = ("" + s).trim();
    if (!key) return s;
    var v = DICT[key];
    if (v == null) return s;
    return ("" + s).replace(key, v); // conserva espacios alrededor
  }

  function applyNode(node) {
    if (!node) return;
    if (node.nodeType === 3) { // texto
      if (!textOrig.has(node)) textOrig.set(node, node.nodeValue);
      var orig = textOrig.get(node);
      var next = (lang === "en") ? tr(orig) : orig;
      if (node.nodeValue !== next) node.nodeValue = next;
      return;
    }
    if (node.nodeType === 1) { // elemento
      var tag = node.tagName;
      if (tag === "SCRIPT" || tag === "STYLE" || node.id === "lang-switch") {
        // no traducir scripts/estilos ni el propio selector
        if (node.id !== "lang-switch") return;
      }
      var store = attrOrig.get(node);
      for (var i = 0; i < ATTRS.length; i++) {
        var a = ATTRS[i];
        if (node.hasAttribute && node.hasAttribute(a)) {
          if (!store) { store = {}; attrOrig.set(node, store); }
          if (!(a in store)) store[a] = node.getAttribute(a);
          node.setAttribute(a, (lang === "en") ? tr(store[a]) : store[a]);
        }
      }
      for (var c = node.firstChild; c; c = c.nextSibling) applyNode(c);
    }
  }

  function updateHtmlLang() {
    try { document.documentElement.setAttribute("lang", lang); } catch (e) {}
  }

  function apply(root) {
    if (observer) observer.disconnect();
    applyNode(root || document.body);
    injectSwitcher();
    refreshSwitcher();
    updateHtmlLang();
    if (observer && document.body) {
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    }
  }

  function setLang(l) {
    if (l !== "es" && l !== "en") return;
    lang = l;
    try { localStorage.setItem(STORE, l); } catch (e) {}
    apply(document.body);
    try { document.dispatchEvent(new CustomEvent("synapse:lang", { detail: l })); } catch (e) {}
  }

  // ───────────────────────── Selector ES/EN ─────────────────────────
  function injectSwitcher() {
    if (document.getElementById("lang-switch")) return;
    var bar = document.querySelector(".topbar");
    if (!bar) return;
    var wrap = document.createElement("div");
    wrap.id = "lang-switch";
    wrap.setAttribute("role", "group");
    wrap.setAttribute("aria-label", "Idioma / Language");
    wrap.style.cssText = "display:inline-flex;gap:2px;margin-left:10px;background:rgba(20,25,37,.7);border:1px solid #262D3D;border-radius:999px;padding:3px;";
    ["es", "en"].forEach(function (l) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("data-l", l);
      b.textContent = l.toUpperCase();
      b.style.cssText = "border:0;background:transparent;color:#8C97A8;font:inherit;font-weight:800;font-size:12px;padding:5px 11px;border-radius:999px;cursor:pointer;min-height:26px;";
      b.addEventListener("click", function () { setLang(l); });
      wrap.appendChild(b);
    });
    var avatar = bar.querySelector(".avatar");
    if (avatar) bar.insertBefore(wrap, avatar); else bar.appendChild(wrap);
  }

  function refreshSwitcher() {
    var sw = document.getElementById("lang-switch");
    if (!sw) return;
    var btns = sw.querySelectorAll("button");
    for (var i = 0; i < btns.length; i++) {
      var on = btns[i].getAttribute("data-l") === lang;
      btns[i].style.background = on ? "linear-gradient(100deg,#8B5CF6,#22D3EE)" : "transparent";
      btns[i].style.color = on ? "#0A0C12" : "#8C97A8";
      btns[i].setAttribute("aria-pressed", on ? "true" : "false");
    }
  }

  // ───────────────────────── Observa renders dinámicos ─────────────────────────
  if (typeof MutationObserver === "function") {
    observer = new MutationObserver(function (list) {
      observer.disconnect();
      for (var i = 0; i < list.length; i++) {
        var m = list[i];
        if (m.type === "characterData") { applyNode(m.target); }
        else if (m.addedNodes) {
          for (var j = 0; j < m.addedNodes.length; j++) applyNode(m.addedNodes[j]);
        }
      }
      if (document.body) observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    });
  }

  // API pública (para usar en JS: SynapseI18N.t("texto"))
  window.SynapseI18N = {
    apply: apply,
    setLang: setLang,
    t: function (s) { return lang === "en" ? tr(s) : s; },
    add: function (obj) { for (var k in obj) if (obj.hasOwnProperty(k)) DICT[k] = obj[k]; },
    get lang() { return lang; }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { apply(); });
  } else {
    apply();
  }
})();
