import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ObservatoryBackground } from '../components/observatory/ObservatoryBackground'
import { AuraBackground } from '../components/aura/AuraBackground'
import { GlassCard } from '../components/ui/GlassCard'
import { BirthDetailsForm } from '../components/birth-form/BirthDetailsForm'
import { CelestialOrb } from '../components/orb/CelestialOrb'
import { useSessionStore } from '../store/sessionStore'
import { createSession, saveBirthDetails } from '../lib/api'

export default function BirthDetails() {
  const navigate = useNavigate()
  const { sessionId, setSessionId, setBirthDetails, reset } = useSessionStore()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (details: Parameters<typeof setBirthDetails>[0]) => {
    setLoading(true)
    try {
      reset() // Clear all old messages, natal chart, and stale session states
      const s = await createSession()
      const sid = s.session_id
      setSessionId(sid)
      await saveBirthDetails(sid, details as unknown as Record<string, unknown>)
      setBirthDetails(details)
      navigate('/chat')
    } catch (err) {
      console.error(err)
      alert('Could not save birth details. Please check your connection.')
    }
    setLoading(false)
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <ObservatoryBackground />
      <AuraBackground />
      <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: 500 }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
          <CelestialOrb size={80} />
        </div>
        <motion.h2 initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ fontFamily: 'Cinzel, serif', textAlign: 'center', fontSize: '1.4rem', letterSpacing: '0.15em', color: 'var(--text-celestial)', marginBottom: '0.5rem' }}
        >
          YOUR BIRTH DETAILS
        </motion.h2>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.2 } }}
          style={{ fontFamily: 'Cormorant Garamond, serif', fontStyle: 'italic', textAlign: 'center', color: 'var(--text-stardust)', marginBottom: '2rem', fontSize: '1.05rem' }}
        >
          The moment you arrived tells the stars your story.
        </motion.p>
        <GlassCard className="p-6">
          <BirthDetailsForm onSubmit={handleSubmit} loading={loading} />
        </GlassCard>
      </div>
    </div>
  )
}