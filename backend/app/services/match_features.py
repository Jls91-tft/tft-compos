"""Enriquecimiento del payload para el coaching ESTRUCTURADO (v2).

Reutiliza `prompts.extract_summary` (que ya detecta el carry por ítems de daño,
rasgos, augments, etc.) y le añade, en LoL, datos de la TIMELINE (muertes con
timestamp y fase, kills/muertes por fase) para anclar la evidencia a momentos.
También deriva los KPIs mostrables (`metrics`) del informe, sin depender del LLM.
"""


def _phase(t_min: float) -> str:
    return "early" if t_min < 14 else ("mid" if t_min < 25 else "late")


def enrich(game: str, match: dict, summary: dict, puuid: str, timeline: dict | None) -> dict:
    """summary (de extract_summary) + línea temporal en LoL si hay timeline."""
    if game == "lol" and timeline:
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
        return {**summary, "linea_temporal": {"muertes": deaths, "kills_por_fase": kp, "muertes_por_fase": dp}}
    return summary


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
