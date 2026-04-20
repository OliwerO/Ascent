// ---------------------------------------------------------------------------
// Supabase row types — match the actual columns fetched by hooks
// ---------------------------------------------------------------------------

// --- Daily summary (view joining daily_metrics + sleep + hrv + body_composition)
export interface DailySummary {
  date: string
  total_steps: number | null
  resting_hr: number | null
  avg_stress_level: number | null
  body_battery_highest: number | null
  body_battery_lowest: number | null
  training_readiness_score: number | null
  vo2max: number | null
  sleep_score: number | null
  total_sleep_seconds: number | null
  deep_sleep_seconds: number | null
  rem_sleep_seconds: number | null
  hrv_avg: number | null
  hrv_weekly_avg: number | null
  hrv_status: string | null
  weight_kg: number | null
  body_fat_pct: number | null
  muscle_mass_grams: number | null
}

// --- HRV
export interface HRVRow {
  date: string
  last_night_avg: number | null
  weekly_avg: number | null
  status: string | null
  baseline_balanced_low: number | null
  baseline_balanced_upper: number | null
}

// --- Sleep
export interface SleepRow {
  date: string
  total_sleep_seconds: number | null
  deep_sleep_seconds: number | null
  rem_sleep_seconds: number | null
  light_sleep_seconds: number | null
  overall_score: number | null
}

// --- Activities
export interface Activity {
  date: string
  activity_type: string
  activity_name: string | null
  duration_seconds: number | null
  calories: number | null
  elevation_gain: number | null
  elevation_loss: number | null
  distance_meters: number | null
  avg_hr: number | null
  max_hr: number | null
  avg_speed: number | null
  max_speed: number | null
  start_time: string | null
  garmin_activity_id: string | null
  training_effect_aerobic: number | null
  training_effect_anaerobic: number | null
  hr_zones: HRZone[] | null
  raw_json: Record<string, unknown> | null
}

export interface HRZone {
  zone: number | string
  seconds: number
  [key: string]: unknown
}

// --- Performance scores (Garmin endurance/hill)
export interface PerformanceScore {
  date: string
  endurance_score: number | null
  hill_score: number | null
  fitness_age: number | null
}

// --- Daily metrics
export interface DailyMetrics {
  date: string
  body_battery_highest: number | null
  body_battery_lowest: number | null
  training_readiness_score: number | null
  resting_hr: number | null
  avg_stress_level: number | null
  vo2max: number | null
  vigorous_intensity_minutes: number | null
  moderate_intensity_minutes: number | null
}

// --- Body composition
export interface BodyComposition {
  date: string
  weight_kg: number | null
  body_fat_pct: number | null
  muscle_mass_grams: number | null
  body_water_pct: number | null
  lean_body_mass_grams: number | null
  bmi: number | null
  visceral_fat_rating: number | null
  metabolic_age: number | null
  bone_mass_grams: number | null
  source: string | null
  raw_json: Record<string, unknown> | null
}

// --- Training sessions
export interface TrainingSession {
  id: number
  date: string
  garmin_activity_id: string | null
  name: string | null
  program: string | null
  duration_minutes: number | null
  pre_hrv: number | null
  pre_body_battery: number | null
  pre_resting_hr: number | null
  sleep_score_prev_night: number | null
  total_volume_kg: number | null
  total_sets: number | null
  notes: string | null
  rating: number | null
  srpe: number | null
  srpe_load: number | null
  created_at: string
}

// --- Training sets (with joined exercise)
export interface TrainingSet {
  id: number
  session_id: number
  exercise_id: number
  set_number: number
  set_type: string
  weight_kg: number | null
  reps: number | null
  rpe: number | null
  tempo: string | null
  rest_seconds: number | null
  volume_kg: number | null
  estimated_1rm: number | null
  notes: string | null
  exercises: { name: string; category: string; muscle_groups: string[] | null } | null
}

// --- Training status
export interface TrainingStatus {
  date: string
  training_status: string | null
  training_load_7d: number | null
  training_load_28d: number | null
  raw_json: Record<string, unknown> | null
}

// --- Goals
export interface Goal {
  id: number
  category: string
  metric: string
  target_value: number
  current_value: number | null
  start_date: string | null
  target_date: string | null
  status: string
  notes: string | null
}

// --- Coaching log
export interface CoachingLogEntry {
  id: number
  date: string
  type: string
  channel: string | null
  message: string
  data_context: Record<string, unknown> | null
  acknowledged: boolean
  created_at: string
  decision_type: string | null
  rule: string | null
  kb_refs: string[] | null
  inputs: Record<string, unknown> | null
}

// --- Subjective wellness
export interface SubjectiveWellness {
  date: string
  sleep_quality: number | null
  energy: number | null
  muscle_soreness: number | null
  motivation: number | null
  stress: number | null
  composite_score: number | null
  notes: string | null
}

// ---------------------------------------------------------------------------
// Planned workouts & definitions
// ---------------------------------------------------------------------------

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
  status: 'planned' | 'pushed' | 'adjusted' | 'rescheduled' | 'completed' | 'skipped'
  actual_garmin_activity_id: string | null
  compliance_score: number | null
  adjustment_reason: string | null
  updated_at: string | null
}

export interface WorkoutDefinition {
  session_label: string
  session_name: string
  estimated_duration_minutes: number
  rpe_range: [number, number]
  warmup: WarmupExercise[]
  exercises: PlannedExercise[]
  venue?: 'gym' | 'home'
  original_gym_definition?: WorkoutDefinition
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

// --- Exercise progression (engine decisions)
export interface ExerciseProgression {
  exercise_name: string
  date: string
  planned_sets: number | null
  planned_reps: number | null
  planned_weight_kg: number | null
  planned_rpe: number | null
  actual_sets: number | null
  actual_reps_per_set: number[] | null
  actual_weight_kg: number | null
  actual_rpe: number | null
  progression_applied: string
  progression_amount: number | null
}

// --- Activity details (splits, weather enrichment)
export interface ActivityDetails {
  garmin_activity_id: string
  hr_zones: HRZone[] | null
  splits: ActivitySplit[] | null
  weather: ActivityWeather | null
}

export interface ActivitySplit {
  distance?: number
  duration?: number
  elevationGain?: number
  elevationLoss?: number
  averageHR?: number
  maxHR?: number
  averageSpeed?: number
  startElevation?: number
  endElevation?: number
  [key: string]: unknown
}

export interface ActivityWeather {
  temp?: number
  apparentTemp?: number
  relativeHumidity?: number
  windSpeed?: number
  windDirection?: number
  weatherType?: string
  [key: string]: unknown
}

export interface ExerciseFeedback {
  id?: number
  session_date: string
  exercise_name: string
  feel: 'light' | 'right' | 'heavy'
  notes: string | null
}

// --- Coach chat (in-app conversational coach)
export interface CoachConversation {
  id: string
  started_at: string
  ended_at: string | null
  title: string | null
  cli_session_id: string
  status: 'active' | 'archived'
}

export interface CoachTurn {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  status: 'pending' | 'in_progress' | 'complete' | 'error'
  error: string | null
  context_snapshot: Record<string, unknown> | null
  kb_refs: string[] | null
}
