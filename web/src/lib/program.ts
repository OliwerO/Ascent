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

// Starting weights (Week 1)
export const STARTING_WEIGHTS: Record<string, { weight: number; increment: number }> = {
  'Barbell Back Squat': { weight: 70, increment: 2.5 },
  'DB Bench Press': { weight: 18, increment: 1 },
  'Barbell Row': { weight: 25, increment: 2.5 },
  'KB Swings': { weight: 24, increment: 0 },
  'KB Halo': { weight: 12, increment: 0 },
  'KB Turkish Get-up': { weight: 12, increment: 0 },
  'Overhead Press': { weight: 20, increment: 2.5 },
  'Chin-ups': { weight: 0, increment: 0 },
  'DB Incline Press': { weight: 14, increment: 1 },
  'Cable Row': { weight: 30, increment: 2.5 },
  'Trap Bar Deadlift': { weight: 65, increment: 2.5 },
  'KB Clean & Press': { weight: 16, increment: 1 },
  'Single-Arm DB Row': { weight: 18, increment: 1 },
  'Bulgarian Split Squat': { weight: 10, increment: 1 },
  'Lateral Raises': { weight: 8, increment: 0.5 },
  'KB Farmer Carry': { weight: 24, increment: 2 },
}

export function getPlannedWeight(exercise: string, week: number): number | null {
  const config = STARTING_WEIGHTS[exercise]
  if (!config || config.increment === 0) return config?.weight ?? null

  let increments: number
  if (week <= 3) {
    increments = week - 1
  } else if (week === 4) {
    increments = 2 // deload uses week 3 weight
  } else if (week <= 7) {
    increments = week - 2
  } else {
    increments = 5 // deload uses week 7 weight
  }

  return config.weight + increments * config.increment
}
