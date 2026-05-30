import { useCallback } from 'react'
import { useSessionStore } from '../store/sessionStore'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useSSE() {
  const { addUserMessage, startAssistantMessage, addToken, finalizeMessage, setToolCall } =
    useSessionStore()

  const stream = useCallback(
    async (message: string, sessionId: string) => {
      addUserMessage(message)
      startAssistantMessage()

      try {
        const response = await fetch(`${BASE}/api/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, session_id: sessionId }),
        })

        if (!response.ok || !response.body) {
          addToken("My apologies, dear seeker. The cosmic connection was briefly interrupted. Please give me a brief moment to realign with the stars and try asking your question again.")
          finalizeMessage({})
          return
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const parts = buffer.split('\n\n')
          buffer = parts.pop() || ''

          for (const part of parts) {
            const lines = part.trim().split('\n')
            let eventType = ''
            let dataStr = ''
            for (const line of lines) {
              if (line.startsWith('event:')) eventType = line.slice(6).trim()
              if (line.startsWith('data:')) dataStr = line.slice(5).trim()
            }
            if (!eventType || !dataStr) continue
            try {
              const data = JSON.parse(dataStr)
              if (eventType === 'token') addToken(data.text || '')
              else if (eventType === 'tool_start') setToolCall({ tool: data.tool, status: 'running', step: data.step })
              else if (eventType === 'tool_end') setToolCall({ tool: data.tool, status: 'done', step: 0 })
              else if (eventType === 'done') finalizeMessage(data)
              else if (eventType === 'error') {
                console.error('SSE error:', data)
                addToken("My apologies, dear seeker. The cosmic energies are currently highly congested. Please give me a brief moment to realign with the stars and try asking your question again.")
                finalizeMessage({})
              }
            } catch { /* skip malformed */ }
          }
        }
      } catch (err) {
        console.error('Stream failed:', err)
        addToken("The celestial connection was briefly interrupted. Please give me a brief moment to realign with the stars and try asking your question again.")
        finalizeMessage({})
      }
    },
    [addUserMessage, startAssistantMessage, addToken, finalizeMessage, setToolCall]
  )

  return { stream }
}