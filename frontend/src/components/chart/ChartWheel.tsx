import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
const SIGN_SYMBOLS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
const PLANET_COLORS: Record<string, string> = {
  Sun:'#FFB347', Moon:'#C8D6E5', Mercury:'#2ECC71', Venus:'#F0E6FF',
  Mars:'#CC2936', Jupiter:'#F4D03F', Saturn:'#7F7F7F',
  Uranus:'#87CEEB', Neptune:'#4169E1', Pluto:'#9B59B6',
  Rahu:'#2C3E50', Ketu:'#7D6608',
}

interface Props { chart: Record<string, unknown> | null; size?: number }

export function ChartWheel({ chart, size = 400 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !chart) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const cx = size / 2, cy = size / 2, r = size * 0.45

    // Background
    svg.append('circle').attr('cx', cx).attr('cy', cy).attr('r', r + 10)
      .attr('fill', 'rgba(13,13,43,0.8)').attr('stroke', 'rgba(120,120,200,0.2)').attr('stroke-width', 1)

    // Sign bands
    const signBandOuter = r, signBandInner = r * 0.82
    SIGNS.forEach((_sign, i) => {
      const startAngle = (i / 12) * 2 * Math.PI - Math.PI / 2
      const endAngle = ((i + 1) / 12) * 2 * Math.PI - Math.PI / 2
      const arc = d3.arc<unknown, unknown>().innerRadius(signBandInner).outerRadius(signBandOuter)
        .startAngle(startAngle).endAngle(endAngle)
      svg.append('path').attr('d', arc({} as unknown) as string).attr('transform', `translate(${cx},${cy})`)
        .attr('fill', i % 2 === 0 ? 'rgba(61,127,191,0.08)' : 'rgba(61,127,191,0.04)')
        .attr('stroke', 'rgba(120,120,200,0.15)').attr('stroke-width', 0.5)

      const midAngle = (startAngle + endAngle) / 2
      const textR = (signBandOuter + signBandInner) / 2
      svg.append('text')
        .attr('x', cx + textR * Math.cos(midAngle)).attr('y', cy + textR * Math.sin(midAngle))
        .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
        .attr('fill', 'rgba(144,144,192,0.7)').attr('font-size', size * 0.03)
        .text(SIGN_SYMBOLS[i])
    })

    // House lines
    const houses = (chart as Record<string, Record<string, Record<string, Record<string, number>>>>).tropical?.houses || {}
    Object.values(houses).forEach((house) => {
      if (!house?.cusp_longitude) return
      const angle = (house.cusp_longitude / 360) * 2 * Math.PI - Math.PI / 2
      svg.append('line')
        .attr('x1', cx + signBandInner * Math.cos(angle)).attr('y1', cy + signBandInner * Math.sin(angle))
        .attr('x2', cx + r * 0.3 * Math.cos(angle)).attr('y2', cy + r * 0.3 * Math.sin(angle))
        .attr('stroke', 'rgba(201,168,76,0.2)').attr('stroke-width', 0.8)
    })

    // Planets
    const planets = (chart as Record<string, Record<string, Record<string, unknown>>>).tropical?.planets || {}
    Object.entries(planets).forEach(([name, data]) => {
      const lon = (data as Record<string, unknown>)?.longitude as number
      if (lon === undefined) return
      const angle = (lon / 360) * 2 * Math.PI - Math.PI / 2
      const pr = r * 0.6
      const px = cx + pr * Math.cos(angle)
      const py = cy + pr * Math.sin(angle)
      const color = PLANET_COLORS[name] || '#ffffff'

      svg.append('circle').attr('cx', px).attr('cy', py).attr('r', size * 0.022)
        .attr('fill', color + 'CC').attr('stroke', color).attr('stroke-width', 1)

      svg.append('text').attr('x', px).attr('y', py + size * 0.01)
        .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
        .attr('fill', 'white').attr('font-size', size * 0.02).attr('font-weight', 'bold')
        .text(name.slice(0, 2))

      // Retrograde indicator
      if ((data as Record<string, unknown>)?.retrograde) {
        svg.append('text').attr('x', px + size * 0.025).attr('y', py - size * 0.02)
          .attr('fill', '#CC2936').attr('font-size', size * 0.018).text('℞')
      }
    })

    // ASC line
    const asc = (chart as Record<string, Record<string, Record<string, number>>>).tropical?.ascendant
    if (asc?.longitude !== undefined) {
      const angle = (asc.longitude / 360) * 2 * Math.PI - Math.PI / 2
      svg.append('line')
        .attr('x1', cx).attr('y1', cy)
        .attr('x2', cx + signBandInner * Math.cos(angle)).attr('y2', cy + signBandInner * Math.sin(angle))
        .attr('stroke', 'var(--gold)').attr('stroke-width', 1.5).attr('stroke-dasharray', '4,2')
    }

    // Center label
    svg.append('text').attr('x', cx).attr('y', cy - 8)
      .attr('text-anchor', 'middle').attr('fill', 'var(--gold)').attr('font-size', size * 0.028)
      .attr('font-family', 'Cinzel, serif').text('NATAL')
    svg.append('text').attr('x', cx).attr('y', cy + 8)
      .attr('text-anchor', 'middle').attr('fill', 'var(--text-stardust)').attr('font-size', size * 0.022)
      .attr('font-family', 'Inter, sans-serif').text('CHART')

  }, [chart, size])

  if (!chart) return <div style={{ width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: '0.9rem' }}>Chart not yet computed</div>

  return <svg ref={svgRef} width={size} height={size} style={{ borderRadius: '50%' }} />
}