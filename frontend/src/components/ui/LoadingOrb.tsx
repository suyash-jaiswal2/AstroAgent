export function LoadingOrb({ size = 40 }: { size?: number }) {
  return (
    <div
      style={{
        width: size, height: size, borderRadius: '50%',
        background: 'radial-gradient(circle at 35% 35%, #3D7FBF, #1a3d5c)',
        boxShadow: '0 0 20px #3D7FBF66',
        animation: 'orb-breathe 2s ease-in-out infinite',
        display: 'inline-block',
      }}
    />
  )
}