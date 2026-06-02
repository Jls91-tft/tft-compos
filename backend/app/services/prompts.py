"""Prompts del coach + extracción de datos de partida + parseo del informe.

Aquí vive la "voz" del coach y la traducción de los datos crudos de Riot a un
resumen que la IA pueda analizar. Centralizarlo facilita iterar la calidad del
coaching sin tocar el resto del backend.
"""
import json
from app.schemas.models import CoachingReport, ImprovementPlan

PROMPT_VERSION = "report-v2.6-motor70b-2026-06"   # sube esto al mejorar el prompt/motor → invalida cachés
PLAN_PROMPT_VERSION = "plan-v3.1-motor70b-2026-06"

# --- Voz del coach (system prompt) ---
COACH_SYSTEM = (
    "Eres Synapse, un analista de TFT y League of Legends de nivel Challenger. Tu coaching "
    "es exigente, específico y honesto: señalas exactamente qué costó posiciones y cómo "
    "subir, como el coach de un jugador profesional. Hablas en español, directo y sin paja.\n"
    "REGLAS INNEGOCIABLES:\n"
    "1. Cada observación DEBE apoyarse en un dato concreto de la partida: nombres de unidades, "
    "rasgos y su nivel, aumentos, ítems concretos, número de ronda, oro, nivel del jugador. "
    "Cita el dato literalmente (p. ej. 'tu carry X estaba a 1 estrella sin ítems en la ronda 4-2').\n"
    "2. PROHIBIDO el consejo genérico vacío ('gestiona mejor tus recursos', 'planifica tu "
    "estrategia', 'mejora tu economía', 'adáptate al meta') si no va acompañado de un dato y una "
    "acción medible (umbral de oro, nivel objetivo en una ronda concreta, ítem o unidad concreta).\n"
    "3. Sé crítico aunque la colocación sea buena: identifica qué separó esta partida del Top 1.\n"
    "4. NUNCA inventes datos que no estén en la información; si un dato no aparece, no lo menciones. "
    "Razona como si cada puesto valiera LP."
)
COACH_SYSTEM_EN = (
    "You are Synapse, a Challenger-level TFT and League of Legends analyst. Your coaching is "
    "demanding, specific and honest: you pinpoint exactly what cost placements and how to climb, "
    "like a pro player's coach. You speak English, direct and with no filler.\n"
    "NON-NEGOTIABLE RULES:\n"
    "1. Every observation MUST be backed by concrete match data: unit names, traits and their tier, "
    "augments, specific items, round number, gold, player level. Quote the data literally (e.g. "
    "'your carry X was 1-star with no items at round 4-2').\n"
    "2. FORBIDDEN: empty generic advice ('manage your resources', 'plan your strategy', 'improve "
    "your economy', 'adapt to the meta') unless paired with a data point and a measurable action "
    "(gold threshold, target level on a specific round, a specific item or unit).\n"
    "3. Be critical even when the placement is good: identify what separated this game from 1st.\n"
    "4. NEVER make up data that isn't in the match information; if a value is missing, don't mention "
    "it. Reason as if every placement were worth LP."
)


def system_for(lang: str = "es") -> str:
    """Devuelve el system prompt del coach según idioma (es por defecto)."""
    return COACH_SYSTEM_EN if lang == "en" else COACH_SYSTEM

_ROLE_ES = {"TOP": "Top", "JUNGLE": "Jungla", "MIDDLE": "Mid", "BOTTOM": "ADC", "UTILITY": "Support"}


# ----------------------------- Extracción de datos -----------------------------
def extract_summary(game: str, match: dict, puuid: str) -> dict:
    return _tft_summary(match, puuid) if game == "tft" else _lol_summary(match, puuid)


def _lol_summary(match: dict, puuid: str) -> dict:
    info = match["info"]
    me = next(p for p in info["participants"] if p.get("puuid") == puuid)
    team = next((t for t in info.get("teams", []) if t.get("teamId") == me.get("teamId")), {})
    obj = team.get("objectives", {})
    dur = info.get("gameDuration", 0) or 0
    cs = me.get("totalMinionsKilled", 0) + me.get("neutralMinionsKilled", 0)
    return {
        "juego": "LoL",
        "resultado": "Victoria" if me.get("win") else "Derrota",
        "rol": _ROLE_ES.get(me.get("teamPosition", ""), me.get("teamPosition")),
        "campeon": me.get("championName"),
        "kda": f"{me.get('kills', 0)}/{me.get('deaths', 0)}/{me.get('assists', 0)}",
        "cs": cs,
        "cs_por_min": round(cs / (dur / 60), 1) if dur else 0,
        "oro": me.get("goldEarned"),
        "daño_a_campeones": me.get("totalDamageDealtToChampions"),
        "vision_score": me.get("visionScore"),
        "duracion_min": round(dur / 60, 1),
        "objetivos_equipo": {
            "dragones": obj.get("dragon", {}).get("kills"),
            "heraldos": obj.get("riftHerald", {}).get("kills"),
            "barones": obj.get("baron", {}).get("kills"),
            "torres": obj.get("tower", {}).get("kills"),
        },
    }


