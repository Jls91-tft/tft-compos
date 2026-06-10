"""Fixtures de los tests del núcleo (FASE 2).

IMPORTANTE: las variables de entorno se fijan ANTES de importar la app para
que el engine apunte a un SQLite de pruebas y no a la BD real.

El match sintético usa identificadores GENÉRICOS (TFT99_*): la decisión
cerrada n.º 10 prohíbe nombres reales del set en datos de ejemplo. El motor
de hechos trata los ids como opacos, así que el test es representativo.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/divisionup_test.db"
os.environ["REDIS_URL"] = ""
os.environ["USE_MOCK"] = "false"

import pytest  # noqa: E402

from app.db import Base, engine  # noqa: E402
import app.models  # noqa: F401,E402 — registra las tablas


@pytest.fixture(scope="session", autouse=True)
def esquema_bd():
    """BD de pruebas limpia para toda la sesión."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _unidad(uid: str, coste: int, estrellas: int, items: list[str] | None = None) -> dict:
    return {
        "character_id": uid,
        "rarity": coste - 1,
        "tier": estrellas,
        "itemNames": items or [],
    }


def _participante(puuid: str, puesto: int, nivel: int, oro: int, ultima_ronda: int,
                  dano: int, unidades: list[dict], rasgos: list[dict] | None = None) -> dict:
    return {
        "puuid": puuid,
        "placement": puesto,
        "level": nivel,
        "gold_left": oro,
        "last_round": ultima_ronda,
        "total_damage_to_players": dano,
        "players_eliminated": 0,
        "time_eliminated": 1800.0,
        "units": unidades,
        "traits": rasgos or [],
    }


@pytest.fixture
def match_sintetico() -> dict:
    """Partida de 8 jugadores. El jugador analizado es puuid-7 (7.º puesto):
    nivel 8, 2 de oro al morir, eliminado en la ronda 34 (etapa 6-2), carry
    con 3 ítems de daño y línea contestada por 3 rivales."""
    carro = "TFT99_CarroA"          # unidad clave contestada
    tanque = "TFT99_TanqueA"
    relleno = ["TFT99_Uno", "TFT99_Dos", "TFT99_Tres", "TFT99_Cuatro"]

    yo = _participante(
        "puuid-7", puesto=7, nivel=8, oro=2, ultima_ronda=34, dano=61,
        unidades=[
            _unidad(carro, 4, 2, ["TFT_Item_InfinityEdge", "TFT_Item_Deathblade", "TFT_Item_GiantSlayer"]),
            _unidad(tanque, 4, 2, ["TFT_Item_BrambleVest"]),
            _unidad(relleno[0], 2, 2),
            _unidad(relleno[1], 2, 2),
            _unidad(relleno[2], 1, 2),
            _unidad(relleno[3], 1, 2),
            _unidad("TFT99_Cinco", 3, 1),
            _unidad("TFT99_Seis", 3, 1),
        ],
        rasgos=[
            {"name": "TFT99_RasgoX", "style": 2, "num_units": 4, "tier_current": 2},
            {"name": "TFT99_RasgoY", "style": 1, "num_units": 2, "tier_current": 1},
            {"name": "TFT99_RasgoZ", "style": 0, "num_units": 1, "tier_current": 0},
        ],
    )

    # Tres rivales juegan mi misma unidad clave (contestación = 3).
    def rival(i: int, puesto: int, nivel: int, con_carro: bool, dano: int) -> dict:
        unidades = [_unidad(f"TFT99_R{i}_{j}", 2, 2) for j in range(7)]
        if con_carro:
            unidades.append(_unidad(carro, 4, 2))
        else:
            unidades.append(_unidad(f"TFT99_R{i}_x", 4, 2))
        return _participante(f"puuid-{i}", puesto, nivel, oro=10, ultima_ronda=38,
                             dano=dano, unidades=unidades)

    participantes = [
        rival(1, 1, 10, con_carro=True, dano=160),
        rival(2, 2, 9, con_carro=True, dano=130),
        rival(3, 3, 9, con_carro=True, dano=110),
        rival(4, 4, 9, con_carro=False, dano=95),
        rival(5, 5, 8, con_carro=False, dano=80),
        rival(6, 6, 8, con_carro=False, dano=70),
        yo,
        rival(8, 8, 7, con_carro=False, dano=40),
    ]
    return {
        "metadata": {"match_id": "EUW1_TEST0001"},
        "info": {
            "queue_id": 1100,
            "game_length": 2100.5,
            "game_datetime": 1750000000000,
            "game_version": "Version test",
            "participants": participantes,
        },
    }
