"""Tests del motor de hechos (CAPA 1) — deterministas, sin red."""
import json

from app.services import facts_engine
from app.services.facts_engine import extraer, ronda_a_etapa


def test_ronda_a_etapa():
    assert ronda_a_etapa(1) == "1-1"
    assert ronda_a_etapa(4) == "1-4"
    assert ronda_a_etapa(5) == "2-1"
    assert ronda_a_etapa(11) == "2-7"
    assert ronda_a_etapa(12) == "3-1"
    assert ronda_a_etapa(34) == "6-2"
    assert ronda_a_etapa(0) == ""


def test_jugador_basico(match_sintetico):
    h = extraer(match_sintetico, "puuid-7")
    yo = h["jugador"]
    assert h["engine_version"] == facts_engine.ENGINE_VERSION
    assert h["match_id"] == "EUW1_TEST0001"
    assert yo["puesto"] == 7
    assert yo["nivel_final"] == 8
    assert yo["oro_al_morir"] == 2
    assert yo["ronda_eliminacion"] == "6-2"
    # 6 unidades a 2★ (carro, tanque y 4 de relleno); ninguna 3★
    assert yo["densidad_2mas"] == 6
    assert yo["densidad_3"] == 0
    # rasgos: solo los activos (style >= 1), ordenados por nivel
    assert [r["id"] for r in yo["rasgos"]] == ["RasgoX", "RasgoY"]


def test_carry_por_items_de_dano(match_sintetico):
    yo = extraer(match_sintetico, "puuid-7")["jugador"]
    assert yo["carry"] is not None
    assert yo["carry"]["id"] == "CarroA"            # el de los ítems de daño, no el tanque
    assert yo["carry"]["items_de_dano"] == 3
    assert yo["carry"]["itemizada_completa"] is True


def test_contestacion(match_sintetico):
    c = extraer(match_sintetico, "puuid-7")["contestacion"]
    assert c["max_rivales_compartiendo"] == 3       # 3 rivales juegan mi unidad clave
    carro = next(d for d in c["unidades_clave"] if d["unidad"] == "CarroA")
    assert carro["rivales_con_ella"] == 3


def test_podio_es_media_del_top4(match_sintetico):
    podio = extraer(match_sintetico, "puuid-7")["lobby"]["podio"]
    # niveles del top 4: 10, 9, 9, 9 → media 9.25 (VS podio, no VS Top 1)
    assert podio["nivel_medio"] == 9.25


def test_percentiles(match_sintetico):
    p = extraer(match_sintetico, "puuid-7")["percentiles"]
    # niveles del lobby: [10,9,9,9,8,8,8,7] → con nivel 8, 4 de 8 son <= → 50
    assert p["nivel"] == 50
    assert 0 <= p["dano_a_jugadores"] <= 100


def test_determinismo(match_sintetico):
    a = json.dumps(extraer(match_sintetico, "puuid-7"), sort_keys=True)
    b = json.dumps(extraer(match_sintetico, "puuid-7"), sort_keys=True)
    assert a == b


def test_puuid_desconocido(match_sintetico):
    import pytest
    with pytest.raises(ValueError):
        extraer(match_sintetico, "puuid-no-existe")
