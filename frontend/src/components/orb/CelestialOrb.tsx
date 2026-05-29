import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSessionStore } from '../../store/sessionStore'

const MOOD_COLORS = {
  favorable:     { primary: '#F4B942', secondary: '#8B6914', glow: '#F4B94244' },
  introspective: { primary: '#4B4B9F', secondary: '#1a1a4a', glow: '#4B4B9F44' },
  dynamic:       { primary: '#C23B22', secondary: '#5a1a0a', glow: '#C23B2244' },
  spiritual:     { primary: '#7B4FBF', secondary: '#2d1a5c', glow: '#7B4FBF44' },
  neutral:       { primary: '#3D7FBF', secondary: '#1a3d5c', glow: '#3D7FBF44' },
  communicative: { primary: '#3DAB8F', secondary: '#1a5c48', glow: '#3DAB8F44' },
}

interface CelestialOrbProps {
  size?: number
  showRipple?: boolean
}

export function CelestialOrb({ size = 200, showRipple = false }: CelestialOrbProps) {
  const { orbMood, isStreaming, currentToolCalls } = useSessionStore()
  const colors = MOOD_COLORS[orbMood.mood] || MOOD_COLORS.neutral
  const [rippleKey, setRippleKey] = useState(0)
  const prevStreaming = useRef(false)

  useEffect(() => {
    if (isStreaming && !prevStreaming.current) {
      setRippleKey(k => k + 1)
    }
    prevStreaming.current = isStreaming
  }, [isStreaming])

  const toolCount = currentToolCalls.filter(t => t.status === 'running').length

  return (
    <div
      style={{ width: size, height: size, position: 'relative', flexShrink: 0 }}
      className="select-none"
    >
      {/* Outer glow layer */}
      <div
        style={{
          position: 'absolute', inset: -size * 0.3,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
          animation: 'orb-breathe 4s ease-in-out infinite',
          animationDuration: orbMood.pulseSpeed === 'fast' ? '2s' : orbMood.pulseSpeed === 'medium' ? '3s' : '4s',
          pointerEvents: 'none',
        }}
      />

      {/* Core orb */}
      <motion.div
        animate={{ scale: isStreaming ? [1, 1.04, 1] : 1 }}
        transition={{ duration: 1.5, repeat: isStreaming ? Infinity : 0 }}
        style={{
          width: '100%', height: '100%', borderRadius: '50%',
          background: `
            radial-gradient(circle at 35% 30%, ${colors.primary}CC 0%, transparent 55%),
            radial-gradient(circle at 65% 70%, ${colors.secondary}AA 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, ${colors.secondary}88 30%, transparent 80%)
          `,
          boxShadow: `
            0 0 ${size * 0.3}px ${size * 0.1}px ${colors.glow},
            0 0 ${size * 0.6}px ${size * 0.2}px ${colors.primary}22,
            inset 0 0 ${size * 0.15}px rgba(255,255,255,0.08)
          `,
          filter: 'blur(0.5px)',
          position: 'relative', overflow: 'hidden',
        }}
      >
        {/* Inner shimmer */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          background: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.12) 0%, transparent 40%)`,
        }} />
      </motion.div>

      {/* Ripple on message send */}
      <AnimatePresence>
        {(showRipple || rippleKey > 0) && (
          <motion.div
            key={rippleKey}
            initial={{ scale: 1, opacity: 0.7 }}
            animate={{ scale: 2.8, opacity: 0 }}
            exit={{}}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              border: `2px solid ${colors.primary}88`,
              pointerEvents: 'none',
            }}
          />
        )}
      </AnimatePresence>

      {/* Energy streams during tool calls */}
      {toolCount > 0 && Array.from({ length: Math.min(toolCount, 4) }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -60 * Math.cos((i / 4) * Math.PI * 2), y: -60 * Math.sin((i / 4) * Math.PI * 2) }}
          animate={{ opacity: [0, 1, 0], x: 0, y: 0 }}
          transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3, ease: 'easeIn' }}
          style={{
            position: 'absolute',
            width: 6, height: 6,
            top: '50%', left: '50%',
            borderRadius: '50%',
            background: colors.primary,
            boxShadow: `0 0 8px ${colors.primary}`,
            pointerEvents: 'none',
          }}
        />
      ))}
    </div>
  )
}