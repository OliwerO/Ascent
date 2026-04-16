import type { PlannedExercise, TrainingSet } from '../lib/types'

function normalizeExName(name: string): string {
  return name.toLowerCase().replace(/[_\s-]+/g, ' ').replace(/&/g, 'and').trim()
}

/** Try exact match first, then fuzzy (contains) for Garmin name variations */
function matchSets(sets: TrainingSet[], exerciseName: string): TrainingSet[] {
  const norm = normalizeExName(exerciseName)
  // Exact match
  const exact = sets.filter(
    (s) => s.exercises?.name != null && normalizeExName(s.exercises.name) === norm && s.set_type === 'working'
  )
  if (exact.length > 0) return exact
  // Fuzzy: check if either name contains the other (handles "Turkish Get-Up" vs "Turkish Getup" etc.)
  const words = norm.split(' ').filter((w) => w.length > 2)
  return sets.filter((s) => {
    if (s.exercises?.name == null || s.set_type !== 'working') return false
    const sNorm = normalizeExName(s.exercises.name)
    return words.every((w) => sNorm.includes(w)) || sNorm.split(' ').filter((w) => w.length > 2).every((w) => norm.includes(w))
  })
}

interface ActualDelta {
  tracked: boolean
  weightDelta: number | null
  repsShort: boolean
  actualWeight: number | null
  setsMismatch: boolean  // different number of sets
  setsActual: number
}

function computeDelta(sets: TrainingSet[], planned: PlannedExercise): ActualDelta {
  if (sets.length === 0) return { tracked: false, weightDelta: null, repsShort: false, actualWeight: null, setsMismatch: false, setsActual: 0 }

  const weights = [...new Set(sets.map((s) => s.weight_kg).filter((w): w is number => w != null))]
  const reps = sets.map((s) => s.reps).filter((r): r is number => r != null)
  const actualWeight = weights.length > 0 ? Math.max(...weights) : null
  const weightDelta = actualWeight != null && planned.weight_kg != null ? actualWeight - planned.weight_kg : null
  const plannedReps = Number(planned.reps) || 0
  const repsShort = plannedReps > 0 && reps.length > 0 && reps.some((r) => r < plannedReps)
  const setsMismatch = sets.length !== planned.sets

  return { tracked: true, weightDelta, repsShort, actualWeight, setsMismatch, setsActual: sets.length }
}

interface Props {
  exercises: PlannedExercise[]
  actualSets: TrainingSet[]
}

export function WorkoutComparison({ exercises, actualSets }: Props) {
  if (exercises.length === 0) return null

  const hasAnyActual = actualSets.length > 0

  const rows = exercises.map((ex) => {
    const matched = matchSets(actualSets, ex.name)
    const delta = computeDelta(matched, ex)
    return { name: ex.name, planned: ex, delta }
  })

  const tracked = rows.filter((r) => r.delta.tracked).length

  return (
    <div className="space-y-2">
      {hasAnyActual && (
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Plan vs Actual</span>
          <span className={`text-[11px] font-semibold ${
            tracked === rows.length ? 'text-accent-green' : tracked >= rows.length * 0.7 ? 'text-accent-yellow' : 'text-accent-red'
          }`}>
            {tracked}/{rows.length} tracked
          </span>
        </div>
      )}
      <div className="space-y-1">
        {rows.map((row) => {
          const { delta } = row
          const targetStr = row.planned.weight_kg
            ? `${row.planned.sets}\u00D7${row.planned.reps} @ ${row.planned.weight_kg}kg`
            : `${row.planned.sets}\u00D7${row.planned.reps}`

          return (
            <div key={row.name} className="flex items-center justify-between py-1 border-b border-border-subtle/50 last:border-0">
              <div className="text-[12px] text-text-primary truncate pr-2 flex-1 min-w-0">{row.name}</div>
              <div className="text-[12px] text-text-secondary font-mono whitespace-nowrap pr-3">{targetStr}</div>
              <div className="shrink-0 min-w-[70px] text-right">
                {!delta.tracked ? (
                  <span className="text-[11px] text-text-dim">&mdash;</span>
                ) : delta.weightDelta === 0 && !delta.repsShort && !delta.setsMismatch ? (
                  <span className="text-[11px] text-accent-green font-semibold">&#10003;</span>
                ) : (
                  <div className="flex items-center justify-end gap-1.5">
                    {delta.weightDelta != null && delta.weightDelta !== 0 && (
                      <span className={`text-[11px] font-semibold ${delta.weightDelta > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {delta.weightDelta > 0 ? '+' : ''}{delta.weightDelta}kg
                      </span>
                    )}
                    {delta.setsMismatch && (
                      <span className="text-[10px] text-accent-yellow">{delta.setsActual}/{row.planned.sets}s</span>
                    )}
                    {delta.repsShort && (
                      <span className="text-[10px] text-accent-yellow">reps&#x2193;</span>
                    )}
                    {delta.weightDelta === 0 && !delta.setsMismatch && delta.repsShort && (
                      <span className="text-[10px] text-accent-yellow">reps&#x2193;</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
