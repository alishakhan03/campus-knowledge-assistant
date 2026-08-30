import { API_BASE_URL } from './client'

/**
 * Streams a chat answer token-by-token using the backend's SSE-style
 * streaming endpoint. Uses native fetch (not axios) because axios does not
 * expose an incremental ReadableStream in the browser the way fetch does.
 *
 * callbacks:
 *   onSources(sources)      - called once, as soon as retrieval finishes
 *   onToken(text)            - called for each streamed text chunk
 *   onDone(messageId)        - called once the answer is fully persisted
 *   onError(message)         - called on any failure (network or server-side)
 */
export async function streamChatMessage(conversationId, content, { onSources, onToken, onDone, onError }) {
  const token = localStorage.getItem('access_token')

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/chat/conversations/${conversationId}/messages/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ content }),
    })
  } catch (err) {
    onError?.('Could not reach the server. Please check your connection and try again.')
    return
  }

  if (!response.ok || !response.body) {
    onError?.('Something went wrong sending your question. Please try again.')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('data:')) continue
      const jsonStr = trimmed.slice(5).trim()
      if (!jsonStr) continue

      let event
      try {
        event = JSON.parse(jsonStr)
      } catch {
        continue
      }

      if (event.type === 'sources') onSources?.(event.sources)
      else if (event.type === 'token') onToken?.(event.text)
      else if (event.type === 'done') onDone?.(event.message_id)
      else if (event.type === 'error') onError?.(event.text)
    }
  }
}