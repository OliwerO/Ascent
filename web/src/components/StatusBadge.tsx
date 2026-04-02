interface Props {
  value: number | string | null | undefined
  thresholds?: { green: number; yellow: number }
  label: string
  unit?: string
  status?: 'green' | 'yellow' | 'red' | null
}

const styles = {
  green: {
    bg: 'bg-glow-green border-accent-green/20',
    value: 'text-accent-green',
    dot: 'bg-accent-green',
  },
  yellow: {
    bg: 'bg-glow-yellow border-accent-yellow/20',
    value: 'text-accent-yellow',
    dot: 'bg-accent-yellow',
  },
  red: {
    bg: 'bg-glow-red border-accent-red/20',
    value: 'text-accent-red',
    dot: 'bg-accent-red',
  },
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

  const s = styles[status]

  return (
    <div className={`rounded-2xl border px-4 py-3 ${s.bg}`}>
      <div className="flex items-center gap-1.5 mb-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
        <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">{label}</span>
      </div>
      <div className={`data-value font-data ${s.value}`}>
        {value ?? '—'}
        {unit && <span className="text-[14px] ml-1 font-normal opacity-60">{unit}</span>}
      </div>
    </div>
  )
}
