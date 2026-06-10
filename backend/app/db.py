"""Acceso a la base de datos relacional (FASE 2).

Motor único de SQLAlchemy para toda la app:
- Producción (compose): PostgreSQL vía DATABASE_URL.
- Fallback/tests: SQLite (mismo código; sirve para la opción B si la VM no aguanta).

El esquema se gestiona con Alembic (backend/alembic). En tests se usa
``Base.metadata.create_all`` sobre SQLite en memoria.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _crear_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        # SQLite necesita check_same_thread=False para FastAPI/RQ y el PRAGMA
        # para que los ON DELETE CASCADE se comporten como en Postgres
        # (sin él, el borrado RGPD dejaría filas huérfanas en los tests).
        eng = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(eng, "connect")
        def _activar_fk(dbapi_con, _rec):
            dbapi_con.execute("PRAGMA foreign_keys=ON")

        return eng
    # pool_pre_ping evita conexiones muertas tras reinicios de Postgres en la VM.
    return create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2)


engine = _crear_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def sesion() -> Session:
    """Sesión nueva. Usar con context manager: ``with sesion() as s: ...``"""
    return SessionLocal()
