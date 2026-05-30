"""Chat con el Coach IA — preguntas sobre una partida concreta."""
from fastapi import APIRouter
from app.schemas.models import ChatRequest, ChatResponse
from app.services import coaching_engine

router = APIRouter(tags=["coaching"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Responde una pregunta sobre la partida (mock en Fase 0; IA en Fase 2)."""
    answer = coaching_engine.answer_question(req.game, req.match_id, req.question)
    return ChatResponse(answer=answer)
