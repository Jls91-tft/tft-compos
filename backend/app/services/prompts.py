"""Prompts del coach + extracción de datos de partida + parseo del informe.

Aquí vive la "voz" del coach y la traducción de los datos crudos de Riot a un
resumen que la IA pueda analizar. Centralizarlo facilita iterar la calidad del
coaching sin tocar el resto del backend.
"""
import json
from app.schemas.models import CoachingReport

# --- Voz del coach (system prompt) ---
COACH_SYSTEM = (
    "Eres Synapse, un coach experto de TFT y League of Legends. Hablas en español, "
    "con tono directo, cercano y motivador, para jugadores de nivel Platino-Diamante. "
    "Tu objetivo es que el jugador mejore con consejos concretos y accionables. "
    "NUNCA inventes datos que no estén en la información de la partida; si un dato no "
    "aparece, no lo menciones. Evita la jerga vacía: ve al grano."
)

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


def _tft_summary(match: dict, puuid: str) -> dict:
    info = match["info"]
    me = next(p for p in info["participants"] if p.get("puuid") == puuid)
    traits = [
        {"rasgo": (t.get("name") or "").split("_")[-1], "unidades": t.get("num_units")}
        for t in me.get("traits", []) if t.get("tier_current", 0) > 0
    ]
    units = [
        {
            "unidad": (u.get("character_id") or "").split("_")[-1],
            "estrellas": u.get("tier"),
            "n_items": len(u.get("itemNames", []) or u.get("items", [])),
        }
        for u in me.get("units", [])
    ]
    return {
        "juego": "TFT",
        "colocacion": me.get("placement"),
        "nivel": me.get("level"),
        "ultima_ronda": me.get("last_round"),
        "oro_sobrante": me.get("gold_left"),
        "jugadores_eliminados": me.get("players_eliminated"),
        "rasgos_activos": traits,
        "unidades": units,
        "duracion_min": round((info.get("game_length", 0) or 0) / 60, 1),
    }


# ----------------------------- Construcción de prompts -----------------------------
def build_report_prompt(game: str, summary: dict) -> str:
    datos = json.dumps(summary, ensure_ascii=False, indent=2)
    return f"""Analiza esta partida y genera un informe de coaching.

DATOS DE LA PARTIDA:
{datos}

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura exacta (todo en español):
{{
  "verdict": "1-2 frases: qué definió la partida",
  "focus": "1 frase: el consejo prioritario para la próxima partida",
  "metrics": [{{"value": "valor", "label": "qué mide", "status": "good|warn|bad", "benchmark": "referencia"}}],
  "did_well": ["2 o 3 aciertos concretos"],
  "errors": [{{"title": "título", "severity": "major|minor", "what": "qué pasó", "why": "por qué te costó", "fix": "cómo subsanarlo", "when": "el momento"}}],
  "corrective": "un párrafo con el ajuste clave",
  "action_plan": ["3 o 4 pasos accionables para la próxima partida"]
}}

Usa SOLO los datos presentes arriba. Entre 3 y 5 métricas y entre 1 y 3 errores."""


def build_chat_prompt(game: str, summary: dict, question: str) -> str:
    datos = json.dumps(summary, ensure_ascii=False)
    return (
        f"Contexto de la partida ({game.upper()}): {datos}\n\n"
        f"Pregunta del jugador: {question}\n\n"
        "Responde en 2-4 frases, concreto y accionable, usando solo el contexto."
    )


# ----------------------------- Parseo del informe -----------------------------
def parse_report(raw: str, game: str, match_id: str) -> CoachingReport:
    """Convierte la respuesta JSON de la IA en un CoachingReport validado.

    Si la IA no devolviera un JSON válido, hacemos un fallback elegante para no
    romper la experiencia.
    """
    try:
        data = json.loads(raw)
        data["game"] = game
        data["match_id"] = match_id
        return CoachingReport(**data)
    except Exception:
        return CoachingReport(
            game=game, match_id=match_id,
            verdict=(raw or "").strip()[:600] or "No se pudo generar el análisis esta vez.",
            focus="", metrics=[], did_well=[], errors=[], corrective="", action_plan=[],
        )
