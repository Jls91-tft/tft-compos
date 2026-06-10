"""Lista de espera de la beta cerrada — POST /waitlist.

Validación estricta en servidor (el frontend solo orienta):
  - email con formato razonable
  - riot_id con formato Nombre#TAG (3-16 caracteres + tag 2-5)
  - rango y frecuencia dentro de las opciones del formulario
  - consentimiento RGPD obligatorio (sin él, 422)

Sin dependencias nuevas: validación por regex, persistencia SQLite stdlib.
"""
import re

from fastapi import APIRouter, HTTPException

from app.schemas.models import WaitlistRequest
from app.services import waitlist_store

router = APIRouter(tags=["waitlist"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_RIOT_ID_RE = re.compile(r"^[^#]{3,16}#[^#\s]{2,5}$")

RANGOS_VALIDOS = {"Hierro / Bronce", "Plata / Oro", "Platino / Esmeralda", "Diamante", "Master+"}
FRECUENCIAS_VALIDAS = {"1 – 5", "6 – 15", "16 – 30", "Más de 30"}


@router.post("/waitlist")
def join_waitlist(req: WaitlistRequest):
    email = (req.email or "").strip().lower()
    riot_id = (req.riot_id or "").strip()

    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="El email no tiene un formato válido.")
    if not _RIOT_ID_RE.match(riot_id):
        raise HTTPException(status_code=422, detail="El Riot ID debe tener el formato Nombre#TAG.")
    if req.rango not in RANGOS_VALIDOS:
        raise HTTPException(status_code=422, detail="Elige un rango de la lista.")
    if req.partidas_semana not in FRECUENCIAS_VALIDAS:
        raise HTTPException(status_code=422, detail="Elige una frecuencia de la lista.")
    if not req.consentimiento:
        raise HTTPException(status_code=422, detail="Necesitamos tu consentimiento para consultar tus partidas.")

    waitlist_store.save(email, riot_id, req.rango, req.partidas_semana)
    return {"ok": True}
