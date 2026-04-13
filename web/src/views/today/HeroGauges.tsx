import { RadialGauge } from '../../components/RadialGauge'
import { useEffect, useRef } from 'react'

interface Props {
  /** Last night HRV in ms */
  hrvVal: number | null
  /** HRV weekly average for context */
  hrvWeeklyAvg: number | null
  /** Coaching state drives the HRV gauge color */
  cardState: 'green' | 'amber' | 'red'
  /** Last night sleep in hours */
  sleepHours: number | null
  /** Gym volume this week in kg */
  gymVolumeKg: number
  /** Mountain elevation this week in meters */
  elevationM: number
}

const stateColors = {
  green: '#34d399',
  amber: '#fbbf24',
  red: '#f87171',
}

function sleepColor(h: number | null): string {
  if (h == null) return '#6a6a82'
  if (h >= 7) return '#34d399'
  if (h >= 6) return '#fbbf24'
  return '#f87171'
}

export function HeroGauges({ hrvVal, hrvWeeklyAvg, cardState, sleepHours, gymVolumeKg, elevationM }: Props) {
  const hrvMax = hrvWeeklyAvg != null ? Math.round(hrvWeeklyAvg * 1.3) : 150

  return (
    <div className="grid grid-cols-3 gap-2">
      <div className="glass-card flex items-center justify-center py-3">
        <RadialGauge
          value={hrvVal}
          max={hrvMax}
          label="HRV"
          color={stateColors[cardState]}
          size="hero"
          unit="ms"
        />
      </div>
      <div className="glass-card flex items-center justify-center py-3">
        <RadialGauge
          value={sleepHours}
          max={9}
          label="Sleep"
          color={sleepColor(sleepHours)}
          size="hero"
          unit="h"
        />
      </div>
      <div className="glass-card flex items-center justify-center py-3">
        <LoadGauge gymKg={gymVolumeKg} elevM={elevationM} />
      </div>
    </div>
  )
}

/** Dual-arc gauge: purple for gym volume (kg), cyan for mountain elevation (m) */
function LoadGauge({ gymKg, elevM }: { gymKg: number; elevM: number }) {
  const diameter = 88
  const strokeWidth = 5
  const radius = (diameter - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  // Normalize: gym targets ~20,000kg/week, mountain ~2000m/week
  const gymPct = Math.min(1, gymKg / 20000)
  const elevPct = Math.min(1, elevM / 2000)

  // Two arcs proportional to their % of target — each can fill up to half the ring
  const gymArc = circumference * gymPct * 0.5
  const elevArc = circumference * elevPct * 0.5

  const gymRef = useRef<SVGCircleElement>(null)
  const elevRef = useRef<SVGCircleElement>(null)

  useEffect(() => {
    const animate = (el: SVGCircleElement | null, target: number) => {
      if (!el) return
      el.style.strokeDashoffset = `${circumference}`
      el.getBoundingClientRect()
      el.style.transition = 'stroke-dashoffset 800ms ease-out'
      el.style.strokeDashoffset = `${circumference - target}`
    }
    animate(gymRef.current, gymArc)
    animate(elevRef.current, gymArc + elevArc)
  }, [circumference, gymArc, elevArc])

  // Display text: show the more prominent value, or both abbreviated
  const hasGym = gymKg > 0
  const hasElev = elevM > 0
  let displayText: string
  let displaySize: number
  if (hasGym && hasElev) {
    // Show both abbreviated
    displayText = `${(gymKg / 1000).toFixed(0)}k`
    displaySize = 16
  } else if (hasGym) {
    displayText = `${(gymKg / 1000).toFixed(1)}k`
    displaySize = 18
  } else if (hasElev) {
    displayText = `${elevM >= 1000 ? (elevM / 1000).toFixed(1) + 'k' : Math.round(elevM)}`
    displaySize = 18
  } else {
    displayText = '—'
    displaySize = 20
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: diameter, height: diameter }}>
        <svg width={diameter} height={diameter} viewBox={`0 0 ${diameter} ${diameter}`}>
          <defs>
            <filter id="glow-load-gym" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#a78bfa" floodOpacity="0.4" />
            </filter>
            <filter id="glow-load-elev" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#38bdf8" floodOpacity="0.4" />
            </filter>
          </defs>
          {/* Track */}
          <circle cx={diameter / 2} cy={diameter / 2} r={radius} fill="none"
            stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth} />
          {/* Elevation arc (bottom layer — draws from where gym ends) */}
          {hasElev && (
            <circle
              ref={elevRef}
              cx={diameter / 2} cy={diameter / 2} r={radius} fill="none"
              stroke="#38bdf8" strokeWidth={strokeWidth} strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={circumference}
              transform={`rotate(-90 ${diameter / 2} ${diameter / 2})`}
              filter="url(#glow-load-elev)"
            />
          )}
          {/* Gym arc (top layer — draws from start) */}
          {hasGym && (
            <circle
              ref={gymRef}
              cx={diameter / 2} cy={diameter / 2} r={radius} fill="none"
              stroke="#a78bfa" strokeWidth={strokeWidth} strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={circumference}
              transform={`rotate(-90 ${diameter / 2} ${diameter / 2})`}
              filter="url(#glow-load-gym)"
            />
          )}
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-data" style={{ fontSize: displaySize, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1, color: '#f0f0f5' }}>
            {displayText}
          </span>
          {hasGym && hasElev && (
            <span className="text-[9px] text-text-muted mt-0.5">{Math.round(elevM)}m</span>
          )}
        </div>
      </div>
      {/* Legend dots */}
      <div className="flex items-center gap-2">
        {hasGym && <span className="flex items-center gap-0.5 text-[9px] text-text-muted"><span className="w-1.5 h-1.5 rounded-full bg-accent-purple inline-block" />kg</span>}
        {hasElev && <span className="flex items-center gap-0.5 text-[9px] text-text-muted"><span className="w-1.5 h-1.5 rounded-full bg-mountain inline-block" />m</span>}
        {!hasGym && !hasElev && <span className="text-[10px] text-text-muted">Load</span>}
      </div>
    </div>
  )
}
