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


class DecisionError(BaseModel):
    timestamp: Optional[str] = None                       # "12:30" (LoL) o "Etapa 4-1" (TFT)
    phase: Optional[Literal["early", "mid", "late"]] = None
    what_happened: str
    why_wrong: str
    better_action: str
    severity: int = 3                                      # 1-5
    evidence: str                                          # cita un timestamp/stat concreto


class CoachingIssue(BaseModel):                            # micro (mecánica) y macro
    title: str
    detail: str
    evidence: str
    severity: Optional[int] = None


class MentalPattern(BaseModel):
    pattern: str
    detail: str
    evidence: str


class CoachingReport(BaseModel):
    game: Game
    match_id: str
    summary: str = ""                                      # veredicto en 1-2 frases
    metrics: list[CoachingMetric] = []                     # KPIs derivados (servidor, sin LLM)
    decision_errors: list[DecisionError] = []
    mechanical_issues: list[CoachingIssue] = []
    macro_issues: list[CoachingIssue] = []
    mental_patterns: list[MentalPattern] = []
    strengths: list[str] = []                             # qué hiciste bien (con dato concreto)
    comparison: str = ""                                  # comparación con el Top 1 (TFT) / referencia del rol (LoL)
    top_3_actionable: list[str] = []
    # meta de caché (opcionales; las rellena el servidor)
    prompt_version: str = ""
    model: str = ""
    generated_at: str = ""
    stale: bool = False
    context: dict = {}                                    # datos para la UI (curva 10/15, muertes por fase, rango); no del LLM


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