_TRAIT_STYLE_ES = {1: "bronce", 2: "plata", 3: "oro", 4: "prismático", 5: "prismático"}


def _clean_id(raw: str) -> str:
    """Limpia un id de Riot (TFT11_Augment_FooBar / TFT_Item_Baz) a su parte legible."""
    return (raw or "").split("_")[-1]


# Clasificación de ítems para detectar al carry REAL (no la unidad con más ítems).
# Nombres ya "limpios" (sin TFT_Item_) y en minúscula. Los ítems completos base son
# bastante estables entre sets; puede necesitar un repaso al cambiar de set.
_DAMAGE_ITEMS = frozenset({
    "infinityedge", "deathblade", "giantslayer", "lastwhisper", "runaanshurricane",
    "rapidfirecannon", "statikkshiv", "guinsoosrageblade", "rabadonsdeathcap",
    "jeweledgauntlet", "hextechgunblade", "spearofshojin", "archangelsstaff",
    "bluebuff", "nashorstooth", "bloodthirster", "morellonomicon", "redbuff",
    "titansresolve", "handofjustice", "voidstaff", "deathfiregrasp", "kraken",
})
_TANK_ITEMS = frozenset({
    "warmogsarmor", "bramblevest", "dragonsclaw", "gargoylestoneplate",
    "frozenheart", "crownguard", "sunfirecape", "redemption", "protectorsvow",
    "steadfastheart", "spectralgauntlet", "evenshroud", "adaptivehelm",
    "ionicspark", "guardianangel", "edgeofnight", "quicksilver",
})


def _damage_items(items: list) -> int:
    return sum(1 for it in items if (it or "").lower() in _DAMAGE_ITEMS)


def _pick_carry(units: list) -> dict | None:
    """El carry es la unidad con más ítems de DAÑO (desempate: estrellas, nº ítems).

    Si ninguna unidad lleva ítems de daño no afirmamos un carry (devolvemos None):
    eso es en sí un hallazgo (ítems repartidos o sin carry de daño claro), no un
    pretexto para etiquetar a un tanque como carry por llevar muchos ítems.
    """
    best = max(
        units,
        key=lambda u: (_damage_items(u["items"]), u["estrellas"] or 0, len(u["items"])),
        default=None,
    )
    return best if best and _damage_items(best["items"]) > 0 else None


def _tft_summary(match: dict, puuid: str) -> dict:
    info = match["info"]
    me = next(p for p in info["participants"] if p.get("puuid") == puuid)
    traits = [
        {
            "rasgo": _clean_id(t.get("name")),
            "unidades": t.get("num_units"),
            "nivel": _TRAIT_STYLE_ES.get(t.get("style"), t.get("style")),
        }
        for t in me.get("traits", []) if t.get("tier_current", 0) > 0
    ]
    units = [
        {
            "unidad": _clean_id(u.get("character_id")),
            "estrellas": u.get("tier"),
            "items": [_clean_id(n) for n in (u.get("itemNames") or [])],
        }
        for u in me.get("units", [])
    ]
    # Carry real: la unidad con ítems de daño (ver _pick_carry). Puede ser None.
    carry = _pick_carry(units)
    return {
        "juego": "TFT",
        "colocacion": me.get("placement"),
        "nivel": me.get("level"),
        "ultima_ronda": me.get("last_round"),
        "oro_sobrante": me.get("gold_left"),
        "jugadores_eliminados": me.get("players_eliminated"),
        "daño_a_jugadores": me.get("total_damage_to_players"),
        "aumentos": [_clean_id(a) for a in me.get("augments", [])],
        "rasgos_activos": traits,
        "unidades": units,
        "carry_principal": carry,
        "duracion_min": round((info.get("game_length", 0) or 0) / 60, 1),
    }


