export function createChatSSE(
  question: string,
  conversationId: string,
  callbacks: {
    onMessage: (text: string) => void
    onDone: () => void
    onError: (err: string) => void
    onRetrieve?: (docs: SourceDocument[]) => void
  }
): AbortController {
  const controller = new AbortController()

  fetch('/api/v1/chat/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_id: conversationId }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()

          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'token') {
              callbacks.onMessage(parsed.content)
            } else if (parsed.type === 'sources') {
              callbacks.onRetrieve?.(parsed.documents)
            } else if (parsed.type === 'done') {
              callbacks.onDone()
              return
            }
          } catch {
            // 非JSON数据，忽略
          }
        }
      }
      callbacks.onDone()
    })
    .catch((err) => {
      if (err.name === 'AbortError') return
      callbacks.onError(err.message)
    })

  return controller
}