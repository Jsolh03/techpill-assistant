"""Endpoints de chat y estado del servicio.

- /api/health                              -> estado de Ollama
- /api/conversations/{id}/chat/stream      -> chat dentro de una conversacion (se guarda)
- /api/chat  y  /api/chat/stream           -> chat sin estado (heredado de la Fase 1)
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
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
        "Respondes en el idioma del usuario. "
        "IMPORTANTE: tu y el usuario sois personas DISTINTAS. El usuario es quien te "
        "escribe; tu eres su asistente. Cuando el usuario diga 'soy', 'me llamo', 'mi', "
        "'me', se refiere a SI MISMO (el usuario), nunca a ti. Si te pregunta '¿quien "
        "soy?' o '¿como me llamo?', respondele sobre EL usando 'eres'/'te llamas'."
    ),
)

# Maximo de caracteres de documentos que metemos en el contexto, para no
# desbordar la ventana del modelo. (Mejora futura: trocear + busqueda/RAG.)
MAX_DOC_CHARS = 8000


# Frases que indican que el usuario quiere que recordemos algo de forma permanente.
_TRIGGERS_MEMORIA = (
    "recuerda que",
    "recuerda ",
    "recuerdame",
    "recuérdame",
    "no olvides",
    "ten en cuenta que",
    "apunta que",
    "memoriza",
    "quiero que recuerdes",
)


def _maybe_store_memory(db: Session, content: str) -> bool:
    """Si el mensaje pide recordar algo, lo guarda en la memoria global.

    Deteccion por palabras clave (robusta y predecible). Evita duplicados exactos.
    """
    texto = content.strip()
    bajo = texto.lower()
    if not any(t in bajo for t in _TRIGGERS_MEMORIA):
        return False

    # Evitar guardar el mismo recuerdo dos veces.
    ya_existe = db.scalar(
        select(models.Memory).where(models.Memory.content == texto)
    )
    if ya_existe is not None:
        return False

    db.add(models.Memory(content=texto))
    db.commit()
    return True


def _build_memory_context(db: Session) -> schemas.Message | None:
    """Crea un mensaje de sistema con TODO lo que el usuario ha pedido recordar.

    Se inyecta en todas las conversaciones, asi el asistente recuerda los datos
    aunque se cambie de conversacion.
    """
    memorias = list(db.scalars(select(models.Memory).order_by(models.Memory.id)).all())
    if not memorias:
        return None

    lineas = "\n".join(f"- {m.content}" for m in memorias)
    return schemas.Message(
        role="system",
        content=(
            "MEMORIA PERSONAL DEL USUARIO: datos que el USUARIO te ha pedido recordar. "
            "Estan escritos desde el punto de vista del usuario, asi que cuando una nota "
            "diga 'soy', 'mi', 'me llamo', etc., se refiere al USUARIO, NO a ti. "
            "Tenlas presentes y usalas para responder sobre el usuario:\n" + lineas
        ),
    )


def _build_tasks_context(db: Session) -> schemas.Message:
    """Crea un mensaje de sistema con la fecha de hoy y las tareas pendientes.

    Asi el asistente puede responder a "que tengo esta semana?", "que es lo mas
    urgente?", etc., basandose en las tareas reales del usuario.
    """
    hoy = date.today()
    pendientes = list(
        db.scalars(select(models.Task).where(models.Task.done == False)).all()  # noqa: E712
    )
    pendientes.sort(key=lambda t: (t.due_date is None, t.due_date or date.max))

    if pendientes:
        lineas = []
        for t in pendientes:
            fecha = t.due_date.isoformat() if t.due_date else "sin fecha"
            lineas.append(f"- (#{t.id}) {t.title} | vence: {fecha} | prioridad: {t.priority}")
        tareas_txt = "\n".join(lineas)
    else:
        tareas_txt = "(no hay tareas pendientes)"

    return schemas.Message(
        role="system",
        content=(
            f"Fecha de hoy: {hoy.isoformat()} ({hoy.strftime('%A')}).\n"
            "Estas son las tareas/recordatorios pendientes del usuario. Usalas para "
            "responder preguntas sobre su agenda (que tiene esta semana, que es urgente, "
            "que vence pronto, etc.). No inventes tareas que no esten en la lista.\n\n"
            f"{tareas_txt}"
        ),
    )


def _build_documents_context(conv: models.Conversation) -> schemas.Message | None:
    """Si la conversacion tiene PDFs, crea un mensaje de sistema con su texto."""
    if not conv.documents:
        return None

    bloques: list[str] = []
    restante = MAX_DOC_CHARS
    for doc in conv.documents:
        if restante <= 0:
            break
        trozo = doc.content[:restante]
        recortado = " [...recortado]" if len(doc.content) > len(trozo) else ""
        bloques.append(f"### Documento: {doc.filename}{recortado}\n{trozo}")
        restante -= len(trozo)

    return schemas.Message(
        role="system",
        content=(
            "El usuario ha adjuntado uno o mas documentos. Usa SU CONTENIDO como "
            "fuente principal para responder. Si la respuesta no esta en los "
            "documentos, dilo claramente.\n\n" + "\n\n".join(bloques)
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

    # Si el usuario pide recordar algo, lo guardamos en la memoria GLOBAL.
    _maybe_store_memory(db, payload.content)

    # 2) Construimos el historial que enviaremos a Ollama:
    #    system + memoria global + tareas + (documentos) + toda la conversacion.
    db.refresh(conv)
    history = [SYSTEM_PROMPT]
    memory_context = _build_memory_context(db)
    if memory_context is not None:
        history.append(memory_context)
    history.append(_build_tasks_context(db))
    docs_context = _build_documents_context(conv)
    if docs_context is not None:
        history.append(docs_context)
    history += [
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
