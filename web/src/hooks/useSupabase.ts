import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { format, subDays } from 'date-fns'

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

const fmt = (d: Date) => format(d, 'yyyy-MM-dd')
const today = () => new Date()
const daysAgo = (n: number) => subDays(today(), n)

export function useDailySummary(days = 7) {
  return useFetch('daily_summary', async () => {
    const { data, error } = await supabase
      .from('daily_summary')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useHRV(days = 14) {
  return useFetch('hrv', async () => {
    const { data, error } = await supabase
      .from('hrv')
      .select('date,last_night_avg,weekly_avg,status,baseline_balanced_low,baseline_balanced_upper')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useSleep(days = 14) {
  return useFetch('sleep', async () => {
    const { data, error } = await supabase
      .from('sleep')
      .select('date,total_sleep_seconds,deep_sleep_seconds,rem_sleep_seconds,light_sleep_seconds,overall_score')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useActivities(days = 14) {
  return useFetch('activities', async () => {
    const { data, error } = await supabase
      .from('activities')
      .select('date,activity_type,activity_name,duration_seconds,calories,elevation_gain,elevation_loss,distance_meters,avg_hr,max_hr,avg_speed,max_speed,start_time,garmin_activity_id,raw_json')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useDailyMetrics(days = 7) {
  return useFetch('daily_metrics', async () => {
    const { data, error } = await supabase
      .from('daily_metrics')
      .select('date,body_battery_highest,body_battery_lowest,training_readiness_score,resting_hr,avg_stress_level,vo2max')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useTrainingStatus(days = 7) {
  return useFetch('training_status', async () => {
    const { data, error } = await supabase
      .from('training_status')
      .select('date,training_status,training_load_7d,training_load_28d,raw_json')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useBodyComposition(days = 90) {
  return useFetch('body_composition', async () => {
    const { data, error } = await supabase
      .from('body_composition')
      .select('date,weight_kg,body_fat_pct,muscle_mass_grams')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useTrainingSessions(days = 60) {
  return useFetch('training_sessions', async () => {
    const { data, error } = await supabase
      .from('training_sessions')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}

export function useTrainingSets(sessionIds: number[]) {
  return useFetch('training_sets', async () => {
    if (!sessionIds.length) return []
    const { data, error } = await supabase
      .from('training_sets')
      .select('*, exercises(name, category)')
      .in('session_id', sessionIds)
      .order('set_number')
    if (error) throw error
    return data
  }, [sessionIds.join(',')])
}

export function useCoachingLog(days = 7) {
  return useFetch('coaching_log', async () => {
    const { data, error } = await supabase
      .from('coaching_log')
      .select('*')
      .gte('date', fmt(daysAgo(days)))
      .order('date', { ascending: false })
    if (error) throw error
    return data
  }, [days])
}
