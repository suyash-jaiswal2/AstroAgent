import { useEffect, useRef } from 'react'
import { useSessionStore } from '../../store/sessionStore'
import { MarkdownText } from './MarkdownText'

export function StreamingText() {
  const { streamingContent, isStreaming } = useSessionStore()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [streamingContent])

  if (!isStreaming && !streamingContent) return null

  return (
    <div ref={ref} style={{ marginBottom: '1rem' }}>
      <div className="message-ai">
        <MarkdownText text={streamingContent} showCursor={isStreaming} />
      </div>
    </div>
  )
}