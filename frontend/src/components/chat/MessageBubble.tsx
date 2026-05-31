import { MarkdownText } from './MarkdownText'
import type { ChatMessage } from '../../store/sessionStore'

interface Props { message: ChatMessage }

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <div className="message-user" style={{ maxWidth: '80%' }}>
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div className="message-ai">
        <MarkdownText text={message.content} />
      </div>
      {message.toolCalls && message.toolCalls.length > 0 && (
        <details style={{ marginTop: '0.5rem' }}>
          <summary style={{ fontSize: '0.75rem', color: 'var(--text-dim)', cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>
            How I reached this ▼
          </summary>
          <div style={{ marginTop: 4, padding: '0.5rem', background: 'rgba(13,13,43,0.4)', borderRadius: 6 }}>
            {message.toolCalls.map((tool, i) => (
              <span key={i} style={{ display: 'inline-block', marginRight: 6, padding: '2px 8px', borderRadius: 12, background: 'rgba(61,127,191,0.2)', fontSize: '0.75rem', color: 'var(--text-stardust)', fontFamily: 'Inter, sans-serif' }}>
                {tool}
              </span>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}