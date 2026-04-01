interface Props {
  value: number | string | null | undefined
  thresholds?: { green: number; yellow: number }
  label: string
  unit?: string
  status?: 'green' | 'yellow' | 'red' | null
}

const colors = {
  green: 'bg-accent-green/20 text-accent-green border-accent-green/30',
  yellow: 'bg-accent-yellow/20 text-accent-yellow border-accent-yellow/30',
  red: 'bg-accent-red/20 text-accent-red border-accent-red/30',
}

export function StatusBadge({ value, thresholds, label, unit, status: explicitStatus }: Props) {
  let status: 'green' | 'yellow' | 'red' = 'green'
  if (explicitStatus) {
    status = explicitStatus
  } else if (thresholds && typeof value === 'number') {
    if (value >= thresholds.green) status = 'green'
    else if (value >= thresholds.yellow) status = 'yellow'
    else status = 'red'
  }

  return (
    <div className={`rounded-lg border px-3 py-2 ${colors[status]}`}>
      <div className="text-xs opacity-70">{label}</div>
      <div className="text-lg font-semibold">
        {value ?? '—'}{unit && <span className="text-xs ml-1 opacity-70">{unit}</span>}
      </div>
    </div>
  )
}
