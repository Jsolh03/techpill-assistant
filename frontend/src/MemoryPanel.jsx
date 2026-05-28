// Panel lateral derecho con la MEMORIA GLOBAL del asistente.
// Lo que aparece aquí lo recuerda en todas las conversaciones.
import { useEffect, useState } from 'react'
import { createMemory, deleteMemory, listMemories } from './api'

function MemoryPanel({ onClose }) {
  const [memories, setMemories] = useState([])
  const [text, setText] = useState('')

  useEffect(() => {
    refresh()
  }, [])

  async function refresh() {
    try {
      setMemories(await listMemories())
    } catch {
      /* sin conexion */
    }
  }

  async function handleAdd(e) {
    e.preventDefault()
    const t = text.trim()
    if (!t) return
    await createMemory(t)
    setText('')
    refresh()
  }

  async function remove(id) {
    await deleteMemory(id)
    refresh()
  }

  return (
    <aside className="tasks-panel">
      <div className="tasks-head">
        <h2>🧠 Memoria</h2>
        <button className="tasks-close" onClick={onClose} title="Cerrar">
          ✕
        </button>
      </div>

      <p className="mem-hint">
        El asistente recuerda esto en <b>todas</b> las conversaciones. También se guarda
        solo cuando le dices <i>“recuerda que…”</i> en el chat.
      </p>

      <form className="task-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Añadir algo a recordar…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button type="submit" className="mem-add" disabled={!text.trim()}>
          Recordar
        </button>
      </form>

      <div className="task-list">
        {memories.length === 0 && <p className="task-empty">Nada recordado todavía.</p>}
        {memories.map((m) => (
          <div key={m.id} className="task-item prio-media">
            <div className="task-body">
              <span className="task-title">{m.content}</span>
            </div>
            <button className="task-del" onClick={() => remove(m.id)} title="Olvidar">
              🗑️
            </button>
          </div>
        ))}
      </div>
    </aside>
  )
}

export default MemoryPanel
