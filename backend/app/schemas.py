"""Modelos de datos (Pydantic) que definen la forma de las peticiones y respuestas."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------- Chat sin estado (heredado de la Fase 1) ----------
class Message(BaseModel):
    """Un mensaje individual de la conversacion (formato que entiende Ollama)."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Chat sin guardar: el frontend envia el historial completo."""
    messages: list[Message] = Field(..., min_length=1)
    model: str | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str


# ---------- Conversaciones persistentes (Fase 2) ----------
class MessageOut(BaseModel):
    """Un mensaje tal y como se devuelve al cliente (desde la BD)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    """Resumen de una conversacion para la lista lateral (sin los mensajes)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class DocumentOut(BaseModel):
    """Un documento (PDF) adjunto, sin su texto completo (solo metadatos)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    char_count: int
    created_at: datetime


class ConversationDetail(ConversationSummary):
    """Conversacion completa, con todos sus mensajes y documentos."""
    messages: list[MessageOut] = []
    documents: list[DocumentOut] = []


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationUpdate(BaseModel):
    """Para renombrar una conversacion."""
    title: str = Field(..., min_length=1, max_length=200)


class SendMessageRequest(BaseModel):
    """El usuario envia un mensaje nuevo dentro de una conversacion."""
    content: str = Field(..., min_length=1)
    model: str | None = None


# ---------- Tareas / recordatorios (Fase 4) ----------
Priority = Literal["alta", "media", "baja"]


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    due_date: date | None
    priority: Priority
    done: bool
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    due_date: date | None = None
    priority: Priority = "media"


class TaskUpdate(BaseModel):
    """Todos los campos opcionales: se actualiza solo lo que llegue."""
    title: str | None = Field(default=None, min_length=1, max_length=300)
    due_date: date | None = None
    priority: Priority | None = None
    done: bool | None = None


# ---------- Memoria global (cross-conversacion) ----------
class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: datetime


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


# ---------- Estado del servicio ----------
class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    models: list[str]
