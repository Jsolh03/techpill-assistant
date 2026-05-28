# 💊 TechPill Assistant

Asistente personal con **IA local** (sin enviar tus datos a internet). Funciona
sobre [Ollama](https://ollama.com), con un backend en **Python + FastAPI** y un
frontend en **React (Vite)**.

> Proyecto por fases. **Fase 5 (actual): selector de modelos + pulido.** ✅ Todas las fases completas.

![estado](https://img.shields.io/badge/fases-1--5%20completas-brightgreen) ![python](https://img.shields.io/badge/python-3.12-3776ab) ![react](https://img.shields.io/badge/react-19-61dafb) ![sqlite](https://img.shields.io/badge/sqlite-SQLAlchemy-003b57) ![ollama](https://img.shields.io/badge/IA-Ollama%20local-000000)

---

## ✨ Funciones

- 💬 **Chat con IA local** con respuestas en *streaming* (palabra a palabra) y
  **formato Markdown**: bloques de código con resaltado y botón de copiar, listas, tablas…
- 🗂️ **Historial de conversaciones** persistente y con memoria de contexto.
- 📎 **Analiza PDFs y TXT**: adjúntalos y pide resúmenes o preguntas tipo test.
- 📋 **Tareas y recordatorios** con fecha y prioridad; la IA conoce tu agenda
  (*"¿qué tengo esta semana?"*).
- 🧠 **Memoria global entre conversaciones**: dile *"recuerda que…"* en cualquier chat
  y lo recordará en **todos** los demás.
- 🔀 **Selector de modelos** de Ollama desde la interfaz (se recuerda entre sesiones).
- 🔒 **100% local y privado**: tus datos no salen de tu equipo.

---

## 🧱 Arquitectura

```
Navegador (React, :5173)
        │  /api/...  (proxy de Vite)
        ▼
Backend FastAPI (:8000) ──► SQLite (techpill.db)   [historial]
        │  HTTP
        ▼
Ollama (:11434)  ──►  modelo local (ej. qwen2.5-coder:7b)
```

- **`backend/`** — API FastAPI.
  - `ollama_service.py` — aísla la comunicación con Ollama.
  - `pdf_service.py` — extracción de texto de PDFs (pypdf).
  - `database.py` / `models.py` — SQLite + SQLAlchemy (conversaciones, mensajes, documentos, tareas, memoria).
  - `routers/` — endpoints separados por tema (`chat`, `conversations`, `documents`, `tasks`, `memories`).
- **`frontend/`** — interfaz de chat en React con barra lateral de historial, streaming
  y adjuntado de PDFs.

El backend es el **dueño del historial**: al enviar un mensaje carga toda la
conversación desde la BD y se la pasa a la IA, así el asistente "recuerda" el contexto.
Si la conversación tiene **PDFs adjuntos**, su texto se inyecta como contexto para que
la IA responda basándose en ellos. Además, en cada mensaje se inyectan la **fecha de hoy
y tus tareas pendientes**, de modo que el asistente puede responder a *"¿qué tengo esta
semana?"* o *"¿qué es lo más urgente?"* basándose en tu agenda real.

También existe una **memoria global**: cuando dices *"recuerda que…"* (o *"no olvides…"*,
*"ten en cuenta que…"*) en cualquier conversación, el dato se guarda y se inyecta en el
contexto de **todas** las conversaciones. Así, si en un chat pides recordar tu número
favorito, en otro chat distinto el asistente lo seguirá sabiendo.

---

## ✅ Requisitos

- [Python 3.12+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/) y npm
- [Ollama](https://ollama.com/) instalado y en marcha, con al menos un modelo:
  ```bash
  ollama pull qwen2.5-coder:7b
  ```

---

## 🚀 Cómo arrancar

Necesitas **dos terminales** (backend y frontend). Ollama debe estar corriendo de fondo.

### 1) Backend (FastAPI)

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # en Linux/macOS: cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

- API en `http://localhost:8000`
- Documentación interactiva en `http://localhost:8000/docs`

### 2) Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Abre **http://localhost:5173**.

---

## ⚙️ Configuración

Edita `backend/.env` (copiado de `.env.example`):

| Variable          | Por defecto                  | Descripción                              |
|-------------------|------------------------------|------------------------------------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434`     | Dónde escucha Ollama                     |
| `OLLAMA_MODEL`    | `qwen2.5-coder:7b`           | Modelo por defecto                       |
| `CORS_ORIGINS`    | `http://localhost:5173,...`  | Orígenes permitidos para el frontend     |

Para usar otro modelo, descárgalo con `ollama pull <modelo>` y cámbialo en `.env`.

---

## 🔌 Endpoints de la API

| Método   | Ruta                                          | Descripción                                   |
|----------|-----------------------------------------------|-----------------------------------------------|
| `GET`    | `/api/health`                                 | Estado del servicio y modelos disponibles     |
| `GET`    | `/api/conversations`                          | Lista las conversaciones                      |
| `POST`   | `/api/conversations`                          | Crea una conversación                         |
| `GET`    | `/api/conversations/{id}`                     | Conversación con todos sus mensajes           |
| `PATCH`  | `/api/conversations/{id}`                     | Renombra una conversación                     |
| `DELETE` | `/api/conversations/{id}`                     | Borra la conversación (y sus mensajes)        |
| `POST`   | `/api/conversations/{id}/chat/stream`         | Envía un mensaje; guarda y responde en streaming |
| `POST`   | `/api/conversations/{id}/documents`           | Sube un PDF o TXT (multipart) y extrae su texto |
| `GET`    | `/api/conversations/{id}/documents`           | Lista los documentos adjuntos                  |
| `DELETE` | `/api/documents/{id}`                         | Quita un documento adjunto                     |
| `GET`    | `/api/tasks`                                  | Lista las tareas (pendientes primero, por fecha/prioridad) |
| `POST`   | `/api/tasks`                                  | Crea una tarea (título, fecha límite, prioridad) |
| `PATCH`  | `/api/tasks/{id}`                             | Actualiza una tarea (marcar hecha, cambiar fecha…) |
| `DELETE` | `/api/tasks/{id}`                             | Borra una tarea                               |
| `GET`    | `/api/memories`                               | Lista la memoria global                       |
| `POST`   | `/api/memories`                               | Añade un recuerdo                             |
| `DELETE` | `/api/memories/{id}`                          | Borra un recuerdo                             |
| `POST`   | `/api/chat` · `/api/chat/stream`              | Chat sin estado (heredado de la Fase 1)       |

Ejemplo: enviar un mensaje a una conversación existente:

```json
POST /api/conversations/1/chat/stream
{ "content": "Explícame qué es FastAPI en una frase" }
```

La base de datos se crea sola en `backend/techpill.db` al arrancar.

---

## 🗺️ Hoja de ruta (fases)

- [x] **Fase 1** — Chat con IA local (streaming).
- [x] **Fase 2** — Guardar conversaciones (SQLite + SQLAlchemy), historial con memoria.
- [x] **Fase 3** — Subir y analizar documentos PDF y TXT (contexto en el chat + acciones rápidas: resumen, test).
- [x] **Fase 4** — Tareas y recordatorios (panel con prioridades y fechas) + IA consciente de tu agenda.
- [x] **Fase 5** — Selector de modelos en la interfaz (se recuerda entre sesiones) + pulido (envío deshabilitado si Ollama no está disponible, errores controlados).
- [x] **Extra** — Memoria global entre conversaciones (*"recuerda que…"*) + robustez de SQLite (`busy_timeout`, claves foráneas).

> ℹ️ **Sobre la creación de tareas por voz/texto natural:** el modelo local actual
> (`qwen2.5-coder:7b`) no rellena de forma fiable el campo nativo de *tool calling* de
> Ollama (devuelve la llamada como texto), así que la creación/edición de tareas se hace
> desde el panel 📋. La IA **sí** lee tus tareas para responder sobre tu agenda. Activar
> *function calling* nativo (con un modelo que lo soporte bien) es una mejora futura.

> ℹ️ **Sobre los PDFs:** el texto extraído se inyecta en el contexto (hasta ~8000
> caracteres). Para documentos muy largos, la mejora futura es trocear + búsqueda
> semántica (RAG con *embeddings*). Los PDFs escaneados (solo imagen) necesitarían OCR.

---

## 📄 Licencia

[MIT](LICENSE) © 2026 Jsolh03. Eres libre de usar, modificar y distribuir este código.
