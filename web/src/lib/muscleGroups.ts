/**
 * Muscle group mapping and aggregation for the radar chart.
 *
 * Maps granular DB muscle groups (from exercises.muscle_groups JSONB)
 * to 6 display categories matching the UI: Chest, Back, Legs, Arms, Shoulders, Core.
 */

import type { TrainingSet, TrainingSession } from './types'

// Granular → display group mapping
const MUSCLE_GROUP_MAP: Record<string, string> = {
  chest: 'Chest',
  upper_chest: 'Chest',
  lats: 'Back',
  rhomboids: 'Back',
  rear_delts: 'Back',
  lower_back: 'Back',
  traps: 'Back',
  back: 'Back',
  quads: 'Legs',
  glutes: 'Legs',
  hamstrings: 'Legs',
  adductors: 'Legs',
  calves: 'Legs',
  legs: 'Legs',
  biceps: 'Arms',
  triceps: 'Arms',
  forearms: 'Arms',
  brachioradialis: 'Arms',
  front_delts: 'Shoulders',
  lateral_delts: 'Shoulders',
  external_rotators: 'Shoulders',
  shoulders: 'Shoulders',
  core: 'Core',
  obliques: 'Core',
  transverse_abdominis: 'Core',
  hip_flexors: 'Core',
  lower_abs: 'Core',
  grip: 'Arms',
}

export const DISPLAY_GROUPS = ['Chest', 'Back', 'Legs', 'Shoulders', 'Core', 'Arms'] as const
export type DisplayGroup = (typeof DISPLAY_GROUPS)[number]

export type RadarMode = 'load' | 'volume' | 'frequency'

export interface RadarDataPoint {
  group: string
  value: number
  label: string // formatted value for display
}

function getDisplayGroups(muscleGroups: string[] | null | undefined): Set<string> {
  const groups = new Set<string>()
  if (!muscleGroups) return groups
  for (const mg of muscleGroups) {
    const display = MUSCLE_GROUP_MAP[mg]
    if (display) groups.add(display)
  }
  return groups
}

export function computeRadarData(
  sets: TrainingSet[],
  sessions: TrainingSession[],
  mode: RadarMode,
): RadarDataPoint[] {
  const workingSets = sets.filter((s) => s.set_type === 'working')

  if (mode === 'volume') {
    // Total volume (kg) per muscle group: weight * reps, distributed across groups
    const volumeByGroup: Record<string, number> = {}
    for (const g of DISPLAY_GROUPS) volumeByGroup[g] = 0

    for (const s of workingSets) {
      const groups = getDisplayGroups(s.exercises?.muscle_groups)
      if (groups.size === 0 || !s.weight_kg || !s.reps) continue
      const setVolume = s.weight_kg * s.reps
      // Distribute evenly across muscle groups
      const share = setVolume / groups.size
      for (const g of groups) {
        volumeByGroup[g] = (volumeByGroup[g] ?? 0) + share
      }
    }

    return DISPLAY_GROUPS.map((g) => ({
      group: g,
      value: Math.round(volumeByGroup[g] ?? 0),
      label: `${Math.round(volumeByGroup[g] ?? 0).toLocaleString()} kg`,
    }))
  }

  if (mode === 'frequency') {
    // Count distinct session dates per muscle group
    const sessionDateMap = new Map<number, string>()
    for (const s of sessions) sessionDateMap.set(s.id, s.date)

    const datesByGroup: Record<string, Set<string>> = {}
    for (const g of DISPLAY_GROUPS) datesByGroup[g] = new Set()

    for (const s of workingSets) {
      const groups = getDisplayGroups(s.exercises?.muscle_groups)
      const date = sessionDateMap.get(s.session_id)
      if (!date) continue
      for (const g of groups) {
        datesByGroup[g].add(date)
      }
    }

    return DISPLAY_GROUPS.map((g) => ({
      group: g,
      value: datesByGroup[g].size,
      label: `${datesByGroup[g].size} sessions`,
    }))
  }

  // mode === 'load': percentage distribution of volume
  const volumeByGroup: Record<string, number> = {}
  for (const g of DISPLAY_GROUPS) volumeByGroup[g] = 0
  let totalVolume = 0

  for (const s of workingSets) {
    const groups = getDisplayGroups(s.exercises?.muscle_groups)
    if (groups.size === 0 || !s.weight_kg || !s.reps) continue
    const setVolume = s.weight_kg * s.reps
    totalVolume += setVolume
    const share = setVolume / groups.size
    for (const g of groups) {
      volumeByGroup[g] = (volumeByGroup[g] ?? 0) + share
    }
  }

  return DISPLAY_GROUPS.map((g) => {
    const pct = totalVolume > 0 ? Math.round(((volumeByGroup[g] ?? 0) / totalVolume) * 100) : 0
    return {
      group: g,
      value: pct,
      label: `${pct}%`,
    }
  })
}
