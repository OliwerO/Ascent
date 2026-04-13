import { RadialGauge } from '../../components/RadialGauge'

interface Props {
  /** Last night HRV in ms */
  hrvVal: number | null
  /** HRV weekly average for context */
  hrvWeeklyAvg: number | null
  /** Coaching state drives the HRV gauge color */
  cardState: 'green' | 'amber' | 'red'
  /** Last night sleep in hours */
  sleepHours: number | null
  /** Garmin body battery high (0-100) */
  bodyBattery: number | null
}

const stateColors = {
  green: '#34d399',
  amber: '#fbbf24',
  red: '#f87171',
}

function bbColor(bb: number | null): string {
  if (bb == null) return '#6a6a82'
  if (bb >= 60) return '#34d399'
  if (bb >= 30) return '#fbbf24'
  return '#f87171'
}

function sleepColor(h: number | null): string {
  if (h == null) return '#6a6a82'
  if (h >= 7) return '#34d399'
  if (h >= 6) return '#fbbf24'
  return '#f87171'
}

export function HeroGauges({ hrvVal, hrvWeeklyAvg, cardState, sleepHours, bodyBattery }: Props) {
  // HRV gauge: show actual value, max based on weekly avg * 1.3 for visual scale
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
        <RadialGauge
          value={bodyBattery}
          max={100}
          label="Battery"
          color={bbColor(bodyBattery)}
          size="hero"
        />
      </div>
    </div>
  )
}
