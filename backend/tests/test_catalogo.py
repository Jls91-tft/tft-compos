"""Tests del catálogo (CAPA 2) sobre el golden dataset — deterministas."""
import json
from pathlib import Path

import pytest

from app.catalog import CATALOG_VERSION, PATRONES, POR_ID
from app.core.config import settings
from app.services import facts_engine, pattern_evaluator

GOLDEN = Path(__file__).parent / "golden"


@pytest.fixture
def golden_contestada() -> dict:
    return json.loads((GOLDEN / "contestada_7o.json").read_text(encoding="utf-8"))


def _evaluar(match, puuid):
    hechos = facts_engine.extraer(match, puuid)
    return hechos, pattern_evaluator.evaluar(hechos)


def test_catalogo_bien_formado():
    assert len(PATRONES) == 10
    assert len(POR_ID) == 10
    for p in PATRONES:
        # las seis piezas del esquema
        assert p.id.startswith("P-") and p.nombre and 1 <= p.severidad <= 4
        assert callable(p.disparador) and callable(p.contraevidencia) and callable(p.confianza)
        assert "{" in p.plantilla_es or p.plantilla_es     # plantilla en castellano
        assert p.objetivo_es                                # regla entrenable
        assert p.telemetria == {"acierta": 0, "falla": 0}


def test_perdedor_contestado_dispara_p001(golden_contestada):
    _, ev = _evaluar(golden_contestada, "puuid-7")
    ids = [s["patron_id"] for s in ev["senales"]]
    assert ids[0] == "P-001"            # señal dominante: contestación sin densidad
    p001 = ev["senales"][0]
    assert p001["severidad"] == 4
    assert p001["confianza"] == 0.8     # 0.6 + 0.15·(3-2) + 0.05·1
    assert "3 rivales" in p001["texto"]
    assert p001["pregunta"]             # pregunta de coach presente
    assert ev["catalogo_version"] == CATALOG_VERSION


def test_ganador_sin_senales(golden_contestada):
    _, ev = _evaluar(golden_contestada, "puuid-1")
    assert ev["senales"] == []          # partida limpia: no se fabrica nada


def test_contraevidencia_anula_y_se_registra(golden_contestada):
    hechos = facts_engine.extraer(golden_contestada, "puuid-7")
    # Forzamos el escenario reroll: 2 unidades a 3★ anulan P-001 (y P-007).
    hechos["jugador"]["densidad_3"] = 2
    ev = pattern_evaluator.evaluar(hechos)
    ids_senales = [s["patron_id"] for s in ev["senales"]]
    assert "P-001" not in ids_senales
    descartado = next(d for d in ev["descartadas"] if d["patron_id"] == "P-001")
    assert "reroll" in descartado["motivo"]


def test_umbral_configurable_descarta(golden_contestada, monkeypatch):
    monkeypatch.setattr(settings, "senal_umbral", 5.0)   # imposible de superar (max 0.95×4)
    _, ev = _evaluar(golden_contestada, "puuid-7")
    assert ev["senales"] == []
    assert any("confianza insuficiente" in d["motivo"] for d in ev["descartadas"])


def test_oro_bajo_no_es_senal(golden_contestada):
    """Terminar con poco oro es NORMAL: ningún patrón castiga el oro bajo."""
    _, ev = _evaluar(golden_contestada, "puuid-7")      # cerró con 2 de oro
    assert all(s["patron_id"] not in ("P-002", "P-006", "P-010") for s in ev["senales"])
