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

      // Set tool activity state before fetch to indicate the celestial calculations are running
      setToolCall({ tool: 'Consulting celestial coordinates...', status: 'running', step: 1 })

      try {
        const url = `${BASE}/api/chat/stream?message=${encodeURIComponent(message)}&session_id=${encodeURIComponent(sessionId)}`
        const response = await fetch(url, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        })

        if (!response.ok) {
          setToolCall({ tool: 'Consulting celestial coordinates...', status: 'error', step: 1 })
          addToken("My apologies, dear seeker. The cosmic connection was briefly interrupted. Please give me a brief moment to realign with the stars and try asking your question again.")
          setTimeout(() => finalizeMessage({}), 50)
          return
        }

        const data = await response.json()
        const content = data.content || ''

        // Set tool activity as successfully completed
        setToolCall({ tool: 'Consulting celestial coordinates...', status: 'done', step: 1 })

        if (!content) {
          addToken("No response could be fetched from the cosmos. Please try again.")
          setTimeout(() => finalizeMessage({}), 50)
          return
        }

        // Split text by spaces but preserve them as separate array items
        const words = content.split(/(\s+)/)
        let index = 0

        const typeNextWord = () => {
          if (index < words.length) {
            addToken(words[index])
            index++

            // Premium organic pacing:
            // - Base speed of 12ms per word element
            // - Add a realistic pause (180ms) at the end of sentences/punctuation to simulate thought
            let delay = 12
            const currentWord = words[index - 1]
            if (currentWord.includes('.') || currentWord.includes('?') || currentWord.includes('!') || currentWord.includes('\n')) {
              delay = 180
            } else if (currentWord.length > 8) {
              delay = 20
            }

            setTimeout(typeNextWord, delay)
          } else {
            finalizeMessage(data)
          }
        }

        // Trigger typing simulation
        typeNextWord()

      } catch (err) {
        console.error('Fetch failed:', err)
        setToolCall({ tool: 'Consulting celestial coordinates...', status: 'error', step: 1 })
        addToken("The celestial connection was briefly interrupted. Please give me a brief moment to realign with the stars and try asking your question again.")
        setTimeout(() => finalizeMessage({}), 50)
      }
    },
    [addUserMessage, startAssistantMessage, addToken, finalizeMessage, setToolCall]
  )

  return { stream }
}