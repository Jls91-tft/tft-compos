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


def save_explorer(game: str, payload: dict) -> None:
    (_dir() / f"explorer_{game}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_explorer(game: str) -> dict | None:
    f = _dir() / f"explorer_{game}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
