"""Normaliza las respuestas crudas de Riot a nuestros schemas (MatchCard).

Mantener esta capa aislada permite que, si Riot cambia su formato, solo toquemos
aquí — el resto de la app trabaja siempre con nuestros modelos.
"""
from app.schemas.models import MatchCard

# Posiciones de Riot → etiqueta en español (rol genérico del género MOBA)
_ROLE_ES = {"TOP": "Top", "JUNGLE": "Jungla", "MIDDLE": "Mid", "BOTTOM": "ADC", "UTILITY": "Support"}


def _fmt_dur(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _find_me(participants: list[dict], puuid: str) -> dict:
    me = next((p for p in participants if p.get("puuid") == puuid), None)
    if me is None:
        raise ValueError("El jugador no aparece en la partida")
    return me


def lol_match_to_card(match: dict, puuid: str) -> MatchCard:
    info = match["info"]
    me = _find_me(info["participants"], puuid)
    role = _ROLE_ES.get(me.get("teamPosition", ""), me.get("teamPosition") or "—")
    cs = me.get("totalMinionsKilled", 0) + me.get("neutralMinionsKilled", 0)
    return MatchCard(
        id=match["metadata"]["matchId"],
        game="lol",
        result="win" if me.get("win") else "loss",
        title=f"{role} · {me.get('championName', '—')}",
        meta={
            "kda": f"{me.get('kills', 0)}/{me.get('deaths', 0)}/{me.get('assists', 0)}",
            "cs": cs,
            "duracion": _fmt_dur(info.get("gameDuration", 0)),
        },
    )


def tft_match_to_card(match: dict, puuid: str) -> MatchCard:
    info = match["info"]
    me = _find_me(info["participants"], puuid)
    placement = me.get("placement", 0)
    return MatchCard(
        id=match["metadata"]["match_id"],
        game="tft",
        result=str(placement),
        title=_tft_comp_name(me),  # aproximación; la detección fina de comp es de la Fase 3
        meta={
            "nivel": me.get("level", 0),
            "duracion": _fmt_dur(int(info.get("game_length", 0))),
            "nota": f"{placement}.º puesto",
        },
    )


def _tft_comp_name(participant: dict) -> str:
    """Nombre aproximado de la comp: el rasgo activo con más unidades.

    # Fase 3: mapear a un nombre de comp con marca propia (no el id crudo de Riot).
    """
    active = [t for t in participant.get("traits", []) if t.get("tier_current", 0) > 0]
    if not active:
        return "Composición TFT"
    top = max(active, key=lambda t: t.get("num_units", 0))
    raw = (top.get("name") or "").split("_")[-1]
    return f"Comp {raw}" if raw else "Composición TFT"