# ----------------------------- Construcción de prompts -----------------------------
# Dimensiones que el modelo PUEDE mirar: no es un checklist obligatorio, es un mapa
# para que el análisis sea específico sin forzar hallazgos donde no los hay.
_RUBRIC_TFT_ES = (
    "Tu trabajo es encontrar el motivo REAL de esta colocación, no rellenar una plantilla. Examina "
    "los datos y comenta SOLO las dimensiones donde haya un problema o un acierto de verdad; ignora "
    "las demás y NUNCA fabriques un error para cumplir una cuota. Dimensiones que puedes considerar: "
    "itemización de la carry_principal (¿sus 3 ítems de daño completos?, ¿ítems de daño desperdiciados "
    "en la unidad equivocada?; si carry_principal es null, ninguna unidad llevaba ítems de daño, eso sí "
    "es un fallo real); el rol de cada unidad lo definen sus ÍTEMS, jamás trates a un tanque como "
    "carry; estrellas de las unidades clave frente a su rareza; el nivel alcanzado según el arquetipo "
    "(fast 8 vs reroll); el encaje de los aumentos con la comp; los breakpoints de los rasgos. "
    "LÍMITES DE LOS DATOS (respétalos): el oro_sobrante es el del FINAL de la partida; terminar con "
    "poco oro es NORMAL y correcto (al cerrar o al morir se gasta todo rolando o subiendo nivel) y NO "
    "es un fallo de economía. No tienes el oro ni el tablero ronda a ronda, así que NO juzgues la "
    "gestión de economía intra-partida ni el posicionamiento exacto a partir del estado final."
)
_RUBRIC_LOL_ES = (
    "EVALÚA específicamente (cita los datos): cs_por_min frente al estándar del rol, el KDA y el "
    "daño_a_campeones, el vision_score, y la participación en objetivos_equipo."
)
_RUBRIC_TFT_EN = (
    "Your job is to find the REAL reason for this placement, not to fill a template. Look at the data "
    "and comment ONLY on the dimensions where there is a genuine problem or strength; ignore the rest "
    "and NEVER fabricate an error to meet a quota. Dimensions you may consider: carry_principal's "
    "itemization (3 complete damage items?, damage items wasted on the wrong unit?; if carry_principal "
    "is null, no unit had damage items, that is a real flaw); a unit's role is defined by its ITEMS, "
    "never treat a tank as a carry; key units' star levels vs rarity; the level reached given the "
    "archetype (fast 8 vs reroll); how augments fit the comp; trait breakpoints. DATA LIMITS (respect "
    "them): leftover gold is the FINAL value; finishing with little gold is NORMAL and correct (when "
    "closing or dying you spend it all rolling or leveling) and is NOT an economy mistake. You do not "
    "have per-round gold or board state, so do NOT judge in-game economy management or exact "
    "positioning from the final state."
)

# Fundamentos duraderos del juego: conceptos que casi no cambian entre parches.
# Sin nombres de campeones/rasgos concretos (eso cambia por set y no es fiable).
_FUNDAMENTOS_TFT_ES = (
    "FUNDAMENTOS DE TFT (aplícalos al juzgar; no los recites literalmente):\n"
    "- ECONOMÍA: ganas interés por cada 10 de oro guardado, hasta un máximo de 50 (5 de interés). "
    "Mantener 50 maximiza el ingreso; bajar de 50 solo se justifica para estabilizar la vida o cerrar. "
    "OJO: el oro que ves es el del FINAL de la partida, no refleja la economía intra-partida; acabar "
    "con poco oro es normal (al cerrar o morir se gasta todo) y NO es un error.\n"
    "- NIVEL Y TEMPO: subir de nivel NO es bueno por sí mismo, depende del arquetipo. 'Fast 8' sube "
    "rápido a nivel 8 para acceder a unidades de 4 coste; las comps 'reroll' se quedan en nivel 6-7 "
    "farmeando estrellas de 1-2 costes. El nivel 9 es para 5 costes y el 10 es raro y casi nunca "
    "decisivo. No recomiendes 'subir más nivel' sin justificarlo con el arquetipo.\n"
    "- ÍTEMS: concentra los ítems de DAÑO en UNA sola carry; repartirlos es un error grave. Los "
    "tanques llevan ítems de resistencia/utilidad. Una carry sin sus 3 ítems completos rinde muy poco. "
    "El rol de una unidad lo definen sus ÍTEMS, no cuántos lleva: un tanque con 3 ítems defensivos "
    "sigue siendo tanque.\n"
    "- RASGOS: un breakpoint alto activo vale más que muchos rasgos a nivel bajo; activar un rasgo "
    "flojo 'porque sí' rara vez aporta.\n"
    "- POSICIONAMIENTO Y VIDA: la carry va protegida detrás y los tanques delante; perder rondas a "
    "propósito (lose streak) para guardar oro e interés es una jugada válida, no siempre un error."
)
_FUNDAMENTOS_TFT_EN = (
    "TFT FUNDAMENTALS (apply them when judging; don't recite verbatim):\n"
    "- ECONOMY: you earn interest per 10 gold banked, capped at 50 (5 interest). Holding 50 maximizes "
    "income; dropping below 50 is only justified to stabilize health or to close out the game. NOTE: "
    "the gold you see is the FINAL value, it does not reflect in-game economy; finishing with little "
    "gold is normal (when closing or dying you spend it all) and is NOT a mistake.\n"
    "- LEVEL & TEMPO: leveling up is NOT good per se, it depends on the archetype. 'Fast 8' levels "
    "quickly to 8 for 4-cost units; 'reroll' comps stay at level 6-7 farming 1-2 cost star-ups. Level "
    "9 is for 5-costs and level 10 is rare and almost never decisive. Don't recommend 'level more' "
    "without justifying it by archetype.\n"
    "- ITEMS: stack DAMAGE items on ONE carry; spreading them is a major error. Tanks carry "
    "resist/utility items. A carry without its 3 complete items underperforms badly. A unit's role is "
    "defined by its ITEMS, not how many it holds: a tank with 3 defensive items is still a tank.\n"
    "- TRAITS: one high active breakpoint beats many low-tier traits; activating a weak trait 'just "
    "because' rarely helps.\n"
    "- POSITIONING & HEALTH: the carry stays protected at the back, tanks at the front; intentionally "
    "losing rounds (lose streak) to bank gold and interest is a valid play, not always a mistake."
)
_RUBRIC_LOL_EN = (
    "ASSESS specifically (cite the data): cs per minute vs the role standard, the KDA and damage to "
    "champions, the vision score, and team objective participation."
)


