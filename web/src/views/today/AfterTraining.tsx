import { RPEPrompt } from '../../components/RPEPrompt'
import { ExerciseFeedbackPrompt } from '../../components/ExerciseFeedbackPrompt'
import { WeeklyReflection } from '../../components/WeeklyReflection'
import type { Activity, PlannedExercise } from '../../lib/types'

interface Props {
  lastActivity: Activity | null
  exercises: PlannedExercise[] | null
  isSunday: boolean
}

export function AfterTraining({ lastActivity, exercises, isSunday }: Props) {
  const isStrength = lastActivity?.activity_type === 'strength_training'

  if (!isStrength && !isSunday) return null

  return (
    <div className="space-y-3">
      <div className="section-label mt-2">After training</div>

      {isStrength && lastActivity && <RPEPrompt activity={lastActivity} />}

      {isStrength && lastActivity && exercises && (
        <ExerciseFeedbackPrompt exercises={exercises} sessionDate={lastActivity.date} />
      )}

      {isSunday && <WeeklyReflection />}
    </div>
  )
}
