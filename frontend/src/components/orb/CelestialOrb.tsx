import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSessionStore } from '../../store/sessionStore'

import orbNeutral from '../../assets/orb_neutral.png'
import orbFavorable from '../../assets/orb_favorable.png'
import orbIntrospective from '../../assets/orb_introspective.png'
import orbDynamic from '../../assets/orb_dynamic.png'
import orbSpiritual from '../../assets/orb_spiritual.png'
import orbCommunicative from '../../assets/orb_communicative.png'

const MOOD_COLORS = {
  favorable:     { primary: '#F4B942', secondary: '#8B6914', glow: '#F4B94244', image: orbFavorable },
  introspective: { primary: '#4B4B9F', secondary: '#1a1a4a', glow: '#4B4B9F44', image: orbIntrospective },
  dynamic:       { primary: '#C23B22', secondary: '#5a1a0a', glow: '#C23B2244', image: orbDynamic },
  spiritual:     { primary: '#7B4FBF', secondary: '#2d1a5c', glow: '#7B4FBF44', image: orbSpiritual },
  neutral:       { primary: '#3D7FBF', secondary: '#1a3d5c', glow: '#3D7FBF44', image: orbNeutral },
  communicative: { primary: '#3DAB8F', secondary: '#1a5c48', glow: '#3DAB8F44', image: orbCommunicative },
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
          position: 'absolute', inset: -size * 0.25,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
          animation: 'orb-breathe 4s ease-in-out infinite',
          animationDuration: orbMood.pulseSpeed === 'fast' ? '2s' : orbMood.pulseSpeed === 'medium' ? '3s' : '4s',
          pointerEvents: 'none',
          mixBlendMode: 'screen',
        }}
      />

      {/* 3D Tilted Astro Ring */}
      <div
        style={{
          position: 'absolute',
          inset: -size * 0.15,
          pointerEvents: 'none',
          transform: 'rotateX(72deg) rotateY(12deg)',
          transformStyle: 'preserve-3d',
        }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 25, ease: 'linear' }}
          style={{
            width: '100%', height: '100%',
            borderRadius: '50%',
            border: '2px double rgba(201, 168, 76, 0.45)',
            borderTopColor: 'transparent',
            borderBottomColor: 'transparent',
            boxShadow: `0 0 15px rgba(201, 168, 76, 0.2)`,
          }}
        />
      </div>

      {/* Outer Dashed Orbit Tracker */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ repeat: Infinity, duration: 35, ease: 'linear' }}
        style={{
          position: 'absolute',
          inset: -size * 0.2,
          borderRadius: '50%',
          border: '1px dashed rgba(255, 255, 255, 0.15)',
          borderLeftColor: 'transparent',
          borderRightColor: 'transparent',
          pointerEvents: 'none',
          boxShadow: `inset 0 0 10px rgba(255, 255, 255, 0.02)`,
        }}
      />

      {/* Core orb */}
      <motion.div
        animate={{ scale: isStreaming ? [1, 1.05, 1] : 1 }}
        transition={{ duration: 1.5, repeat: isStreaming ? Infinity : 0 }}
        style={{
          width: '100%', height: '100%', borderRadius: '50%',
          backgroundImage: `url(${colors.image})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          boxShadow: `
            0 0 ${size * 0.2}px ${size * 0.05}px ${colors.glow},
            0 0 ${size * 0.4}px ${size * 0.1}px ${colors.primary}22,
            inset 0 0 15px rgba(255,255,255,0.1)
          `,
          position: 'relative', overflow: 'hidden',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}
      >
        {/* Inner shimmering glass overlay */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          background: `radial-gradient(circle at 30% 30%, rgba(255,255,255,0.2) 0%, transparent 60%)`,
          pointerEvents: 'none',
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