import { AnimatePresence, motion } from 'framer-motion'
import { useSessionStore } from '../../store/sessionStore'

const TOOL_ICONS: Record<string, string> = {
  geocode_place: '📍', compute_birth_chart: '🔭', get_daily_transits: '💫',
  knowledge_lookup: '📚', find_muhurta: '⏰', compute_compatibility: '💞',
  detect_yogas: '✨', get_panchang: '🌙', compute_dasha_timeline: '📅',
}
const TOOL_LABELS: Record<string, string> = {
  geocode_place: 'Locating', compute_birth_chart: 'Computing birth chart',
  get_daily_transits: 'Reading the skies', knowledge_lookup: 'Consulting the texts',
  find_muhurta: 'Finding auspicious times', compute_compatibility: 'Comparing charts',
  detect_yogas: 'Detecting yogas', get_panchang: 'Computing panchang',
  compute_dasha_timeline: 'Building dasha timeline',
}

export function ToolActivity() {
  const { currentToolCalls } = useSessionStore()
  const active = currentToolCalls.filter(t => t.status === 'running')

  return (
    <AnimatePresence>
      {active.map(tc => (
        <motion.div key={tc.tool}
          initial={{ opacity: 0, y: -10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.95 }}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '4px 12px', borderRadius: 20, marginBottom: 6, marginRight: 6,
            background: 'rgba(61,127,191,0.15)', border: '1px solid rgba(61,127,191,0.3)',
            fontSize: '0.8rem', fontFamily: 'Inter, sans-serif',
            color: 'var(--text-stardust)',
          }}
        >
          <span>{TOOL_ICONS[tc.tool] || '⚡'}</span>
          <span>{TOOL_LABELS[tc.tool] || tc.tool}...</span>
          <span style={{ animation: 'pulse-soft 1s ease-in-out infinite' }}>●</span>
        </motion.div>
      ))}
    </AnimatePresence>
  )
}