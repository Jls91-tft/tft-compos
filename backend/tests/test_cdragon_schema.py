"""Canario del esquema de CommunityDragon (FASE 4).

Si CDragon cambia el formato de su JSON (pasa al cambiar de set), este test
FALLA RUIDOSAMENTE para que lo veamos antes que los usuarios. Necesita red:
sin conexión se marca como skip (no como pass silencioso).
"""
import pytest

from app.services import cdragon_client


@pytest.fixture(scope="module")
def indice():
    try:
        idx = cdragon_client.index()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"CDragon inaccesible (sin red): {e}")
    if not idx.get("champions"):
        pytest.fail("CDragon respondió pero SIN campeones: el esquema ha cambiado — revisar cdragon_client.")
    return idx


def test_set_activo_detectado(indice):
    assert indice["set_number"] >= 10, "No se detecta el número de set — esquema setData cambiado"


def test_campeones_con_campos_minimos(indice):
    assert len(indice["champions"]) >= 40, "Menos de 40 campeones: ¿bloque del set incompleto?"
    for api, c in list(indice["champions"].items())[:10]:
        assert c["name"], f"Campeón {api} sin nombre"
        assert isinstance(c["cost"], int), f"Campeón {api} sin coste entero"
        assert c["icon"] is None or c["icon"].startswith("https://"), f"Icono raro en {api}"


def test_rasgos_e_items_presentes(indice):
    assert len(indice["traits"]) >= 15, "Menos de 15 rasgos: esquema de traits cambiado"
    assert len(indice["items"]) >= 50, "Menos de 50 ítems: esquema de items cambiado"


def test_lookup_relajado_funciona(indice):
    # El lookup por nombre limpio es lo que usa el pipeline de meta.
    cualquiera = next(iter(indice["champions"].values()))
    encontrado = cdragon_client.lookup(indice, "champions", cualquiera["name"])
    assert encontrado is not None and encontrado["name"] == cualquiera["name"]
