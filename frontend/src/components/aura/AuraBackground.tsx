import { useEffect, useState } from 'react'

const DAY_CLASSES = [
  'aura-sunday','aura-monday','aura-tuesday','aura-wednesday',
  'aura-thursday','aura-friday','aura-saturday',
]

export function AuraBackground() {
  const [dayClass, setDayClass] = useState('')

  useEffect(() => {
    const day = new Date().getDay()
    setDayClass(DAY_CLASSES[day])
  }, [])

  return (
    <div
      className={dayClass}
      style={{
        position: 'fixed', inset: 0, zIndex: 1,
        pointerEvents: 'none',
        transition: 'background 3s ease',
      }}
    />
  )
}