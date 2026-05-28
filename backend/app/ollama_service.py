"""Capa de comunicacion con Ollama.

Aisla toda la logica de hablar con el servidor de Ollama para que los
endpoints (en main.py) no tengan que saber como funciona la API por dentro.
"""
import json
from collections.abc import AsyncGenerator

import httpx

from .config import settings
from .schemas import Message


class OllamaError(Exception):
    """Error al comunicarse con Ollama (no esta arrancado, modelo inexistente, etc.)."""


async def list_models() -> list[str]:
    """Devuelve los nombres de los modelos disponibles en Ollama."""
    try:
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=10) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
        raise OllamaError(f"No se pudo conectar con Ollama: {exc}") from exc


async def chat(messages: list[Message], model: str | None = None) -> str:
    """Envia la conversacion a Ollama y devuelve la respuesta completa (sin streaming)."""
    model = model or settings.ollama_model
    payload = {
        "model": model,
        "messages": [m.model_dump() for m in messages],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120) as client:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
    except httpx.HTTPStatusError as exc:
        raise OllamaError(
            f"Ollama respondio con error {exc.response.status_code}. "
            f"Comprueba que el modelo '{model}' existe (ollama pull {model})."
        ) from exc
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
        raise OllamaError(f"No se pudo conectar con Ollama: {exc}") from exc


async def chat_stream(messages: list[Message], model: str | None = None) -> AsyncGenerator[str, None]:
    """Igual que chat() pero va devolviendo los trozos de texto segun llegan (streaming)."""
    model = model or settings.ollama_model
    payload = {
        "model": model,
        "messages": [m.model_dump() for m in messages],
        "stream": True,
    }
    try:
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=None) as client:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done"):
                        break
    except httpx.HTTPStatusError as exc:
        raise OllamaError(
            f"Ollama respondio con error {exc.response.status_code}. "
            f"Comprueba que el modelo '{model}' existe (ollama pull {model})."
        ) from exc
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise OllamaError(f"No se pudo conectar con Ollama: {exc}") from exc
