"""Modelos del núcleo de análisis (FASE 2).

Seis tablas, según la arquitectura aprobada:
  usuarios_beta     jugadores activos de la beta (puuid = clave pseudónima RGPD)
  partidas          partidas descargadas (payload crudo para reproducibilidad)
  hechos            snapshot del motor de hechos por (partida, jugador, versión)
  informes          informes generados (FASE 3) con su versión de catálogo
  feedback          votos ✓/✗ por señal (telemetría por patrón)
  catalogo_version  registro de versiones del catálogo publicadas

El borrado RGPD elimina en cascada todo lo asociado a un puuid.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class UsuarioBeta(Base):
    __tablename__ = "usuarios_beta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    puuid: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    riot_id: Mapped[str] = mapped_column(String(40))            # Nombre#TAG (visible)
    region: Mapped[str] = mapped_column(String(10), default="euw1")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    partidas: Mapped[list["Partida"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class Partida(Base):
    __tablename__ = "partidas"
    __table_args__ = (UniqueConstraint("match_id", "puuid", name="uq_partida_jugador"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(30), index=True)
    puuid: Mapped[str] = mapped_column(ForeignKey("usuarios_beta.puuid", ondelete="CASCADE"), index=True)
    game_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queue_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)             # match crudo de la Riot API
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)

    usuario: Mapped["UsuarioBeta"] = relationship(back_populates="partidas")
    hechos: Mapped[list["Hechos"]] = relationship(back_populates="partida", cascade="all, delete-orphan")


class Hechos(Base):
    __tablename__ = "hechos"
    __table_args__ = (
        UniqueConstraint("partida_id", "engine_version", name="uq_hechos_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id", ondelete="CASCADE"), index=True)
    puuid: Mapped[str] = mapped_column(String(100), index=True)
    engine_version: Mapped[str] = mapped_column(String(20))
    hechos_json: Mapped[str] = mapped_column(Text)              # snapshot CAPA 1 (reproducibilidad)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)

    partida: Mapped["Partida"] = relationship(back_populates="hechos")


class Informe(Base):
    __tablename__ = "informes"
    __table_args__ = (
        UniqueConstraint("partida_id", "catalogo_version", name="uq_informe_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id", ondelete="CASCADE"), index=True)
    puuid: Mapped[str] = mapped_column(String(100), index=True)
    hechos_id: Mapped[int] = mapped_column(ForeignKey("hechos.id", ondelete="CASCADE"))
    catalogo_version: Mapped[str] = mapped_column(String(20))
    informe_json: Mapped[str] = mapped_column(Text)             # informe template-first (FASE 3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    informe_id: Mapped[int] = mapped_column(ForeignKey("informes.id", ondelete="CASCADE"), index=True)
    patron_id: Mapped[str] = mapped_column(String(20), index=True)   # ej. "P-014"
    voto: Mapped[str] = mapped_column(String(10))                    # "acierta" | "falla"
    puuid: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)


class CatalogoVersion(Base):
    __tablename__ = "catalogo_version"

    version: Mapped[str] = mapped_column(String(20), primary_key=True)  # semver, ej. "1.0.0"
    descripcion: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)
