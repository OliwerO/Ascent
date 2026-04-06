import { differenceInDays, addDays, startOfWeek } from 'date-fns'

// Program started Apr 1 (Wed), but weeks are Monday-aligned for training
// Week 1 = Mon Mar 30 – Sun Apr 5, Week 2 = Mon Apr 6 – Sun Apr 12, etc.
export const BLOCK_1_START = new Date(2026, 2, 30) // Mon Mar 30 (week containing Apr 1)
export const BLOCK_2_START = new Date(2026, 3, 27) // Mon Apr 27
export const BLOCK_2_END = new Date(2026, 4, 24) // Sun May 24

export const DELOAD_WEEKS = new Set([4, 8])

export function getProgramWeek(date: Date): { block: number; week: number; ended: boolean } {
  const dateMonday = startOfWeek(date, { weekStartsOn: 1 })
  const days = differenceInDays(dateMonday, BLOCK_1_START)
  if (days < 0) return { block: 1, week: 1, ended: false }
  const week = Math.floor(days / 7) + 1
  if (week > 8) return { block: 2, week: 8, ended: true }
  return { block: week <= 4 ? 1 : 2, week, ended: false }
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
  // BLOCK_1_START is already Monday-aligned
  const monday = addDays(BLOCK_1_START, (weekNum - 1) * 7)

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
