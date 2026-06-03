"""Enriquecimiento del payload para el coaching ESTRUCTURADO (v2).

Reutiliza `prompts.extract_summary` (que ya detecta el carry por ítems de daño) y le
añade HECHOS YA CALCULADOS para que el modelo no divague:
  - LoL: línea temporal del `get_match_timeline` (muertes con timestamp y fase).
  - TFT: `señales` derivadas del estado final (itemización del carry, fuerza de tablero,
    estrellas, huecos, tempo) + `lobby` con COMPARATIVA estructurada frente al 1.º
    (nivel, 2★/3★, unidades de coste alto, carry e ítems, contest) — todo VERIFICABLE.
También deriva los KPIs mostrables (`metrics`) del informe, sin depender del LLM.
"""
from app.services.prompts import _damage_items, _unit_cost
from app.services import tft_names


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


def lol_comparison(match: dict, puuid: str) -> dict:
    """Comparativa de LoL: rival de línea (mismo rol en el equipo rival) + contexto de equipo.
    Sale del propio match-v5 (trae los 10 participantes), sin llamadas extra."""
    info = match.get("info", {})
    parts = info.get("participants", [])
    me = next((p for p in parts if p.get("puuid") == puuid), {})
    pos = me.get("teamPosition") or ""
    cs = lambda p: (p.get("totalMinionsKilled", 0) or 0) + (p.get("neutralMinionsKilled", 0) or 0)  # noqa: E731

    out = {"rival_de_linea": None, "diferencias_con_rival": None}
    opp = None
    if pos:
        opp = next((p for p in parts if p.get("teamPosition") == pos and p.get("teamId") != me.get("teamId")), None)
    if opp:
        out["rival_de_linea"] = {
            "campeon": opp.get("championName"),
            "kda": f'{opp.get("kills", 0)}/{opp.get("deaths", 0)}/{opp.get("assists", 0)}',
            "cs": cs(opp), "oro": opp.get("goldEarned"),
            "dano_a_campeones": opp.get("totalDamageDealtToChampions"),
            "nivel": opp.get("champLevel"), "vision": opp.get("visionScore"),
        }
        out["diferencias_con_rival"] = {
            "cs": cs(me) - cs(opp),
            "oro": (me.get("goldEarned") or 0) - (opp.get("goldEarned") or 0),
            "dano_a_campeones": (me.get("totalDamageDealtToChampions") or 0) - (opp.get("totalDamageDealtToChampions") or 0),
            "nivel": (me.get("champLevel") or 0) - (opp.get("champLevel") or 0),
            "vision": (me.get("visionScore") or 0) - (opp.get("visionScore") or 0),
        }
    myteam = [p for p in parts if p.get("teamId") == me.get("teamId")]
    team_dmg = sum(p.get("totalDamageDealtToChampions", 0) or 0 for p in myteam) or 1
    team_kills = sum(p.get("kills", 0) or 0 for p in myteam) or 1
    out["cuota_dano_equipo_pct"] = round(100 * (me.get("totalDamageDealtToChampions", 0) or 0) / team_dmg)
    out["participacion_en_kills_pct"] = round(100 * ((me.get("kills", 0) or 0) + (me.get("assists", 0) or 0)) / team_kills)
    return out


# 'challenges' de match-v5 de alta señal para coaching (apiName → etiqueta legible, transform)
_LOL_CHALLENGES = [
    ("goldPerMinute", "oro_por_min", lambda v: round(v)),
    ("damagePerMinute", "dano_por_min", lambda v: round(v)),
    ("laneMinionsFirst10Minutes", "cs_primeros_10_min", lambda v: round(v)),
    ("maxLevelLeadLaneOpponent", "ventaja_max_nivel_vs_rival", lambda v: int(v)),
    ("laningPhaseGoldExpAdvantage", "ventaja_oro_exp_en_lineas", lambda v: int(v)),
    ("soloKills", "asesinatos_en_solitario", lambda v: int(v)),
    ("controlWardsPlaced", "guardianes_de_control", lambda v: int(v)),
    ("dragonTakedowns", "participacion_dragones", lambda v: int(v)),
    ("baronTakedowns", "participacion_barones", lambda v: int(v)),
    ("turretPlatesTaken", "placas_de_torre", lambda v: int(v)),
    ("skillshotsHit", "habilidades_acertadas", lambda v: int(v)),
    ("skillshotsDodged", "habilidades_esquivadas", lambda v: int(v)),
]


