"""Pipeline de agregación de COMPS REAL para TFT (opción A: clusterización por rasgos).

Toma la MISMA muestra de partidas que ``meta_pipeline`` (ladder Challenger vía la
Riot API oficial) y agrupa a los participantes en composiciones reconocibles a
partir de su huella de rasgos activos + carry detectado por ítems de daño.

Salida con la MISMA forma que ``mock.meta('tft')`` para que el router pueda
sustituirla sin tocar el frontend. Para LoL no aplica (no hay 'comp' equivalente);
ese juego se mantiene en el mock por ahora.

Llamado por el worker (app/worker/refresh_meta.py); NO se invoca desde la API.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.core.config import settings
from app.services.meta_pipeline import _clean, _pct, _tier_from_avg
from app.services.prompts import _DAMAGE_ITEMS


# Rasgos que activamos en estilo 2+ (silver+) — descartamos rasgos sueltos.
_MIN_TRAIT_STYLE = 2

# Marcadores para inferir estilo (Reroll / Fast 8 / Standard) sin notas de parche.
_REROLL_COST_MAX = 2          # 3 estrellas en un 1-2 cost → reroll claro
_FAST8_LEVEL_MIN = 9          # nivel >= 9 al final → fast 8


def _clean_item(raw: str) -> str:
    """Devuelve el nombre limpio del ítem en minúscula (compatible con _DAMAGE_ITEMS)."""
    return _clean(raw).replace(" ", "").lower()


def _is_unique_trait(api_name: str) -> bool:
    """Rasgos únicos de campeones legendarios (no definen una comp)."""
    n = (api_name or "").lower()
    return "unique" in n or "_singleton" in n


def _active_traits(traits: list[dict]) -> list[tuple[str, int]]:
    """Lista de (nombre_limpio, style) para rasgos en silver+ que NO sean únicos."""
    out = []
    for t in traits or []:
        style = t.get("style", 0) or 0
        api = t.get("name", "")
        if style >= _MIN_TRAIT_STYLE and not _is_unique_trait(api):
            out.append((_clean(api), style))
    # Ordenar por style desc y num_units desc para que los más cargados manden.
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _comp_signature(traits: list[dict]) -> tuple[str, ...] | None:
    """Toma los dos rasgos más fuertes (silver+) como huella de la comp.
    Si no hay al menos uno, no hay comp clasificable."""
    active = [n for n, _ in _active_traits(traits)]
    if not active:
        return None
    return tuple(sorted(active[:2]))


def _carry_name(units: list[dict]) -> str | None:
    """Unidad con más ítems de daño; desempata por estrellas y por nº de ítems."""
    best = max(
        units or [],
        key=lambda u: (
            sum(1 for it in u.get("itemNames", []) if _clean_item(it) in _DAMAGE_ITEMS),
            u.get("tier", 0),
            len(u.get("itemNames", []) or []),
        ),
        default=None,
    )
    if not best:
        return None
    dmg = sum(1 for it in best.get("itemNames", []) if _clean_item(it) in _DAMAGE_ITEMS)
    if dmg == 0:
        return None
    return _clean(best.get("character_id", ""))


def _infer_style(units: list[dict], level: int) -> str:
    """Heurística sin notas de parche: nivel final + 3★ en 1-2 cost = reroll."""
    has_lowcost_3star = any(
        (u.get("rarity", 0) + 1) <= _REROLL_COST_MAX and (u.get("tier", 1) or 1) >= 3
        for u in units or []
    )
    if has_lowcost_3star:
        return "Reroll"
    if level >= _FAST8_LEVEL_MIN:
        return "Fast 8"
    return "Standard"


def _difficulty_from(avg_place: float, sample: int) -> str:
    """Aproximación: comps con buena media y muestra alta son 'Fácil' (consistentes);
    con varianza alta o medias justas, 'Media/Difícil'. Sin LLM no afinamos más."""
    if avg_place <= 4.2 and sample >= 25:
        return "Fácil"
    if avg_place <= 4.6:
        return "Media"
    return "Difícil"


def _comp_name(traits_pair: tuple[str, ...], carry: str | None, style: str) -> str:
    """'Reroll Mystic·Vanguard — carry Ahri' o 'Fast 8 Mystic·Sorcerer' si sin carry."""
    base = " · ".join(traits_pair)
    if style == "Reroll":
        head = f"Reroll {base}"
    elif style == "Fast 8":
        head = f"Fast 8 {base}"
    else:
        head = base
    return f"{head} — carry {carry}" if carry else head


# ---------------------------------- Agregación ----------------------------------
def _aggregate(matches: list[dict]) -> dict:
    """Devuelve el dict listo para el endpoint /meta (forma idéntica al mock)."""
    clusters: dict[tuple, dict] = defaultdict(lambda: {
        "places": [],            # lista de placements (para avg y top4)
        "carries": Counter(),    # nombre → veces
        "units": Counter(),      # nombre → veces
        "unit_costs": {},        # nombre → coste (más común)
        "_unit_cost_obs": defaultdict(Counter),  # para resolver el coste por mayoría
        "augments": Counter(),
        "items_by_carry": defaultdict(Counter),  # carry → ítems más vistos
        "levels": [],            # niveles finales (para estilo)
        "styles": Counter(),     # 'Reroll'/'Fast 8'/'Standard'
    })
    total_participants = 0

    for m in matches:
        for p in m.get("info", {}).get("participants", []):
            sig = _comp_signature(p.get("traits", []) or [])
            if not sig:
                continue
            total_participants += 1
            place = p.get("placement", 8) or 8
            level = p.get("level", 0) or 0
            units = p.get("units", []) or []
            carry = _carry_name(units)
            style = _infer_style(units, level)

            c = clusters[sig]
            c["places"].append(place)
            c["levels"].append(level)
            c["styles"][style] += 1
            if carry:
                c["carries"][carry] += 1
                for it in (next((u for u in units if _clean(u.get("character_id", "")) == carry), {}).get("itemNames", []) or []):
                    c["items_by_carry"][carry][_clean(it)] += 1
            for u in units:
                name = _clean(u.get("character_id", ""))
                if not name:
                    continue
                c["units"][name] += 1
                cost = (u.get("rarity", 0) or 0) + 1
                c["_unit_cost_obs"][name][cost] += 1
            for a in p.get("augments", []) or []:
                c["augments"][_clean(a)] += 1

    mn = max(settings.meta_min_games, 4)   # exige más muestra para una comp que para una unidad suelta
    top = settings.meta_top_n
    comps_out: list[dict] = []

    for sig, c in clusters.items():
        games = len(c["places"])
        if games < mn:
            continue
        avg_place = sum(c["places"]) / games
        top4 = sum(1 for p in c["places"] if p <= 4)
        wins = sum(1 for p in c["places"] if p == 1)
        carry = c["carries"].most_common(1)[0][0] if c["carries"] else None
        style = c["styles"].most_common(1)[0][0] if c["styles"] else "Standard"
        diff = _difficulty_from(avg_place, games)

        # Resuelve el coste de cada unidad por mayoría (evita un outlier raro).
        for name, obs in c["_unit_cost_obs"].items():
            c["unit_costs"][name] = obs.most_common(1)[0][0]

        # Núcleo de la comp: las 5-6 unidades más recurrentes.
        core_units = [
            {"n": name, "c": c["unit_costs"].get(name, 0)}
            for name, _ in c["units"].most_common(6)
        ]

        comps_out.append({
            "tier": _tier_from_avg(avg_place),
            "name": _comp_name(sig, carry, style),
            "_traits_raw": list(sig),   # consumido por _cdragon_enrich para re-traducir
            "style": style,
            "difficulty": diff,
            "metrics": {
                "avg": f"{avg_place:.1f}",
                "top4": f"{_pct(top4, games)}%",
                "win": f"{_pct(wins, games)}%",
                "pick": f"{_pct(games, total_participants)}%",
            },
            "units": core_units,
            "carry": carry,                                # extra (no rompe la UI)
            "carry_items": [it for it, _ in c["items_by_carry"].get(carry, Counter()).most_common(3)] if carry else [],
            "augments": [a for a, _ in c["augments"].most_common(3)],
            "_games": games,                               # interno, util para debug
        })

    # Orden por mejor placement medio, luego por frecuencia.
    comps_out.sort(key=lambda x: (float(x["metrics"]["avg"]), -x["_games"]))
    return {
        "patch": "live",                                   # se rellena desde fuera si lo sabemos
        "rank": "Challenger",
        "guide": True,
        "styles": ["Todos", "Standard", "Reroll", "Fast 8"],
        "metricCols": [
            {"k": "avg", "label": "Coloc."},
            {"k": "top4", "label": "Top 4"},
            {"k": "win", "label": "1.º"},
            {"k": "pick", "label": "Pick"},
        ],
        "comps": comps_out[:top],
    }


# ----------------------------------- Entrada -----------------------------------
def _enrich_named(idx: dict, kind: str, raw: str) -> dict:
    """Devuelve {name, icon} resolviendo `raw` (apiName limpio) vía CDragon."""
    from app.services import cdragon_client
    meta = cdragon_client.lookup(idx, kind, raw) or {}
    return {"name": meta.get("name") or raw, "icon": meta.get("icon")}


def _cdragon_enrich(payload: dict) -> dict:
    """Resuelve nombres limpios → display name traducido + icon URL vía CDragon.
    Si CDragon no responde, deja todo tal cual (no rompe nada)."""
    try:
        from app.services import cdragon_client
        idx = cdragon_client.index()
    except Exception:   # noqa: BLE001 — degradación silenciosa
        return payload
    if not idx.get("champions") and not idx.get("items"):
        return payload

    for comp in payload.get("comps", []):
        for u in comp.get("units", []) or []:
            meta = cdragon_client.lookup(idx, "champions", u.get("n", ""))
            if meta:
                u["n"] = meta["name"]
                u["icon"] = meta.get("icon")
                if meta.get("cost"):
                    u["c"] = meta["cost"]
        if comp.get("carry"):
            meta = cdragon_client.lookup(idx, "champions", comp["carry"])
            if meta:
                comp["carry"] = meta["name"]
                comp["carry_icon"] = meta.get("icon")
        # Reconstruir el nombre con los rasgos traducidos al idioma del CDragon.
        traits_raw = comp.pop("_traits_raw", None) or []
        if traits_raw:
            translated = []
            for t in traits_raw:
                tmeta = cdragon_client.lookup(idx, "traits", t)
                translated.append(tmeta["name"] if tmeta else t)
            translated.sort()
            base = " · ".join(translated)
            head = (
                f"Reroll {base}" if comp.get("style") == "Reroll"
                else f"Fast 8 {base}" if comp.get("style") == "Fast 8"
                else base
            )
            comp["name"] = f"{head} — {comp['carry']}" if comp.get("carry") else head
        comp["carry_items"] = [_enrich_named(idx, "items", it) for it in comp.get("carry_items", []) or []]
        comp["augments"] = [_enrich_named(idx, "augments", a) for a in comp.get("augments", []) or []]
    if idx.get("set_name"):
        payload["patch"] = f"{idx['set_name']} (en vivo)"
    return payload


def run_sync(matches: list[dict]) -> dict:
    """Versión sin red: recibe las partidas ya descargadas (lo llama el worker
    tras ``meta_pipeline._matches`` para reutilizar la misma muestra).
    """
    agg = _aggregate(matches)
    agg["sample"] = {"matches": len(matches)}
    agg["generated_at"] = datetime.now(timezone.utc).isoformat()
    agg["source"] = "real"
    return _cdragon_enrich(agg)
