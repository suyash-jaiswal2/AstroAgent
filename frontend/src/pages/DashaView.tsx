import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ObservatoryBackground } from '../components/observatory/ObservatoryBackground'
import { GlassCard } from '../components/ui/GlassCard'
import { DashaTimeline } from '../components/chart/DashaTimeline'
import { useSessionStore } from '../store/sessionStore'
import { getDashas } from '../lib/api'

export default function DashaView() {
  const navigate = useNavigate()
  const { sessionId } = useSessionStore()
  const [dashaData, setDashaData] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    if (!sessionId) { navigate('/'); return }
    getDashas(sessionId).then(setDashaData).catch(console.error)
  }, [sessionId, navigate])

  const timeline = dashaData?.timeline as Array<{ planet: string; start: string; end: string; years: number }> | null

  return (
    <div style={{ position: 'relative', minHeight: '100vh', padding: '2rem' }}>
      <ObservatoryBackground />
      <div style={{ position: 'relative', zIndex: 10, maxWidth: 900, margin: '0 auto' }}>
        <button onClick={() => navigate('/chat')} style={{ color: 'var(--text-stardust)', background: 'none', border: 'none', cursor: 'pointer', marginBottom: '1rem', fontFamily: 'Inter, sans-serif', fontSize: '0.85rem' }}>← Back</button>
        <h1 style={{ fontFamily: 'Cinzel, serif', fontSize: '1.5rem', color: 'var(--gold)', marginBottom: '1.5rem', letterSpacing: '0.15em' }}>DASHA TIMELINE</h1>
        {Boolean(dashaData?.current_period) && (
          <GlassCard className="p-4 mb-4">
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: '0.7rem', color: 'var(--gold)', letterSpacing: '0.1em', marginBottom: 4 }}>CURRENT PERIOD</p>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.2rem', color: 'var(--text-celestial)' }}>
              {String((dashaData!.current_period as Record<string, Record<string, string>>).mahadasha?.planet)} Mahadasha · {String((dashaData!.current_period as Record<string, Record<string, string>>).antardasha?.planet)} Antardasha
            </p>
          </GlassCard>
        )}
        <GlassCard className="p-4">
          <DashaTimeline timeline={timeline || null} width={window.innerWidth > 900 ? 820 : window.innerWidth - 80} />
        </GlassCard>
      </div>
    </div>
  )
}