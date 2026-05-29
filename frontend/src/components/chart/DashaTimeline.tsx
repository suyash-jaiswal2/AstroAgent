import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const PLANET_COLORS: Record<string, string> = {
  Ketu:'#9B59B6', Venus:'#E8D5FF', Sun:'#FFB347', Moon:'#C8D6E5',
  Mars:'#CC2936', Rahu:'#2C3E50', Jupiter:'#F4D03F', Saturn:'#7F7F7F', Mercury:'#2ECC71',
}

interface DashaPeriod {
  planet: string; start: string; end: string; years: number
  antardasha?: Array<{ planet: string; start: string; end: string }>
}

interface Props { timeline: DashaPeriod[] | null; width?: number }

export function DashaTimeline({ timeline, width = 700 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const height = 120

  useEffect(() => {
    if (!svgRef.current || !timeline?.length) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const today = new Date()
    const allStart = new Date(timeline[0].start)
    const allEnd = new Date(timeline[timeline.length - 1].end)
    const totalDays = (allEnd.getTime() - allStart.getTime()) / 86400000

    const xScale = d3.scaleTime().domain([allStart, allEnd]).range([10, width - 10])
    const barY = 30, barH = 40

    // Dasha blocks
    timeline.forEach(d => {
      const x0 = xScale(new Date(d.start))
      const x1 = xScale(new Date(d.end))
      const blockW = Math.max(2, x1 - x0)
      const color = PLANET_COLORS[d.planet] || '#888'

      svg.append('rect').attr('x', x0).attr('y', barY).attr('width', blockW).attr('height', barH)
        .attr('fill', color + '55').attr('stroke', color + 'AA').attr('stroke-width', 1)
        .attr('rx', 3).style('cursor', 'pointer')
        .append('title').text(`${d.planet} Mahadasha\n${d.start} → ${d.end}\n${d.years} years`)

      if (blockW > 30) {
        svg.append('text').attr('x', x0 + blockW / 2).attr('y', barY + barH / 2 + 4)
          .attr('text-anchor', 'middle').attr('fill', color).attr('font-size', Math.min(11, blockW / 5))
          .attr('font-family', 'Cinzel, serif').text(d.planet)
      }
    })

    // NOW marker
    const nowX = xScale(today)
    if (nowX > 10 && nowX < width - 10) {
      svg.append('line').attr('x1', nowX).attr('y1', barY - 8).attr('x2', nowX).attr('y2', barY + barH + 16)
        .attr('stroke', 'var(--gold)').attr('stroke-width', 2)
      svg.append('circle').attr('cx', nowX).attr('cy', barY - 10).attr('r', 4)
        .attr('fill', 'var(--gold)').style('animation', 'pulse-soft 2s infinite')
      svg.append('text').attr('x', nowX).attr('y', barY + barH + 28)
        .attr('text-anchor', 'middle').attr('fill', 'var(--gold)').attr('font-size', 9)
        .attr('font-family', 'Inter, sans-serif').text('NOW')
    }

    // Year axis
    const yearScale = d3.axisBottom(xScale).ticks(d3.timeYear.every(5)).tickSize(4)
    svg.append('g').attr('transform', `translate(0, ${barY + barH + 5})`).call(yearScale)
      .selectAll('text').attr('fill', 'var(--text-dim)').attr('font-size', 8).attr('font-family', 'Inter, sans-serif')
    svg.select('.domain').attr('stroke', 'rgba(120,120,200,0.3)')
    svg.selectAll('.tick line').attr('stroke', 'rgba(120,120,200,0.3)')

  }, [timeline, width])

  if (!timeline) return <div style={{ color: 'var(--text-dim)', fontSize: '0.9rem', padding: '1rem' }}>Dasha data not available</div>

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg ref={svgRef} width={width} height={height} style={{ display: 'block' }} />
    </div>
  )
}