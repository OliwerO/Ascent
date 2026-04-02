export interface PlannedWorkout {
  id: number
  training_block: string
  week_number: number
  session_name: string
  session_type: string
  scheduled_date: string
  scheduled_time: string | null
  estimated_duration_minutes: number | null
  workout_definition: WorkoutDefinition
  status: 'planned' | 'adjusted' | 'completed' | 'skipped'
  actual_garmin_activity_id: string | null
  compliance_score: number | null
  adjustment_reason: string | null
}

export interface WorkoutDefinition {
  session_label: string
  session_name: string
  estimated_duration_minutes: number
  rpe_range: [number, number]
  warmup: WarmupExercise[]
  exercises: PlannedExercise[]
}

export interface WarmupExercise {
  name: string
  reps: number | null
  duration_s: number | null
}

export interface PlannedExercise {
  name: string
  sets: number
  reps: number | string
  weight_kg: number | null
  rest_s: number
  equipment: string
  note: string | null
  duration_s?: number
  distance_m?: number
}
