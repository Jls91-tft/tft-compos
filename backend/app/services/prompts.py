"""Prompts del coach + extracción de datos de partida + parseo del informe.

Aquí vive la "voz" del coach y la traducción de los datos crudos de Riot a un
resumen que la IA pueda analizar. Centralizarlo facilita iterar la calidad del
coaching sin tocar el resto del backend.
"""
import json
from app.schemas.models import CoachingReport

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
    # Carry probable: la que más ítems lleva (desempate por estrellas).
    carry = max(units, key=lambda x: (len(x["items"]), x["estrellas"] or 0), default=None)
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
        "carry_principal": carry["unidad"] if carry else None,
        "duracion_min": round((info.get("game_length", 0) or 0) / 60, 1),
    }


# ----------------------------- Construcción de prompts -----------------------------
# Rúbrica de qué mirar en cada juego: empuja al modelo a un análisis específico.
_RUBRIC_TFT_ES = (
    "EVALÚA específicamente (cita los datos): la itemización de tu carry_principal (¿ítems "
    "completos y correctos para esa unidad?, ¿ítems repartidos en unidades equivocadas?); las "
    "estrellas de las unidades clave frente a su rareza; el nivel del jugador para la última_ronda "
    "alcanzada (tempo de subida/economía); el encaje de los aumentos con la comp final; la fuerza y "
    "nivel de los rasgos_activos (¿breakpoints desperdiciados?); y el oro_sobrante al final."
)
_RUBRIC_LOL_ES = (
    "EVALÚA específicamente (cita los datos): cs_por_min frente al estándar del rol, el KDA y el "
    "daño_a_campeones, el vision_score, y la participación en objetivos_equipo."
)
_RUBRIC_TFT_EN = (
    "ASSESS specifically (cite the data): your carry_principal's itemization (complete/correct items "
    "for that unit?, items wasted on the wrong units?); key units' star levels vs their rarity; the "
    "player level for the last_round reached (econ/leveling tempo); how the augments fit the final "
    "comp; the strength and tier of active traits (wasted breakpoints?); and leftover gold."
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
    if lang == "en":
        return f"""Analyze this match like a Challenger coach and produce a demanding coaching report.

MATCH DATA:
{datos}

{rubric_en}

Return ONLY valid JSON with this EXACT structure. Keep the keys exactly as shown, write ALL text values in English:
{structure}

RULES: Use ONLY the data above; never invent. Every point must quote a concrete data value. NO generic filler. 3 to 5 metrics and 1 to 3 errors. If the placement was good, still name what separated it from 1st."""
    return f"""Analiza esta partida como un coach de Challenger y genera un informe de coaching exigente.

DATOS DE LA PARTIDA:
{datos}

{rubric}

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura exacta (todos los textos en español):
{structure}

REGLAS: Usa SOLO los datos de arriba; nunca inventes. Cada punto debe citar un dato concreto. NADA de relleno genérico. Entre 3 y 5 métricas y entre 1 y 3 errores. Si la colocación fue buena, di igualmente qué la separó del puesto 1."""


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
