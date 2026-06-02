"""Mapa de nombres internos de Riot (TFT) → nombres mostrables, vía Data Dragon.

match-v1 devuelve nombres internos (p. ej. el rasgo 'TFT13_Bastion' o la unidad
'TFT13_Xayah'). Para que el informe sea profesional mostramos el nombre real.
Se descarga UNA vez por proceso y se cachea. Si la descarga falla o falta una
clave, caemos al id limpiado (último segmento) — el mismo comportamiento de antes,
así que nunca hay regresión.
"""
import httpx

_TRAIT_MAP: dict[str, str] = {}
_UNIT_MAP: dict[str, str] = {}
_loaded = False


def _clean(raw: str) -> str:
    return (raw or "").split("_")[-1]


async def ensure_loaded() -> None:
    """Descarga (1 vez) el mapa de nombres de TFT desde Data Dragon. Tolerante a fallos."""
    global _loaded
    if _loaded:
        return
    _loaded = True  # marcamos aunque falle: no reintentamos en cada informe
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            versions = (await c.get("https://ddragon.leagueoflegends.com/api/versions.json")).json()
            ver = versions[0]
            base = f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US"
            traits = (await c.get(f"{base}/tft-trait.json")).json().get("data", {})
            champs = (await c.get(f"{base}/tft-champion.json")).json().get("data", {})
        for key, val in traits.items():
            name = (val or {}).get("name")
            if name:
                _TRAIT_MAP[key.lower()] = name
        for key, val in champs.items():
            name = (val or {}).get("name")
            if name:
                _UNIT_MAP[key.lower()] = name
    except Exception:
        pass  # sin mapa → trait_display/unit_display caen al id limpiado


def trait_display(raw: str) -> str:
    return _TRAIT_MAP.get((raw or "").lower()) or _clean(raw)


def unit_display(raw: str) -> str:
    return _UNIT_MAP.get((raw or "").lower()) or _clean(raw)
