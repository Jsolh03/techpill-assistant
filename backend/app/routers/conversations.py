"""CRUD de conversaciones: crear, listar, ver, renombrar y borrar."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/conversations", tags=["conversaciones"])


def _get_or_404(db: Session, conversation_id: int) -> models.Conversation:
    conv = db.get(models.Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    return conv


@router.get("", response_model=list[schemas.ConversationSummary])
def list_conversations(db: Session = Depends(get_db)):
    """Lista las conversaciones, de la mas reciente a la mas antigua."""
    stmt = select(models.Conversation).order_by(models.Conversation.updated_at.desc())
    return db.scalars(stmt).all()


@router.post("", response_model=schemas.ConversationDetail, status_code=201)
def create_conversation(payload: schemas.ConversationCreate, db: Session = Depends(get_db)):
    """Crea una conversacion vacia."""
    conv = models.Conversation(title=payload.title or "Nueva conversacion")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=schemas.ConversationDetail)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Devuelve una conversacion con todos sus mensajes."""
    return _get_or_404(db, conversation_id)


@router.patch("/{conversation_id}", response_model=schemas.ConversationSummary)
def rename_conversation(
    conversation_id: int, payload: schemas.ConversationUpdate, db: Session = Depends(get_db)
):
    """Renombra una conversacion."""
    conv = _get_or_404(db, conversation_id)
    conv.title = payload.title
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Borra una conversacion y todos sus mensajes."""
    conv = _get_or_404(db, conversation_id)
    db.delete(conv)
    db.commit()
