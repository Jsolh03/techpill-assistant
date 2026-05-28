"""Endpoints de chat y estado del servicio.

- /api/health                              -> estado de Ollama
- /api/conversations/{id}/chat/stream      -> chat dentro de una conversacion (se guarda)
- /api/chat  y  /api/chat/stream           -> chat sin estado (heredado de la Fase 1)
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, ollama_service, schemas
from ..config import settings
from ..database import get_db

router = APIRouter(tags=["chat"])

# Personalidad del asistente. Ahora la define el backend (es el dueno del historial).
SYSTEM_PROMPT = schemas.Message(
    role="system",
    content=(
        "Eres TechPill Assistant, un asistente personal util, claro y conciso. "
        "Respondes en el idioma del usuario."
    ),
)


@router.get("/api/health", response_model=schemas.HealthResponse)
async def health() -> schemas.HealthResponse:
    """Comprueba si Ollama esta accesible y que modelos hay instalados."""
    try:
        models_list = await ollama_service.list_models()
        return schemas.HealthResponse(status="ok", ollama_connected=True, models=models_list)
    except ollama_service.OllamaError:
        return schemas.HealthResponse(status="ollama_unavailable", ollama_connected=False, models=[])


@router.post("/api/conversations/{conversation_id}/chat/stream")
async def conversation_chat_stream(
    conversation_id: int,
    payload: schemas.SendMessageRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Anade el mensaje del usuario, pide respuesta a la IA en streaming y guarda todo."""
    conv = db.get(models.Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    # 1) Guardamos el mensaje del usuario.
    user_msg = models.Message(conversation_id=conv.id, role="user", content=payload.content)
    db.add(user_msg)

    # Si es el primer mensaje, usamos su texto como titulo de la conversacion.
    if conv.title in ("", "Nueva conversacion"):
        conv.title = payload.content[:60] + ("…" if len(payload.content) > 60 else "")

    db.commit()

    # 2) Construimos el historial que enviaremos a Ollama (system + toda la conversacion).
    db.refresh(conv)
    history = [SYSTEM_PROMPT] + [
        schemas.Message(role=m.role, content=m.content)
        for m in conv.messages
        if m.role in ("user", "assistant")
    ]

    async def event_generator():
        full_reply = ""
        try:
            async for piece in ollama_service.chat_stream(history, payload.model):
                full_reply += piece
                yield piece
        except ollama_service.OllamaError as exc:
            yield f"\n\n[Error: {exc}]"
        finally:
            # 3) Al terminar (o si se corta), guardamos lo que haya respondido la IA.
            if full_reply.strip():
                db.add(
                    models.Message(
                        conversation_id=conv.id, role="assistant", content=full_reply
                    )
                )
                db.commit()

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")


# ---------- Chat sin estado (Fase 1, sigue disponible) ----------
@router.post("/api/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest) -> schemas.ChatResponse:
    try:
        reply = await ollama_service.chat(request.messages, request.model)
        return schemas.ChatResponse(reply=reply, model=request.model or settings.ollama_model)
    except ollama_service.OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/chat/stream")
async def chat_stream(request: schemas.ChatRequest) -> StreamingResponse:
    async def event_generator():
        try:
            async for piece in ollama_service.chat_stream(request.messages, request.model):
                yield piece
        except ollama_service.OllamaError as exc:
            yield f"\n\n[Error: {exc}]"

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")
