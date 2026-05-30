"""Agrega el historial de partidas (Riot) en estadísticas personales.

Importante: la META global (tier list del parche) NO se puede derivar del
historial de un único jugador — necesita agregar datos de muchos jugadores de
alto elo (un pipeline de datos aparte). Por eso /meta sirve un dataset curado.
Aquí calculamos solo las estadísticas PERSONALES, que sí salen del historial.
"""
from collections import Counter, defaultdict

from app.services.riot_client import riot_client, RiotApiError

_ROLE_ES = {"TOP": "Top", "JUNGLE": "Jungla", "MIDDLE": "Mid", "BOTTOM": "ADC", "UTILITY": "Support"}
_PLACE_COLOR = ["gold", "good", "good", "good", "warn", "warn", "bad", "bad"]  # 1.º .. 8.º


async def compute_stats(game: str, riot_id: str, count: int = 20) -> dict:
    if "#" not in riot_id:
        raise RiotApiError(400, "Riot ID requerido (Nombre#TAG)")
    name, tag = riot_id.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    ids = await riot_client.get_match_ids(puuid, game, count=count)
    matches = [await riot_client.get_match(mid, game) for mid in ids]
    return _tft_stats(matches, puuid) if game == "tft" else _lol_stats(matches, puuid)


# ----------------------------- TFT -----------------------------
def _dominant_comp(me: dict) -> str:
    active = [t for t in me.get("traits", []) if t.get("tier_current", 0) > 0]
    if not active:
        return "Composición TFT"
    top = max(active, key=lambda t: t.get("num_units", 0))
    raw = (top.get("name") or "").split("_")[-1]
    return f"Comp {raw}" if raw else "Composición TFT"


def _tft_stats(matches: list[dict], puuid: str) -> dict:
    placements, comps, comp_place, level_place = [], Counter(), defaultdict(list), defaultdict(list)
    for m in matches:
        me = next((p for p in m["info"]["participants"] if p.get("puuid") == puuid), None)
        if not me:
            continue
        pl = me.get("placement", 0)
        placements.append(pl)
        comp = _dominant_comp(me)
        comps[comp] += 1
        comp_place[comp].append(pl)
        level_place[me.get("level", 0)].append(pl)

    n = len(placements) or 1
    avg = round(sum(placements) / n, 2)
    top4 = round(100 * sum(1 for p in placements if p <= 4) / n)
    top1 = round(100 * sum(1 for p in placements if p == 1) / n)

    counts = Counter(placements)
    bars = [{"label": f"{i}.º", "value": counts.get(i, 0), "color": _PLACE_COLOR[i - 1]} for i in range(1, 9)]
    evol = [{"label": f"P{i + 1}", "value": pl} for i, pl in enumerate(reversed(placements))]

    rows_a = []
    for comp, c in comps.most_common(5):
        pls = comp_place[comp]
        a = round(sum(pls) / len(pls), 1)
        t4 = round(100 * sum(1 for p in pls if p <= 4) / len(pls))
        rows_a.append([comp, str(c), str(a), f"{t4}%"])

    rows_b = []
    for lvl in sorted(level_place.keys(), reverse=True)[:4]:
        pls = level_place[lvl]
        rows_b.append([f"Nivel {lvl}", str(len(pls)), str(round(sum(pls) / len(pls), 1))])

    return {
        "kpis": [
            {"v": str(avg), "k": "Colocación media", "cls": "good" if avg < 4.5 else "warn", "bench": f"{n} partidas"},
            {"v": f"{top4}%", "k": "Top 4", "cls": "good" if top4 >= 50 else "warn", "bench": "Media: 50%"},
            {"v": f"{top1}%", "k": "Top 1", "cls": "good", "bench": "Media: 12.5%"},
            {"v": str(n), "k": "Partidas analizadas", "cls": "", "bench": "Historial reciente"},
        ],
        "evol": {"label": "Colocación por partida (menor es mejor)", "min": 1, "max": 8,
                 "invert": True, "suffix": "", "points": evol},
        "dist": {"label": "Distribución de colocaciones", "bars": bars},
        "tableA": {"title": "Comps más jugadas", "cols": ["Comp", "Partidas", "Coloc.", "Top 4"], "rows": rows_a},
        "tableB": {"title": "Rendimiento por nivel final", "cols": ["Nivel", "Partidas", "Coloc."], "rows": rows_b},
        "insights": _tft_insights(comp_place, top4),
    }