def build_report_prompt(game: str, summary: dict, lang: str = "es") -> str:
    datos = json.dumps(summary, ensure_ascii=False, indent=2)
    structure = """{
  "verdict": "1-2 frases citando el dato que definió la partida (no genérico)",
  "focus": "1 frase: la palanca #1 para subir, con dato y acción medible",
  "metrics": [{"value": "valor", "label": "qué mide", "status": "good|warn|bad", "benchmark": "referencia objetiva"}],
  "did_well": ["2 o 3 aciertos concretos, cada uno con su dato"],
  "errors": [{"title": "título concreto", "severity": "major|minor", "what": "qué pasó (con el dato exacto: unidad/ítem/ronda/oro)", "why": "por qué te costó la posición", "fix": "acción concreta y medible", "when": "la ronda o momento exacto"}],
  "corrective": "un párrafo con el ajuste clave, anclado a lo que pasó en ESTA partida",
  "action_plan": ["3 o 4 pasos accionables y medibles para la próxima partida"]
}"""
    rubric = _RUBRIC_TFT_ES if game == "tft" else _RUBRIC_LOL_ES
    rubric_en = _RUBRIC_TFT_EN if game == "tft" else _RUBRIC_LOL_EN
    fundamentos = (_FUNDAMENTOS_TFT_ES + "\n\n") if game == "tft" else ""
    fundamentals_en = (_FUNDAMENTOS_TFT_EN + "\n\n") if game == "tft" else ""
    if lang == "en":
        return f"""Analyze this match like a Challenger coach and produce a demanding coaching report.

{fundamentals_en}MATCH DATA:
{datos}

{rubric_en}

Return ONLY valid JSON with this EXACT structure. Keep the keys exactly as shown, write ALL text values in English:
{structure}

RULES: Use ONLY the data above; never invent or pad. Every claim must quote a concrete data value. NO generic filler. Quality over quantity: include 2 to 5 metrics that actually matter and 0 to 3 REAL errors; if the game was clean it is correct to list no major errors and instead name the fine detail that separated it from 1st. Never fabricate a problem to fill a slot."""
    return f"""Analiza esta partida como un coach de Challenger y genera un informe de coaching exigente.

{fundamentos}DATOS DE LA PARTIDA:
{datos}

{rubric}

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura exacta (todos los textos en español):
{structure}

REGLAS: Usa SOLO los datos de arriba; nunca inventes ni rellenes. Cada afirmación debe citar un dato concreto. PROHIBIDO el relleno genérico. Calidad sobre cantidad: incluye 2 a 5 métricas que de verdad importen y entre 0 y 3 errores REALES; si la partida fue limpia es correcto no listar errores mayores y centrarte en el matiz fino que la separó del puesto 1. No fabriques un problema para rellenar un hueco."""


