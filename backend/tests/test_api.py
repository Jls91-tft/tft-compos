"""Tests de los endpoints del núcleo (FASE 4) — TestClient sobre SQLite, sin red."""
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db import sesion
from app.main import app
from app.models import Partida, UsuarioBeta
from app.worker import jobs

cliente = TestClient(app)
RIOT_ID = "Api#TST"
PUUID = "puuid-api"
MATCH = "EUW1_API0001"


@pytest.fixture(autouse=True)
def _siembra(match_sintetico):
    """Usuario + partida + hechos + informe (vía el job real, sin red).
    Idempotente: la BD es de sesión y el job cachea por versión."""
    m = json.loads(json.dumps(match_sintetico))
    m["metadata"]["match_id"] = MATCH
    # El jugador analizado del match sintético es puuid-7 → lo mapeamos al usuario API.
    for p in m["info"]["participants"]:
        if p["puuid"] == "puuid-7":
            p["puuid"] = PUUID
    with sesion() as s:
        if s.query(UsuarioBeta).filter_by(puuid=PUUID).first() is None:
            s.add(UsuarioBeta(puuid=PUUID, riot_id=RIOT_ID, region="euw1"))
            s.add(Partida(match_id=MATCH, puuid=PUUID, payload_json=json.dumps(m, ensure_ascii=False)))
            s.commit()
    jobs.analizar_partida(MATCH, PUUID)
    yield


def test_matches_requiere_riot_id():
    assert cliente.get("/matches").status_code == 400


def test_matches_usuario_no_registrado():
    assert cliente.get("/matches", params={"riot_id": "NoExiste#XXX"}).status_code == 403


def test_matches_lista_informes():
    r = cliente.get("/matches", params={"riot_id": RIOT_ID})
    assert r.status_code == 200
    item = next(i for i in r.json() if i["match_id"] == MATCH)
    assert item["puesto"] == 7
    assert item["titulo"] == "Línea contestada"
    assert item["senales"] >= 1


def test_report_completo_y_votos():
    r = cliente.get(f"/report/{MATCH}", params={"riot_id": RIOT_ID})
    assert r.status_code == 200
    inf = r.json()
    assert inf["titulo"] == "Línea contestada"
    assert inf["hipotesis"].startswith("mantuviste")

    # Voto ✓/✗ persistente y con upsert (revotar sustituye, no acumula).
    r = cliente.post("/feedback", params={"riot_id": RIOT_ID},
                     json={"match_id": MATCH, "patron_id": "P-001", "voto": "falla"})
    assert r.status_code == 200
    r = cliente.post("/feedback", params={"riot_id": RIOT_ID},
                     json={"match_id": MATCH, "patron_id": "P-001", "voto": "acierta"})
    assert r.status_code == 200
    inf = cliente.get(f"/report/{MATCH}", params={"riot_id": RIOT_ID}).json()
    assert inf["votos"] == {"P-001": "acierta"}


def test_feedback_validaciones():
    r = cliente.post("/feedback", params={"riot_id": RIOT_ID},
                     json={"match_id": MATCH, "patron_id": "P-001", "voto": "regular"})
    assert r.status_code == 422
    r = cliente.post("/feedback", params={"riot_id": RIOT_ID},
                     json={"match_id": MATCH, "patron_id": "P-999", "voto": "falla"})
    assert r.status_code == 422


def test_objective_endpoint():
    r = cliente.get("/objective", params={"riot_id": RIOT_ID})
    assert r.status_code == 200
    assert "objetivo" in r.json()      # objeto o null: nunca inventado


def test_debug_protegido(monkeypatch):
    # Sin token configurado: el visor "no existe".
    monkeypatch.setattr(settings, "debug_token", "")
    assert cliente.get("/debug", params={"token": "x"}).status_code == 404
    # Con token: HTML del visor y JSON verboso de la evaluación.
    monkeypatch.setattr(settings, "debug_token", "secreto")
    assert cliente.get("/debug", params={"token": "mal"}).status_code == 403
    assert cliente.get("/debug", params={"token": "secreto"}).status_code == 200
    r = cliente.get("/debug/json", params={"token": "secreto", "match_id": MATCH, "riot_id": RIOT_ID})
    assert r.status_code == 200
    d = r.json()
    assert len(d["patrones"]) == 10
    p001 = next(p for p in d["patrones"] if p["patron_id"] == "P-001")
    assert p001["disparo"] is True and p001["publicada"] is True
    assert d["origen_payload"] == "bd"


def test_borrado_rgpd():
    # ÚLTIMO test del módulo: borra al usuario sembrado.
    r = cliente.request("DELETE", "/account", params={"riot_id": RIOT_ID})
    assert r.status_code == 200
    assert cliente.get("/matches", params={"riot_id": RIOT_ID}).status_code == 403
