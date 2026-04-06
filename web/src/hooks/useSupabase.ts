import { useState, useEffect, useRef } from 'react'
import { supabase } from '../lib/supabase'
import { format, subDays } from 'date-fns'
import type {
  DailySummary, HRVRow, SleepRow, Activity, DailyMetrics,
  BodyComposition, TrainingSession, TrainingSet, SubjectiveWellness,
  Goal, CoachingLogEntry, PlannedWorkout,
} from '../lib/types'

function useFetch<T>(
  _key: string,
  fetcher: () => Promise<T>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetcher()
      .then((d) => { if (!cancelled) setData(d) })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, deps)

  return { data, loading, error }
}

/**
 * Subscribe to Supabase Realtime changes on a table.
 * Returns a refresh counter that increments on any change, suitable as a dep for useFetch.
 */
function useRealtimeRefresh(table: string): number {
  const [tick, setTick] = useState(0)
  const tickRef = useRef(0)

  useEffect(() => {
    const channel = supabase.channel(`${table}_realtime`)
      .on('postgres_changes', { event: '*', schema: 'public', table }, () => {
        tickRef.current += 1
        setTick(tickRef.current)
      })
      .subscribe()
    return () => { supabase.removeChannel(channel) }
  }, [table])

  return tick
}

const fmt = (d: Date) => format(d, 'yyyy-MM-dd')
const today = () => new Date()
const daysAgo = (n: number) => subDays(today(), n)

export function useDailySummary(days = 7) {
  const rt = useRealtimeRefresh('daily_metrics')
  return useFetch<DailySummary[]>('daily_summary', async () => {
    const { data, error } = await supabase
      .from('daily_summary')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
}

export function useHRV(days = 14) {
  return useFetch<HRVRow[]>('hrv', async () => {
    const { data, error } = await supabase
      .from('hrv')
      .select('date,last_night_avg,weekly_avg,status,baseline_balanced_low,baseline_balanced_upper')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days])
}

export function useSleep(days = 14) {
  return useFetch<SleepRow[]>('sleep', async () => {
    const { data, error } = await supabase
      .from('sleep')
      .select('date,total_sleep_seconds,deep_sleep_seconds,rem_sleep_seconds,light_sleep_seconds,overall_score')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days])
}

export function useActivities(days = 14) {
  return useFetch<Activity[]>('activities', async () => {
    const { data, error } = await supabase
      .from('activities')
      .select('date,activity_type,activity_name,duration_seconds,calories,elevation_gain,elevation_loss,distance_meters,avg_hr,max_hr,avg_speed,max_speed,start_time,garmin_activity_id,raw_json')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days])
}

export function useDailyMetrics(days = 7) {
  const rt = useRealtimeRefresh('daily_metrics')
  return useFetch<DailyMetrics[]>('daily_metrics', async () => {
    const { data, error } = await supabase
      .from('daily_metrics')
      .select('date,body_battery_highest,body_battery_lowest,training_readiness_score,resting_hr,avg_stress_level,vo2max')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
}

export function useBodyComposition(days = 90) {
  return useFetch<BodyComposition[]>('body_composition', async () => {
    const { data, error } = await supabase
      .from('body_composition')
      .select('date,weight_kg,body_fat_pct,muscle_mass_grams,body_water_pct,lean_body_mass_grams,bmi,visceral_fat_rating,metabolic_age,bone_mass_grams,source,raw_json')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days])
}

export function useTrainingSessions(days = 60) {
  return useFetch<TrainingSession[]>('training_sessions', async () => {
    const { data, error } = await supabase
      .from('training_sessions')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days])
}

export function useTrainingSets(sessionIds: number[]) {
  return useFetch<TrainingSet[]>('training_sets', async () => {
    if (!sessionIds.length) return []
    const { data, error } = await supabase
      .from('training_sets')
      .select('*, exercises(name, category)')
      .in('session_id', sessionIds)
      .order('set_number')
    if (error) throw error
    return data ?? []
  }, [sessionIds.join(',')])
}

export function useSubjectiveWellness(days = 30) {
  return useFetch<SubjectiveWellness[]>('subjective_wellness', async () => {
    const { data, error } = await supabase
      .from('subjective_wellness')
      .select('date,sleep_quality,energy,muscle_soreness,motivation,stress,composite_score,notes')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) return [] // table may not exist yet
    return data ?? []
  }, [days])
}

export function useGoals() {
  return useFetch<Goal[]>('goals', async () => {
    const { data, error } = await supabase
      .from('goals')
      .select('*')
      .eq('status', 'active')
      .order('category')
    if (error) return []
    return data ?? []
  }, [])
}

export function useCoachingLog(days = 7) {
  return useFetch<CoachingLogEntry[]>('coaching_log', async () => {
    const { data, error } = await supabase
      .from('coaching_log')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days])
}

export function usePlannedWorkouts(weeksBehind = 2, weeksAhead = 4) {
  const rt = useRealtimeRefresh('planned_workouts')
  return useFetch<PlannedWorkout[]>('planned_workouts', async () => {
    const from = fmt(subDays(today(), weeksBehind * 7))
    const to = fmt(new Date(today().getTime() + weeksAhead * 7 * 86400000))
    const { data, error } = await supabase
      .from('planned_workouts')
      .select('id,training_block,week_number,session_name,session_type,scheduled_date,scheduled_time,estimated_duration_minutes,workout_definition,status,actual_garmin_activity_id,compliance_score,adjustment_reason')
      .gte('scheduled_date', from)
      .lte('scheduled_date', to)
      .order('scheduled_date', { ascending: true })
    if (error) return []
    return data ?? []
  }, [weeksBehind, weeksAhead, rt])
}
