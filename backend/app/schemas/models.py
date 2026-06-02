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
    # meta de caché (opcionales; las rellena el servidor, no rompen el contrato)
    prompt_version: str = ""
    model: str = ""
    generated_at: str = ""
    stale: bool = False


# ---------- Plan de mejora global (multi-partida) ----------
class RecurringWeakness(BaseModel):
    title: str
    frequency_pct: int = 0
    avg_severity: float = 0
    evidence: str = ""


class RoadmapItem(BaseModel):
    focus: str
    drills: list[str] = []
    resource: str = ""           # qué practicar, modo, tipo de oponente
    success_metric: str = ""     # métrica de éxito medible


class Roadmap(BaseModel):
    this_week: list[RoadmapItem] = []
    this_month: list[RoadmapItem] = []
    next_3_months: list[RoadmapItem] = []


class ImprovementPlan(BaseModel):
    game: Game
    summary: str = ""
    recurring_weaknesses: list[RecurringWeakness] = []
    root_causes: list[str] = []
    roadmap: Roadmap = Roadmap()
    priority_order: list[str] = []
    based_on_match_ids: list[str] = []
    new_matches: int = 0
    prompt_version: str = ""
    model: str = ""
    generated_at: str = ""


# ---------- Chat con el coach ----------
class ChatRequest(BaseModel):
    game: Game
    match_id: str
    question: str
    riot_id: str = ""            # opcional: da contexto de partida al chat real
    lang: str = "es"             # idioma de la respuesta del coach (es | en)


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
