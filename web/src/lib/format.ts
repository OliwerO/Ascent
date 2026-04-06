export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export function formatActivityType(type: string | null | undefined): string {
  if (!type) return '--'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