def lol_challenges(match: dict, puuid: str) -> dict:
    """Métricas avanzadas YA calculadas por Riot ('challenges' de match-v5), curadas.
    Sale del propio match-v5 (sin llamadas extra). Campos ausentes se omiten."""
    me = next((p for p in match.get("info", {}).get("participants", []) if p.get("puuid") == puuid), {})
    ch = me.get("challenges") or {}
    out = {}
    for api, label, fn in _LOL_CHALLENGES:
        v = ch.get(api)
        if v is None:
            continue
        try:
            out[label] = fn(v)
        except (TypeError, ValueError):
            continue
    return out


def tft_signals(summary: dict) -> dict:
    """Hechos calculados del tablero FINAL (verificables), para anclar el análisis."""
    units = summary.get("unidades", []) or []
    nivel = summary.get("nivel") or 0
    carry = summary.get("carry_principal")

    total_dmg = sum(_damage_items(u.get("items", [])) for u in units)
    dmg_units = [u for u in units if _damage_items(u.get("items", [])) > 0]
    carry_dmg = _damage_items(carry.get("items", [])) if carry else 0
    items_fuera = max(total_dmg - carry_dmg, 0)

    if total_dmg == 0:
        reparto = "0 ítems de daño en el tablero (ninguna carry de daño)"
    elif len(dmg_units) == 1:
        reparto = f"{total_dmg} ítems de daño, todos en 1 unidad (correcto)"
    else:
        reparto = f"{total_dmg} ítems de daño REPARTIDOS en {len(dmg_units)} unidades (mal: {items_fuera} fuera del carry)"

    stars = {}
    for u in units:
        s = u.get("estrellas") or 1
        s = 3 if s > 3 else (1 if s < 1 else s)
        stars[s] = stars.get(s, 0) + 1

    carry_info = None
    if carry:
        citems = carry.get("items", []) or []
        carry_info = {
            "unidad": carry.get("unidad"),
            "estrellas": carry.get("estrellas"),
            "coste": carry.get("coste"),
            "items_de_dano": carry_dmg,
            "items_totales": len(citems),
            "le_faltan_items_para_3": max(0, 3 - len(citems)),
        }

    return {
        "unidades_en_tablero": len(units),
        "huecos_libres": max(nivel - len(units), 0),
        "estrellas": {f"{k}★": v for k, v in sorted(stars.items()) if v},
        "unidades_2_estrellas_o_mas": sum(1 for u in units if (u.get("estrellas") or 1) >= 2),
        "unidades_3_estrellas": sum(1 for u in units if (u.get("estrellas") or 1) >= 3),
        "unidades_coste_alto_4_5": sum(1 for u in units if (u.get("coste") or 0) >= 4),
        "reparto_items_dano": reparto,
        "items_dano_fuera_del_carry": items_fuera,
        "carry_detectado": carry_info,
        "carry_completo": bool(carry and len(carry.get("items", []) or []) >= 3),
        "carry_sin_definir": carry is None,
        "rasgos_activos": summary.get("rasgos_activos", []),
        "augments": summary.get("aumentos", []),
        "nivel": nivel,
        "ultima_ronda": summary.get("ultima_ronda"),
        "oro_final": summary.get("oro_sobrante"),
        "tempo": f"nivel {nivel} al final; última ronda registrada {summary.get('ultima_ronda')}",
    }


def _dmg_raw(unit: dict, clean) -> int:
    return _damage_items([clean(i) for i in (unit.get("itemNames") or [])])


def _tft_board_stats(p: dict, clean):
    """Fingerprint de fuerza de un tablero (mío o del ganador) desde el estado final."""
    units = p.get("units", []) or []
    carry = max(units, key=lambda u: (_dmg_raw(u, clean), u.get("tier") or 0, len(u.get("itemNames") or [])),
                default=None)
    carry_info, carry_cid = None, None
    if carry and _dmg_raw(carry, clean) > 0:
        carry_cid = carry.get("character_id")
        carry_info = {
            "unidad": tft_names.unit_display(carry_cid),
            "estrellas": carry.get("tier"),
            "coste": _unit_cost(carry.get("rarity")),
            "items_de_dano": _dmg_raw(carry, clean),
            "items_totales": len(carry.get("itemNames") or []),
        }
    stats = {
        "nivel": p.get("level"),
        "dos_estrellas_o_mas": sum(1 for u in units if (u.get("tier") or 1) >= 2),
        "tres_estrellas": sum(1 for u in units if (u.get("tier") or 1) >= 3),
        "unidades_coste_alto_4_5": sum(1 for u in units if (_unit_cost(u.get("rarity")) or 0) >= 4),
        "carry": carry_info,
    }
    return stats, carry_cid


