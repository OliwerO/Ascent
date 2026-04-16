import type { PlannedExercise, TrainingSet } from '../lib/types'

function normalizeExName(name: string): string {
  return name.toLowerCase().replace(/[_\s-]+/g, ' ').replace(/&/g, 'and').trim()
}

function matchSets(sets: TrainingSet[], exerciseName: string): TrainingSet[] {
  const norm = normalizeExName(exerciseName)
  return sets.filter(
    (s) => s.exercises?.name != null && normalizeExName(s.exercises.name) === norm && s.set_type === 'working'
  )
}

interface ActualResult {
  text: string
  hit: boolean
  weightDelta: number | null  // actual - planned (kg)
  repsShort: boolean | null   // true if any set missed target reps
}

function formatActual(sets: TrainingSet[], planned?: PlannedExercise): ActualResult {
  if (sets.length === 0) return { text: '\u2014', hit: false, weightDelta: null, repsShort: null }
  const weights = [...new Set(sets.map((s) => s.weight_kg).filter(Boolean))]
  const reps = sets.map((s) => s.reps).filter(Boolean)

  // Compute deltas vs planned
  const actualWeight = weights.length === 1 ? weights[0] : (weights.length > 0 ? Math.max(...(weights as number[])) : null)
  const weightDelta = actualWeight != null && planned?.weight_kg != null ? actualWeight - planned.weight_kg : null
  const plannedRepsNum = planned?.reps != null ? Number(planned.reps) : null
  const repsShort = plannedRepsNum != null && reps.length > 0 ? reps.some((r) => r != null && r < plannedRepsNum) : null

  if (weights.length === 1) {
    return { text: `${sets.length}\u00D7${reps.join('/')} @ ${weights[0]}kg`, hit: true, weightDelta, repsShort }
  }
  if (weights.length > 1) {
    return { text: sets.map((s) => `${s.reps}@${s.weight_kg}`).join(', '), hit: true, weightDelta, repsShort }
  }
  return { text: `${sets.length}\u00D7${reps.join('/')}`, hit: true, weightDelta, repsShort }
}

interface Props {
  exercises: PlannedExercise[]
  actualSets: TrainingSet[]
}

export function WorkoutComparison({ exercises, actualSets }: Props) {
  if (exercises.length === 0) return null

  const hasAnyActual = actualSets.length > 0
  let hitsCount = 0
  let totalExercises = 0

  const rows = exercises.map((ex) => {
    const matched = matchSets(actualSets, ex.name)
    const targetStr = ex.weight_kg
      ? `${ex.sets}\u00D7${ex.reps} @ ${ex.weight_kg}kg`
      : `${ex.sets}\u00D7${ex.reps}`
    const actual = formatActual(matched, ex)

    totalExercises++
    if (actual.hit) hitsCount++

    return { name: ex.name, note: ex.note, targetStr, actual }
  })

  return (
    <div className="space-y-2">
      {hasAnyActual && (
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Plan vs Actual</span>
          <span className={`text-[11px] font-semibold ${
            hitsCount === totalExercises ? 'text-accent-green' : hitsCount >= totalExercises * 0.7 ? 'text-accent-yellow' : 'text-accent-red'
          }`}>
            {hitsCount}/{totalExercises} tracked
          </span>
        </div>
      )}
      <div className="overflow-x-auto -mx-3 px-3">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="text-text-muted border-b border-border-subtle">
              <th className="text-left py-1 font-semibold text-[10px] uppercase tracking-wider">Exercise</th>
              <th className="text-left py-1 font-semibold text-[10px] uppercase tracking-wider">Target</th>
              {hasAnyActual && <th className="text-left py-1 font-semibold text-[10px] uppercase tracking-wider">Actual</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-b border-border-subtle/50 last:border-0">
                <td className="py-1.5 text-text-primary pr-2">
                  <span className="truncate block max-w-[140px]">{row.name}</span>
                </td>
                <td className="py-1.5 text-text-secondary font-mono whitespace-nowrap">{row.targetStr}</td>
                {hasAnyActual && (
                  <td className="py-1.5 font-mono whitespace-nowrap">
                    <span className={`font-semibold ${row.actual.hit ? 'text-accent-green' : 'text-text-dim'}`}>
                      {row.actual.text}
                    </span>
                    {row.actual.hit && (row.actual.weightDelta !== null || row.actual.repsShort !== null) && (
                      <div className="flex items-center gap-1.5 mt-0.5">
                        {row.actual.weightDelta !== null && row.actual.weightDelta !== 0 && (
                          <span className={`text-[10px] font-semibold ${row.actual.weightDelta > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                            {row.actual.weightDelta > 0 ? '+' : ''}{row.actual.weightDelta}kg
                          </span>
                        )}
                        {row.actual.repsShort === true && (
                          <span className="text-[10px] text-accent-yellow">reps short</span>
                        )}
                        {row.actual.weightDelta === 0 && row.actual.repsShort === false && (
                          <span className="text-[10px] text-accent-green">on target</span>
                        )}
                      </div>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
