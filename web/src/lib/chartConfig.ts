/** Shared chart styling — glass tooltip, axis styles, grid color */

export const glassTooltipStyle: React.CSSProperties = {
  backgroundColor: 'rgba(15, 16, 22, 0.85)',
  backdropFilter: 'blur(16px)',
  WebkitBackdropFilter: 'blur(16px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: '12px',
  color: '#f0f0f5',
  fontSize: '12px',
  padding: '8px 12px',
}

export const axisTickStyle = { fill: '#6a6a82', fontSize: 11 }
export const axisLineStyle = { stroke: 'rgba(255,255,255,0.04)' }
export const gridStroke = 'rgba(255,255,255,0.04)'
