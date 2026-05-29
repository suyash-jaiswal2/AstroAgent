import { useMemo } from 'react'

interface Star { id: number; x: number; y: number; r: number; opacity: number; delay: number }

function StarField() {
  const stars = useMemo<Star[]>(() =>
    Array.from({ length: 200 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      r: Math.random() * 1.5 + 0.3,
      opacity: Math.random() * 0.6 + 0.3,
      delay: Math.random() * 4,
    })), []
  )

  return (
    <svg
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
      preserveAspectRatio="xMidYMid slice"
      viewBox="0 0 100 100"
    >
      {stars.map(s => (
        <circle
          key={s.id}
          cx={s.x} cy={s.y} r={s.r * 0.05}
          fill="white"
          opacity={s.opacity}
          style={{
            animation: `twinkle ${2 + Math.random() * 3}s ease-in-out infinite alternate`,
            animationDelay: `${s.delay}s`,
          }}
        />
      ))}
    </svg>
  )
}

function NebulaClouds() {
  const nebulae: Array<{ w: string; h: string; color: string; delay: string; top?: string; left?: string; right?: string; bottom?: string }> = [
    { top: '-20%', left: '-10%', w: '60%', h: '60%', color: '#0D0D2B', delay: '0s' },
    { top: '30%', right: '-20%', w: '50%', h: '50%', color: '#12123A', delay: '7s' },
    { bottom: '-10%', left: '20%', w: '55%', h: '45%', color: '#0a0a1f', delay: '14s' },
  ]
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {nebulae.map((n, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: n.w, height: n.h,
            top: n.top, left: n.left,
            right: n.right,
            bottom: n.bottom,
            background: `radial-gradient(ellipse at center, ${n.color} 0%, transparent 70%)`,
            animation: `nebula-drift 20s ease-in-out infinite`,
            animationDelay: n.delay,
            opacity: 0.8,
          }}
        />
      ))}
    </div>
  )
}

export function ObservatoryBackground() {
  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'var(--color-deep-space)',
        zIndex: 0, overflow: 'hidden',
      }}
    >
      <NebulaClouds />
      <StarField />
      {/* Subtle grid perspective */}
      <div
        style={{
          position: 'absolute', inset: 0,
          backgroundImage: `
            linear-gradient(rgba(61,127,191,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(61,127,191,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          transform: 'perspective(800px) rotateX(10deg)',
          transformOrigin: 'bottom',
          opacity: 0.4,
          pointerEvents: 'none',
        }}
      />
    </div>
  )
}