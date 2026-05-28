import { useEffect, useRef, useState } from 'react'
import {
  createConversation,
  deleteConversation,
  getConversation,
  getHealth,
  listConversations,
  renameConversation,
  streamConversationChat,
} from './api'
import Sidebar from './Sidebar'
import './App.css'

function App() {
  const [conversations, setConversations] = useState([]) // lista lateral
  const [activeId, setActiveId] = useState(null) // conversacion abierta
  const [messages, setMessages] = useState([]) // mensajes de la conversacion abierta
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [health, setHealth] = useState(null)
  const bottomRef = useRef(null)
  const abortRef = useRef(null)

  // Al cargar: estado de Ollama + lista de conversaciones.
  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ ollama_connected: false, models: [] }))
    refreshConversations()
  }, [])

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
  }

  function handleNew() {
    // No creamos la conversacion en la BD hasta que se envia el primer mensaje.
    setActiveId(null)
    setMessages([])
    setInput('')
  }

  async function handleDelete(id) {
    await deleteConversation(id)
    if (id === activeId) {
      setActiveId(null)
      setMessages([])
    }
    refreshConversations()
  }

  async function handleRename(id, title) {
    await renameConversation(id, title)
    refreshConversations()
  }

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setLoading(true)
    setInput('')

    // Si no hay conversacion activa, creamos una nueva en la BD.
    let convId = activeId
    let isNew = false
    if (convId == null) {
      const conv = await createConversation()
      convId = conv.id
      isNew = true
      setActiveId(convId)
    }

    // Mostramos el mensaje del usuario y un hueco para la respuesta.
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
      // Refrescamos la lista: el backend pudo auto-generar el titulo (conversacion nueva)
      // o actualizar la fecha (reordenar).
      if (isNew) await refreshConversations()
      else refreshConversations()
    }
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
          <div className="status">
            <span className={`dot ${health?.ollama_connected ? 'on' : 'off'}`} />
            {health?.ollama_connected
              ? `Ollama conectado · ${health.models[0] ?? ''}`
              : 'Ollama no disponible'}
          </div>
        </header>

        <main className="chat">
          {messages.length === 0 && (
            <div className="empty">
              <p className="empty-title">¡Hola! 👋</p>
              <p>Soy tu asistente personal con IA local. Preguntame lo que quieras.</p>
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

        <form className="composer" onSubmit={handleSend}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) handleSend(e)
            }}
            placeholder="Escribe tu mensaje…  (Enter para enviar, Shift+Enter para salto de linea)"
            rows={1}
          />
          {loading ? (
            <button type="button" className="btn stop" onClick={handleStop}>
              Detener
            </button>
          ) : (
            <button type="submit" className="btn send" disabled={!input.trim()}>
              Enviar
            </button>
          )}
        </form>
      </div>
    </div>
  )
}

export default App
