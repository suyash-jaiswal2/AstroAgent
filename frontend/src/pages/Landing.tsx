// Landing page
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ObservatoryBackground } from '../components/observatory/ObservatoryBackground'
import { AuraBackground } from '../components/aura/AuraBackground'
import { CelestialOrb } from '../components/orb/CelestialOrb'
import { useSessionStore } from '../store/sessionStore'
import { createSession } from '../lib/api'

const stagger = { hidden: { opacity: 0, y: 20 }, visible: (i: number) => ({
  opacity: 1, y: 0, transition: { delay: i * 0.3, duration: 0.8, ease: 'easeOut' as const },
})}

export default function Landing() {
  const navigate = useNavigate()
  const { sessionId, setSessionId, birthDetails } = useSessionStore()

  const handleBegin = async () => {
    if (!sessionId) {
      const data = await createSession()
      setSessionId(data.session_id)
    }
    navigate('/birth')
  }

  const handleContinue = () => navigate('/chat')

  return (
    <div style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      <ObservatoryBackground />
      <AuraBackground />

      <div style={{ position: 'relative', zIndex: 10, textAlign: 'center', maxWidth: 600, padding: '2rem' }}>
        {/* Constellation SVG */}
        <motion.div custom={0} variants={stagger} initial="hidden" animate="visible">
          <svg width="60" height="60" viewBox="0 0 60 60" style={{ margin: '0 auto 1.5rem' }}>
            {[[30,5],[55,20],[45,50],[15,50],[5,20]].map(([x,y], i, pts) => (
              <g key={i}>
                <line x1={x} y1={y} x2={pts[(i+1)%pts.length][0]} y2={pts[(i+1)%pts.length][1]} stroke="#C9A84C" strokeWidth="0.8" opacity="0.6"/>
                <circle cx={x} cy={y} r="2.5" fill="#F4D03F" opacity="0.9"/>
              </g>
            ))}
          </svg>
        </motion.div>

        <motion.h1 custom={1} variants={stagger} initial="hidden" animate="visible"
          style={{ fontFamily: 'Cinzel, serif', fontSize: 'clamp(2.5rem, 6vw, 4rem)', letterSpacing: '0.2em', color: 'var(--text-celestial)', marginBottom: '0.5rem' }}
        >
          ARADHANA
        </motion.h1>

        <motion.p custom={2} variants={stagger} initial="hidden" animate="visible"
          style={{ fontFamily: 'Cormorant Garamond, serif', fontStyle: 'italic', fontSize: '1.3rem', color: 'var(--text-stardust)', marginBottom: '0.5rem' }}
        >
          Your personal celestial companion
        </motion.p>

        <motion.p custom={3} variants={stagger} initial="hidden" animate="visible"
          style={{ fontFamily: 'Cinzel, serif', fontSize: '0.8rem', letterSpacing: '0.3em', color: 'var(--gold)', marginBottom: '3rem', textTransform: 'uppercase' }}
        >
          Know yourself through the stars
        </motion.p>

        <motion.div custom={4} variants={stagger} initial="hidden" animate="visible"
          style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}
        >
          <CelestialOrb size={120} />
        </motion.div>

        <motion.div custom={5} variants={stagger} initial="hidden" animate="visible"
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}
        >
          <button onClick={handleBegin}
            style={{
              padding: '0.875rem 2.5rem', borderRadius: 8,
              background: 'linear-gradient(135deg, var(--gold) 0%, #8B6914 100%)',
              border: 'none', color: '#04040C', fontFamily: 'Cinzel, serif',
              fontSize: '0.9rem', letterSpacing: '0.15em', cursor: 'pointer',
              boxShadow: '0 0 20px #C9A84C44',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 0 30px #C9A84C88')}
            onMouseLeave={e => (e.currentTarget.style.boxShadow = '0 0 20px #C9A84C44')}
          >
            Begin Your Reading
          </button>

          {birthDetails && (
            <button onClick={handleContinue}
              style={{
                padding: '0.6rem 2rem', borderRadius: 8,
                background: 'transparent', border: '1px solid var(--glass-border)',
                color: 'var(--text-stardust)', fontFamily: 'Inter, sans-serif',
                fontSize: '0.85rem', cursor: 'pointer', letterSpacing: '0.05em',
              }}
            >
              Continue your journey, {birthDetails.name}
            </button>
          )}
        </motion.div>
      </div>
    </div>
  )
}