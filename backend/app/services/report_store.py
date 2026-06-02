"""Persistencia de informes de coaching y planes de mejora (SQLite, stdlib).

No añade dependencias: usa `sqlite3` de la librería estándar y crea las tablas al
vuelo (CREATE TABLE IF NOT EXISTS). Lo usa SOLO el módulo de Coaching.

  match_reports(id, user_key, game, match_id, report_json, prompt_version, model, status, generated_at)
  improvement_plans(id, user_key, game, plan_json, based_on_match_ids, prompt_version, model, generated_at)

`user_key` = Riot ID normalizado. Los informes NO se sobrescriben: cada generación
INSERTA una fila (versionado); se lee siempre la más reciente por (user_key, game, match_id).
"""
import json
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
        path = Path(settings.reports_db)
        path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS match_reports(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_key TEXT NOT NULL, game TEXT NOT NULL, match_id TEXT NOT NULL,
              report_json TEXT NOT NULL, prompt_version TEXT, model TEXT,
              status TEXT DEFAULT 'ok', generated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS ix_reports ON match_reports(user_key, game, match_id, id);
            CREATE TABLE IF NOT EXISTS improvement_plans(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_key TEXT NOT NULL, game TEXT NOT NULL,
              plan_json TEXT NOT NULL, based_on_match_ids TEXT,
              prompt_version TEXT, model TEXT, generated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS ix_plans ON improvement_plans(user_key, game, id);
            """
        )
        _conn.commit()
    return _conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_key(riot_id: str) -> str:
    return (riot_id or "").strip().lower()


# ----------------------------- Informes -----------------------------
def get_report(user_key: str, game: str, match_id: str) -> dict | None:
    with _lock:
        row = _db().execute(
            "SELECT * FROM match_reports WHERE user_key=? AND game=? AND match_id=? AND status='ok' "
            "ORDER BY id DESC LIMIT 1",
            (user_key, game, match_id),
        ).fetchone()
    if not row:
        return None
    rep = json.loads(row["report_json"])
    rep["prompt_version"] = row["prompt_version"] or ""
    rep["model"] = row["model"] or ""
    rep["generated_at"] = row["generated_at"] or ""
    return rep


def save_report(user_key, game, match_id, report: dict, prompt_version, model, status="ok") -> dict:
    ts = _now()
    with _lock:
        _db().execute(
            "INSERT INTO match_reports(user_key,game,match_id,report_json,prompt_version,model,status,generated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (user_key, game, match_id, json.dumps(report, ensure_ascii=False), prompt_version, model, status, ts),
        )
        _db().commit()
    out = dict(report)
    out["prompt_version"], out["model"], out["generated_at"] = prompt_version, model, ts
    return out


def latest_reports(user_key, game, limit: int) -> list[dict]:
    """Informe más reciente por match_id (status ok), hasta `limit`, recientes primero."""
    with _lock:
        rows = _db().execute(
            """SELECT r.* FROM match_reports r
               JOIN (SELECT match_id, MAX(id) AS mid FROM match_reports
                     WHERE user_key=? AND game=? AND status='ok' GROUP BY match_id) m
               ON r.id = m.mid ORDER BY r.id DESC LIMIT ?""",
            (user_key, game, limit),
        ).fetchall()
    out = []
    for row in rows:
        rep = json.loads(row["report_json"])
        rep["match_id"] = row["match_id"]
        out.append(rep)
    return out


# ----------------------------- Planes -----------------------------
def get_plan(user_key, game) -> dict | None:
    with _lock:
        row = _db().execute(
            "SELECT * FROM improvement_plans WHERE user_key=? AND game=? ORDER BY id DESC LIMIT 1",
            (user_key, game),
        ).fetchone()
    if not row:
        return None
    plan = json.loads(row["plan_json"])
    plan["based_on_match_ids"] = json.loads(row["based_on_match_ids"] or "[]")
    plan["prompt_version"] = row["prompt_version"] or ""
    plan["model"] = row["model"] or ""
    plan["generated_at"] = row["generated_at"] or ""
    return plan


def save_plan(user_key, game, plan: dict, based_on_match_ids, prompt_version, model) -> dict:
    ts = _now()
    with _lock:
        _db().execute(
            "INSERT INTO improvement_plans(user_key,game,plan_json,based_on_match_ids,prompt_version,model,generated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (user_key, game, json.dumps(plan, ensure_ascii=False), json.dumps(based_on_match_ids), prompt_version, model, ts),
        )
        _db().commit()
    out = dict(plan)
    out["based_on_match_ids"] = based_on_match_ids
    out["prompt_version"], out["model"], out["generated_at"] = prompt_version, model, ts
    return out
