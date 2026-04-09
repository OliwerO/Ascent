// Shared color/threshold helpers for status-based UI coloring

export function metricColor(value: number | null, green: number, yellow: number): string {
  if (value == null) return 'text-text-muted'
  if (value >= green) return 'text-accent-green'
  if (value >= yellow) return 'text-accent-yellow'
  return 'text-accent-red'
}

export function hrvStatusInfo(status: string | null | undefined): { color: string; label: string } {
  if (!status) return { color: 'text-accent-yellow', label: 'Unknown' }
  const s = status.toUpperCase()
  if (s === 'BALANCED') return { color: 'text-accent-green', label: 'Balanced' }
  if (s === 'UNBALANCED') return { color: 'text-accent-yellow', label: 'Unbalanced' }
  return { color: 'text-accent-red', label: 'Low' }
}

export function loadChangeColor(pct: number): string {
  if (Math.abs(pct) <= 15) return 'text-accent-green'
  if (Math.abs(pct) <= 25) return 'text-accent-yellow'
  return 'text-accent-red'
}

export function sleepBarColor(hours: number): string {
  if (hours >= 7) return '#4ade80'
  if (hours >= 6) return '#fbbf24'
  return '#f87171'
}
