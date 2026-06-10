"""API del núcleo de análisis (FASE 4) — lo que consume la app v3.

  GET    /matches            partidas analizadas del jugador (con ✓/✗ de objetivo)
  GET    /report/{match_id}  informe template-first + votos previos del usuario
  POST   /feedback           voto ✓/✗ por señal (telemetría por patrón)
  GET    /objective          objetivo semanal activo (o null, sin inventar)
  GET    /rank               rango/LP actuales (Riot API)
  DELETE /account            borrado RGPD completo (cascada por puuid)

Modelo de acceso de la beta: el riot_id identifica al usuario registrado en
``usuarios_beta`` (alta vía app.worker.registrar). Sin registro → 403.
"""
import json

from fastapi import APIRouter, Body, HTTPException, Query
from sqlalchemy import delete as sa_delete, func, select

from app.catalog import CATALOG_VERSION, POR_ID
from app.db import sesion
from app.models import Feedback, Informe, Partida, UsuarioBeta
from app.services import objective_engine
from app.services.riot_client import RiotApiError, riot_client

router = APIRouter(tags=["analisis"])


def _usuario(s, riot_id: str) -> UsuarioBeta:
    rid = (riot_id or "").strip()
    if not rid:
        raise HTTPException(status_code=400, detail="Indica tu Riot ID (?riot_id=Nombre%23TAG).")
    u = s.scalar(select(UsuarioBeta).where(func.lower(UsuarioBeta.riot_id) == rid.lower(),
                                           UsuarioBeta.activo == True))  # noqa: E712
    if u is None:
        raise HTTPException(status_code=403, detail="Tu cuenta aún no está activada en la beta.")
    return u


@router.get("/matches")
def list_matches(riot_id: str = Query(default="")):
    """Partidas con informe, recientes primero, con la marca ✓/✗ del objetivo."""
    with sesion() as s:
        u = _usuario(s, riot_id)
        filas = s.execute(
            select(Informe, Partida)
            .join(Partida, Informe.partida_id == Partida.id)
            .where(Informe.puuid == u.puuid, Informe.catalogo_version == CATALOG_VERSION)
            .order_by(Partida.game_datetime.desc().nullslast(), Informe.id.desc())
            .limit(20)
        ).all()
        marcas = objective_engine.cumplimiento_por_partida(u.puuid)
        out = []
        for informe, partida in filas:
            cuerpo = json.loads(informe.informe_json)
            out.append({
                "match_id": partida.match_id,
                "puesto": cuerpo.get("puesto"),
                "titulo": cuerpo.get("titulo", ""),
                "senales": len(cuerpo.get("senales", [])),
                "fecha": partida.game_datetime.isoformat() if partida.game_datetime else None,
                "objetivo": marcas.get(partida.match_id),   # true/false, o null sin objetivo
            })
        return out


@router.get("/report/{match_id}")
def get_report(match_id: str, riot_id: str = Query(default="")):
    """Informe completo (cacheado, determinista) + votos previos del usuario."""
    with sesion() as s:
        u = _usuario(s, riot_id)
        fila = s.execute(
            select(Informe, Partida)
            .join(Partida, Informe.partida_id == Partida.id)
            .where(Partida.match_id == match_id, Informe.puuid == u.puuid,
                   Informe.catalogo_version == CATALOG_VERSION)
        ).first()
        if fila is None:
            raise HTTPException(status_code=404, detail="Esa partida aún no tiene informe.")
        informe, _ = fila
        cuerpo = json.loads(informe.informe_json)
        votos = s.execute(
            select(Feedback.patron_id, Feedback.voto)
            .where(Feedback.informe_id == informe.id, Feedback.puuid == u.puuid)
        ).all()
        cuerpo["votos"] = {p: v for p, v in votos}
        cuerpo["objetivo_cumplido"] = objective_engine.cumplimiento_por_partida(u.puuid).get(match_id)
        return cuerpo


@router.post("/feedback")
def post_feedback(
    riot_id: str = Query(default=""),
    datos: dict = Body(...),
):
    """Persiste el voto ✓/✗ de una señal. Un voto por (informe, patrón, usuario):
    revotar sustituye el anterior."""
    match_id = (datos.get("match_id") or "").strip()
    patron_id = (datos.get("patron_id") or "").strip()
    voto = (datos.get("voto") or "").strip()
    if voto not in ("acierta", "falla"):
        raise HTTPException(status_code=422, detail="El voto debe ser 'acierta' o 'falla'.")
    if patron_id not in POR_ID:
        raise HTTPException(status_code=422, detail="Patrón desconocido.")
    with sesion() as s:
        u = _usuario(s, riot_id)
        informe = s.execute(
            select(Informe).join(Partida, Informe.partida_id == Partida.id)
            .where(Partida.match_id == match_id, Informe.puuid == u.puuid,
                   Informe.catalogo_version == CATALOG_VERSION)
        ).scalar()
        if informe is None:
            raise HTTPException(status_code=404, detail="Esa partida aún no tiene informe.")
        s.execute(sa_delete(Feedback).where(
            Feedback.informe_id == informe.id,
            Feedback.patron_id == patron_id,
            Feedback.puuid == u.puuid,
        ))
        s.add(Feedback(informe_id=informe.id, patron_id=patron_id, voto=voto, puuid=u.puuid))
        s.commit()
    return {"ok": True}


@router.get("/objective")
def get_objective(riot_id: str = Query(default="")):
    """Objetivo semanal activo. Si no hay patrón recurrente: null (no se fabrica)."""
    with sesion() as s:
        u = _usuario(s, riot_id)
    return {"objetivo": objective_engine.calcular(u.puuid)}


@router.get("/rank")
async def get_rank(riot_id: str = Query(default="")):
    """Rango/LP actuales del jugador (contexto del topbar)."""
    with sesion() as s:
        u = _usuario(s, riot_id)
    try:
        return await riot_client.get_rank(u.puuid, "tft") or {}
    except RiotApiError as e:
        raise HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)


@router.delete("/account")
def delete_account(riot_id: str = Query(default="")):
    """Borrado RGPD completo: usuario + partidas + hechos + informes + feedback
    (cascada por puuid). Irreversible."""
    with sesion() as s:
        u = _usuario(s, riot_id)
        puuid = u.puuid
        # Feedback no cuelga de usuarios_beta: se borra explícitamente por puuid.
        s.execute(sa_delete(Feedback).where(Feedback.puuid == puuid))
        s.delete(u)   # cascada BD: partidas → hechos / informes
        s.commit()
    return {"ok": True, "eliminado": riot_id}
