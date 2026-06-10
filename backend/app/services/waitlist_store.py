"""Persistencia de la lista de espera de la beta (SQLite, stdlib).

Mismo patrón que report_store: sqlite3 de la librería estándar, tabla creada al
vuelo, sin dependencias nuevas. Fichero propio (waitlist.db) dentro del volumen
persistido en producción (app/data/generated).

Una solicitud por email: reenviar actualiza los datos (idempotente). El
consentimiento RGPD se guarda con su timestamp.
"""
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

_lock = threading.Lock()
_conn = None


def _db():
    global _conn
    if _conn is None:
        path = Path(settings.waitlist_db)
        path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS waitlist(
              email TEXT PRIMARY KEY,
              riot_id TEXT NOT NULL,
              rango TEXT NOT NULL,
              partidas_semana TEXT NOT NULL,
              consent_at TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        _conn.commit()
    return _conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(email: str, riot_id: str, rango: str, partidas_semana: str) -> None:
    """Inserta o actualiza la solicitud (clave: email normalizado)."""
    ts = _now()
    with _lock:
        _db().execute(
            """INSERT INTO waitlist(email, riot_id, rango, partidas_semana, consent_at, created_at, updated_at)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(email) DO UPDATE SET
                 riot_id=excluded.riot_id, rango=excluded.rango,
                 partidas_semana=excluded.partidas_semana,
                 consent_at=excluded.consent_at, updated_at=excluded.updated_at""",
            (email.strip().lower(), riot_id.strip(), rango, partidas_semana, ts, ts, ts),
        )
        _db().commit()


def count() -> int:
    with _lock:
        row = _db().execute("SELECT COUNT(*) AS n FROM waitlist").fetchone()
    return int(row["n"]) if row else 0