def tft_lobby(match: dict, puuid: str) -> dict:
    """Señales del LOBBY (los 8 tableros finales): contest + COMPARATIVA con el 1.º.

    No cuesta llamadas extra (ya viene en el match). El contest explica por qué una
    unidad no subió de estrellas (la jugaban otros); la comparativa contra el ganador
    es la referencia real de cuánto te faltó (nivel, 2★/3★, coste alto, carry e ítems).
    """
    clean = lambda s: (s or "").split("_")[-1]  # noqa: E731
    parts = match.get("info", {}).get("participants", [])
    me = next((p for p in parts if p.get("puuid") == puuid), {})

    my_cids = {(u.get("character_id") or "") for u in me.get("units", []) if u.get("character_id")}
    contest = []
    for cid in my_cids:
        rivals = sum(1 for p in parts if p is not me and any(u.get("character_id") == cid for u in p.get("units", [])))
        if rivals > 0:
            contest.append({"unidad": tft_names.unit_display(cid), "rivales_con_ella": rivals})
    contest.sort(key=lambda x: -x["rivales_con_ella"])

    me_stats, my_carry_cid = _tft_board_stats(me, clean)
    win = next((p for p in parts if p.get("placement") == 1), None)
    win_stats, _wc = _tft_board_stats(win, clean) if win else ({}, None)

    ganador = None
    if win:
        ganador = {
            "nivel": win.get("level"),
            "carry": win_stats.get("carry"),
            "rasgos": [tft_names.trait_display(t.get("name")) for t in win.get("traits", []) if t.get("tier_current", 0) > 0][:6],
        }

    niveles = sorted((p.get("level") or 0 for p in parts), reverse=True)
    mi_rank = (niveles.index(me.get("level") or 0) + 1) if parts else None

    carry_contestada = False
    if my_carry_cid:
        n = sum(1 for p in parts if p is not me and any(u.get("character_id") == my_carry_cid for u in p.get("units", [])))
        carry_contestada = n >= 2

    comparativa = None
    if win:
        comparativa = {
            "dif_nivel_conmigo": (me.get("level") or 0) - (win.get("level") or 0),
            "mis_2estrellas_o_mas": me_stats["dos_estrellas_o_mas"],
            "ganador_2estrellas_o_mas": win_stats.get("dos_estrellas_o_mas"),
            "mis_3estrellas": me_stats["tres_estrellas"],
            "ganador_3estrellas": win_stats.get("tres_estrellas"),
            "mis_unidades_coste_alto": me_stats["unidades_coste_alto_4_5"],
            "ganador_unidades_coste_alto": win_stats.get("unidades_coste_alto_4_5"),
            "mi_carry": me_stats["carry"],
            "carry_ganador": win_stats.get("carry"),
            "mi_carry_contestada_por_2_o_mas": carry_contestada,
            "mi_rank_de_nivel_en_lobby": mi_rank,
            "jugadores": len(parts),
        }

    return {
        "tamano_lobby": len(parts),
        "unidades_contestadas": contest[:6],
        "mi_tablero": me_stats,
        "ganador": ganador,
        "comparativa": comparativa,
    }


def enrich(game: str, match: dict, summary: dict, puuid: str, timeline: dict | None) -> dict:
    """summary (de extract_summary) + hechos calculados según el juego."""
    if game == "lol":
        out = {**summary, "comparativa": lol_comparison(match, puuid)}
        ch = lol_challenges(match, puuid)
        if ch:
            out["challenges"] = ch
        if timeline:
            out["linea_temporal"] = _lol_timeline(match, puuid, timeline)
        return out
    # TFT: sin timeline; añadimos señales del estado final + señales del lobby (8 tableros)
    return {**summary, "señales": tft_signals(summary), "lobby": tft_lobby(match, puuid)}


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
