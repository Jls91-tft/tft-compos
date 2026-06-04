"""Cliente de CommunityDragon — metadatos del set TFT en vivo.

CDragon (raw.communitydragon.org) es un CDN comunitario que indexa los assets
oficiales del cliente de LoL/TFT. Es lo mismo que usan MetaTFT, Lolchess y
Tactics.tools para mostrar iconos y nombres del set actual. Es gratuito y
respeta los términos de Riot (no es scraping, son los propios assets del juego).

De aquí sacamos:
- Nombres traducidos de campeones, rasgos, ítems y aumentos.
- URLs de iconos PNG (CDragon convierte .dds/.tex internamente).
- Identificación del SET activo (el más alto en setData).

El JSON pesa ~10 MB; cacheamos a disco con TTL de 24 h.

Esto NO requiere clave Riot — funciona desde el día 1.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from app.core.config import settings


_LOCALE_DEFAULT = "es_es"
_CACHE_TTL_SECONDS = 24 * 60 * 60
_CDRAGON_URL = "https://raw.communitydragon.org/latest/cdragon/tft/{locale}.json"
_ICON_CDN = "https://raw.communitydragon.org/latest/game/"


def _cache_path(locale: str) -> Path:
    d = Path(settings.meta_data_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"cdragon_tft_{locale}.json"


def icon_url(raw_path: str | None) -> str | None:
    """Convierte 'ASSETS/Foo/Bar.dds' (lo que viene en el JSON) en una URL PNG del CDN."""
    if not raw_path:
        return None
    p = raw_path.strip().lower()
    # CDragon sirve .png; el JSON suele decir .dds / .tex / .tex2 / .skn.
    for ext in (".dds", ".tex2", ".tex", ".skn"):
        if p.endswith(ext):
            p = p[: -len(ext)] + ".png"
            break
    if not p.endswith(".png"):
        p += ".png"
    return _ICON_CDN + p.lstrip("/")


def _fetch(locale: str) -> dict:
    """Descarga el JSON crudo de CDragon (puede tardar; ~10 MB)."""
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        r = client.get(_CDRAGON_URL.format(locale=locale))
        r.raise_for_status()
        return r.json()


def _load_cached(locale: str) -> dict | None:
    p = _cache_path(locale)
    if not p.exists():
        return None
    age = time.time() - p.stat().st_mtime
    if age > _CACHE_TTL_SECONDS:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _save_cache(locale: str, payload: dict) -> None:
    _cache_path(locale).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


# ------------------------------- API pública -------------------------------
def raw(locale: str = _LOCALE_DEFAULT, force: bool = False) -> dict:
    """JSON entero (cacheado). force=True ignora la caché y vuelve a bajarlo."""
    if not force:
        cached = _load_cached(locale)
        if cached is not None:
            return cached
    data = _fetch(locale)
    _save_cache(locale, data)
    return data


def active_set(data: dict) -> dict | None:
    """Devuelve el bloque del SET ACTIVO (el de número más alto en setData)."""
    sets = data.get("setData") or []
    if not sets:
        # Formato alternativo: {"sets": {"14": {...}}}
        alt = data.get("sets") or {}
        if alt:
            best_key = max(alt.keys(), key=lambda k: int(k) if k.isdigit() else -1)
            block = dict(alt[best_key])
            block.setdefault("number", int(best_key) if best_key.isdigit() else 0)
            return block
        return None
    return max(sets, key=lambda s: int(s.get("number") or 0))


def index(locale: str = _LOCALE_DEFAULT) -> dict:
    """Índice ligero por apiName: {champions, traits, items, augments, set_number, set_name}.

    Cada valor es {name, cost?, icon, traits?} con la info que el frontend necesita.
    Si CDragon no responde, devuelve un dict vacío para que el caller pueda caer al
    mock invented.
    """
    try:
        data = raw(locale)
    except Exception:   # red caída, JSON malformado, etc. — el caller cae al mock invented
        return {"champions": {}, "traits": {}, "items": {}, "augments": {}, "set_number": 0, "set_name": ""}

    aset = active_set(data) or {}
    set_number = int(aset.get("number") or 0)
    set_name = aset.get("name") or ""

    champions = {}
    for c in aset.get("champions") or []:
        api = c.get("apiName") or c.get("characterName") or ""
        if not api:
            continue
        champions[api] = {
            "name": c.get("name") or api,
            "cost": int(c.get("cost") or 0),
            "icon": icon_url(c.get("icon") or c.get("squareIcon") or c.get("tileIcon")),
            "traits": c.get("traits") or [],
        }

    traits = {}
    for t in aset.get("traits") or []:
        api = t.get("apiName") or t.get("name") or ""
        if not api:
            continue
        traits[api] = {
            "name": t.get("name") or api,
            "icon": icon_url(t.get("icon")),
        }

    # Los ítems y aumentos suelen estar fuera del bloque del set (a nivel raíz).
    items = {}
    for it in data.get("items") or []:
        api = it.get("apiName") or it.get("nameId") or ""
        if not api:
            continue
        items[api] = {
            "name": it.get("name") or api,
            "icon": icon_url(it.get("icon")),
        }

    augments = {}
    for a in data.get("setAugments") or data.get("augments") or []:
        api = a.get("apiName") or ""
        if not api:
            continue
        augments[api] = {
            "name": a.get("name") or api,
            "icon": icon_url(a.get("icon")),
        }
    # Algunos sets meten los aumentos como ítems con "tier" o flag isAugment;
    # los exponemos también desde items para que la búsqueda no falle.
    for api, meta in items.items():
        if "augment" in api.lower() and api not in augments:
            augments[api] = meta

    return {
        "champions": champions,
        "traits": traits,
        "items": items,
        "augments": augments,
        "set_number": set_number,
        "set_name": set_name,
    }


# ------------------------- Resolución por nombre crudo -------------------------
def _candidates(name: str, set_number: int, kind: str) -> list[str]:
    """Lista de apiNames probables para un nombre limpio (sin TFT_*)."""
    snake = name.replace(" ", "")
    out = [
        f"TFT{set_number}_{snake}",
        f"TFT{set_number}_{name}",
        f"TFT_{kind}_{snake}",
        snake,
        name,
    ]
    return out


def lookup(idx: dict, kind: str, raw_or_name: str) -> dict | None:
    """Busca por apiName exacto o por nombre limpio.

    `kind` ∈ {champions, traits, items, augments}.
    Devuelve {name, cost?, icon, traits?} o None.
    """
    if not raw_or_name:
        return None
    bucket = idx.get(kind) or {}
    # Hit directo por apiName.
    if raw_or_name in bucket:
        return bucket[raw_or_name]
    # Por nombre limpio: probamos varios prefijos del set actual.
    set_n = idx.get("set_number") or 0
    item_kind = "Item" if kind == "items" else "Augment" if kind == "augments" else ""
    for cand in _candidates(raw_or_name, set_n, item_kind):
        if cand in bucket:
            return bucket[cand]
    # Búsqueda relajada por display name (case-insensitive).
    needle = raw_or_name.lower()
    for meta in bucket.values():
        if (meta.get("name") or "").lower() == needle:
            return meta
    return None
