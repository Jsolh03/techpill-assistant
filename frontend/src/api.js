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

/**
 * Envia un mensaje dentro de una conversacion y recibe la respuesta en streaming.
 * El backend guarda automaticamente el mensaje del usuario y el de la IA.
 *
 * @param {number} conversationId
 * @param {string} content
 * @param {(chunk: string) => void} onChunk
 * @param {AbortSignal} [signal]
 */
export async function streamConversationChat(conversationId, content, onChunk, signal) {
  const resp = await fetch(`/api/conversations/${conversationId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
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