def build_chat_prompt(game: str, summary: dict, question: str, lang: str = "es") -> str:
    datos = json.dumps(summary, ensure_ascii=False)
    if lang == "en":
        return (
            f"Match context ({game.upper()}): {datos}\n\n"
            f"Player question: {question}\n\n"
            "Answer in 2-4 sentences, concrete and actionable, using only the context. Reply in English."
        )
    return (
        f"Contexto de la partida ({game.upper()}): {datos}\n\n"
        f"Pregunta del jugador: {question}\n\n"
        "Responde en 2-4 frases, concreto y accionable, usando solo el contexto."
    )


# ----------------------------- Parseo del informe -----------------------------
def _fallback_report(raw: str, game: str, match_id: str) -> CoachingReport:
    return CoachingReport(
        game=game, match_id=match_id,
        verdict=(raw or "").strip()[:600] or "No se pudo generar el análisis esta vez.",
        focus="", metrics=[], did_well=[], errors=[], corrective="", action_plan=[],
    )


def parse_report(raw: str, game: str, match_id: str) -> CoachingReport:
    """Convierte la respuesta JSON de la IA en un CoachingReport validado.

    La IA a veces se desvía del schema (p. ej. devuelve números donde se espera
    texto, u omite campos). Normalizamos antes de validar para conservar el
    informe estructurado; solo si todo falla volcamos un fallback elegante.
    """
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("la respuesta de la IA no es un objeto JSON")
    except Exception:
        return _fallback_report(raw, game, match_id)

    data["game"] = game
    data["match_id"] = match_id

    # La IA suele mandar números (p. ej. la colocación) donde el schema pide texto.
    norm_metrics = []
    for m in data.get("metrics") or []:
        if not isinstance(m, dict):
            continue
        if m.get("value") is not None:
            m["value"] = str(m["value"])
        if m.get("benchmark") is not None:
            m["benchmark"] = str(m["benchmark"])
        norm_metrics.append(m)
    data["metrics"] = norm_metrics

    for k in ("verdict", "focus", "corrective"):
        data.setdefault(k, "")
    for k in ("did_well", "action_plan", "errors"):
        data.setdefault(k, [])

    try:
        return CoachingReport(**data)
    except Exception:
        # Reintento tolerante: si los 'errors' vienen mal formados, descártalos
        # antes que perder todo el informe.
        try:
            data["errors"] = []
            return CoachingReport(**data)
        except Exception:
            return _fallback_report(raw, game, match_id)


# ====================== Plan de mejora global (multi-partida) ======================
PLAN_SYSTEM = (
    "Eres Synapse, coach de élite de TFT y League of Legends. Sintetizas patrones a partir de los "
    "hallazgos de varias partidas YA analizadas. No inventas: solo agregas lo que viene en los datos. "
    "Eres concreto y exigente. Devuelves SIEMPRE JSON válido conforme al esquema y NADA más."
)
PLAN_SYSTEM_EN = (
    "You are Synapse, an elite TFT and League of Legends coach. You synthesize patterns from the findings "
    "of several already-analyzed matches. You do not invent: you only aggregate what the data shows. "
    "Concrete and demanding. You ALWAYS reply with valid JSON per the schema and NOTHING else."
)


def system_plan(lang: str = "es") -> str:
    return PLAN_SYSTEM_EN if lang == "en" else PLAN_SYSTEM


