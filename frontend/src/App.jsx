import { useEffect, useRef, useState } from 'react'
import {
  createConversation,
  deleteConversation,
  deleteDocument,
  getConversation,
  getHealth,
  listConversations,
  listDocuments,
  renameConversation,
  streamConversationChat,
  uploadDocument,
} from './api'
import Sidebar from './Sidebar'
import TasksPanel from './TasksPanel'
import './App.css'

function App() {
  const [conversations, setConversations] = useState([]) // lista lateral
  const [activeId, setActiveId] = useState(null) // conversacion abierta
  const [messages, setMessages] = useState([]) // mensajes de la conversacion abierta
  const [documents, setDocuments] = useState([]) // PDFs de la conversacion abierta
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showTasks, setShowTasks] = useState(false) // panel de tareas visible
  const [health, setHealth] = useState(null)
  // Modelo de Ollama elegido (se recuerda entre sesiones con localStorage).
  const [model, setModel] = useState(() => localStorage.getItem('techpill_model') || '')
  const bottomRef = useRef(null)
  const abortRef = useRef(null)
  const fileRef = useRef(null)

  // Al cargar: estado de Ollama + lista de conversaciones.
  useEffect(() => {
    getHealth()
      .then((h) => {
        setHealth(h)
        // Si no hay modelo elegido (o el guardado ya no existe), usamos el primero.
        setModel((prev) =>
          prev && h.models?.includes(prev) ? prev : h.models?.[0] || '',
        )
      })
      .catch(() => setHealth({ ollama_connected: false, models: [] }))
    refreshConversations()
  }, [])

  // Persistimos el modelo elegido.
  useEffect(() => {
    if (model) localStorage.setItem('techpill_model', model)
  }, [model])

  // Auto-scroll al ultimo mensaje.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function refreshConversations() {
    try {
      setConversations(await listConversations())
    } catch {
      /* el indicador de estado ya avisa si el backend no responde */
    }
  }

  async function handleSelect(id) {
    if (id === activeId || loading) return
    setActiveId(id)
    const detail = await getConversation(id)
    setMessages(detail.messages.map((m) => ({ role: m.role, content: m.content })))
    setDocuments(detail.documents ?? [])
  }

  function handleNew() {
    // No creamos la conversacion en la BD hasta que se envia el primer mensaje.
    setActiveId(null)
    setMessages([])
    setDocuments([])
    setInput('')
  }

  async function handleDelete(id) {
    await deleteConversation(id)
    if (id === activeId) handleNew()
    refreshConversations()
  }

  async function handleRename(id, title) {
    await renameConversation(id, title)
    refreshConversations()
  }

  // Crea la conversacion en la BD si todavia no existe; devuelve su id.
  async function ensureConversation() {
    if (activeId != null) return activeId
    const conv = await createConversation()
    setActiveId(conv.id)
    return conv.id
  }

  // ---------- Subida de PDFs ----------
  async function handleFilePick(e) {
    const file = e.target.files?.[0]
    e.target.value = '' // permite volver a subir el mismo archivo
    if (!file) return

    setUploading(true)
    try {
      const convId = await ensureConversation()
      const doc = await uploadDocument(convId, file)
      setDocuments((prev) => [...prev, doc])
      await refreshConversations()
    } catch (err) {
      alert(`No se pudo subir el PDF: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }

  async function handleRemoveDoc(docId) {
    await deleteDocument(docId)
    setDocuments((prev) => prev.filter((d) => d.id !== docId))
  }

  // ---------- Envio de mensajes ----------
  async function sendMessage(text) {
    if (!text.trim() || loading) return
    setLoading(true)

    const convId = await ensureConversation()

    setMessages((prev) => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '' },
    ])

    abortRef.current = new AbortController()

    try {
      await streamConversationChat(
        convId,
        text,
        (chunk) => {
          setMessages((prev) => {
            const copy = [...prev]
            copy[copy.length - 1] = {
              role: 'assistant',
              content: copy[copy.length - 1].content + chunk,
            }
            return copy
          })
        },
        abortRef.current.signal,
        model,
      )
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => {
          const copy = [...prev]
          copy[copy.length - 1] = { role: 'assistant', content: `⚠️ Error: ${err.message}` }
          return copy
        })
      }
    } finally {
      setLoading(false)
      abortRef.current = null
      refreshConversations()
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setInput('')
    sendMessage(text)
  }

  function handleStop() {
    abortRef.current?.abort()
  }

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelect}
        onNew={handleNew}
        onDelete={handleDelete}
        onRename={handleRename}
      />

      <div className="main">
        <header className="header">
          <div className="brand">
            <span className="logo">💊</span>
            <h1>TechPill Assistant</h1>
          </div>
          <div className="header-right">
            <div className="status">
              <span className={`dot ${health?.ollama_connected ? 'on' : 'off'}`} />
              {health?.ollama_connected ? 'Ollama conectado' : 'Ollama no disponible'}
            </div>
            {health?.ollama_connected && health.models.length > 0 && (
              <select
                className="model-select"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                title="Modelo de IA"
              >
                {health.models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            )}
            <button
              className={`tasks-toggle ${showTasks ? 'active' : ''}`}
              onClick={() => setShowTasks((v) => !v)}
              title="Tareas y recordatorios"
            >
              📋 Tareas
            </button>
          </div>
        </header>

        <main className="chat">
          {messages.length === 0 && (
            <div className="empty">
              <p className="empty-title">¡Hola! 👋</p>
              <p>
                Soy tu asistente personal con IA local. Preguntame lo que quieras o adjunta
                un PDF o TXT 📎 para que lo analice.
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="avatar">{m.role === 'user' ? '🧑' : '🤖'}</div>
              <div className="bubble">
                {m.content || <span className="typing">escribiendo…</span>}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </main>

        {/* Documentos adjuntos + acciones rapidas */}
        {documents.length > 0 && (
          <div className="docs-bar">
            {documents.map((d) => (
              <span className="doc-chip" key={d.id} title={`${d.char_count} caracteres`}>
                📄 {d.filename}
                <button onClick={() => handleRemoveDoc(d.id)} title="Quitar">
                  ✕
                </button>
              </span>
            ))}
            <span className="quick-actions">
              <button onClick={() => sendMessage('Hazme un resumen claro del documento.')}>
                📝 Resumen
              </button>
              <button
                onClick={() =>
                  sendMessage('Genera 5 preguntas tipo test (con 4 opciones y la respuesta correcta) sobre el documento.')
                }
              >
                ❓ Test
              </button>
            </span>
          </div>
        )}

        <form className="composer" onSubmit={handleSubmit}>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            style={{ display: 'none' }}
            onChange={handleFilePick}
          />
          <button
            type="button"
            className="btn attach"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            title="Adjuntar PDF o TXT"
          >
            {uploading ? '⏳' : '📎'}
          </button>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) handleSubmit(e)
            }}
            placeholder="Escribe tu mensaje…  (Enter para enviar, Shift+Enter para salto de linea)"
            rows={1}
          />
          {loading ? (
            <button type="button" className="btn stop" onClick={handleStop}>
              Detener
            </button>
          ) : (
            <button
              type="submit"
              className="btn send"
              disabled={!input.trim() || !health?.ollama_connected}
              title={health?.ollama_connected ? 'Enviar' : 'Ollama no está disponible'}
            >
              Enviar
            </button>
          )}
        </form>
      </div>

      {showTasks && <TasksPanel onClose={() => setShowTasks(false)} />}
    </div>
  )
}

export default App
