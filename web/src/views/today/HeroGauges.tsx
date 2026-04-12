import { RadialGauge } from '../../components/RadialGauge'

interface Props {
  /** HRV-based recovery: 0-100 mapped from coaching state */
  recoveryScore: number | null
  recoveryState: 'green' | 'amber' | 'red'
  /** Weekly training load as hours */
  strainHours: number
  /** Target weekly training hours (gym + mountain + cycling) */
  strainTarget: number
  /** Last night sleep in hours */
  sleepHours: number | null
}

const recoveryColors = {
  green: '#34d399',
  amber: '#fbbf24',
  red: '#f87171',
}

export function HeroGauges({ recoveryScore, recoveryState, strainHours, strainTarget, sleepHours }: Props) {
  const strainPct = strainTarget > 0 ? (strainHours / strainTarget) * 100 : 0

  return (
    <div className="grid grid-cols-3 gap-2">
      <div className="glass-card flex items-center justify-center py-3">
        <RadialGauge
          value={recoveryScore}
          max={100}
          label="Recovery"
          color={recoveryColors[recoveryState]}
          size="hero"
        />
      </div>
      <div className="glass-card flex items-center justify-center py-3">
        <RadialGauge
          value={Math.round(strainPct)}
          max={100}
          label="Strain"
          color="#fb923c"
          size="hero"
          unit="%"
        />
      </div>
      <div className="glass-card flex items-center justify-center py-3">
        <RadialGauge
          value={sleepHours}
          max={8}
          label="Sleep"
          color="#818cf8"
          size="hero"
          unit="h"
        />
      </div>
    </div>
  )
}
