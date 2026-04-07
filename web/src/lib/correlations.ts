// Lightweight correlation helpers for TrendsView insights.
// All functions tolerate sparse data and return null when insufficient.

export interface DayPoint {
  date: string // YYYY-MM-DD
  value: number | null
}

function pearson(xs: number[], ys: number[]): number | null {
  const n = xs.length
  if (n < 5) return null
  const mx = xs.reduce((a, b) => a + b, 0) / n
  const my = ys.reduce((a, b) => a + b, 0) / n
  let num = 0, dx = 0, dy = 0
  for (let i = 0; i < n; i++) {
    const a = xs[i] - mx
    const b = ys[i] - my
    num += a * b
    dx += a * a
    dy += b * b
  }
  if (dx === 0 || dy === 0) return null
  return num / Math.sqrt(dx * dy)
}

export function correlateLagged(
  cause: DayPoint[],
  effect: DayPoint[],
  lagDays: number,
): { r: number; n: number } | null {
  const effectMap = new Map<string, number>()
  for (const e of effect) if (e.value != null) effectMap.set(e.date, e.value)
  const xs: number[] = []
  const ys: number[] = []
  for (const c of cause) {
    if (c.value == null) continue
    const d = new Date(c.date)
    d.setDate(d.getDate() + lagDays)
    const key = d.toISOString().slice(0, 10)
    const ev = effectMap.get(key)
    if (ev == null) continue
    xs.push(c.value)
    ys.push(ev)
  }
  const r = pearson(xs, ys)
  if (r == null) return null
  return { r, n: xs.length }
}

export function describeR(r: number): { strength: string; direction: 'positive' | 'negative' | 'flat' } {
  const a = Math.abs(r)
  const direction = r > 0.05 ? 'positive' : r < -0.05 ? 'negative' : 'flat'
  if (a >= 0.5) return { strength: 'strong', direction }
  if (a >= 0.3) return { strength: 'moderate', direction }
  if (a >= 0.15) return { strength: 'weak', direction }
  return { strength: 'no clear', direction: 'flat' }
}

// Compare metric values on days following a "high load" day vs baseline.
// Returns difference (high-load mean − baseline mean) and sample sizes.
export function loadImpact(
  loadByDate: Map<string, number>,
  metric: DayPoint[],
  loadThreshold: number,
  lagDays: number,
): { delta: number; nHigh: number; nBase: number } | null {
  const high: number[] = []
  const base: number[] = []
  for (const m of metric) {
    if (m.value == null) continue
    const d = new Date(m.date)
    d.setDate(d.getDate() - lagDays)
    const key = d.toISOString().slice(0, 10)
    const load = loadByDate.get(key) ?? 0
    if (load >= loadThreshold) high.push(m.value)
    else base.push(m.value)
  }
  if (high.length < 3 || base.length < 3) return null
  const mean = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length
  return { delta: mean(high) - mean(base), nHigh: high.length, nBase: base.length }
}