def build_plan_prompt(game: str, aggregate: dict, lang: str = "es") -> str:
    payload = json.dumps(aggregate, ensure_ascii=False, indent=2)
    schema = (
        '{\n'
        '  "summary": "diagnóstico global en 1-2 frases",\n'
        '  "recurring_weaknesses": [{"title": "...", "frequency_pct": 40, "avg_severity": 1.6, "evidence": "en cuántas de las N partidas aparece"}],\n'
        '  "root_causes": ["hipótesis de causa raíz"],\n'
        '  "roadmap": {"this_week": [{"focus": "...", "drills": ["..."], "resource": "qué practicar/modo/oponente", "success_metric": "medible"}], "this_month": [], "next_3_months": []},\n'
        '  "priority_order": ["por qué empezar por X antes que por Y"]\n'
        '}'
    )
    n = aggregate.get("n_matches", 0)
    if lang == "en":
        return (f"AGGREGATED findings from the player's last {n} ALREADY-ANALYZED matches:\n{payload}\n\n"
                f"These are PATTERNS across matches, not one game — one match's variance is NOT a pattern. Rules: in "
                f"recurring_weaknesses include ONLY themes that repeat in >=30% of matches. CLUSTER findings of the same "
                f"theme even if worded differently across the 'partidas' list; frequency_pct = in how many of the {n} matches "
                f"the theme appears (count them, don't invent). root_causes connects the weaknesses into a hypothesis "
                f"(e.g. 'midgame passivity -> you don't read tempo'). roadmap in 3 horizons, each item with concrete drills, "
                f"a resource (what to practice, in which mode, vs whom) and a MEASURABLE success metric. priority_order "
                f"explains why to start with X before Y. With only {n} matches the plan is PRELIMINARY: say so and don't "
                f"overstate. Nothing generic; if the data doesn't support a pattern, don't invent it.\n"
                f"Return ONLY valid JSON with these keys (English):\n{schema}")
    return (f"Hallazgos AGREGADOS de las últimas {n} partidas YA analizadas del jugador:\n{payload}\n\n"
            f"Esto son PATRONES de varias partidas, no una sola — la varianza de UNA partida NO es un patrón. Reglas: en "
            f"recurring_weaknesses incluye SOLO temas que se repiten en >=30% de las partidas. AGRUPA los hallazgos del mismo "
            f"tema aunque estén redactados distinto a lo largo de la lista 'partidas'; frequency_pct = en cuántas de las {n} "
            f"partidas aparece el tema (cuéntalas, no lo inventes). root_causes conecta las debilidades en una hipótesis (p. ej. "
            f"«pasividad en midgame → no lees el tempo»). roadmap en 3 horizontes, cada ítem con drills concretos, un recurso "
            f"(qué practicar, en qué modo, contra quién) y una métrica de éxito MEDIBLE. priority_order explica por qué "
            f"empezar por X antes que por Y. Con solo {n} partidas el plan es PRELIMINAR: dilo y no exageres. Nada genérico; "
            f"si el dato no soporta un patrón, no lo inventes.\n"
            f"Devuelve EXCLUSIVAMENTE un JSON válido con estas claves (en español):\n{schema}")


def validate_plan(raw: str, base: dict) -> ImprovementPlan:
    """Valida el JSON del plan global. Lanza si no valida (para reintento)."""
    data = json.loads(raw)
    data.update(base)              # game, based_on_match_ids, new_matches
    return ImprovementPlan(**data)


# ====================== Informe ESTRUCTURADO v2 (anclado a evidencia) ======================
REPORT_SYSTEM = (
    "Eres Synapse, analista de TFT y League of Legends de nivel Challenger. Exigente, específico y honesto. "
    "Hablas español, directo y sin paja.\n"
    "REGLAS INNEGOCIABLES:\n"
    "1. CADA hallazgo se apoya en un dato concreto del payload (unidad, rasgo y su nivel, augment, ítem, ronda, "
    "oro, nivel o un timestamp). El campo 'evidence' es una FRASE BREVE y CLARA en lenguaje natural que nombra ese dato y su valor "
    "(p. ej. «terminaste sin augments» o «tu carry Fizz no llevaba ítems de daño»); PROHIBIDO copiar el JSON crudo o nombres de campos "
    "como 'aumentos: []' o 'unidades: [...]'. Sin evidencia clara → no incluyas el hallazgo. Un campo vacío puede significar que ese "
    "dato no existe en este modo: no lo conviertas en error sin más.\n"
    "2. PROHIBIDO el consejo genérico ('mejora tu visión', 'gestiona recursos') si no va con un dato y una acción medible.\n"
    "3. El rol de una unidad lo definen sus ÍTEMS: nunca trates a un tanque como carry. En TFT el carry es la unidad "
    "con ítems de daño; si ninguna los lleva, ESO es el hallazgo.\n"
    "4. El oro_sobrante es el del FINAL de la partida: terminar con poco oro es NORMAL y no es un fallo de economía.\n"
    "5. Sé crítico aunque la colocación sea buena: di qué la separó del 1.º. No fabriques errores para rellenar; listas vacías son válidas.\n"
    "6. decision_errors, macro_issues y mechanical_issues deben ser hallazgos DISTINTOS: NUNCA repitas el mismo problema "
    "en varias secciones. Si solo hay un problema real, repórtalo UNA vez en la sección que mejor encaje y deja vacías las "
    "demás. Profundidad sobre rellenar secciones.\n"
    "7. 'summary' explica la CAUSA RAÍZ de la colocación como cadena causal con datos reales (p. ej. «subiste a nivel 9 con "
    "4 de oro pero tu carry seguía a 1★: llegaste tarde y sin daño»). 'top_3_actionable' va ordenado por impacto: el primero "
    "es la palanca #1, la que más habría cambiado el resultado.\n"
    "Devuelves SIEMPRE JSON válido conforme al esquema pedido y NADA más."
)
REPORT_SYSTEM_EN = (
    "You are Synapse, a Challenger-level TFT and League of Legends analyst. Demanding, specific and honest. "
    "You speak English, direct and with no filler.\n"
    "NON-NEGOTIABLE RULES:\n"
    "1. EVERY finding is backed by a concrete data point from the payload (unit, trait and its tier, augment, item, "
    "round, gold, level or a timeline timestamp). The 'evidence' field is a SHORT, CLEAR natural-language phrase naming that data and "
    "its value (e.g. 'you finished with no augments' or 'your carry Fizz had no damage items'); FORBIDDEN: copying raw JSON or field "
    "names like 'augments: []'. No clear evidence → don't include the finding. An empty field may mean that data doesn't exist in this "
    "mode: don't turn it into a mistake on its own.\n"
    "2. FORBIDDEN: generic advice ('improve your vision', 'manage resources') without a data point and a measurable action.\n"
    "3. A unit's role is defined by its ITEMS: never treat a tank as a carry. In TFT the carry is the unit with damage "
    "items; if none carry them, THAT is the finding.\n"
    "4. leftover gold is the END-of-game value: finishing with little gold is NORMAL, not an economy mistake.\n"
    "5. Be critical even if the placement is good: say what separated it from 1st. Don't fabricate errors; empty lists are fine.\n"
    "6. decision_errors, macro_issues and mechanical_issues must be DISTINCT findings: NEVER repeat the same problem across "
    "sections. If there's only one real problem, report it ONCE in the section that fits best and leave the others empty. "
    "Depth over filling sections.\n"
    "7. 'summary' explains the ROOT CAUSE of the placement as a causal chain with real data (e.g. 'you leveled to 9 with 4 "
    "gold but your carry was still 1-star: you arrived late and without damage'). 'top_3_actionable' is ordered by impact: "
    "the first is the #1 lever, the one that would have changed the result most.\n"
    "You ALWAYS reply with valid JSON matching the requested schema and NOTHING else."
)


