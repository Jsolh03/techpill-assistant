"""Modelos ORM (las tablas de la base de datos).

Una conversacion (Conversation) tiene muchos mensajes (Message).
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="Nueva conversacion")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Si se borra la conversacion, se borran sus mensajes (cascade).
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )
    # Documentos (PDFs) adjuntos a la conversacion.
    documents: Mapped[list["Document"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Document.id",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Document(Base):
    """Un PDF subido a una conversacion. Guardamos su texto extraido."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(300))
    char_count: Mapped[int] = mapped_column(default=0)
    content: Mapped[str] = mapped_column(Text)  # texto extraido del PDF
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="documents")


class Memory(Base):
    """Un dato que el usuario ha pedido recordar (memoria GLOBAL, no por conversacion).

    Se inyecta en el contexto de todas las conversaciones, asi el asistente "recuerda"
    el dato aunque cambies de conversacion.
    """
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Task(Base):
    """Una tarea o recordatorio personal del usuario (global, no por conversacion)."""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # fecha limite
    priority: Mapped[str] = mapped_column(String(10), default="media")  # alta | media | baja
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
