import { differenceInDays, addDays } from 'date-fns'

export const BLOCK_1_START = new Date(2026, 3, 1) // Apr 1
export const BLOCK_2_START = new Date(2026, 3, 29) // Apr 29
export const BLOCK_2_END = new Date(2026, 4, 26) // May 26

export const DELOAD_WEEKS = new Set([4, 8])

export function getProgramWeek(date: Date): { block: number; week: number } {
  const days = differenceInDays(date, BLOCK_1_START)
  if (days < 0) return { block: 1, week: 1 }
  const week = Math.floor(days / 7) + 1
  if (week > 8) return { block: 2, week: 8 }
  return { block: week <= 4 ? 1 : 2, week }
}

export function isDeloadWeek(week: number): boolean {
  return DELOAD_WEEKS.has(week)
}

export type SessionType = 'A' | 'B' | 'C' | 'A2' | 'B2'

const DAY_TO_SESSION: Record<number, SessionType> = {
  1: 'B', // Monday
  3: 'A', // Wednesday
  5: 'C', // Friday
}

export function getSessionForDate(date: Date): SessionType | null {
  return DAY_TO_SESSION[date.getDay()] ?? null
}

export const SESSION_NAMES: Record<SessionType, string> = {
  A: 'Strength A: Full Body',
  B: 'Strength B: Upper + Core',
  C: 'Strength C: Full Body Variant',
  A2: 'Full Body A (Heavy)',
  B2: 'Full Body B (Functional)',
}

export const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export interface WeekSchedule {
  weekNum: number
  block: number
  deload: boolean
  days: {
    date: Date
    label: string
    session: SessionType | null
    dayType: 'gym' | 'rest' | 'mobility' | 'mountain' | 'cardio' | 'intervals'
  }[]
}

export function getWeekSchedule(weekNum: number): WeekSchedule {
  const block = weekNum <= 4 ? 1 : 2
  const deload = isDeloadWeek(weekNum)
  const weekStart = addDays(BLOCK_1_START, (weekNum - 1) * 7)
  // BLOCK_1_START is Wednesday, so we need Monday of that week
  const monday = addDays(weekStart, -2) // Wed - 2 = Mon

  const dayTypes: ('gym' | 'rest' | 'mobility' | 'mountain' | 'cardio' | 'intervals')[] =
    block === 1
      ? ['gym', 'mobility', 'gym', 'rest', 'gym', 'mountain', 'rest']
      : ['gym', 'mobility', 'gym', 'intervals', 'gym', 'mountain', 'rest']

  const days = dayTypes.map((dayType, i) => {
    const date = addDays(monday, i)
    const session = dayType === 'gym' ? getSessionForDate(date) : null
    return {
      date,
      label: DAY_LABELS[date.getDay()],
      session,
      dayType,
    }
  })

  return { weekNum, block, deload, days }
}

// Starting weights (Week 1) — fallback only, real weights come from exercise_progression
export const STARTING_WEIGHTS: Record<string, { weight: number; increment: number }> = {
  'Barbell Back Squat': { weight: 70, increment: 2.5 },
  'Dumbbell Bench Press': { weight: 18, increment: 2.5 },
  'Barbell Row': { weight: 40, increment: 2.5 },
  'KB Swings': { weight: 24, increment: 0 },
  'KB Halo': { weight: 12, increment: 0 },
  'KB Turkish Get-up': { weight: 8, increment: 0 },
  'Overhead Press': { weight: 35, increment: 2.5 },
  'Chin-ups': { weight: 0, increment: 0 },
  'Dumbbell Incline Press': { weight: 14, increment: 2.5 },
  'Cable Row': { weight: 35, increment: 2.5 },
  'Trap Bar Deadlift': { weight: 65, increment: 2.5 },
  'KB Clean & Press': { weight: 16, increment: 0 },
  'Single-Arm DB Row': { weight: 22, increment: 2.5 },
  'Bulgarian Split Squat': { weight: 10, increment: 2.5 },
  'Lateral Raises': { weight: 6, increment: 2.5 },
  'KB Farmer Carry': { weight: 24, increment: 0 },
}

// Name aliases for backward compatibility with older keys
const NAME_ALIASES: Record<string, string> = {
  'DB Bench Press': 'Dumbbell Bench Press',
  'DB Incline Press': 'Dumbbell Incline Press',
}

export function resolveExerciseName(name: string): string {
  return NAME_ALIASES[name] ?? name
}

/**
 * Get the planned weight for an exercise.
 *
 * If exercise_progression data is available (from the progression engine),
 * uses the latest planned_weight_kg from that table. Otherwise falls back
 * to the formula-based calculation.
 */
