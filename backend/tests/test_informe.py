"""Tests del generador template-first (CAPA 3) — formato y determinismo."""
import json
from pathlib import Path

import pytest

from app.catalog import CATALOG_VERSION
from app.services import facts_engine, pattern_evaluator, report_builder

GOLDEN = Path(__file__).parent / "golden"


@pytest.fixture
def golden_contestada() -> dict:
    return json.loads((GOLDEN / "contestada_7o.json").read_text(encoding="utf-8"))


def _informe(match, puuid):
    hechos = facts_engine.extraer(match, puuid)
    return report_builder.construir(hechos, pattern_evaluator.evaluar(hechos))


def test_informe_completo_formato_app(golden_contestada):
    inf = _informe(golden_contestada, "puuid-7")
    # Estructura que pinta la app v3 (referencia canónica)
    assert inf["titulo"] == "Línea contestada"
    assert inf["hipotesis"].startswith("mantuviste una línea contestada")
    assert inf["puesto"] == 7
    # VS · PODIO DE TU LOBBY (media del top 4, valores tipo 9.25)
    etiquetas = [v["l"] for v in inf["vs_podio"]]
    assert etiquetas == ["NIVEL", "UNID. 2★+", "ÍTEMS CARRY"]
    nivel = inf["vs_podio"][0]
    assert nivel["tu"] == 8 and nivel["podio"] == 9.25
    # Señales con pregunta de coach
    assert inf["senales"][0]["patron_id"] == "P-001"
    assert inf["senales"][0]["pregunta"]
    # Lo que hiciste bien: hechos medibles (carry completa), máx. 2
    assert 1 <= len(inf["bien"]) <= 2
    assert any("itemizada al completo" in b for b in inf["bien"])
    # Hechos verificados crudos + pie con versión
    assert any("oro_al_morir" in l for l in inf["hechos_verificados"])
    assert inf["catalogo_version"] == CATALOG_VERSION
    assert inf["engine_version"] == facts_engine.ENGINE_VERSION


def test_informe_ganador_sin_senales(golden_contestada):
    inf = _informe(golden_contestada, "puuid-1")
    assert inf["titulo"] == "Partida de referencia"
    assert inf["senales"] == []
    assert inf["bien"]                  # siempre hay algo bien hecho que señalar en un top 1


def test_descartados_visibles_en_inspector(golden_contestada):
    hechos = facts_engine.extraer(golden_contestada, "puuid-7")
    hechos["jugador"]["densidad_3"] = 2          # fuerza contraevidencia de P-001
    ev = pattern_evaluator.evaluar(hechos)
    inf = report_builder.construir(hechos, ev)
    assert any(l.startswith("[DESCARTADO] P-001") for l in inf["hechos_verificados"])
    assert any(d["patron_id"] == "P-001" for d in inf["descartados"])


def test_determinismo_total(golden_contestada):
    """Misma partida + misma versión de catálogo = mismo informe, byte a byte."""
    a = json.dumps(_informe(golden_contestada, "puuid-7"), sort_keys=True, ensure_ascii=False)
    b = json.dumps(_informe(golden_contestada, "puuid-7"), sort_keys=True, ensure_ascii=False)
    assert a == b


def test_lenguaje_de_hipotesis(golden_contestada):
    """Decisión cerrada n.º 2: nunca 'veredicto' ni 'error' en el informe."""
    texto = json.dumps(_informe(golden_contestada, "puuid-7"), ensure_ascii=False).lower()
    assert "veredicto" not in texto
    assert "error" not in texto
