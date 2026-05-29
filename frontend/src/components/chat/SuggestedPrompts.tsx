interface Props { prompts: string[]; onSelect: (p: string) => void }

export function SuggestedPrompts({ prompts, onSelect }: Props) {
  if (!prompts.length) return null
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: '1rem' }}>
      {prompts.map(p => (
        <button key={p} onClick={() => onSelect(p)}
          style={{
            padding: '6px 14px', borderRadius: 20,
            background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.25)',
            color: 'var(--text-stardust)', fontFamily: 'Inter, sans-serif',
            fontSize: '0.82rem', cursor: 'pointer', transition: 'all 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(201,168,76,0.2)'; e.currentTarget.style.color = 'var(--gold)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(201,168,76,0.1)'; e.currentTarget.style.color = 'var(--text-stardust)' }}
        >
          {p}
        </button>
      ))}
    </div>
  )
}