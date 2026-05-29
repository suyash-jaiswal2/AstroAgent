import { useEffect, useRef } from 'react'
import { useSessionStore } from '../../store/sessionStore'

export function StreamingText() {
  const { streamingContent, isStreaming } = useSessionStore()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [streamingContent])

  if (!isStreaming && !streamingContent) return null

  return (
    <div ref={ref} style={{ marginBottom: '1rem' }}>
      <div className="message-ai" style={{ whiteSpace: 'pre-wrap' }}>
        {streamingContent}
        {isStreaming && (
          <span style={{
            display: 'inline-block', width: 2, height: '1em', marginLeft: 2,
            background: 'var(--gold)', animation: 'cursor-blink 1s ease-in-out infinite',
            verticalAlign: 'text-bottom',
          }} />
        )}
      </div>
    </div>
  )
}