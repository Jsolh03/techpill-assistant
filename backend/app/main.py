"""Punto de entrada de la API (FastAPI).

Fase 1: chat con IA local via Ollama.
Fase 2: persistencia de conversaciones en SQLite (historial).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import chat, conversations, documents, memories, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar: crea las tablas de la BD si no existen.
    init_db()
    yield


app = FastAPI(
    title="TechPill Assistant API",
    description="Asistente personal con IA local (Ollama). Fase 2: historial de conversaciones.",
    version="0.2.0",
    lifespan=lifespan,
)

# Permite que el frontend de React (otro origen/puerto) llame a esta API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(tasks.router)
app.include_router(memories.router)
