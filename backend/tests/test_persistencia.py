"""Tests de persistencia (FASE 2): job de análisis idempotente sobre la BD.

Sin red: la partida se pre-inserta con su payload, así que el job no llama a
la Riot API.
"""
import json

from sqlalchemy import select

from app.db import sesion
from app.models import Hechos, Partida, UsuarioBeta
from app.services import facts_engine
from app.worker import jobs


def test_job_extrae_y_es_idempotente(match_sintetico):
    with sesion() as s:
        s.add(UsuarioBeta(puuid="puuid-7", riot_id="Prueba#TST", region="euw1"))
        s.add(Partida(
            match_id="EUW1_TEST0001",
            puuid="puuid-7",
            payload_json=json.dumps(match_sintetico, ensure_ascii=False),
        ))
        s.commit()

    # Primera ejecución: extrae hechos y genera el informe.
    r1 = jobs.analizar_partida("EUW1_TEST0001", "puuid-7")
    assert "hechos extraídos" in r1 and "informe generado" in r1

    # Segunda ejecución: no duplica ni regenera (cacheado por versión).
    r2 = jobs.analizar_partida("EUW1_TEST0001", "puuid-7")
    assert "hechos ya existentes" in r2 and "informe ya existente" in r2

    with sesion() as s:
        filas = list(s.scalars(select(Hechos).where(Hechos.puuid == "puuid-7")))
        assert len(filas) == 1
        snapshot = json.loads(filas[0].hechos_json)
        assert snapshot["engine_version"] == facts_engine.ENGINE_VERSION
        assert snapshot["jugador"]["ronda_eliminacion"] == "6-2"
        assert snapshot["contestacion"]["max_rivales_compartiendo"] == 3

        from app.models import Informe
        informes = list(s.scalars(select(Informe).where(Informe.puuid == "puuid-7")))
        assert len(informes) == 1
        cuerpo = json.loads(informes[0].informe_json)
        assert cuerpo["catalogo_version"] == informes[0].catalogo_version
        assert cuerpo["titulo"]            # siempre hay titular, haya señales o no