export function getPlannedWeight(
  exercise: string,
  week: number,
  progressionData?: Array<{ exercise_name: string; planned_weight_kg: number; progression_applied: string }>,
): number | null {
  const resolved = resolveExerciseName(exercise)

  // Check progression engine data first (data-driven weights)
  if (progressionData) {
    const entry = progressionData.find(
      (p) => p.exercise_name === exercise || p.exercise_name === resolved
    )
    if (entry?.planned_weight_kg != null) {
      return entry.planned_weight_kg
    }
  }

  // Formula fallback
  const config = STARTING_WEIGHTS[resolved] ?? STARTING_WEIGHTS[exercise]
  if (!config || config.increment === 0) return config?.weight ?? null

  let increments: number
  if (week <= 3) {
    increments = week - 1
  } else if (week === 4) {
    increments = 2
  } else if (week <= 7) {
    increments = week - 2
  } else {
    increments = 5
  }

  return config.weight + increments * config.increment
}

/**
 * Analyze actual lift performance vs the plan.
 * Returns progression status and next recommended weight.
 *
 * Rules from coaching-context.md:
 * - If RPE >= 8 before week 3: hold weight, add reps
 * - If same weight 2+ consecutive weeks: stall detected
 * - If stalled 3 weeks: drop 10%, increase to 12 reps, rebuild
 * - Block 2 resumes at week 3 actual weight + increment (not planned)
 */
export type ProgressionStatus = 'on_track' | 'ahead' | 'stalled' | 'behind' | 'no_data'

export interface LiftAnalysis {
  status: ProgressionStatus
  statusLabel: string
  lastActualWeight: number | null
  nextTargetWeight: number | null
  weeksAtSameWeight: number
  trend: 'up' | 'flat' | 'down' | null
}

export function analyzeLiftProgression(
  exercise: string,
  currentWeek: number,
  actualWeightsByWeek: Map<number, number>, // week -> max weight used
): LiftAnalysis {
  const config = STARTING_WEIGHTS[exercise]
  if (!config) return { status: 'no_data', statusLabel: 'Unknown exercise', lastActualWeight: null, nextTargetWeight: null, weeksAtSameWeight: 0, trend: null }

  // Find most recent actual weight
  let lastActualWeight: number | null = null
  let lastActualWeek: number | null = null
  for (let w = currentWeek; w >= 1; w--) {
    if (actualWeightsByWeek.has(w)) {
      lastActualWeight = actualWeightsByWeek.get(w)!
      lastActualWeek = w
      break
    }
  }

  if (lastActualWeight === null) {
    return {
      status: 'no_data',
      statusLabel: 'No sessions yet',
      lastActualWeight: null,
      nextTargetWeight: getPlannedWeight(exercise, Math.min(currentWeek, 3)),
      weeksAtSameWeight: 0,
      trend: null,
    }
  }

  // Count consecutive weeks at same weight
  let weeksAtSameWeight = 0
  for (let w = lastActualWeek!; w >= 1; w--) {
    const wt = actualWeightsByWeek.get(w)
    if (wt === lastActualWeight) weeksAtSameWeight++
    else break
  }

  // Determine trend from last 3 data points
  const recentWeights: number[] = []
  for (let w = lastActualWeek!; w >= 1 && recentWeights.length < 3; w--) {
    if (actualWeightsByWeek.has(w)) recentWeights.unshift(actualWeightsByWeek.get(w)!)
  }
  let trend: 'up' | 'flat' | 'down' | null = null
  if (recentWeights.length >= 2) {
    const last = recentWeights[recentWeights.length - 1]
    const prev = recentWeights[recentWeights.length - 2]
    if (last > prev) trend = 'up'
    else if (last < prev) trend = 'down'
    else trend = 'flat'
  }

  // Compare actual vs planned
  const plannedForLastWeek = getPlannedWeight(exercise, lastActualWeek!)

  let status: ProgressionStatus
  let statusLabel: string
  let nextTargetWeight: number | null

  if (weeksAtSameWeight >= 3 && config.increment > 0) {
    // Stalled 3+ weeks: drop 10%, rebuild
    status = 'stalled'
    statusLabel = `Stalled ${weeksAtSameWeight} weeks — consider drop & rebuild`
    nextTargetWeight = Math.round(lastActualWeight * 0.9 / config.increment) * config.increment
  } else if (weeksAtSameWeight >= 2 && config.increment > 0) {
    // Stalled 2 weeks: hold one more
    status = 'stalled'
    statusLabel = `Same weight for ${weeksAtSameWeight} weeks`
    nextTargetWeight = lastActualWeight // hold
  } else if (plannedForLastWeek && lastActualWeight > plannedForLastWeek) {
    status = 'ahead'
    statusLabel = 'Ahead of plan'
    nextTargetWeight = lastActualWeight + config.increment
  } else if (plannedForLastWeek && lastActualWeight < plannedForLastWeek - config.increment) {
    status = 'behind'
    statusLabel = 'Behind plan'
    nextTargetWeight = lastActualWeight + config.increment
  } else {
    status = 'on_track'
    statusLabel = 'On track'
    nextTargetWeight = lastActualWeight + config.increment
  }

  return { status, statusLabel, lastActualWeight, nextTargetWeight, weeksAtSameWeight, trend }
}
