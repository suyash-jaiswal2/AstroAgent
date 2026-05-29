interface GlassCardProps {
  children: React.ReactNode
  className?: string
  glow?: boolean
  glowColor?: string
  onClick?: () => void
  style?: React.CSSProperties
}

export function GlassCard({ children, className = '', glow, glowColor = '#3D7FBF', onClick, style }: GlassCardProps) {
  return (
    <div
      className={`glass-card ${className}`}
      style={{ ...(glow ? { boxShadow: `0 0 20px ${glowColor}44, 0 8px 32px rgba(0,0,0,0.4)` } : undefined), ...style }}
      onClick={onClick}
    >
      {children}
    </div>
  )
}