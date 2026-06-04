"""Mock dinámico de /meta construido desde CommunityDragon.

Genera una "tier list de ejemplo" que usa los NOMBRES Y RASGOS REALES del set
en vivo (vía CDragon, asset oficial). Las métricas (avg place, top4, pick, etc.)
y la elección de comps siguen siendo plausibles pero NO son datos reales del
ladder — para eso hace falta la clave Riot y el worker corriendo.

Por eso la respuesta lleva ``source: "mock_cdragon"`` y el frontend mantiene el
banner amarillo de "datos de ejemplo".

Si CDragon no responde o el set viene vacío, devolvemos None y el router cae al
mock invented (``mock.meta``).
"""
from __future__ import annotations

import random
from collections import Counter

from app.services import cdragon_client


# Pseudo-aleatoriedad determinista para que un mismo set produzca siempre la
# misma tier list de ejemplo (estabilidad visual entre reloads).
_RNG = random.Random(20260605)


def _trait_to_units(champions: dict) -> dict[str, list[tuple[str, int]]]:
    """Mapa trait_apiName → lista de (champion_display_name, cost)."""
    out: dict[str, list[tuple[str, int]]] = {}
    for c in champions.values():
        for trait in c.get("traits") or []:
            out.setdefault(trait, []).append((c.get("name") or "", int(c.get("cost") or 0)))
    return out


def _pick_iconic_pairs(traits: dict, t2u: dict, top_n: int = 9) -> list[tuple[str, str]]:
    """Combinaciones de dos rasgos con suficientes campeones compartiendo cada uno."""
    # Cuenta cuántos pares (t1, t2) tienen unidades compartidas — los más altos hacen una comp real.
    pair_counts: Counter[tuple[str, str]] = Counter()
    for trait_a, units_a in t2u.items():
        names_a = {n for n, _ in units_a}
        for trait_b, units_b in t2u.items():
            if trait_a >= trait_b:
                continue
            shared = names_a & {n for n, _ in units_b}
            if len(shared) >= 1 and len(units_a) >= 3 and len(units_b) >= 3:
                pair_counts[(trait_a, trait_b)] = len(shared) * 10 + len(units_a) + len(units_b)
    return [pair for pair, _ in pair_counts.most_common(top_n)]


def _comp_from_pair(pair: tuple[str, str], traits: dict, t2u: dict, rng: random.Random) -> dict:
    """Construye una comp ejemplo a partir de un par de rasgos."""
    trait_a, trait_b = pair
    name_a = (traits.get(trait_a) or {}).get("name") or trait_a
    name_b = (traits.get(trait_b) or {}).get("name") or trait_b

    units_pool = list({(n, c) for n, c in (t2u.get(trait_a, []) + t2u.get(trait_b, []))})
    units_pool.sort(key=lambda x: -x[1])     # de más caro a más barato
    core = units_pool[:6] if len(units_pool) >= 6 else units_pool

    # Carry: el más caro del pool (heurística honesta para mock).
    carry = core[0][0] if core else None
    carry_cost = core[0][1] if core else 0

    # Estilo plausible según el coste del carry.
    if carry_cost <= 2 and any(c <= 2 for _, c in core):
        style = "Reroll"
    elif carry_cost >= 4:
        style = "Fast 8"
    else:
        style = "Standard"

    # Métricas inventadas pero coherentes (el banner avisa de que es ejemplo).
    avg = round(rng.uniform(3.6, 4.8), 1)
    top4 = round(100 - (avg - 3.6) * 25)
    win = round(rng.uniform(8, 18))
    pick = round(rng.uniform(2.0, 12.0), 1)

    return {
        "tier": "S" if avg <= 4.0 else "A" if avg <= 4.4 else "B" if avg <= 4.7 else "C",
        "name": f"{name_a} · {name_b}",
        "style": style,
        "difficulty": rng.choice(["Fácil", "Media", "Difícil"]),
        "metrics": {
            "avg": f"{avg}",
            "top4": f"{top4}%",
            "win": f"{win}%",
            "pick": f"{pick}%",
        },
        "units": [{"n": n, "c": c} for n, c in core],
        "carry": carry,
    }


def build(locale: str = "es_es") -> dict | None:
    """Devuelve un payload /meta listo si CDragon responde; None si no."""
    idx = cdragon_client.index(locale)
    champs = idx.get("champions") or {}
    traits = idx.get("traits") or {}
    if not champs or not traits:
        return None

    t2u = _trait_to_units(champs)
    pairs = _pick_iconic_pairs(traits, t2u, top_n=9)
    if not pairs:
        return None

    comps = [_comp_from_pair(p, traits, t2u, _RNG) for p in pairs]
    comps.sort(key=lambda c: float(c["metrics"]["avg"]))

    set_label = idx.get("set_name") or f"Set {idx.get('set_number') or '?'}"
    return {
        "patch": f"{set_label} (en vivo)",
        "rank": "Diamante +",
        "guide": True,
        "styles": ["Todos", "Standard", "Reroll", "Fast 8"],
        "metricCols": [
            {"k": "avg", "label": "Coloc."},
            {"k": "top4", "label": "Top 4"},
            {"k": "win", "label": "1.º"},
            {"k": "pick", "label": "Pick"},
        ],
        "comps": comps,
        "source": "mock_cdragon",
    }
