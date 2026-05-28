// Barra lateral con la lista de conversaciones guardadas.

function Sidebar({ conversations, activeId, onSelect, onNew, onDelete, onRename }) {
  function handleRename(conv, e) {
    e.stopPropagation()
    const title = window.prompt('Nuevo nombre de la conversacion:', conv.title)
    if (title && title.trim()) onRename(conv.id, title.trim())
  }

  function handleDelete(conv, e) {
    e.stopPropagation()
    if (window.confirm(`¿Borrar "${conv.title}"?`)) onDelete(conv.id)
  }

  return (
    <aside className="sidebar">
      <button className="new-chat" onClick={onNew}>
        + Nueva conversación
      </button>

      <div className="conv-list">
        {conversations.length === 0 && (
          <p className="conv-empty">Aún no hay conversaciones.</p>
        )}
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conv-item ${conv.id === activeId ? 'active' : ''}`}
            onClick={() => onSelect(conv.id)}
          >
            <span className="conv-title">{conv.title}</span>
            <span className="conv-actions">
              <button title="Renombrar" onClick={(e) => handleRename(conv, e)}>
                ✏️
              </button>
              <button title="Borrar" onClick={(e) => handleDelete(conv, e)}>
                🗑️
              </button>
            </span>
          </div>
        ))}
      </div>
    </aside>
  )
}

export default Sidebar
