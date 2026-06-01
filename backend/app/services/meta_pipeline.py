"""Pipeline de agregación de META REAL (docs/DATOS.md, opción B: ligero).

Toma el ladder Challenger de la región configurada para Riot, muestrea
jugadores, descarga sus últimas partidas vía la Riot API OFICIAL y agrega
winrate (top-4 en TFT / victorias en LoL) y uso por unidad, ítem y augment.

Son DATOS REALES de la API oficial (uso legítimo, como MetaTFT/OP.GG); por eso
aquí sí aparecen nombres reales del juego. El mock genérico (mock_lab) se
mantiene como FALLBACK mientras el worker no haya generado datos.

Lo ejecuta el worker (app/worker/refresh_meta.py); NO se llama desde la API.
"""
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.core.config import settings
from app.services.riot_client import riot_client

# 'TFT11_Ahri' / 'TFT_Item_X' / 'TFT11_Augment_Y' → quita el prefijo del set.
_PREFIX = re.compile(r"^TFT[^_]*_(?:Item_|Augment_)?")


def _clean(raw: str) -> str:
    """'TFT11_Ahri'→'Ahri'; 'TFT_Item_GuinsoosRageblade'→'Guinsoos Rageblade'."""
    name = _PREFIX.sub("", raw or "").replace("_", " ")
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)  # separa CamelCase
    return name.strip() or (raw or "")


def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def _tier_from_avg(avg: float) -> str:
    if avg <= 4.2:
        return "S"
    if avg <= 4.5:
        return "A"
    if avg <= 4.8:
        return "B"
    return "C"


# ---------------------------- Muestreo del ladder ----------------------------
async def _sample_puuids(game: str, limit: int) -> list[str]:
    entries = await riot_client.get_challenger(game)
    puuids: list[str] = []
    for e in entries[: limit * 2]:  # margen: algunas entradas no resuelven puuid
        if len(puuids) >= limit:
            break
        puuid = e.get("puuid")
        if not puuid and e.get("summonerId"):
            try:
                puuid = await riot_client.get_summoner_puuid(e["summonerId"], game)
            except Exception:
                continue
        if puuid:
            puuids.append(puuid)
    return puuids


async def _matches(game: str, puuids: list[str]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for puuid in puuids:
        try:
            ids = await riot_client.get_match_ids(puuid, game, count=settings.meta_matches_per_player)
        except Exception:
            continue
        for mid in ids:
            if mid in seen:
                continue
            seen.add(mid)
            try:
                out.append(await riot_client.get_match(mid, game))
            except Exception:
                continue
    return out


# ------------------------------- Agregación TFT -------------------------------
def _aggregate_tft(matches: list[dict]) -> dict:
    units = defaultdict(lambda: {"g": 0, "top4": 0, "cost": Counter(), "items": Counter()})
    items = defaultdict(lambda: {"g": 0, "top4": 0, "units": Counter()})
    augs = defaultdict(lambda: {"g": 0, "top4": 0, "place": 0})
    total = 0
    for m in matches:
        for p in m.get("info", {}).get("participants", []):
            total += 1
            place = p.get("placement", 8)
            top4 = 1 if place <= 4 else 0
            for u in p.get("units", []):
                name = _clean(u.get("character_id", ""))
                if not name:
                    continue
                units[name]["g"] += 1
                units[name]["top4"] += top4
                units[name]["cost"][u.get("rarity", 0) + 1] += 1
                for it in u.get("itemNames", []) or []:
                    iname = _clean(it)
                    units[name]["items"][iname] += 1
                    items[iname]["g"] += 1
                    items[iname]["top4"] += top4
                    items[iname]["units"][name] += 1
            for a in p.get("augments", []) or []:
                aname = _clean(a)
                augs[aname]["g"] += 1
                augs[aname]["top4"] += top4
                augs[aname]["place"] += place

    mn, top = settings.meta_min_games, settings.meta_top_n
    ulist = [
        {
            "n": n,
            "cost": d["cost"].most_common(1)[0][0] if d["cost"] else 0,
            "wr": _pct(d["top4"], d["g"]),
            "use": _pct(d["g"], total),
            "sub": f"Coste {d['cost'].most_common(1)[0][0]}" if d["cost"] else "",
            "chips": [c for c, _ in d["items"].most_common(3)],
        }
        for n, d in units.items() if d["g"] >= mn
    ]
    ilist = [
        {
            "n": n,
            "wr": _pct(d["top4"], d["g"]),
            "use": _pct(d["g"], total),
            "sub": "",
            "chips": [c for c, _ in d["units"].most_common(3)],
        }
        for n, d in items.items() if d["g"] >= mn
    ]
    alist = [
        {
            "n": n,
            "tier": _tier_from_avg(d["place"] / d["g"]),
            "wr": _pct(d["top4"], d["g"]),
            "use": _pct(d["g"], total),
            "sub": f"Media {d['place'] / d['g']:.2f}",
            "chips": [],
        }
        for n, d in augs.items() if d["g"] >= mn
    ]
    by_use = lambda x: x["use"]  # noqa: E731
    return {
        "units": sorted(ulist, key=by_use, reverse=True)[:top],
        "items": sorted(ilist, key=by_use, reverse=True)[:top],
        "augments": sorted(alist, key=by_use, reverse=True)[:top],
    }


# ------------------------------- Agregación LoL -------------------------------
def _aggregate_lol(matches: list[dict]) -> dict:
    champs = defaultdict(lambda: {"g": 0, "w": 0, "roles": Counter()})
    total = 0
    for m in matches:
        for p in m.get("info", {}).get("participants", []):
            name = p.get("championName")
            if not name:
                continue
            total += 1
            champs[name]["g"] += 1
            champs[name]["w"] += 1 if p.get("win") else 0
            role = p.get("teamPosition") or p.get("individualPosition") or ""
            if role:
                champs[name]["roles"][role] += 1

    mn, top = settings.meta_min_games, settings.meta_top_n
    ulist = [
        {
            "n": n,
            "cost": "",
            "wr": _pct(d["w"], d["g"]),
            "use": _pct(d["g"], total),
            "sub": d["roles"].most_common(1)[0][0].title() if d["roles"] else "",
            "chips": [],
        }
        for n, d in champs.items() if d["g"] >= mn
    ]
    # Ítems y runas de LoL son ids NUMÉRICOS → requieren mapear con Data Dragon
    # (trabajo futuro). De momento solo agregamos campeones; el router cae al
    # mock para 'items'/'augments' de LoL.
    return {"units": sorted(ulist, key=lambda x: x["use"], reverse=True)[:top], "items": [], "augments": []}


# ---------------------------------- Entrada ----------------------------------
async def run(game: str) -> dict:
    puuids = await _sample_puuids(game, settings.meta_sample_players)
    matches = await _matches(game, puuids)
    agg = _aggregate_tft(matches) if game == "tft" else _aggregate_lol(matches)

    from app.data import mock_lab  # import local: evita ciclo y solo se usa aquí

    agg["styles"] = mock_lab.STYLES.get(game, [])
    agg["sample"] = {"players": len(puuids), "matches": len(matches)}
    agg["generated_at"] = datetime.now(timezone.utc).isoformat()
    agg["source"] = "real"
    return agg
