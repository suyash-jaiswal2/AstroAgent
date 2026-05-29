import { useState } from 'react'
import { PlaceAutocomplete } from './PlaceAutocomplete'
import type { BirthDetails } from '../../store/sessionStore'

interface Props { onSubmit: (d: BirthDetails) => void; loading?: boolean }

export function BirthDetailsForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState({ name: '', date: '', time: '', place: '', time_unknown: false })
  const [geoResult, setGeoResult] = useState<{ latitude: number; longitude: number; timezone: string } | null>(null)
  const [error, setError] = useState('')

  const set = (k: string, v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  const validate = () => {
    if (!form.name.trim()) return 'How should the stars address you?'
    if (!form.date) return 'A birth date is needed to cast your chart.'
    const d = new Date(form.date)
    if (d > new Date()) return "The stars haven't written that chapter yet."
    if (d.getFullYear() < 1800) return 'Please enter a birth year after 1800.'
    if (!form.place) return 'A birthplace helps the stars find you.'
    if (!geoResult) return 'Please wait for the place to be resolved.'
    return null
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const err = validate()
    if (err) { setError(err); return }
    setError('')
    onSubmit({
      name: form.name.trim(),
      date: form.date,
      time: form.time_unknown ? null : form.time || null,
      place: form.place,
      latitude: geoResult?.latitude,
      longitude: geoResult?.longitude,
      timezone: geoResult?.timezone,
      time_unknown: form.time_unknown,
    })
  }

  const inputStyle = {
    width: '100%', padding: '0.75rem 1rem',
    background: 'rgba(13,13,43,0.8)',
    border: '1px solid var(--glass-border)',
    borderRadius: 8, color: 'var(--text-celestial)',
    fontFamily: 'Inter, sans-serif', fontSize: '0.95rem', outline: 'none',
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div>
        <label style={{ display: 'block', fontFamily: 'Cinzel, serif', fontSize: '0.75rem', letterSpacing: '0.1em', color: 'var(--gold)', marginBottom: 8 }}>YOUR NAME</label>
        <input value={form.name} onChange={e => set('name', e.target.value)}
          placeholder="How should the stars address you?" style={inputStyle} />
      </div>

      <div>
        <label style={{ display: 'block', fontFamily: 'Cinzel, serif', fontSize: '0.75rem', letterSpacing: '0.1em', color: 'var(--gold)', marginBottom: 8 }}>DATE OF BIRTH</label>
        <input type="date" value={form.date} onChange={e => set('date', e.target.value)}
          max={new Date().toISOString().split('T')[0]} style={inputStyle} />
      </div>

      <div>
        <label style={{ display: 'block', fontFamily: 'Cinzel, serif', fontSize: '0.75rem', letterSpacing: '0.1em', color: 'var(--gold)', marginBottom: 8 }}>TIME OF BIRTH</label>
        {!form.time_unknown && (
          <input type="time" value={form.time} onChange={e => set('time', e.target.value)} style={inputStyle} />
        )}
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, cursor: 'pointer', color: 'var(--text-stardust)', fontSize: '0.85rem' }}>
          <input type="checkbox" checked={form.time_unknown} onChange={e => set('time_unknown', e.target.checked)} />
          I don't know my exact birth time
        </label>
        {form.time_unknown && (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-stardust)', marginTop: 4 }}>
            No problem — we'll cast the chart for solar noon and note the uncertainty.
          </p>
        )}
      </div>

      <div>
        <label style={{ display: 'block', fontFamily: 'Cinzel, serif', fontSize: '0.75rem', letterSpacing: '0.1em', color: 'var(--gold)', marginBottom: 8 }}>PLACE OF BIRTH</label>
        <PlaceAutocomplete value={form.place} onChange={v => set('place', v)} onSelect={r => setGeoResult(r)} />
      </div>

      {error && <p style={{ color: '#CC2936', fontSize: '0.9rem', fontFamily: 'Cormorant Garamond, serif' }}>{error}</p>}

      <button type="submit" disabled={loading}
        style={{
          padding: '0.875rem', borderRadius: 8,
          background: loading ? '#555' : 'linear-gradient(135deg, var(--gold) 0%, #8B6914 100%)',
          border: 'none', color: '#04040C', fontFamily: 'Cinzel, serif',
          fontSize: '0.9rem', letterSpacing: '0.1em', cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Consulting the stars...' : 'Cast My Chart'}
      </button>
    </form>
  )
}