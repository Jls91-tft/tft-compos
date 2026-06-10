"""Esquema inicial del núcleo de análisis (FASE 2).

Revision ID: 0001
Revises:
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios_beta",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("puuid", sa.String(100), nullable=False),
        sa.Column("riot_id", sa.String(40), nullable=False),
        sa.Column("region", sa.String(10), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("puuid"),
    )
    op.create_index("ix_usuarios_beta_puuid", "usuarios_beta", ["puuid"])

    op.create_table(
        "partidas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("match_id", sa.String(30), nullable=False),
        sa.Column("puuid", sa.String(100), sa.ForeignKey("usuarios_beta.puuid", ondelete="CASCADE"), nullable=False),
        sa.Column("game_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("queue_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("match_id", "puuid", name="uq_partida_jugador"),
    )
    op.create_index("ix_partidas_match_id", "partidas", ["match_id"])
    op.create_index("ix_partidas_puuid", "partidas", ["puuid"])

    op.create_table(
        "hechos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("partida_id", sa.Integer(), sa.ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("puuid", sa.String(100), nullable=False),
        sa.Column("engine_version", sa.String(20), nullable=False),
        sa.Column("hechos_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("partida_id", "engine_version", name="uq_hechos_version"),
    )
    op.create_index("ix_hechos_partida_id", "hechos", ["partida_id"])
    op.create_index("ix_hechos_puuid", "hechos", ["puuid"])

    op.create_table(
        "informes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("partida_id", sa.Integer(), sa.ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("puuid", sa.String(100), nullable=False),
        sa.Column("hechos_id", sa.Integer(), sa.ForeignKey("hechos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("catalogo_version", sa.String(20), nullable=False),
        sa.Column("informe_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("partida_id", "catalogo_version", name="uq_informe_version"),
    )
    op.create_index("ix_informes_partida_id", "informes", ["partida_id"])
    op.create_index("ix_informes_puuid", "informes", ["puuid"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("informe_id", sa.Integer(), sa.ForeignKey("informes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patron_id", sa.String(20), nullable=False),
        sa.Column("voto", sa.String(10), nullable=False),
        sa.Column("puuid", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feedback_informe_id", "feedback", ["informe_id"])
    op.create_index("ix_feedback_patron_id", "feedback", ["patron_id"])
    op.create_index("ix_feedback_puuid", "feedback", ["puuid"])

    op.create_table(
        "catalogo_version",
        sa.Column("version", sa.String(20), primary_key=True),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("catalogo_version")
    op.drop_table("feedback")
    op.drop_table("informes")
    op.drop_table("hechos")
    op.drop_table("partidas")
    op.drop_table("usuarios_beta")
