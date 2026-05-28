// Panel lateral derecho con las tareas/recordatorios del usuario.
import { useEffect, useState } from 'react'
import { createTask, deleteTask, listTasks, updateTask } from './api'

const PRIORIDADES = ['alta', 'media', 'baja']

function TasksPanel({ onClose, onChanged }) {
  const [tasks, setTasks] = useState([])
  const [title, setTitle] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [priority, setPriority] = useState('media')

  useEffect(() => {
    refresh()
  }, [])

  async function refresh() {
    try {
      setTasks(await listTasks())
    } catch {
      /* sin conexion: el panel quedara vacio */
    }
  }

  async function handleAdd(e) {
    e.preventDefault()
    const t = title.trim()
    if (!t) return
    await createTask({ title: t, due_date: dueDate || null, priority })
    setTitle('')
    setDueDate('')
    setPriority('media')
    await refresh()
    onChanged?.()
  }

  async function toggleDone(task) {
    await updateTask(task.id, { done: !task.done })
    await refresh()
    onChanged?.()
  }

  async function remove(id) {
    await deleteTask(id)
    await refresh()
    onChanged?.()
  }

  // ¿Vence hoy o ya paso? (para resaltar en rojo)
  function isUrgent(task) {
    if (!task.due_date || task.done) return false
    const hoy = new Date()
    hoy.setHours(0, 0, 0, 0)
    return new Date(task.due_date) <= hoy
  }

  return (
    <aside className="tasks-panel">
      <div className="tasks-head">
        <h2>📋 Tareas</h2>
        <button className="tasks-close" onClick={onClose} title="Cerrar">
          ✕
        </button>
      </div>

      <form className="task-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Nueva tarea…"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <div className="task-form-row">
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            title="Fecha límite (opcional)"
          />
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            {PRIORIDADES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button type="submit" disabled={!title.trim()}>
            +
          </button>
        </div>
      </form>

      <div className="task-list">
        {tasks.length === 0 && <p className="task-empty">No hay tareas todavía.</p>}
        {tasks.map((t) => (
          <div key={t.id} className={`task-item prio-${t.priority} ${t.done ? 'done' : ''}`}>
            <input
              type="checkbox"
              checked={t.done}
              onChange={() => toggleDone(t)}
              title="Marcar como hecha"
            />
            <div className="task-body">
              <span className="task-title">{t.title}</span>
              <span className="task-meta">
                {t.due_date && (
                  <span className={isUrgent(t) ? 'due urgent' : 'due'}>📅 {t.due_date}</span>
                )}
                <span className={`prio-tag prio-${t.priority}`}>{t.priority}</span>
              </span>
            </div>
            <button className="task-del" onClick={() => remove(t.id)} title="Borrar">
              🗑️
            </button>
          </div>
        ))}
      </div>
    </aside>
  )
}

export default TasksPanel
