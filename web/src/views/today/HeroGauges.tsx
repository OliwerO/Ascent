import { RadialGauge } from '../../components/RadialGauge'

interface Props {
  hrvVal: number | null
  hrvWeeklyAvg: number | null
  cardState: 'green' | 'amber' | 'red'
  sleepHours: number | null
  gymVolumeKg: number
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

function fmtKg(kg: number): string {
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)}k`
  return `${Math.round(kg)}`
}

function fmtElev(m: number): string {
  if (m >= 1000) return `${(m / 1000).toFixed(1)}k`
  return `${Math.round(m)}`
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
      <div className="glass-card flex flex-col items-center justify-center gap-1.5 py-2">
        <div className="flex items-center gap-1.5">
          <RadialGauge
            value={gymVolumeKg > 0 ? gymVolumeKg : null}
            max={20000}
            label=""
            color="#a78bfa"
            size="compact"
            hideValue
          />
          <RadialGauge
            value={elevationM > 0 ? elevationM : null}
            max={2000}
            label=""
            color="#38bdf8"
            size="compact"
            hideValue
          />
        </div>
        <div className="flex items-center gap-2 text-[9px] text-text-muted">
          <span><span className="text-accent-purple font-semibold">{fmtKg(gymVolumeKg)}</span> kg</span>
          <span><span className="text-mountain font-semibold">{fmtElev(elevationM)}</span> m</span>
        </div>
        <span className="text-[10px] text-text-muted font-medium -mt-0.5">7d load</span>
      </div>
    </div>
  )
}
