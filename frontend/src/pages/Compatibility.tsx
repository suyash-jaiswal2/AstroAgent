import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ObservatoryBackground } from '../components/observatory/ObservatoryBackground'
import { GlassCard } from '../components/ui/GlassCard'
import { useSessionStore } from '../store/sessionStore'
import { api } from '../lib/api'

export default function Compatibility() {
  const navigate = useNavigate()
  const { sessionId } = useSessionStore()
  const [partnerForm, setPartnerForm] = useState({ name: '', date: '', time: '', place: '' })
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sessionId) return
    setLoading(true)
    try {
      const resp = await api.post('/api/compatibility', {
        session_id: sessionId, partner_name: partnerForm.name,
        partner_date: partnerForm.date, partner_time: partnerForm.time || null,
        partner_place: partnerForm.place,
      })
      setResult(resp.data)
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const ashtakoot = result?.ashtakoot as Record<string, unknown> | null
  const inputStyle = { width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(13,13,43,0.8)', border: '1px solid var(--glass-border)', borderRadius: 8, color: 'var(--text-celestial)', fontFamily: 'Inter, sans-serif', fontSize: '0.9rem', outline: 'none' }

  return (
    <div style={{ position: 'relative', minHeight: '100vh', padding: '2rem' }}>
      <ObservatoryBackground />
      <div style={{ position: 'relative', zIndex: 10, maxWidth: 600, margin: '0 auto' }}>
        <button onClick={() => navigate('/chat')} style={{ color: 'var(--text-stardust)', background: 'none', border: 'none', cursor: 'pointer', marginBottom: '1rem', fontFamily: 'Inter, sans-serif', fontSize: '0.85rem' }}>← Back</button>
        <h1 style={{ fontFamily: 'Cinzel, serif', fontSize: '1.5rem', color: 'var(--gold)', marginBottom: '1.5rem', letterSpacing: '0.15em' }}>COMPATIBILITY</h1>
        <GlassCard className="p-6">
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {['name','date','time','place'].map(k => (
              <div key={k}>
                <label style={{ display: 'block', fontFamily: 'Cinzel, serif', fontSize: '0.7rem', color: 'var(--gold)', letterSpacing: '0.1em', marginBottom: 6 }}>{k.toUpperCase()}</label>
                <input type={k === 'date' ? 'date' : k === 'time' ? 'time' : 'text'}
                  value={(partnerForm as Record<string, string>)[k]} onChange={e => setPartnerForm(f => ({...f, [k]: e.target.value}))}
                  placeholder={k === 'name' ? "Partner's name" : k === 'place' ? 'City, Country' : undefined}
                  style={inputStyle} />
              </div>
            ))}
            <button type="submit" disabled={loading} style={{ padding: '0.75rem', background: loading ? '#555' : 'linear-gradient(135deg, var(--gold), #8B6914)', border: 'none', borderRadius: 8, color: '#04040C', fontFamily: 'Cinzel, serif', fontSize: '0.85rem', letterSpacing: '0.1em', cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? 'Computing...' : 'Compute Compatibility'}
            </button>
          </form>
        </GlassCard>
        {ashtakoot && (
          <GlassCard className="p-6 mt-4">
            <h2 style={{ fontFamily: 'Cinzel, serif', fontSize: '1rem', color: 'var(--gold)', marginBottom: 8 }}>ASHTAKOOT SCORE</h2>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '2rem', color: 'var(--text-celestial)' }}>{String(ashtakoot.total_score)}<span style={{ fontSize: '1rem', color: 'var(--text-stardust)' }}>/36</span></p>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontStyle: 'italic', color: 'var(--text-stardust)', marginTop: 4 }}>{String(ashtakoot.overall)}</p>
            {(ashtakoot.doshas_present as string[])?.length > 0 && (
              <p style={{ color: '#CC2936', fontSize: '0.85rem', marginTop: 8 }}>⚠️ {(ashtakoot.doshas_present as string[]).join(', ')} present</p>
            )}
          </GlassCard>
        )}
      </div>
    </div>
  )
}