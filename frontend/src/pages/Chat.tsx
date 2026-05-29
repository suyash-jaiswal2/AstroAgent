import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ObservatoryBackground } from '../components/observatory/ObservatoryBackground'
import { AuraBackground } from '../components/aura/AuraBackground'
import { CelestialOrb } from '../components/orb/CelestialOrb'
import { ToolActivity } from '../components/chat/ToolActivity'
import { MessageBubble } from '../components/chat/MessageBubble'
import { StreamingText } from '../components/chat/StreamingText'
import { SuggestedPrompts } from '../components/chat/SuggestedPrompts'
import { PanchangCard } from '../components/panchang/PanchangCard'
import { GlassCard } from '../components/ui/GlassCard'
import { useSessionStore } from '../store/sessionStore'
import { useSSE } from '../hooks/useSSE'
import { useOrbMood } from '../hooks/useOrbMood'

const SUGGESTED_PROMPTS = [
  'What does my chart say about my career?',
  'What dasha period am I currently in?',
  'Do I have any special yogas?',
  "What's today's panchang?",
  'When is a good time to start a new venture?',
]

export default function Chat() {
  const navigate = useNavigate()
  const { sessionId, birthDetails, messages, isStreaming } = useSessionStore()
  const { stream } = useSSE()
  useOrbMood()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!sessionId || !birthDetails) navigate('/birth')
  }, [sessionId, birthDetails, navigate])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  const sendMessage = async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || isStreaming || !sessionId) return
    setInput('')
    await stream(msg, sessionId)
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const sun = (birthDetails as Record<string, unknown> | null)
  const sunSign = 'your chart'

  return (
    <div style={{ position: 'relative', height: '100vh', overflow: 'hidden' }}>
      <ObservatoryBackground />
      <AuraBackground />

      <div style={{ position: 'relative', zIndex: 10, height: '100vh', display: 'flex' }}>
        {/* LEFT PANEL */}
        <div className="hidden lg:flex" style={{ width: 260, flexDirection: 'column', gap: 12, padding: '1rem', borderRight: '1px solid var(--glass-border)', overflowY: 'auto', flexShrink: 0 }}>
          <GlassCard className="p-4">
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: '0.7rem', letterSpacing: '0.1em', color: 'var(--gold)', marginBottom: 8 }}>YOUR CHART</p>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', color: 'var(--text-celestial)' }}>{birthDetails?.name}</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-stardust)', fontFamily: 'Inter, sans-serif' }}>
              {birthDetails?.date} · {birthDetails?.place?.split(',')[0]}
            </p>
          </GlassCard>
          <button onClick={() => navigate('/chart')}
            style={{ padding: '8px', borderRadius: 8, background: 'rgba(61,127,191,0.1)', border: '1px solid rgba(61,127,191,0.2)', color: 'var(--text-stardust)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>
            🔭 Explore Full Chart
          </button>
          <button onClick={() => navigate('/dasha')}
            style={{ padding: '8px', borderRadius: 8, background: 'rgba(61,127,191,0.1)', border: '1px solid rgba(61,127,191,0.2)', color: 'var(--text-stardust)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>
            📅 Dasha Timeline
          </button>
          <button onClick={() => navigate('/compatibility')}
            style={{ padding: '8px', borderRadius: 8, background: 'rgba(61,127,191,0.1)', border: '1px solid rgba(61,127,191,0.2)', color: 'var(--text-stardust)', fontSize: '0.8rem', cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>
            💞 Compatibility
          </button>
        </div>

        {/* CENTER */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Orb + Tool Activity */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem 1rem 0.5rem', flexShrink: 0 }}>
            <CelestialOrb size={100} />
            <div style={{ marginTop: 8 }}>
              <ToolActivity />
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '0 1.25rem' }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>
                <p style={{ fontFamily: 'Cormorant Garamond, serif', fontStyle: 'italic', fontSize: '1.1rem' }}>
                  The stars await your question, {birthDetails?.name?.split(' ')[0]}...
                </p>
              </div>
            )}
            {messages.map(m => <MessageBubble key={m.id} message={m} />)}
            <StreamingText />
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div style={{ padding: '0.75rem 1.25rem 1rem', borderTop: '1px solid var(--glass-border)', flexShrink: 0 }}>
            {messages.length === 0 && (
              <SuggestedPrompts prompts={SUGGESTED_PROMPTS} onSelect={sendMessage} />
            )}
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
              <textarea ref={textareaRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                placeholder="Ask the stars anything..."
                rows={1}
                style={{
                  flex: 1, padding: '0.75rem 1rem', borderRadius: 12,
                  background: 'var(--glass-bg)', border: '1px solid var(--glass-border)',
                  color: 'var(--text-celestial)', fontFamily: 'Inter, sans-serif',
                  fontSize: '0.95rem', outline: 'none', resize: 'none',
                  maxHeight: 100, overflowY: 'auto',
                }}
              />
              <button onClick={() => sendMessage()} disabled={isStreaming || !input.trim()}
                style={{
                  width: 44, height: 44, borderRadius: '50%', border: 'none', cursor: isStreaming ? 'wait' : 'pointer',
                  background: isStreaming ? '#555' : 'var(--gold)',
                  color: '#04040C', fontSize: '1.1rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                {isStreaming ? '◉' : '↑'}
              </button>
            </div>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: 4, fontFamily: 'Inter, sans-serif' }}>
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="hidden xl:flex" style={{ width: 280, flexDirection: 'column', gap: 12, padding: '1rem', borderLeft: '1px solid var(--glass-border)', overflowY: 'auto', flexShrink: 0 }}>
          <PanchangCard />
        </div>
      </div>
    </div>
  )
}