"""Enriquecimiento del payload para el coaching ESTRUCTURADO (v2).

Reutiliza `prompts.extract_summary` (que ya detecta el carry por ítems de daño) y le
añade HECHOS YA CALCULADOS para que el modelo no divague:
  - LoL: línea temporal del `get_match_timeline` (muertes con timestamp y fase).
  - TFT: `señales` derivadas del estado final (reparto de ítems de daño, estrellas,
    huecos de tablero, carry, rasgos, nivel) — todo VERIFICABLE, sin inventar rondas.
También deriva los KPIs mostrables (`metrics`) del informe, sin depender del LLM.
"""
from app.services.prompts import _damage_items


def _phase(t_min: float) -> str:
    return "early" if t_min < 14 else ("mid" if t_min < 25 else "late")


def _lol_timeline(match, puuid, timeline):
    me = next((p for p in match.get("info", {}).get("participants", []) if p.get("puuid") == puuid), {})
    pid = me.get("participantId")
    deaths, kp, dp = [], {"early": 0, "mid": 0, "late": 0}, {"early": 0, "mid": 0, "late": 0}
    for fr in timeline.get("info", {}).get("frames", []):
        for ev in fr.get("events", []):
            if ev.get("type") != "CHAMPION_KILL":
                continue
            tmin = ev.get("timestamp", 0) / 60000.0
            ph = _phase(tmin)
            if ev.get("killerId") == pid:
                kp[ph] += 1
            if ev.get("victimId") == pid:
                dp[ph] += 1
                pos = ev.get("position", {}) or {}
                deaths.append({"t": f"{int(tmin)}:{int((tmin % 1) * 60):02d}", "fase": ph,
                               "x": pos.get("x"), "y": pos.get("y")})
    return {"muertes": deaths, "kills_por_fase": kp, "muertes_por_fase": dp}


def tft_signals(summary: dict) -> dict:
    """Hechos calculados del tablero FINAL (verificables), para anclar el análisis."""
    units = summary.get("unidades", []) or []
    nivel = summary.get("nivel") or 0
    dmg_units = [u for u in units if _damage_items(u.get("items", [])) > 0]
    total_dmg = sum(_damage_items(u.get("items", [])) for u in units)
    stars = {}
    for u in units:
        s = u.get("estrellas") or 1
        s = 3 if s > 3 else (1 if s < 1 else s)
        stars[s] = stars.get(s, 0) + 1
    carry = summary.get("carry_principal")
    if total_dmg == 0:
        reparto = "0 ítems de daño en el tablero (ninguna carry de daño)"
    elif len(dmg_units) == 1:
        reparto = f"{total_dmg} ítems de daño, todos en 1 unidad (correcto)"
    else:
        reparto = f"{total_dmg} ítems de daño REPARTIDOS en {len(dmg_units)} unidades"
    return {
        "unidades_en_tablero": len(units),
        "huecos_libres": max(nivel - len(units), 0),
        "estrellas": {f"{k}★": v for k, v in sorted(stars.items()) if v},
        "reparto_items_dano": reparto,
        "carry_detectado": (None if not carry else
                            {"unidad": carry.get("unidad"), "estrellas": carry.get("estrellas"),
                             "n_items": len(carry.get("items", []))}),
        "carry_sin_definir": carry is None,
        "rasgos_activos": summary.get("rasgos_activos", []),
        "augments": summary.get("aumentos", []),
        "nivel": nivel,
        "ultima_ronda": summary.get("ultima_ronda"),
        "oro_final": summary.get("oro_sobrante"),
    }


def enrich(game: str, match: dict, summary: dict, puuid: str, timeline: dict | None) -> dict:
    """summary (de extract_summary) + hechos calculados según el juego."""
    if game == "lol":
        if timeline:
            return {**summary, "linea_temporal": _lol_timeline(match, puuid, timeline)}
        return summary
    # TFT: sin timeline; añadimos señales derivadas del estado final
    return {**summary, "señales": tft_signals(summary)}


def metrics_for(game: str, summary: dict) -> list[dict]:
    """KPIs mostrables (value/label/status/benchmark) derivados del summary (sin LLM)."""
    out = []
    if game == "lol":
        res = summary.get("resultado", "—")
        out.append({"value": res, "label": "Resultado", "status": "good" if res == "Victoria" else "bad", "benchmark": ""})
        out.append({"value": str(summary.get("kda", "—")), "label": "KDA", "status": "", "benchmark": ""})
        cspm = summary.get("cs_por_min", 0) or 0
        out.append({"value": str(cspm), "label": "CS/min", "status": "good" if cspm >= 7 else "warn", "benchmark": "Obj. ~7.5"})
        if summary.get("vision_score") is not None:
            out.append({"value": str(summary.get("vision_score")), "label": "Visión", "status": "", "benchmark": ""})
        ob = summary.get("objetivos_equipo", {}) or {}
        out.append({"value": str(ob.get("dragones") or 0), "label": "Dragones equipo", "status": "", "benchmark": ""})
    else:
        pl = summary.get("colocacion") or 8
        out.append({"value": f"{pl}.º", "label": "Colocación", "status": "good" if pl <= 4 else "bad", "benchmark": "Top 4" if pl <= 4 else "Fuera de Top 4"})
        out.append({"value": str(summary.get("nivel", "—")), "label": "Nivel final", "status": "", "benchmark": ""})
        out.append({"value": str(summary.get("oro_sobrante") or 0), "label": "Oro sobrante", "status": "", "benchmark": "al final"})
        if summary.get("daño_a_jugadores") is not None:
            out.append({"value": str(summary.get("daño_a_jugadores")), "label": "Daño a jugadores", "status": "", "benchmark": ""})
    return out
