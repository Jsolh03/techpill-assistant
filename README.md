# 💊 TechPill Assistant

Asistente personal con **IA local** (sin enviar tus datos a internet). Funciona
sobre [Ollama](https://ollama.com), con un backend en **Python + FastAPI** y un
frontend en **React (Vite)**.

> Proyecto por fases. **Fase 2 (actual): historial de conversaciones persistente (SQLite).**

![estado](https://img.shields.io/badge/fase-2%20historial-blue) ![python](https://img.shields.io/badge/python-3.12-3776ab) ![react](https://img.shields.io/badge/react-19-61dafb) ![sqlite](https://img.shields.io/badge/sqlite-SQLAlchemy-003b57)

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
  - `database.py` / `models.py` — SQLite + SQLAlchemy (conversaciones y mensajes).
  - `routers/` — endpoints separados por tema (`chat`, `conversations`).
- **`frontend/`** — interfaz de chat en React con barra lateral de historial y streaming.

El backend es el **dueño del historial**: al enviar un mensaje carga toda la
conversación desde la BD y se la pasa a la IA, así el asistente "recuerda" el contexto.

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
- [ ] **Fase 3** — Subir y analizar PDFs (resúmenes, preguntas tipo test).
- [ ] **Fase 4** — Memoria personal, tareas y recordatorios.
- [ ] **Fase 5** — Selector de modelos / modo offline pulido.

---

## 📄 Licencia

Uso personal y educativo.
