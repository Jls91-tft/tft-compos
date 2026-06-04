"""Almacén en disco de los datos de meta generados por el worker (JSON).

El worker (app/worker/refresh_meta.py) ESCRIBE; la API (routers/lab.py) LEE.
Si no hay fichero, devuelve None y el router cae al mock genérico (mock_lab).
"""
import json
from pathlib import Path

from app.core.config import settings


def _dir() -> Path:
    p = Path(settings.meta_data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save(name: str, payload: dict) -> None:
    (_dir() / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load(name: str) -> dict | None:
    f = _dir() / name
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_explorer(game: str, payload: dict) -> None:
    _save(f"explorer_{game}.json", payload)


def load_explorer(game: str) -> dict | None:
    return _load(f"explorer_{game}.json")


def save_comps(game: str, payload: dict) -> None:
    """Tier list de comps generada por comps_pipeline (solo TFT por ahora)."""
    _save(f"comps_{game}.json", payload)


def load_comps(game: str) -> dict | None:
    return _load(f"comps_{game}.json")
