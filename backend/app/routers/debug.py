"""Visor de debug interno (FASE 4) — ruta protegida por token.

Pego un match_id y veo TODOS los hechos extraídos y la evaluación de cada
patrón (disparó / descartado / por qué, con valores). Solo para diagnóstico
interno de la beta.

Protección: DEBUG_TOKEN en el .env. Sin token configurado, las rutas devuelven
404 (el visor "no existe"). El token viaja como query (?token=...) — uso
interno puntual, no una API pública.

  GET /debug?token=...                      formulario HTML mínimo
  GET /debug/json?token=&match_id=&riot_id= evaluación verbosa en JSON
"""
import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select

from app.core.config import settings
from app.db import sesion
from app.models import Partida, UsuarioBeta
from app.services import facts_engine, pattern_evaluator
from app.services.riot_client import RiotApiError, riot_client

router = APIRouter(prefix="/debug", tags=["debug"])


def _exigir_token(token: str) -> None:
    if not settings.debug_token:
        raise HTTPException(status_code=404)            # visor desactivado
    if token != settings.debug_token:
        raise HTTPException(status_code=403, detail="Token incorrecto.")


async def _puuid_de(riot_id: str) -> str:
    rid = (riot_id or "").strip()
    if "#" not in rid:
        raise HTTPException(status_code=400, detail="riot_id en formato Nombre#TAG.")
    with sesion() as s:
        u = s.scalar(select(UsuarioBeta).where(func.lower(UsuarioBeta.riot_id) == rid.lower()))
    if u is not None:
        return u.puuid
    nombre, tag = rid.split("#", 1)
    try:
        return await riot_client.get_puuid(nombre.strip(), tag.strip())
    except RiotApiError as e:
        raise HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)


@router.get("/json")
async def debug_json(
    token: str = Query(default=""),
    match_id: str = Query(...),
    riot_id: str = Query(...),
):
    _exigir_token(token)
    puuid = await _puuid_de(riot_id)

    # Partida de BD si existe (reproducible); si no, se baja de Riot al vuelo.
    with sesion() as s:
        partida = s.scalar(select(Partida).where(Partida.match_id == match_id))
    if partida is not None:
        match = json.loads(partida.payload_json)
        origen = "bd"
    else:
        try:
            match = await riot_client.get_match(match_id, "tft")
        except RiotApiError as e:
            raise HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)
        origen = "riot"

    try:
        hechos = facts_engine.extraer(match, puuid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    detalle = pattern_evaluator.evaluar_debug(hechos)
    detalle["match_id"] = match_id
    detalle["origen_payload"] = origen
    detalle["engine_version"] = facts_engine.ENGINE_VERSION
    return detalle


_HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>DivisionUp · debug</title>
<style>body{font-family:monospace;background:#070B12;color:#EAF1FA;padding:24px;max-width:980px;margin:0 auto}
input,button{font-family:inherit;padding:8px 12px;background:#101724;color:#EAF1FA;border:1px solid #2B3B52;border-radius:6px}
button{cursor:pointer;background:#16314f}
table{border-collapse:collapse;margin-top:18px;width:100%}
td,th{border:1px solid #1F2C3E;padding:6px 10px;text-align:left;font-size:13px;vertical-align:top}
.ok{color:#53E0C4}.no{color:#62758F}.desc{color:#F0668F}
pre{background:#05080D;border:1px solid #1F2C3E;padding:14px;overflow:auto;font-size:12px}</style></head>
<body><h2>Visor de debug · motor de hechos + catálogo</h2>
<form onsubmit="ev(event)">
<input id="m" placeholder="match_id (EUW1_...)" size="24" required>
<input id="r" placeholder="Riot ID (Nombre#TAG)" size="20" required>
<button>Evaluar</button></form>
<div id="out"></div>
<script>
const token = new URLSearchParams(location.search).get('token') || '';
async function ev(e){
  e.preventDefault();
  const out = document.getElementById('out');
  out.textContent = 'evaluando…';
  const u = `/api/debug/json?token=${encodeURIComponent(token)}&match_id=${encodeURIComponent(document.getElementById('m').value.trim())}&riot_id=${encodeURIComponent(document.getElementById('r').value.trim())}`;
  const res = await fetch(u);
  if(!res.ok){ out.textContent = 'ERROR ' + res.status + ': ' + await res.text(); return; }
  const d = await res.json();
  const filas = d.patrones.map(p => `<tr>
    <td>${p.patron_id}</td><td>${p.nombre}</td><td>SEV ${p.severidad}</td>
    <td class="${p.disparo?'ok':'no'}">${p.disparo?'disparó':'—'}</td>
    <td class="desc">${p.contraevidencia||''}</td>
    <td>${p.confianza??''}</td>
    <td class="${p.publicada?'ok':'no'}">${p.publicada?'PUBLICADA':''}</td></tr>`).join('');
  out.innerHTML = `<p>match <b>${d.match_id}</b> · payload: ${d.origen_payload} · motor ${d.engine_version} · catálogo ${d.catalogo_version} · umbral ${d.umbral}</p>
  <table><tr><th>id</th><th>patrón</th><th>sev</th><th>disparo</th><th>contraevidencia</th><th>confianza</th><th>estado</th></tr>${filas}</table>
  <h3>Hechos planos</h3><pre>${JSON.stringify(d.hechos_planos, null, 2)}</pre>`;
}
</script></body></html>"""


@router.get("", response_class=HTMLResponse)
def debug_html(token: str = Query(default="")):
    _exigir_token(token)
    return HTMLResponse(_HTML)
