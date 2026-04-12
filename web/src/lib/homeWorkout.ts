import type { WorkoutDefinition, PlannedExercise, WarmupExercise } from './types'
import homeConfig from '../../../config/home_substitutions.json'

// ---------------------------------------------------------------------------
// Home exercise substitution map — loaded from shared config/home_substitutions.json
// Both this file and scripts/workout_push.py consume the same JSON
// ---------------------------------------------------------------------------

interface HomeSubstitution {
  name: string
  equipment: string
  max_weight_kg: number | null
  weight_strategy: 'same' | 'cap_at' | 'fixed' | 'bodyweight'
  note: string
}

const HOME_SUBSTITUTIONS: Record<string, HomeSubstitution> =
  homeConfig.substitutions as Record<string, HomeSubstitution>

const HOME_COMPATIBLE = new Set(homeConfig.home_compatible)

const BARBELL_WEIGHT_CAP = homeConfig.weight_caps.barbell
const DB_WEIGHT_CAP = homeConfig.weight_caps.dumbbell

function applyHomeWeight(exerciseName: string, gymWeight: number | null, equipment?: string): number | null {
  if (gymWeight == null) return null
  const sub = HOME_SUBSTITUTIONS[exerciseName]
  if (sub) {
    if (sub.weight_strategy === 'bodyweight') return null
    if (sub.weight_strategy === 'fixed') return sub.max_weight_kg
    if (sub.weight_strategy === 'cap_at') return Math.min(gymWeight, sub.max_weight_kg!)
    return gymWeight
  }
  if (HOME_COMPATIBLE.has(exerciseName)) {
    if (equipment === 'barbell') return Math.min(gymWeight, BARBELL_WEIGHT_CAP)
    if (equipment === 'dumbbell') return Math.min(gymWeight, DB_WEIGHT_CAP)
  }
  return gymWeight
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function buildHomeWorkout(gym: WorkoutDefinition): WorkoutDefinition {
  const exercises: PlannedExercise[] = gym.exercises.map((ex) => {
    const sub = HOME_SUBSTITUTIONS[ex.name]
    if (sub) {
      return {
        ...ex,
        name: sub.name,
        equipment: sub.equipment,
        weight_kg: applyHomeWeight(ex.name, ex.weight_kg, ex.equipment),
        note: sub.note,
      }
    }
    if (HOME_COMPATIBLE.has(ex.name)) {
      return { ...ex, weight_kg: applyHomeWeight(ex.name, ex.weight_kg, ex.equipment) }
    }
    return { ...ex }
  })

  const jumpRopeWarmup: WarmupExercise = { name: 'Jump Rope', reps: null, duration_s: 180 }
  const warmup = [jumpRopeWarmup, ...(gym.warmup ?? [])]

  return {
    ...gym,
    session_name: `${gym.session_name} (Home)`,
    warmup,
    exercises,
    venue: 'home',
    original_gym_definition: { ...gym, original_gym_definition: undefined },
  }
}

export function restoreGymWorkout(home: WorkoutDefinition): WorkoutDefinition | null {
  return home.original_gym_definition ?? null
}

export function countSubstitutions(gym: WorkoutDefinition): number {
  return gym.exercises.filter((ex) => ex.name in HOME_SUBSTITUTIONS).length
}

export function isHomeWorkout(wd: WorkoutDefinition | null | undefined): boolean {
  return wd?.venue === 'home'
}
