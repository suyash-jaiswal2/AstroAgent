import type { ReactNode } from 'react'

interface Props {
  text: string
  showCursor?: boolean
}

export function MarkdownText({ text, showCursor = false }: Props) {
  if (!text) return null

  const paragraphs = text.split('\n')

  return (
    <>
      {paragraphs.map((para, i) => {
        const isLastLine = i === paragraphs.length - 1
        const trimmed = para.trim()

        // Check for bullet list items
        const bulletMatch = trimmed.match(/^[*|-]\s+(.*)/)

        const parseBold = (str: string): ReactNode[] => {
          const parts = str.split('**')
          const nodes: ReactNode[] = parts.map((part, index) => {
            if (index % 2 === 1) {
              return (
                <strong key={index} style={{ color: 'var(--gold-bright)', fontWeight: 600 }}>
                  {part}
                </strong>
              )
            }
            return part
          })

          // Dynamically append the blinking gold cursor to the absolute end of the last line
          if (isLastLine && showCursor) {
            nodes.push(
              <span
                key="cursor"
                style={{
                  display: 'inline-block',
                  width: 2,
                  height: '1.1em',
                  marginLeft: 4,
                  background: 'var(--gold)',
                  animation: 'cursor-blink 1s ease-in-out infinite',
                  verticalAlign: 'text-bottom',
                }}
              />
            )
          }

          return nodes
        }

        if (bulletMatch) {
          return (
            <li key={i} style={{ marginLeft: '1.25rem', listStyleType: 'disc', marginBottom: '0.6rem' }}>
              {parseBold(bulletMatch[1])}
            </li>
          )
        }

        // Render spacing for empty paragraphs
        if (!trimmed) {
          return <div key={i} style={{ height: '0.6rem' }} />
        }

        return (
          <p key={i} style={{ marginBottom: '0.6rem' }}>
            {parseBold(para)}
          </p>
        )
      })}
    </>
  )
}
