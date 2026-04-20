import { useEffect, useRef } from 'react'

interface Props {
  value: number | null
  max: number
  label: string
  color: string
  size?: 'hero' | 'compact'
  unit?: string
  hideValue?: boolean
  onClick?: () => void
}

export function RadialGauge({ value, max, label, color, size = 'hero', unit, hideValue, onClick }: Props) {
  const isHero = size === 'hero'
  const diameter = isHero ? 88 : 52
  const strokeWidth = isHero ? 5 : 4
  const radius = (diameter - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const pct = value != null ? Math.min(1, Math.max(0, value / max)) : 0
  const offset = circumference * (1 - pct)

  const circleRef = useRef<SVGCircleElement>(null)

  useEffect(() => {
    const el = circleRef.current
    if (!el) return
    // Start from full offset, animate to target
    el.style.strokeDashoffset = `${circumference}`
    // Force reflow
    el.getBoundingClientRect()
    el.style.transition = 'stroke-dashoffset 800ms ease-out'
    el.style.strokeDashoffset = `${offset}`
  }, [circumference, offset])

  const filterId = `glow-${label.replace(/\s+/g, '-')}`

  return (
    <div
      className={`flex flex-col items-center gap-1 ${onClick ? 'cursor-pointer active:scale-[0.96] transition-transform' : ''}`}
      onClick={onClick}
    >
      <div className="relative" style={{ width: diameter, height: diameter }}>
        <svg
          width={diameter}
          height={diameter}
          viewBox={`0 0 ${diameter} ${diameter}`}
          className="block"
        >
          <defs>
            <filter id={filterId} x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor={color} floodOpacity="0.4" />
            </filter>
          </defs>
          {/* Track */}
          <circle
            cx={diameter / 2}
            cy={diameter / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            ref={circleRef}
            cx={diameter / 2}
            cy={diameter / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference}
            transform={`rotate(-90 ${diameter / 2} ${diameter / 2})`}
            filter={value != null ? `url(#${filterId})` : undefined}
          />
        </svg>
        {/* Center value */}
        {!hideValue && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span
              className="font-data"
              style={{
                fontSize: isHero ? 20 : 14,
                fontWeight: 700,
                letterSpacing: '-0.02em',
                lineHeight: 1,
                color: value != null ? color : 'var(--color-text-dim)',
              }}
            >
              {value != null ? Math.round(value) : '—'}
              {unit && value != null && (
                <span style={{ fontSize: isHero ? 11 : 9, fontWeight: 500, opacity: 0.6 }}>{unit}</span>
              )}
            </span>
          </div>
        )}
      </div>
      <span className="text-[10px] text-text-muted font-medium tracking-wide">{label}</span>
    </div>
  )
}