def _tft_insights(comp_place: dict, top4: int) -> list[dict]:
    out = []
    best = None
    for comp, pls in comp_place.items():
        if len(pls) >= 2:
            a = sum(pls) / len(pls)
            if best is None or a < best[1]:
                best = (comp, a, len(pls))
    if best:
        out.append({"cls": "good", "ic": "✅", "t": f"Tu mejor comp es {best[0]}",
                    "d": f"Colocación media {round(best[1], 1)} en {best[2]} partidas. Es tu línea más fiable."})
    out.append({"cls": "good" if top4 >= 55 else "warn", "ic": "🎯", "t": f"Entras en Top 4 el {top4}% de las veces",
                "d": "Tu consistencia para no perder LP. Sube este número priorizando Top 4 sobre forzar el 1.º."})
    return out


# ----------------------------- LoL -----------------------------
def _lol_stats(matches: list[dict], puuid: str) -> dict:
    n = wins = ks = ds = as_ = 0
    cspm, kda_points = [], []
    roles, champs = Counter(), Counter()
    role_wl, champ_wl = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])  # [partidas, victorias]

    for m in matches:
        info = m["info"]
        me = next((p for p in info["participants"] if p.get("puuid") == puuid), None)
        if not me:
            continue
        n += 1
        win = bool(me.get("win"))
        wins += 1 if win else 0
        k, d, a = me.get("kills", 0), me.get("deaths", 0), me.get("assists", 0)
        ks += k; ds += d; as_ += a
        kda_points.append(round((k + a) / max(d, 1), 2))
        dur = info.get("gameDuration", 0) or 1
        cs = me.get("totalMinionsKilled", 0) + me.get("neutralMinionsKilled", 0)
        cspm.append(cs / (dur / 60))
        role = _ROLE_ES.get(me.get("teamPosition", ""), me.get("teamPosition") or "—")
        roles[role] += 1
        role_wl[role][0] += 1; role_wl[role][1] += 1 if win else 0
        ch = me.get("championName", "—")
        champs[ch] += 1
        champ_wl[ch][0] += 1; champ_wl[ch][1] += 1 if win else 0

    n = n or 1
    wr = round(100 * wins / n)
    kda = round((ks + as_) / max(ds, 1), 2)
    avg_cspm = round(sum(cspm) / len(cspm), 1) if cspm else 0
    main_role = roles.most_common(1)[0][0] if roles else "—"

    bars = [{"label": r, "value": c, "color": "accent"} for r, c in roles.most_common()]
    evol = [{"label": f"P{i + 1}", "value": v} for i, v in enumerate(reversed(kda_points))]
    max_kda = max([5] + kda_points)

    rows_a = []
    for ch, c in champs.most_common(5):
        wl = champ_wl[ch]
        rows_a.append([ch, str(c), f"{round(100 * wl[1] / wl[0])}%"])
    rows_b = []
    for r, c in roles.most_common():
        wl = role_wl[r]
        rows_b.append([r, str(c), f"{round(100 * wl[1] / wl[0])}%"])

    return {
        "kpis": [
            {"v": f"{wr}%", "k": "Winrate", "cls": "good" if wr >= 50 else "warn", "bench": f"{n} partidas"},
            {"v": str(kda), "k": "KDA medio", "cls": "good" if kda >= 2.5 else "warn", "bench": "Objetivo: 2.5"},
            {"v": str(avg_cspm), "k": "CS por minuto", "cls": "good" if avg_cspm >= 6.5 else "warn", "bench": "Objetivo: 6.5"},
            {"v": main_role, "k": "Rol principal", "cls": "", "bench": f"{roles.get(main_role, 0)} partidas"},
        ],
        "evol": {"label": "KDA por partida", "min": 0, "max": max_kda, "invert": False, "suffix": "", "points": evol},
        "dist": {"label": "Partidas por rol", "bars": bars},
        "tableA": {"title": "Campeones más jugados", "cols": ["Campeón", "Partidas", "Winrate"], "rows": rows_a},
        "tableB": {"title": "Rendimiento por rol", "cols": ["Rol", "Partidas", "Winrate"], "rows": rows_b},
        "insights": _lol_insights(role_wl, wr, main_role),
    }


def _lol_insights(role_wl: dict, wr: int, main_role: str) -> list[dict]:
    out = []
    best = None
    for role, wl in role_wl.items():
        if wl[0] >= 2:
            r = 100 * wl[1] / wl[0]
            if best is None or r > best[1]:
                best = (role, r, wl[0])
    if best:
        out.append({"cls": "good", "ic": "✅", "t": f"Tu mejor rol es {best[0]}",
                    "d": f"Ganas el {round(best[1])}% en {best[2]} partidas. Prioriza este rol cuando puedas elegir."})
    out.append({"cls": "good" if wr >= 50 else "warn", "ic": "📊", "t": f"Winrate global del {wr}%",
                "d": "Sobre tu historial reciente. Por encima del 52% sostenido = subes de rango."})
    return out
