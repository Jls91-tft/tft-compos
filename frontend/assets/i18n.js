/* DivisionUp i18n — web bilingüe ES/EN sin framework.
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

    // ───────── Home / Landing ─────────
    "Funciones": "Features",

    // ── Home "Nebula" (rediseño): etiquetas de sección y textos nuevos ──
    "El problema": "The problem",
    "Qué hace DivisionUp": "What DivisionUp does",
    "Coaching de verdad, no otro panel de stats": "Real coaching, not another stats dashboard",
    "Así es un informe": "What a report looks like",
    "Llegaste tarde al pico de poder y el tablero no aguantó.":
      "You hit your power spike too late and the board couldn't hold.",
    "Pico de poder tardío y tablero contestado.": "Late power spike and a contested board.",
    "detectado y explicado": "detected and explained",
    "+2 niveles": "+2 levels",
    "vs. el ganador": "vs. the winner",
    "de tus partidas analizadas": "of your games analyzed",
    "juegos: TFT y LoL": "games: TFT & LoL",
    "comparación con quien ganó": "comparison with the winner",
    "accionable y medible": "actionable, measurable",
    "Tanques contestados manteniendo economía sin densidad.":
      "Contested tanks while holding economy without board density.",
    "Veredicto claro de por qué quedaste donde quedaste.":
      "A clear verdict on why you placed where you did.",
    "Comparación con el Top 1: nivel, tablero e itemización.":
      "Comparison with 1st place: level, board and itemization.",
    "Errores priorizados por severidad, no una lista plana.":
      "Mistakes ranked by severity, not a flat list.",
    "Lo que hiciste bien, para no romper lo que funciona.":
      "What you did well, so you don't break what works.",
    "Empieza a subir": "Start climbing",
    "Conecta tu Riot ID y deja que la IA te diga exactamente qué entrenar primero.":
      "Connect your Riot ID and let the AI tell you exactly what to train first.",

    // ── Home: secciones nuevas (problema / preview / FAQ) ──
    "¿Atascado de rango? No es (solo) mala suerte": "Hardstuck? It's not (just) bad luck",
    "Pierdes partidas y no sabes exactamente por qué. Las webs de estadísticas te dan números, pero no te dicen qué decisión te costó el puesto.":
      "You lose games and don't know exactly why. Stats sites give you numbers, but they don't tell you which decision cost you the placement.",
    "Juegas a ciegas": "You play blind",
    "Repites los mismos errores partida tras partida porque nadie te los señala con datos.":
      "You repeat the same mistakes game after game because nobody points them out with data.",
    "Consejos genéricos": "Generic advice",
    '"Mejora tu macro", "farmea más"… frases vacías que no se anclan a TU partida.':
      "\"Improve your macro\", \"farm more\"… empty phrases not anchored to YOUR game.",
    "Sin un plan": "No plan",
    "Sabes que algo falla, pero no qué entrenar primero para subir de verdad.":
      "You know something's off, but not what to train first to actually climb.",
    "Así es un informe de DivisionUp": "This is what a DivisionUp report looks like",
    "Cada partida, un análisis profundo anclado a tus datos reales: errores, comparación con el ganador y qué hiciste bien.":
      "Every game, a deep analysis anchored to your real data: mistakes, comparison with the winner and what you did well.",
    "Caíste en la ronda 26 porque tu tablero llegó suelto: nivel 8 con menos densidad y unidades de coste alto que el ganador. La itemización repartida fue la causa raíz del 8.º puesto.":
      "You went out in round 26 because your board arrived weak: level 8 with less density and fewer high-cost units than the winner. Spread itemization was the root cause of 8th place.",
    "Comparación con el Top 1": "Comparison with 1st place",
    "El ganador tenía nivel 10 (2 más que tú), 10 unidades a 2★ o más (4 más) y una a 3★ que tú no tenías. Ambos con 3 ítems en la carry.":
      "The winner was level 10 (2 more than you), 10 units at 2★ or more (4 more) and one 3★ you didn't have. Both with 3 items on the carry.",
    "Error de decisión": "Decision error",
    "Mantuviste 2 tanques de 4 coste contestados por 3 rivales: bloqueó tu economía sin densidad para sobrevivir.":
      "You kept 2 four-cost tanks contested by 3 opponents: it choked your economy without enough density to survive.",
    "Lo que hiciste bien": "What you did well",
    "Tu carry principal quedó completamente itemizada con sus 3 ítems de daño, y colocaste 6 unidades a 2★ pese al nivel bajo.":
      "Your main carry ended fully itemized with its 3 damage items, and you fielded 6 units at 2★ despite the low level.",
    "Preguntas frecuentes": "FAQ",
    "¿Cómo obtiene DivisionUp mis partidas?": "How does DivisionUp get my games?",
    "Con la API oficial de Riot. Solo necesitas tu Riot ID (Nombre#TAG); leemos tus partidas recientes de TFT y LoL.":
      "Through the official Riot API. You just need your Riot ID (Name#TAG); we read your recent TFT and LoL games.",
    "¿En qué se diferencia de una web de estadísticas?": "How is it different from a stats site?",
    "Las webs de stats te dan números. DivisionUp te da coaching: te dice qué decisión te costó el puesto, lo compara con quien ganó y te marca un plan para mejorar.":
      "Stats sites give you numbers. DivisionUp gives you coaching: it tells you which decision cost you the placement, compares it with the winner and sets you a plan to improve.",
    "¿Funciona para TFT y para LoL?": "Does it work for both TFT and LoL?",
    "Sí, en ambos. En TFT analizamos tablero, itemización y lobby; en LoL, tu rendimiento frente a tu rival de línea y tus muertes por fase.":
      "Yes, both. In TFT we analyze board, itemization and lobby; in LoL, your performance vs your lane opponent and your deaths by phase.",
    "¿Es gratis?": "Is it free?",
    "Estamos en beta cerrada por invitación. Más adelante habrá un plan de acceso; quienes entren en la beta tendrán condiciones especiales.":
      "We're in a closed, invite-only beta. There will be an access plan later; beta members will get special terms.",
    "¿Estáis afiliados a Riot Games?": "Are you affiliated with Riot Games?",
    "No. DivisionUp es una marca independiente; usamos la API oficial de Riot solo para mostrar tus datos reales.":
      "No. DivisionUp is an independent brand; we use the official Riot API only to show your real data.",
    "Cómo funciona": "How it works",
    "Acceso": "Access",
    "Acceder": "Sign in",
    "Coaching IA · TFT y LoL": "AI Coaching · TFT & LoL",
    "Tu coach personal de IA,": "Your personal AI coach,",
    "partida a partida": "game by game",
    "DivisionUp analiza cada partida que juegas, te dice exactamente qué falló, lo compara con quien ganó y te da un plan accionable para subir. Deja de adivinar por qué pierdes.":
      "DivisionUp analyzes every game you play, tells you exactly what went wrong, compares it with the winner and gives you an actionable plan to climb. Stop guessing why you lose.",
    "Empezar ahora": "Get started",
    "Ver cómo funciona": "See how it works",
    "Análisis tras cada partida · Comparación con el Top 1 · Plan de mejora global":
      "Analysis after every game · Comparison with 1st place · Global improvement plan",
    "Lo que hace DivisionUp": "What DivisionUp does",
    "El coaching tras cada partida es el diferencial. Las estadísticas y la meta son el complemento.":
      "Per-match coaching is the differentiator. Stats and meta are the complement.",
    "Coaching tras cada partida": "Coaching after every game",
    "Errores de decisión, fallos de macro y mecánica, y la causa raíz real de tu resultado — anclado a los datos de TU partida, no a consejos genéricos.":
      "Decision errors, macro and mechanics mistakes, and the real root cause of your result — anchored to YOUR match data, not generic advice.",
    "Comparación con quien ganó": "Comparison with the winner",
    "Te decimos en concreto cuánto te faltó: nivel, fuerza de tablero e itemización en TFT; o frente a tu rival de línea en LoL.":
      "We tell you exactly what you lacked: level, board strength and itemization in TFT; or vs your lane opponent in LoL.",
    "Plan de mejora global": "Global improvement plan",
    "Cruzamos todas tus partidas para detectar tus patrones recurrentes y darte un roadmap medible: esta semana, este mes y los próximos meses.":
      "We cross all your games to detect recurring patterns and give you a measurable roadmap: this week, this month and the coming months.",
    "Estadísticas y meta": "Stats and meta",
    "Tu rendimiento de un vistazo y la meta del parche, para tomar decisiones con datos en lugar de intuición.":
      "Your performance at a glance and the patch meta, to make data-driven decisions instead of guessing.",
    "Conecta tu Riot ID": "Connect your Riot ID",
    "Introduce tu Nombre#TAG. Leemos tus partidas con la API oficial de Riot.":
      "Enter your Name#TAG. We read your games with the official Riot API.",
    "La IA analiza cada partida": "The AI analyzes every game",
    "Genera un informe profundo con tus errores, la comparación con el ganador y tus aciertos.":
      "It generates a deep report with your mistakes, the comparison with the winner and what you did well.",
    "Aplicas el plan y subes": "Apply the plan and climb",
    "Entrenas lo que de verdad mueve la aguja, partida a partida.":
      "You train what actually moves the needle, game by game.",
    "Acceso a la beta": "Beta access",
    "Estamos en beta cerrada, afinando el coaching con jugadores reales.":
      "We're in closed beta, refining the coaching with real players.",
    "Beta cerrada": "Closed beta",
    "Por invitación": "Invite only",
    "Coaching IA tras cada partida, sin límite": "AI coaching after every game, unlimited",
    "Comparación con el Top 1 y plan de mejora global": "Comparison with 1st place and global improvement plan",
    "Estadísticas de tu rendimiento y meta del parche": "Your performance stats and the patch meta",
    "Acceso prioritario a las novedades": "Priority access to new features",
    "Si aún no tienes acceso, escríbenos para entrar en la beta.":
      "Don't have access yet? Write to us to join the beta.",
    "Marca propia, no afiliada a los titulares de los juegos.":
      "Own brand, not affiliated with the games' owners.",
    "Arquetipos, objetos y runas genéricos en la maqueta. Marca propia, no afiliada a los titulares de los juegos.":
      "Generic archetypes, items and runes in this mockup. Own brand, not affiliated with the games' owners.",

    // ───────── Perfil (GPI) ─────────
    "DivisionUp — Perfil": "DivisionUp — Profile",
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
    "DivisionUp — Build de campeón": "DivisionUp — Champion build",
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

    // ───────── Home / Coaching / Stats / Meta (index.html) ─────────
    "DivisionUp, inicio": "DivisionUp, home",
    "Seleccionar juego": "Select game",
    "Tu Riot ID (Nombre#TAG)": "Your Riot ID (Name#TAG)",
    "Tu Riot ID": "Your Riot ID",
    "IA": "AI",
    "Coaching IA · lo que nos diferencia": "AI coaching · what sets us apart",
    "Mejora partida a partida": "Improve game by game",
    "Analizamos cada partida terminada y te decimos qué hiciste bien, qué falló y qué hacer la próxima vez. Consejos accionables.":
      "We analyze every finished game and tell you what you did well, what went wrong and what to do next time. Actionable advice.",
    "Analiza tu última partida": "Analyze your last game",
    "Genera un informe de coaching con tus métricas clave y un análisis en lenguaje natural.":
      "Generate a coaching report with your key metrics and a natural-language analysis.",
    "La IA usará tu partida más reciente": "The AI will use your most recent game",
    "Generar coaching": "Generate coaching",
    "Tus partidas recientes": "Your recent games",
    "— elige una para ver su coaching": "— pick one to see its coaching",
    "Sección complementaria · TFT": "Complementary section · TFT",
    "Sección complementaria · LoL": "Complementary section · LoL",
    "Estadísticas personales": "Personal stats",
    "Tu rendimiento de un vistazo: tendencias, comps favoritas y dónde ganas (o pierdes) puntos.":
      "Your performance at a glance: trends, favorite comps and where you gain (or lose) points.",
    "Meta del parche": "Patch meta",
    "Las comps con mejor rendimiento ahora mismo, ordenadas por tier. Filtra y abre la guía de cada una.":
      "The best-performing comps right now, ranked by tier. Filter and open each one's guide.",
    "Analizando tu partida…": "Analyzing your game…",
    "Leyendo el desarrollo del combate": "Reading how the fight developed",
    "Detectando errores y aciertos": "Detecting mistakes and good plays",
    "Redactando tu informe": "Writing your report",
    "DivisionUp — Coaching IA y estadísticas para auto-battler y MOBA":
      "DivisionUp — AI coaching and stats for auto-battler and MOBA",
    "Marca propia genérica. No está afiliada, asociada ni respaldada por los titulares de los juegos.":
      "Generic own brand. Not affiliated with, associated with or endorsed by the games' owners.",
    "Cargando tus partidas…": "Loading your games…",
    "Calculando tus estadísticas…": "Calculating your stats…",
    "Cargando la meta…": "Loading the meta…",
    "No se pudieron cargar los datos.": "Couldn't load the data.",
    "Tu plan de mejora": "Your improvement plan",
    "Actualizado tras tu última partida": "Updated after your last game",
    "Subir de nivel a tiempo en la etapa 3": "Level up on time in stage 3",
    "Marcado en 3 de tus últimos informes.": "Flagged in 3 of your recent reports.",
    "Proteger al portador del asesino": "Protect the carry from the assassin",
    "Foco nuevo desde tu partida de hoy.": "New focus since today's game.",
    "Jugar alrededor de los timers de objetivos": "Play around objective timers",
    "Foco recurrente en jungla.": "Recurring focus in jungle.",
    "No entrar sin visión a la jungla rival": "Don't enter the enemy jungle without vision",
    "Foco nuevo desde tu derrota de hoy.": "New focus since today's loss.",
    "Aplicado en": "Applied in",
    "partidas": "games",
    "Victoria": "Victory",
    "Derrota": "Defeat",
    "Duración": "Duration",
    "Ver coaching →": "View coaching →",
    "Dónde pierdes LP": "Where you lose LP",
    "Ninguna comp coincide con el filtro.": "No comp matches the filter.",
    "Ver guía →": "View guide →",
    "Tier": "Tier",
    "Estilo": "Style",
    "Rol": "Role",
    "1.º puesto": "1st place",
    "2.º puesto": "2nd place",
    "3.º puesto": "3rd place",
    "4.º puesto": "4th place",
    "5.º puesto": "5th place",
    "6.º puesto": "6th place",
    "7.º puesto": "7th place",
    "8.º puesto": "8th place",

    // ───────── Informe de coaching (informe.html) ─────────
    "DivisionUp — Informe de coaching": "DivisionUp — Coaching report",
    "Marca propia no afiliada a los titulares de los juegos.": "Own brand not affiliated with the games' owners.",
    "Informe de partida": "Match report",
    "← Volver a mis partidas": "← Back to my games",
    "Pregunta a tu coach": "Ask your coach",
    "Pregúntame lo que quieras sobre esta partida. Aquí tienes algunas ideas:":
      "Ask me anything about this game. Here are some ideas:",
    "Escribe tu pregunta…": "Type your question…",
    "Tu pregunta para el coach": "Your question for the coach",
    "Enviar pregunta": "Send question",
    "No se pudo cargar el informe.": "Couldn't load the report.",
    "de 8 jugadores": "of 8 players",
    "1.er puesto": "1st place",
    "Partida": "Game",
    "Análisis generado por DivisionUp IA": "Analysis generated by DivisionUp AI",
    "Foco para tu próxima partida": "Focus for your next game",
    "Mayor": "Major",
    "Menor": "Minor",
    "Qué pasó": "What happened",
    "Por qué te costó": "Why it cost you",
    "Cómo subsanarlo": "How to fix it",
    "El momento": "The moment",
    "Lo que hiciste bien": "What you did well",
    "Errores clave": "Key mistakes",
    "Qué deberías haber hecho": "What you should have done",
    "El ajuste clave": "The key adjustment",
    "Plan de acción": "Action plan",
    "Generando tu informe de coaching…": "Generating your coaching report…",
    "escribiendo…": "typing…",
    "Has cambiado el idioma de la web.": "You changed the site language.",
    "Regenerar el informe en este idioma": "Regenerate the report in this language",
    "¿Por qué perdí la pelea del 4-1?": "Why did I lose the 4-1 fight?",
    "¿Qué augment debí coger?": "Which augment should I have taken?",
    "¿Cómo mejoro mi economía?": "How do I improve my economy?",
    "¿Por qué cedí objetivos?": "Why did I give up objectives?",
    "¿Cómo evito morir en su jungla?": "How do I avoid dying in their jungle?",
    "¿Qué cambio me hace subir?": "What change will help me climb?",

    // ───────── Guía de comp (guia-comp.html) ─────────
    "DivisionUp — Guía de comp (datos de ejemplo)": "DivisionUp — Comp guide (sample data)",
    "Comp, ítems y augments inventados con fines de prototipado. Marca propia no afiliada a los titulares de los juegos.":
      "Comp, items and augments invented for prototyping purposes. Own brand not affiliated with the games' owners.",
    "Guía de comp": "Comp guide",
    "← Volver a la meta": "← Back to the meta",
    "Estilo:": "Style:",
    "Nivel objetivo:": "Target level:",
    "Standard": "Standard",
    "Comp flexible de daño mágico sostenido. Fuerte si empiezas con componentes de maná o poder mágico. Tu colocación del portador decide las peleas.":
      "Flexible sustained-magic-damage comp. Strong if you start with mana or ability-power components. Your carry positioning decides fights.",
    "Coloc. media": "Avg place.",
    "1.º": "1st",
    "Composición final (nivel 9)": "Final composition (level 9)",
    "Cómo jugarla": "How to play it",
    "Variaciones": "Variations",
    "Niveleo": "Leveling",
    "Augments recomendados": "Recommended augments",
    "Posicionamiento recomendado": "Recommended positioning",
    "Juega el tablero más fuerte que tengas y prioriza los ítems del portador (Místico). No fuerces la comp: gana rondas y economía.":
      "Play the strongest board you have and prioritize the carry's items (Mystic). Don't force the comp: win rounds and economy.",
    "Transiciona a la línea mística y sube de nivel con tempo. En 4-1 busca tus 4 costes. Mantén la vida > 50 para subir a 8 seguro y coloca al Místico a salvo.":
      "Transition to the mystic line and level with tempo. At 4-1 look for your 4-costs. Keep your HP > 50 to reach level 8 safely and place the Mystic out of danger.",
    "A nivel 9 añade tus 5 costes y mejora a 2★ tus unidades clave. Ajusta el posicionamiento ronda a ronda según las amenazas.":
      "At level 9 add your 5-costs and upgrade your key units to 2★. Adjust positioning round by round based on threats.",
    "Control:": "Control:",
    "Escalado:": "Scaling:",
    "Tanque:": "Tank:",
    "Etapa 2-1": "Stage 2-1",
    "Etapa 3-2": "Stage 3-2",
    "Etapa 4-1": "Stage 4-1",
    "Etapa 4-5": "Stage 4-5",
    "Etapa 5-1": "Stage 5-1",
    "Tablero fuerte para buscar racha.": "Strong board to chase a win streak.",
    "Nivel 6 con tempo; estabiliza.": "Level 6 with tempo; stabilize.",
    "Primer roll ligero buscando 4 costes.": "First light roll looking for 4-costs.",
    "Rollea por Místico y Centinela.": "Roll for Mystic and Sentinel.",
    "Añade 5 costes y persigue 2★ clave.": "Add 5-costs and chase key 2★.",
    "Bueno": "Good",
    "Situac.": "Situat.",
    "4 costes": "4-costs",
    "3 costes": "3-costs",
    "2 costes": "2-costs",
    "1 coste": "1-cost",
    "Sin ítems prioritarios": "No priority items",

    // ───────── Vocabulario de juego (arquetipos / roles / ítems / augments) ─────────
    "Místico": "Mystic", "Centinela": "Sentinel", "Francotirador": "Sniper", "Vanguardia": "Vanguard",
    "Invocador": "Summoner", "Pistolero": "Gunner", "Hechicero": "Sorcerer", "Guardián": "Guardian",
    "Berserker": "Berserker", "Vidente": "Seer", "Curandera": "Healer", "Mago": "Mage",
    "Tanque principal": "Main tank", "Tanque": "Tank", "Frontline": "Frontline", "Daño mágico": "Magic damage",
    "Sostén": "Sustain", "Portador": "Carry", "Escalado": "Scaling", "Control": "Control",
    "Flex Místicos": "Mystic Flex", "Reroll Vanguardias": "Vanguard Reroll", "Fast 8 Francotiradores": "Fast 8 Snipers",
    "Convergencia Mística": "Mystic Convergence", "Corazón de Cristal": "Crystal Heart",
    "Mente Táctica": "Tactical Mind", "Eco Resonante": "Resonant Echo",
    "Égida del Guardián": "Guardian's Aegis", "Manto Rúnico": "Runic Mantle", "Reloj de Arena": "Hourglass",
    "Báculo Arcano": "Arcane Staff", "Velo Espectral": "Spectral Veil", "Filo de Maná": "Mana Edge",

    // ───────── Lab (lab.html) ─────────
    "Busca un ítem, unidad o augment…": "Search an item, unit or augment…",
    "rápido": "fast",
    "Modo presentación (texto grande para vídeo)": "Presentation mode (large text for video)",
    "Modo captura limpia (oculta la interfaz para grabar)": "Clean capture mode (hides the UI for recording)",
    "Exportar como imagen PNG (o imprimir si no hay conexión)": "Export as PNG image (or print if offline)",
    "Centro de entrenamiento": "Training center",
    "Estudia el juego: simula comps, y consulta winrates de unidades, ítems y augments. Pensado para mirar rápido, incluso en mitad de una partida.":
      "Study the game: simulate comps and check win rates of units, items and augments. Designed for quick lookups, even mid-game.",
    "Cerrar": "Close",
    "Máximo 3 ítems por unidad. Toca para añadir o quitar.": "Max 3 items per unit. Tap to add or remove.",
    "✕ Salir de captura": "✕ Exit capture",
    "DivisionUp — Lab (maqueta de rediseño · datos de ejemplo). Marca propia, no afiliada a los titulares de los juegos.":
      "DivisionUp — Lab (redesign mockup · sample data). Own brand, not affiliated with the games' owners.",
    "Builds": "Builds",
    // Descriptores de unidades
    "Portador mágico": "Magic carry", "Carry físico": "Physical carry", "Frontline reroll": "Frontline reroll",
    "Escalado tardío": "Late scaling", "Carry reroll": "Carry reroll", "Tanque reroll": "Tank reroll",
    "Luchador": "Fighter", "Mid": "Mid", "ADC": "ADC", "Support": "Support", "Mid/Jungla": "Mid/Jungle",
    // Descriptores de ítems
    "Poder mágico": "Ability power", "Robo de vida": "Lifesteal", "Aguante": "Durability", "Utilidad": "Utility",
    "Crítico": "Crit", "Resist. mágica": "Magic resist", "Anti-mágico": "Anti-magic", "Maná": "Mana", "Daño en área": "Area damage",
    // Descriptores de augments
    "Refuerza Místicos": "Boosts Mystics", "Económico-poder": "Econ-power", "Tempo": "Tempo", "Oro por combate": "Gold per combat",
    "Situacional": "Situational", "Tempo de nivel": "Level tempo", "Económico": "Economy", "Reroll agresivo": "Aggressive reroll",
    // Nombres de ítems
    "Filo Voraz": "Voracious Blade", "Guante Letal": "Lethal Glove", "Cota Reforzada": "Reinforced Mail",
    "Tomo Arcano": "Arcane Tome", "Vara Letal": "Lethal Rod", "Lágrima Eterna": "Eternal Tear", "Corona Solar": "Solar Crown",
    "Cetro Abisal": "Abyssal Scepter", "Botas Veloces": "Swift Boots", "Égida de Hierro": "Iron Aegis",
    "Lanza Crepuscular": "Twilight Spear", "Grimorio Prohibido": "Forbidden Grimoire", "Coraza Vital": "Vital Plate", "Daga Veloz": "Swift Dagger",
    // Nombres de augments / sinergias
    "Botín de Guerra": "War Spoils", "Tempo Perfecto": "Perfect Tempo", "Reserva de Oro": "Gold Reserve", "Doble Problema": "Double Trouble",
    "Hiperscaling Magos": "Mage Hyperscaling", "Reroll Pistoleros": "Gunner Reroll",
    // Campeones (LoL)
    "Mago de control": "Control Mage", "Tirador hipercarry": "Hypercarry Marksman", "Luchador de línea": "Lane Fighter",
    "Encantador": "Enchanter", "Asesino": "Assassin", "Tanque iniciador": "Initiator Tank", "Asesino de acceso": "Access Assassin",
    "Bruiser de jungla": "Jungle Bruiser", "Maga de poke": "Poke Mage", "Soporte de enganche": "Hook Support",
    // Filtros (rango / cola)
    "Esmeralda+": "Emerald+", "Diamante+": "Diamond+", "Maestro+": "Master+", "Challenger": "Challenger", "Normal": "Normal",

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

  // API pública (para usar en JS: DivisionUpI18N.t("texto"))
  window.DivisionUpI18N = {
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
