import { useEffect, useState } from 'react'
import { GlassCard } from '../ui/GlassCard'
import { getPanchang } from '../../lib/api'
import { useSessionStore } from '../../store/sessionStore'

export function PanchangCard() {
  const { birthDetails } = useSessionStore()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!birthDetails?.latitude) return
    const today = new Date().toISOString().split('T')[0]
    getPanchang(today, birthDetails.latitude!, birthDetails.longitude!, birthDetails.timezone!)
      .then(setData).catch(console.error).finally(() => setLoading(false))
  }, [birthDetails])

  if (loading) return <GlassCard className="p-4"><p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Loading panchang...</p></GlassCard>
  if (!data) return null

  const tithi = data.tithi as Record<string, string>
  const nakshatra = data.nakshatra as Record<string, string | number>
  const vara = data.vara as Record<string, string>
  const yoga = data.yoga as Record<string, string>
  const rahu = data.rahu_kalam as Record<string, string>

  const rows = [
    { icon: '🌑', label: 'Tithi', value: `${tithi?.paksha} ${tithi?.name}` },
    { icon: '📅', label: 'Vara', value: `${vara?.name} (${vara?.lord})` },
    { icon: '⭐', label: 'Nakshatra', value: `${nakshatra?.name} Pada ${nakshatra?.pada}` },
    { icon: '🔱', label: 'Yoga', value: yoga?.name },
    { icon: '🚫', label: 'Rahu Kalam', value: `${rahu?.start} – ${rahu?.end}` },
  ]

  return (
    <GlassCard className="p-4">
      <h3 style={{ fontFamily: 'Cinzel, serif', fontSize: '0.7rem', letterSpacing: '0.15em', color: 'var(--gold)', marginBottom: '0.75rem' }}>
        TODAY'S PANCHANG
      </h3>
      {rows.map(r => (
        <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: '1rem', flexShrink: 0 }}>{r.icon}</span>
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'Inter, sans-serif' }}>{r.label}</div>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-celestial)', fontFamily: 'Cormorant Garamond, serif' }}>{String(r.value)}</div>
          </div>
        </div>
      ))}
      {Boolean(data.moon_phase) && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--glass-border)', fontSize: '0.82rem', color: 'var(--text-stardust)', fontFamily: 'Cormorant Garamond, serif', fontStyle: 'italic' }}>
          🌙 {String(data.moon_phase)} · {String(data.moon_illumination_pct)}% illuminated
        </div>
      )}
    </GlassCard>
  )
}