"""Tests del objetivo semanal — patrón recurrente, progreso y ✓/✗ por partida."""
import json

from app.catalog import CATALOG_VERSION
from app.db import sesion
from app.models import Hechos, Informe, Partida, UsuarioBeta
from app.services import objective_engine


def _sembrar_informes(puuid: str, senales_por_partida: list[list[str]]) -> None:
    """Crea usuario + partidas + informes mínimos con los patron_id indicados."""
    with sesion() as s:
        s.add(UsuarioBeta(puuid=puuid, riot_id=f"Obj#{puuid[-3:]}", region="euw1"))
        for i, ids in enumerate(senales_por_partida):
            partida = Partida(match_id=f"EUW1_OBJ{i:04d}_{puuid[-3:]}", puuid=puuid, payload_json="{}")
            s.add(partida)
            s.flush()
            hechos = Hechos(partida_id=partida.id, puuid=puuid, engine_version="0.1.0", hechos_json="{}")
            s.add(hechos)
            s.flush()
            cuerpo = {
                "match_id": partida.match_id,
                "senales": [{"patron_id": pid, "severidad": 4, "confianza": 0.8,
                             "texto": "x", "pregunta": None} for pid in ids],
            }
            s.add(Informe(partida_id=partida.id, puuid=puuid, hechos_id=hechos.id,
                          catalogo_version=CATALOG_VERSION,
                          informe_json=json.dumps(cuerpo, ensure_ascii=False)))
        s.commit()


def test_objetivo_del_patron_recurrente():
    # P-001 dispara en 4 de 6 partidas → objetivo = P-001, cumplidas 2/6.
    _sembrar_informes("puuid-obj-a", [
        ["P-001"], ["P-001", "P-008"], [], ["P-001"], ["P-001"], ["P-002"],
    ])
    obj = objective_engine.calcular("puuid-obj-a")
    assert obj is not None
    assert obj["patron_id"] == "P-001"
    assert obj["apariciones"] == 4
    assert obj["ventana"] == 6
    assert obj["cumplidas"] == 2
    assert "pivota" in obj["regla"].lower()

    marcas = objective_engine.cumplimiento_por_partida("puuid-obj-a")
    assert len(marcas) == 6
    assert sum(1 for v in marcas.values() if v) == 2


def test_sin_recurrencia_no_se_inventa_objetivo():
    # Ningún patrón llega al mínimo de apariciones → None (no fabricamos).
    _sembrar_informes("puuid-obj-b", [["P-001"], ["P-002"], [], ["P-008"]])
    assert objective_engine.calcular("puuid-obj-b") is None
    assert objective_engine.cumplimiento_por_partida("puuid-obj-b") == {}
