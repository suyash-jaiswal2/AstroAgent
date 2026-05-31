import orbNeutral from '../../assets/orb_neutral.png'

export function LoadingOrb({ size = 40 }: { size?: number }) {
  return (
    <div
      style={{
        width: size, height: size, borderRadius: '50%',
        backgroundImage: `url(${orbNeutral})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        boxShadow: '0 0 20px rgba(61, 127, 191, 0.4)',
        animation: 'orb-breathe 2s ease-in-out infinite',
        display: 'inline-block',
      }}
    />
  )
}