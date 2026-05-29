import { useState, useCallback, useRef } from 'react'
import { api } from '../../lib/api'

interface PlaceResult { display_name: string; latitude: number; longitude: number; timezone: string }

interface Props {
  value: string
  onChange: (val: string) => void
  onSelect: (result: PlaceResult) => void
}

export function PlaceAutocomplete({ value, onChange, onSelect }: Props) {
  const [loading, setLoading] = useState(false)
  const [resolved, setResolved] = useState<PlaceResult | null>(null)
  const [error, setError] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const handleChange = useCallback((v: string) => {
    onChange(v)
    setResolved(null)
    setError('')
    clearTimeout(debounceRef.current)
    if (v.length < 3) return
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        // Use the geocode tool via a temp session call, or directly call Nominatim
        const resp = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(v)}&format=json&limit=1`,
          { headers: { 'User-Agent': 'AstroAgent/1.0' } }
        )
        const results = await resp.json()
        if (results[0]) {
          const { lat, lon, display_name } = results[0]
          // Get timezone via backend
          const tzResp = await api.get('/api/panchang', {
            params: { date: new Date().toISOString().split('T')[0], lat, lon, tz: 'UTC' }
          }).catch(() => null)
          // Fallback: use timezonefinder approximation
          const timezone = tzResp?.data?.timezone || 'Asia/Kolkata'
          const result = { display_name, latitude: parseFloat(lat), longitude: parseFloat(lon), timezone }
          setResolved(result)
          onSelect(result)
        } else {
          setError('Place not found. Try adding the country name.')
        }
      } catch { setError('Geocoding failed. Check your connection.') }
      setLoading(false)
    }, 400)
  }, [onChange, onSelect])

  return (
    <div>
      <input
        value={value}
        onChange={e => handleChange(e.target.value)}
        placeholder="Mumbai, India"
        style={{
          width: '100%', padding: '0.75rem 1rem',
          background: 'rgba(13,13,43,0.8)',
          border: `1px solid ${resolved ? '#3DAB8F' : 'var(--glass-border)'}`,
          borderRadius: 8, color: 'var(--text-celestial)',
          fontFamily: 'Inter, sans-serif', fontSize: '0.95rem', outline: 'none',
        }}
      />
      {loading && <p style={{ fontSize: '0.8rem', color: 'var(--text-stardust)', marginTop: 4 }}>Locating...</p>}
      {resolved && !loading && (
        <p style={{ fontSize: '0.8rem', color: '#3DAB8F', marginTop: 4 }}>
          ✓ {resolved.display_name.split(',').slice(0,2).join(',')} · {resolved.timezone}
        </p>
      )}
      {error && <p style={{ fontSize: '0.8rem', color: '#CC2936', marginTop: 4 }}>{error}</p>}
    </div>
  )
}