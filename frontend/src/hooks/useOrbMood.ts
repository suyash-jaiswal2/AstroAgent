import { useEffect } from 'react'
import { useSessionStore } from '../store/sessionStore'

const HORA_MOODS: Record<string, 'favorable' | 'introspective' | 'dynamic' | 'spiritual' | 'neutral' | 'communicative'> = {
  Jupiter: 'favorable', Venus: 'favorable',
  Saturn: 'introspective', Moon: 'introspective',
  Mars: 'dynamic', Sun: 'neutral',
  Mercury: 'communicative',
}

const MOOD_COLORS = {
  favorable:     { primaryColor: '#F4B942', secondaryColor: '#8B6914' },
  introspective: { primaryColor: '#4B4B9F', secondaryColor: '#1a1a4a' },
  dynamic:       { primaryColor: '#C23B22', secondaryColor: '#5a1a0a' },
  spiritual:     { primaryColor: '#7B4FBF', secondaryColor: '#2d1a5c' },
  neutral:       { primaryColor: '#3D7FBF', secondaryColor: '#1a3d5c' },
  communicative: { primaryColor: '#3DAB8F', secondaryColor: '#1a5c48' },
}

export function useOrbMood() {
  const { setOrbMood, isStreaming, currentToolCalls } = useSessionStore()

  useEffect(() => {
    if (isStreaming) {
      setOrbMood({ pulseSpeed: 'fast' })
    } else if (currentToolCalls.some(t => t.status === 'running')) {
      setOrbMood({ pulseSpeed: 'medium' })
    } else {
      setOrbMood({ pulseSpeed: 'slow' })
    }
  }, [isStreaming, currentToolCalls, setOrbMood])

  useEffect(() => {
    // Set mood based on current day's planetary hora
    const hour = new Date().getHours()
    const day = new Date().getDay()
    const HORA_SEQUENCE = ['Sun','Venus','Mercury','Moon','Saturn','Jupiter','Mars']
    const DAY_START = [0, 3, 6, 2, 5, 1, 4]
    const horaIdx = (DAY_START[day] + hour) % 7
    const horaLord = HORA_SEQUENCE[horaIdx]
    const mood = HORA_MOODS[horaLord] || 'neutral'
    setOrbMood({ mood, ...MOOD_COLORS[mood] })
  }, [setOrbMood])
}