// Capa de acceso a la API del backend.
// El proxy de Vite (vite.config.js) reenvia "/api/..." al backend de FastAPI.

export async function getHealth() {
  const resp = await fetch('/api/health')
  if (!resp.ok) throw new Error('No se pudo consultar el estado del servidor')
  return resp.json()
}

// ---------- Conversaciones (Fase 2) ----------

export async function listConversations() {
  const resp = await fetch('/api/conversations')
  if (!resp.ok) throw new Error('No se pudieron cargar las conversaciones')
  return resp.json()
}

export async function createConversation() {
  const resp = await fetch('/api/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!resp.ok) throw new Error('No se pudo crear la conversacion')
  return resp.json()
}

export async function getConversation(id) {
  const resp = await fetch(`/api/conversations/${id}`)
  if (!resp.ok) throw new Error('No se pudo cargar la conversacion')
  return resp.json()
}

export async function renameConversation(id, title) {
  const resp = await fetch(`/api/conversations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!resp.ok) throw new Error('No se pudo renombrar la conversacion')
  return resp.json()
}

export async function deleteConversation(id) {
  const resp = await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('No se pudo borrar la conversacion')
}

// ---------- Tareas / recordatorios (Fase 4) ----------

export async function listTasks() {
  const resp = await fetch('/api/tasks')
  if (!resp.ok) throw new Error('No se pudieron cargar las tareas')
  return resp.json()
}

export async function createTask(task) {
  const resp = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  })
  if (!resp.ok) throw new Error('No se pudo crear la tarea')
  return resp.json()
}

export async function updateTask(id, changes) {
  const resp = await fetch(`/api/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(changes),
  })
  if (!resp.ok) throw new Error('No se pudo actualizar la tarea')
  return resp.json()
}

export async function deleteTask(id) {
  const resp = await fetch(`/api/tasks/${id}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('No se pudo borrar la tarea')
}

// ---------- Memoria global (cross-conversación) ----------

export async function listMemories() {
  const resp = await fetch('/api/memories')
  if (!resp.ok) throw new Error('No se pudo cargar la memoria')
  return resp.json()
}

export async function createMemory(content) {
  const resp = await fetch('/api/memories', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
  if (!resp.ok) throw new Error('No se pudo guardar el recuerdo')
  return resp.json()
}

export async function deleteMemory(id) {
  const resp = await fetch(`/api/memories/${id}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('No se pudo borrar el recuerdo')
}

// ---------- Documentos / PDFs (Fase 3) ----------

export async function listDocuments(conversationId) {
  const resp = await fetch(`/api/conversations/${conversationId}/documents`)
  if (!resp.ok) throw new Error('No se pudieron cargar los documentos')
  return resp.json()
}

export async function uploadDocument(conversationId, file) {
  const form = new FormData()
  form.append('file', file)
  const resp = await fetch(`/api/conversations/${conversationId}/documents`, {
    method: 'POST',
    body: form,
  })
  if (!resp.ok) {
    let detalle = `Error ${resp.status}`
    try {
      detalle = (await resp.json()).detail || detalle
    } catch {
      /* la respuesta no era JSON */
    }
    throw new Error(detalle)
  }
  return resp.json()
}

export async function deleteDocument(documentId) {
  const resp = await fetch(`/api/documents/${documentId}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('No se pudo borrar el documento')
}

/**
 * Envia un mensaje dentro de una conversacion y recibe la respuesta en streaming.
 * El backend guarda automaticamente el mensaje del usuario y el de la IA.
 *
 * @param {number} conversationId
 * @param {string} content
 * @param {(chunk: string) => void} onChunk
 * @param {AbortSignal} [signal]
 * @param {string} [model] modelo de Ollama a usar (si no, el del backend por defecto)
 */
export async function streamConversationChat(conversationId, content, onChunk, signal, model) {
  const resp = await fetch(`/api/conversations/${conversationId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, model: model || null }),
    signal,
  })

  if (!resp.ok) {
    throw new Error(`El servidor respondio con error ${resp.status}`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value, { stream: true }))
  }
}