def system_report(lang: str = "es") -> str:
    return REPORT_SYSTEM_EN if lang == "en" else REPORT_SYSTEM


def build_report_prompt_v2(game: str, payload: dict, lang: str = "es") -> str:
    datos = json.dumps(payload, ensure_ascii=False, indent=2)
    schema = (
        '{\n'
        '  "summary": "1-2 frases: qué definió la partida (anclado a datos)",\n'
        '  "decision_errors": [{"timestamp": "min:seg solo en LoL; null en TFT", "phase": "early|mid|late", "what_happened": "...", "why_wrong": "...", "better_action": "...", "severity": 4, "evidence": "frase breve y clara con el dato; NO copies el JSON ni nombres de campos"}],\n'
        '  "mechanical_issues": [{"title": "...", "detail": "cs/trades/skillshots/cooldowns/itemización", "evidence": "frase clara con el dato", "severity": 3}],\n'
        '  "macro_issues": [{"title": "...", "detail": "rotaciones/visión/objetivos/tempo/nivel", "evidence": "frase clara con el dato o momento", "severity": 3}],\n'
        '  "mental_patterns": [{"pattern": "tilt|sobreextensión|pasividad", "detail": "...", "evidence": "solo si los datos lo soportan"}],\n'
        '  "top_3_actionable": ["3 cosas concretas a entrenar esta semana"]\n'
        '}'
    )
    es = lang != "en"
    rubric = (_RUBRIC_TFT_ES if es else _RUBRIC_TFT_EN) if game == "tft" else (_RUBRIC_LOL_ES if es else _RUBRIC_LOL_EN)
    blocks = [rubric]
    if game == "tft":
        blocks.append(_FUNDAMENTOS_TFT_ES if es else _FUNDAMENTOS_TFT_EN)
        blocks.append(
            "DATOS DISPONIBLES EN TFT: SOLO el ESTADO FINAL (tablero, ítems finales, rasgos, augments, colocación, "
            "nivel, última ronda, oro final). NO tienes historial por rondas. Por tanto: NUNCA inventes etapas ni "
            "rondas ('4-1', '6-1') ni afirmes CUÁNDO conseguiste una unidad o un ítem (que una unidad tenga o no "
            "ítems es el estado final, no un evento con hora). En 'timestamp' pon null. Los augments SOLO existen en "
            "2-1, 3-2 y 4-2; si 'aumentos' está vacío puede ser un modo sin augments — NO es un fallo. Ancla cada "
            "hallazgo a un hecho VERIFICABLE del tablero final (unidad y sus estrellas/ítems, rasgo y su nivel, "
            "augments, nivel frente al arquetipo). Tienes un bloque 'señales' con hechos YA CALCULADOS (reparto de ítems "
            "de daño, estrellas, huecos de tablero, carry detectado): ÚSALO para ser concreto. "
            "REGLA DE VARIANZA (clave): NO tienes datos de tienda, oro gastado ni rivales, así que NO puedes saber si una "
            "unidad quedó a 1★ por no rolar o porque NO salió o estaba contestada. Si el oro_final es bajo y el nivel alto, "
            "el jugador SÍ gastó recursos rolando/subiendo: NUNCA le acuses de 'no priorizar' ni de 'pasividad'. Una carry "
            "clave a 1★ con poco oro final suele ser VARIANZA o unidad contestada, NO un error de decisión; en ese caso da "
            "la lección de FUTURO (cuándo cortar pérdidas y estabilizar, transición alternativa, no sobre-rolar a nivel 9), "
            "no un reproche. "
            "LOBBY (úsalo SIEMPRE): 'unidades_contestadas' dice cuántos rivales jugaban tus mismas unidades — si tu carry "
            "estaba contestada por 2 o más, ESA es la causa real de que no subiera de estrellas, y el aprendizaje es "
            "reconocer el contest pronto y pivotar. 'ganador' es la comp del 1.º: compárate (nivel, carry y sus estrellas, "
            "rasgos) y di en concreto qué hizo distinto que tú no."
            if es else
            "DATA AVAILABLE IN TFT: ONLY the FINAL state (board, final items, traits, augments, placement, level, "
            "last round, final gold). You have NO per-round history. Therefore: NEVER invent stages or rounds "
            "('4-1', '6-1') nor claim WHEN you got a unit or item (whether a unit has items is the final state, not "
            "a timed event). Set 'timestamp' to null. Augments ONLY exist at 2-1, 3-2 and 4-2; if 'augments' is empty "
            "it may be a no-augment mode — NOT a mistake. Anchor every finding to a VERIFIABLE fact of the final board "
            "(unit and its stars/items, trait and its tier, augments, level vs archetype). You have a 'señales' block with "
            "PRECOMPUTED facts (damage-item spread, stars, empty board slots, detected carry): USE IT to be concrete. "
            "VARIANCE RULE (key): you have NO shop/gold-spent/opponent data, so you CANNOT know if a unit stayed 1-star "
            "because the player didn't roll or because it didn't show up / was contested. If final gold is low and level is "
            "high, the player DID spend resources rolling/leveling: NEVER accuse them of 'not prioritizing' or 'passivity'. "
            "A key carry at 1-star with low final gold is usually VARIANCE or a contested unit, NOT a decision error; give "
            "the FORWARD lesson (when to cut losses and stabilize, alternative transition, don't over-roll to level 9), not "
            "a reproach. "
            "LOBBY (always use it): 'unidades_contestadas' tells how many opponents fielded your same units — if your carry "
            "was contested by 2+, THAT is the real reason it didn't star up, and the lesson is to recognize the contest early "
            "and pivot. 'ganador' is the 1st-place comp: compare yourself (level, carry and its stars, traits) and say "
            "specifically what they did differently that you didn't.")
    else:
        blocks.append(
            "DATOS EN LoL: tienes el resumen + la línea temporal (muertes con timestamp y fase). Usa esos timestamps "
            "REALES para anclar la evidencia; no inventes momentos que no estén en los datos."
            if es else
            "DATA IN LoL: you have the summary + the timeline (deaths with timestamp and phase). Use those REAL "
            "timestamps to anchor evidence; don't invent moments not present in the data.")
    guide = "\n\n".join(blocks)
    if not es:
        return (f"Analyze THIS match and produce DEEP, specific coaching grounded ONLY in the data below.\n\n"
                f"MATCH DATA:\n{datos}\n\n{guide}\n\n"
                f"Name the REAL units/traits/items/values from the data. If you can't point to a concrete, verifiable "
                f"flaw, say the game was solid and name the single factor that kept it from a better placement. "
                f"Return ONLY valid JSON with EXACTLY these keys (values in English):\n{schema}")
    return (f"Analiza ESTA partida y genera un coaching PROFUNDO y concreto, basado SOLO en los datos de abajo.\n\n"
            f"DATOS DE LA PARTIDA:\n{datos}\n\n{guide}\n\n"
            f"Menciona las unidades/rasgos/ítems/valores REALES de los datos. Si no puedes señalar un fallo concreto "
            f"y verificable, di que la partida fue sólida y nombra el único factor que la separó de una mejor "
            f"colocación. Devuelve EXCLUSIVAMENTE un JSON válido con EXACTAMENTE estas claves (textos en español):\n{schema}")


def validate_report(raw: str, base: dict) -> CoachingReport:
    """Valida el JSON del informe v2 contra el schema. Lanza si no valida (para reintento)."""
    data = json.loads(raw)
    data.update(base)              # game, match_id, metrics (servidor)
    return CoachingReport(**data)
