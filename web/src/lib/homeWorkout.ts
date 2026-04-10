import type { WorkoutDefinition, PlannedExercise, WarmupExercise } from './types'

// ---------------------------------------------------------------------------
// Home exercise substitution map — mirrors workout_push.py HOME_SUBSTITUTIONS
// ---------------------------------------------------------------------------

interface HomeSubstitution {
  name: string
  equipment: string
  maxWeightKg: number | null
  weightStrategy: 'same' | 'cap_at' | 'fixed' | 'bodyweight'
  note: string
}

const HOME_SUBSTITUTIONS: Record<string, HomeSubstitution> = {
  // --- Session A ---
  'Barbell Back Squat': {
    name: 'Barbell Front Squat',
    equipment: 'barbell',
    maxWeightKg: 70.0,
    weightStrategy: 'cap_at',
    note: 'Clean to front rack — max ~70kg',
  },
  'Dumbbell Bench Press': {
    name: 'DB Floor Press',
    equipment: 'dumbbell',
    maxWeightKg: 20.0,
    weightStrategy: 'fixed',
    note: '20kg fixed DBs, floor press (no bench)',
  },
  'Kettlebell Swing': {
    name: 'DB Swing',
    equipment: 'dumbbell',
    maxWeightKg: 20.0,
    weightStrategy: 'fixed',
    note: 'Single 20kg fixed DB, two-hand swing',
  },
  'Kettlebell Halo': {
    name: 'DB Halo',
    equipment: 'dumbbell',
    maxWeightKg: 12.5,
    weightStrategy: 'cap_at',
    note: '12.5kg adjustable DB',
  },
  'Turkish Get-Up': {
    name: 'DB Turkish Get-Up',
    equipment: 'dumbbell',
    maxWeightKg: 20.0,
    weightStrategy: 'cap_at',
    note: 'Up to 20kg fixed DB',
  },
  // --- Session B ---
  'Chin-Up': {
    name: 'Band-Assisted Inverted Row',
    equipment: 'band',
    maxWeightKg: null,
    weightStrategy: 'bodyweight',
    note: 'Heavy band, table edge or sturdy bar',
  },
  'Dumbbell Incline Press': {
    name: 'Feet-Elevated Push-Up',
    equipment: 'bodyweight',
    maxWeightKg: null,
    weightStrategy: 'bodyweight',
    note: 'Feet on chair/step for upper chest emphasis',
  },
  'DB Incline Press': {
    name: 'Feet-Elevated Push-Up',
    equipment: 'bodyweight',
    maxWeightKg: null,
    weightStrategy: 'bodyweight',
    note: 'Feet on chair/step for upper chest emphasis',
  },
  'Cable Row': {
    name: 'Band Row',
    equipment: 'band',
    maxWeightKg: null,
    weightStrategy: 'bodyweight',
    note: 'Heavy resistance band, door anchor',
  },
  'Pallof Walkouts': {
    name: 'Band Pallof Press',
    equipment: 'band',
    maxWeightKg: null,
    weightStrategy: 'bodyweight',
    note: 'Medium band, door anchor at chest height',
  },
  // --- Session C ---
  'Trap Bar Deadlift': {
    name: 'Conventional Deadlift',
    equipment: 'barbell',
    maxWeightKg: 100.0,
    weightStrategy: 'cap_at',
    note: 'Conventional barbell deadlift from floor',
  },
  'KB Clean & Press': {
    name: 'DB Clean & Press',
    equipment: 'dumbbell',
    maxWeightKg: 20.0,
    weightStrategy: 'fixed',
    note: '20kg fixed DB, single-arm',
  },
  'KB Farmer Carry': {
    name: 'DB Farmer Carry',
    equipment: 'dumbbell',
    maxWeightKg: 20.0,
    weightStrategy: 'fixed',
    note: '20kg fixed DBs, one per hand',
  },
}

const HOME_COMPATIBLE = new Set([
  'Barbell Row',
  'Overhead Press',
  'Single-Arm DB Row',
  'Bulgarian Split Squat',
  'Lateral Raise',
  'Dead Bugs',
  'Copenhagen Plank',
])

const BARBELL_WEIGHT_CAP = 100.0
const DB_WEIGHT_CAP = 20.0

function applyHomeWeight(exerciseName: string, gymWeight: number | null, equipment?: string): number | null {
  if (gymWeight == null) return null
  const sub = HOME_SUBSTITUTIONS[exerciseName]
  if (sub) {
    if (sub.weightStrategy === 'bodyweight') return null
    if (sub.weightStrategy === 'fixed') return sub.maxWeightKg
    if (sub.weightStrategy === 'cap_at') return Math.min(gymWeight, sub.maxWeightKg!)
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
