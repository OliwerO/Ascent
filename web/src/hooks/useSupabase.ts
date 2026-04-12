import { useState, useEffect, useRef, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { format, subDays } from 'date-fns'
import type {
  DailySummary, HRVRow, SleepRow, Activity, DailyMetrics,
  BodyComposition, TrainingSession, TrainingSet, SubjectiveWellness,
  Goal, CoachingLogEntry, PlannedWorkout, PerformanceScore,
} from '../lib/types'

const MAX_RETRIES = 2
const RETRY_DELAY_MS = 1000

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Track online/offline state globally so all hooks share one listener pair. */
function useOnlineStatus(): boolean {
  const [online, setOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  return online
}

function useFetch<T>(
  _key: string,
  fetcher: () => Promise<T>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [offline, setOffline] = useState(false)
  const [manualTick, setManualTick] = useState(0)
  const hasFetched = useRef(false)
  const online = useOnlineStatus()

  // Retry-when-back-online: bump manualTick so the effect re-runs
  const prevOnlineRef = useRef(online)
  useEffect(() => {
    if (online && !prevOnlineRef.current) {
      // Just came back online — trigger a refetch
      setManualTick((t) => t + 1)
    }
    prevOnlineRef.current = online
  }, [online])

  useEffect(() => {
    let cancelled = false

    // If offline and we already have data, keep showing stale data
    if (!online) {
      setOffline(true)
      if (!hasFetched.current) setLoading(false)
      return
    }

    setOffline(false)

    // Only show loading spinner on initial fetch (stale-while-revalidate)
    if (!hasFetched.current) setLoading(true)

    const fetchWithRetry = async (): Promise<void> => {
      let lastError: string | null = null
      for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        if (cancelled) return
        try {
          const d = await fetcher()
          if (!cancelled) {
            setData(d)
            setError(null)
            hasFetched.current = true
          }
          return
        } catch (e: unknown) {
          lastError = e instanceof Error ? e.message : String(e)
          if (attempt < MAX_RETRIES) {
            await delay(RETRY_DELAY_MS)
          }
        }
      }
      // All retries exhausted
      if (!cancelled) setError(lastError)
    }

    fetchWithRetry().finally(() => {
      if (!cancelled) setLoading(false)
    })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, manualTick, online])

  const refetch = useCallback(() => setManualTick((t) => t + 1), [])

  return { data, loading, error, offline, refetch }
}

/**
 * Subscribe to Supabase Realtime changes on a table.
 * Returns a refresh counter that increments on any change, suitable as a dep for useFetch.
 */
let channelCounter = 0

function useRealtimeRefresh(table: string): number {
  const [tick, setTick] = useState(0)
  const tickRef = useRef(0)
  const idRef = useRef(++channelCounter)

  useEffect(() => {
    const channel = supabase.channel(`${table}_rt_${idRef.current}`)
      .on('postgres_changes', { event: '*', schema: 'public', table }, () => {
        tickRef.current += 1
        setTick(tickRef.current)
      })
      .subscribe((_status: string, err?: Error) => {
        if (err) console.warn(`Realtime subscription error for ${table}:`, err.message)
      })
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
  const rt = useRealtimeRefresh('hrv')
  return useFetch<HRVRow[]>('hrv', async () => {
    const { data, error } = await supabase
      .from('hrv')
      .select('date,last_night_avg,weekly_avg,status,baseline_balanced_low,baseline_balanced_upper')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
}

export function useSleep(days = 14) {
  const rt = useRealtimeRefresh('sleep')
  return useFetch<SleepRow[]>('sleep', async () => {
    const { data, error } = await supabase
      .from('sleep')
      .select('date,total_sleep_seconds,deep_sleep_seconds,rem_sleep_seconds,light_sleep_seconds,overall_score')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
}

export function useActivities(days = 14) {
  const rt = useRealtimeRefresh('activities')
  return useFetch<Activity[]>('activities', async () => {
    const { data, error } = await supabase
      .from('activities')
      .select('date,activity_type,activity_name,duration_seconds,calories,elevation_gain,elevation_loss,distance_meters,avg_hr,max_hr,avg_speed,max_speed,start_time,garmin_activity_id,training_effect_aerobic,training_effect_anaerobic,hr_zones,raw_json')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
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
  const rt = useRealtimeRefresh('body_composition')
  return useFetch<BodyComposition[]>('body_composition', async () => {
    const { data, error } = await supabase
      .from('body_composition')
      .select('date,weight_kg,body_fat_pct,muscle_mass_grams,body_water_pct,lean_body_mass_grams,bmi,visceral_fat_rating,metabolic_age,bone_mass_grams,source,raw_json')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
}

export function useTrainingSessions(days = 60) {
  const rt = useRealtimeRefresh('training_sessions')
  return useFetch<TrainingSession[]>('training_sessions', async () => {
    const { data, error } = await supabase
      .from('training_sessions')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
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
  const rt = useRealtimeRefresh('subjective_wellness')
  return useFetch<SubjectiveWellness[]>('subjective_wellness', async () => {
    const { data, error } = await supabase
      .from('subjective_wellness')
      .select('date,sleep_quality,energy,muscle_soreness,motivation,stress,composite_score,notes')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    // Graceful degradation if table doesn't exist yet
    if (error) {
      if (error.message?.includes('relation') || error.message?.includes('does not exist')) return []
      throw error
    }
    return data ?? []
  }, [days, rt])
}

export function useGoals() {
  return useFetch<Goal[]>('goals', async () => {
    const { data, error } = await supabase
      .from('goals')
      .select('*')
      .eq('status', 'active')
      .order('category')
    if (error) throw error
    return data ?? []
  }, [])
}

export function useCoachingLog(days = 7) {
  const rt = useRealtimeRefresh('coaching_log')
  return useFetch<CoachingLogEntry[]>('coaching_log', async () => {
    const { data, error } = await supabase
      .from('coaching_log')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data ?? []
  }, [days, rt])
}

export function usePlannedWorkouts(weeksBehind = 2, weeksAhead = 4) {
  const rt = useRealtimeRefresh('planned_workouts')
  return useFetch<PlannedWorkout[]>('planned_workouts', async () => {
    const from = fmt(subDays(today(), weeksBehind * 7))
    const to = fmt(new Date(today().getTime() + weeksAhead * 7 * 86400000))
    const { data, error } = await supabase
      .from('planned_workouts')
      .select('id,training_block,week_number,session_name,session_type,scheduled_date,scheduled_time,estimated_duration_minutes,workout_definition,status,actual_garmin_activity_id,compliance_score,adjustment_reason,updated_at')
      .gte('scheduled_date', from)
      .lte('scheduled_date', to)
      .order('scheduled_date', { ascending: true })
    if (error) throw error
    return data ?? []
  }, [weeksBehind, weeksAhead, rt])
}

export function usePerformanceScores(days = 90) {
  const rt = useRealtimeRefresh('performance_scores')
  return useFetch<PerformanceScore[]>('performance_scores', async () => {
    const { data, error } = await supabase
      .from('performance_scores')
      .select('date,endurance_score,hill_score,fitness_age')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: true })
    if (error) {
      if (error.message?.includes('relation') || error.message?.includes('does not exist')) return []
      throw error
    }
    return data ?? []
  }, [days, rt])
}

/**
 * Reschedule a planned workout to a new date.
 * If another workout already exists on the target date, swaps them.
 */
export async function rescheduleWorkout(
  workoutId: number,
  newDate: string,
  existingWorkoutOnTarget?: PlannedWorkout
): Promise<void> {
  if (existingWorkoutOnTarget) {
    // Swap: move the target workout to the source's old date
    const { data: source } = await supabase
      .from('planned_workouts')
      .select('scheduled_date')
      .eq('id', workoutId)
      .single()
    if (!source) throw new Error('Workout not found')

    const { error: e1 } = await supabase
      .from('planned_workouts')
      .update({
        scheduled_date: source.scheduled_date,
        status: 'adjusted',
        adjustment_reason: `Swapped with session on ${newDate}`,
      })
      .eq('id', existingWorkoutOnTarget.id)
    if (e1) throw e1

    const { error: e2 } = await supabase
      .from('planned_workouts')
      .update({
        scheduled_date: newDate,
        status: 'adjusted',
        adjustment_reason: `Moved from ${source.scheduled_date}`,
      })
      .eq('id', workoutId)
    if (e2) throw e2
  } else {
    // Simple move
    const { data: source } = await supabase
      .from('planned_workouts')
      .select('scheduled_date')
      .eq('id', workoutId)
      .single()
    if (!source) throw new Error('Workout not found')

    const { error } = await supabase
      .from('planned_workouts')
      .update({
        scheduled_date: newDate,
        status: 'adjusted',
        adjustment_reason: `Moved from ${source.scheduled_date}`,
      })
      .eq('id', workoutId)
    if (error) throw error
  }
}
