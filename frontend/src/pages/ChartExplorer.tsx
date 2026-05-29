import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ObservatoryBackground } from '../components/observatory/ObservatoryBackground'
import { GlassCard } from '../components/ui/GlassCard'
import { ChartWheel } from '../components/chart/ChartWheel'
import { useSessionStore } from '../store/sessionStore'
import { getSession } from '../lib/api'

export default function ChartExplorer() {
  const navigate = useNavigate()
  const { sessionId, natalChart, setNatalChart } = useSessionStore()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!sessionId) { navigate('/'); return }
    if (!natalChart) {
      setLoading(true)
      getSession(sessionId).then(d => { if (d.natal_chart) setNatalChart(d.natal_chart) }).finally(() => setLoading(false))
    }
  }, [sessionId, natalChart, setNatalChart, navigate])

  return (
    <div style={{ position: 'relative', minHeight: '100vh', padding: '2rem' }}>
      <ObservatoryBackground />
      <div style={{ position: 'relative', zIndex: 10, maxWidth: 800, margin: '0 auto' }}>
        <button onClick={() => navigate('/chat')} style={{ color: 'var(--text-stardust)', background: 'none', border: 'none', cursor: 'pointer', marginBottom: '1rem', fontFamily: 'Inter, sans-serif', fontSize: '0.85rem' }}>← Back to Chat</button>
        <h1 style={{ fontFamily: 'Cinzel, serif', fontSize: '1.5rem', color: 'var(--gold)', marginBottom: '1.5rem', letterSpacing: '0.15em' }}>BIRTH CHART</h1>
        <GlassCard className="p-6" style={{ display: 'flex', justifyContent: 'center' }}>
          {loading ? <p style={{ color: 'var(--text-dim)' }}>Loading chart...</p> : <ChartWheel chart={natalChart as Record<string, unknown>} size={400} />}
        </GlassCard>
      </div>
    </div>
  )
}