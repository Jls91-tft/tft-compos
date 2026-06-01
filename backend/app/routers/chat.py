"""Chat con el Coach IA — preguntas sobre una partida concreta."""
from fastapi import APIRouter, HTTPException

from app.schemas.models import ChatRequest, ChatResponse
from app.services import coaching_engine
from app.services.riot_client import RiotApiError
from app.services.ollama_client import OllamaError

router = APIRouter(tags=["coaching"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Responde una pregunta sobre la partida (mock o IA local según USE_MOCK)."""
    try:
        answer = await coaching_engine.answer_question(
            req.game, req.match_id, req.question, req.riot_id, req.lang
        )
    except RiotApiError as e:
        raise HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return ChatResponse(answer=answer)
