"""Contratos de datos (Pydantic) que la API expone y el frontend consume.

Definir esto primero nos da un 'contrato' estable: el frontend puede integrarse
contra estos modelos aunque por dentro aún devolvamos mocks. Al conectar Riot e
IA en fases posteriores, la forma de la respuesta no cambia.
"""
from typing import Literal, Optional
from pydantic import BaseModel

Game = Literal["tft", "lol"]


# ---------- Partidas ----------
class MatchCard(BaseModel):
    id: str
    game: Game
    result: str                  # TFT: "1".."8" · LoL: "win"/"loss"
    title: str                   # comp (TFT) o "rol · arquetipo" (LoL)
    meta: dict                   # nivel/duración/nota (TFT) o kda/cs/duración (LoL)


# ---------- Coaching ----------
class CoachingMetric(BaseModel):
    value: str
    label: str
    status: Literal["good", "warn", "bad", ""] = ""
    benchmark: Optional[str] = None


class CoachingError(BaseModel):
    title: str
    severity: Literal["major", "minor"]
    what: str                    # qué pasó
    why: str                     # por qué te costó
    fix: str                     # cómo subsanarlo
    when: str                    # el momento


class CoachingReport(BaseModel):
    game: Game
    match_id: str
    verdict: str
    focus: str                   # foco para la próxima partida
    metrics: list[CoachingMetric]
    did_well: list[str]
    errors: list[CoachingError]
    corrective: str
    action_plan: list[str]


# ---------- Chat con el coach ----------
class ChatRequest(BaseModel):
    game: Game
    match_id: str
    question: str
    riot_id: str = ""            # opcional: da contexto de partida al chat real


class ChatResponse(BaseModel):
    answer: str


# ---------- Meta ----------
class MetaComp(BaseModel):
    tier: Literal["S", "A", "B", "C"]
    name: str
    style: str
    difficulty: str
    metrics: dict                # coloc/top4/win/pick (TFT) o win/pick/ban/kda (LoL)
    units: list[dict] = []       # [{"n": "Místico", "c": 4}]  (vacío en LoL)
