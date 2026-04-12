import { supabase } from '../lib/supabase'
import { buildHomeWorkout, restoreGymWorkout, isHomeWorkout, countSubstitutions } from '../lib/homeWorkout'
import { LoadingState, EmptyState } from '../components/LoadingState'
import { WellnessInput } from '../components/WellnessInput'
import { PostSessionLog } from '../components/PostSessionLog'
import { WeeklyReflection } from '../components/WeeklyReflection'
import { useDailySummary, useHRV, useDailyMetrics, useActivities, useSubjectiveWellness, usePlannedWorkouts, useCoachingLog } from '../hooks/useSupabase'
import type { WarmupExercise, PlannedExercise } from '../lib/types'
import {
  getProgramWeek, isDeloadWeek, getSessionForDate, SESSION_NAMES,
} from '../lib/program'
import { metricColor, hrvStatusInfo } from '../lib/colors'
import { MOUNTAIN_ACTIVITY_TYPES, SELF_POWERED_MOUNTAIN_TYPES } from '../lib/constants'
import { computeCoachingState } from '../lib/coachingDecision'
import { formatDuration, formatActivityType } from '../lib/format'
import { Clock, Flame, ArrowUpRight, Heart, ChevronDown, TrendingUp, Activity as ActivityIcon, Info, Home, Dumbbell, Send } from 'lucide-react'
import { useState, useMemo } from 'react'
import { format } from 'date-fns'

// ═══════════════════════════════════════════════════════════════════

export default function TodayView() {
  const summary = useDailySummary(7)
  const hrv = useHRV(14)
  const metrics = useDailyMetrics(14)
  const activities = useActivities(14)
  const wellness = useSubjectiveWellness(30)
  const planned = usePlannedWorkouts()
  const coachingLog = useCoachingLog(7)
  const [showExercises, setShowExercises] = useState(false)
  const [, setWellnessRefresh] = useState(0)
  const [switching, setSwitching] = useState(false)
  const [switchError, setSwitchError] = useState<string | null>(null)
  const [showHomePreview, setShowHomePreview] = useState(false)
  const [pushing, setPushing] = useState(false)
  const [pushMsg, setPushMsg] = useState<string | null>(null)

  const recentActivities = activities.data ?? []

  const sleep7dAvg = useMemo(() => {
    const sleepDays = (summary.data ?? []).slice(0, 7)
    const valid = sleepDays.filter((d) => d.total_sleep_seconds != null)
    if (valid.length === 0) return null
    return valid.reduce((s: number, d) => s + d.total_sleep_seconds! / 3600, 0) / valid.length
  }, [summary.data])

  const thisWeekActivities = useMemo(() => {
    const now = new Date()
    const dayOfWeek = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7))
    monday.setHours(0, 0, 0, 0)
    return recentActivities.filter((a) => new Date(a.date) >= monday)
  }, [recentActivities])

  const lastWeekActivities = useMemo(() => {
    const now = new Date()
    const dayOfWeek = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7))
    const prevMonday = new Date(monday)
    prevMonday.setDate(monday.getDate() - 7)
    return recentActivities.filter((a) => {
      const d = new Date(a.date)
      return d >= prevMonday && d < monday
    })
  }, [recentActivities])

  // ─── Mountain load in last 72h (interference context) ───
  const mountainLoad72h = useMemo(() => {
    const threeDaysAgo = new Date()
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3)
    threeDaysAgo.setHours(0, 0, 0, 0)
    const mountainActivities = recentActivities.filter(
      (a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type) && new Date(a.date) >= threeDaysAgo
    )
    if (mountainActivities.length === 0) return null
    const elevation = mountainActivities
      .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
      .reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
    const hours = mountainActivities.reduce((s: number, a) => s + (a.duration_seconds ?? 0), 0) / 3600
    const category = elevation >= 2000 || hours >= 5 ? 'heavy' : elevation >= 1000 || hours >= 3 ? 'moderate' : 'light'
    return { days: mountainActivities.length, elevation: Math.round(elevation), hours: Math.round(hours * 10) / 10, category }
  }, [recentActivities])

  const loading = summary.loading || hrv.loading || metrics.loading || activities.loading
  if (loading) return <LoadingState />

  if (!summary.data?.length && !metrics.data?.length) {
    return <EmptyState icon="📡" title="No data yet" subtitle="Sync your Garmin to get started — data typically arrives within 5 minutes" />
  }

  const today = summary.data?.[0]
  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const lastActivity = recentActivities[0]
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const todayWellness = (wellness.data ?? []).find((w) => w.date === todayStr) ?? null

  // ─── Derived values ───
  const sleepHours = today?.total_sleep_seconds
    ? Number((today.total_sleep_seconds / 3600).toFixed(1)) : null
  const { block, week, ended: programEnded } = getProgramWeek(new Date())
  const deload = isDeloadWeek(week)
  const todayPlanned = planned.data?.find((pw) => pw.scheduled_date === todayStr) ?? null

  // Check coaching log for today's adjustment entries
  const todayAdjustment = (coachingLog.data ?? []).find(
    (entry) => entry.date === todayStr &&
      (entry.type === 'adjustment' || entry.type === 'daily_adjustment')
  )
  const adjustedSessionName = todayAdjustment?.data_context?.session_name as string | undefined

  // Find coaching rationale (rule + inputs) for today
  const todayRationale = (coachingLog.data ?? []).find(
    (entry) => entry.date === todayStr && entry.rule != null
  )
  const [showRationale, setShowRationale] = useState(false)

  const todaySession = todayPlanned
    ? todayPlanned.workout_definition?.session_label
    : (adjustedSessionName ? null : getSessionForDate(new Date()))
  const isGymDay = todayPlanned != null || todayAdjustment != null || getSessionForDate(new Date()) != null
  const todaySessionName = todayPlanned?.workout_definition?.session_name
    ?? adjustedSessionName
    ?? (todaySession ? SESSION_NAMES[todaySession as keyof typeof SESSION_NAMES] : null)
  const isAdjusted = todayPlanned?.status === 'adjusted' || todayAdjustment != null
  const bbHigh = todayMetrics?.body_battery_highest ?? null
  const readiness = todayMetrics?.training_readiness_score != null
    ? Math.round(todayMetrics.training_readiness_score) : null

  // ─── HRV context ───
  const hrvVal = todayHRV?.last_night_avg != null ? Math.round(todayHRV.last_night_avg) : null
  const hrvWeeklyAvg = todayHRV?.weekly_avg != null ? Math.round(todayHRV.weekly_avg) : null
  const hrvInfo = hrvStatusInfo(todayHRV?.status)

  // ─── Sleep context ───
  const sleepDays = (summary.data ?? []).slice(0, 7)
  const sleepBelowCount = sleepDays.filter(
    (d) => d.total_sleep_seconds != null && d.total_sleep_seconds / 3600 < 6
  ).length

  // ─── Resting HR context ───
  const rhrValues = (metrics.data ?? []).slice(0, 7).filter((d) => d.resting_hr != null)
  const rhr7dAvg = rhrValues.length > 0
    ? rhrValues.reduce((s: number, d) => s + d.resting_hr!, 0) / rhrValues.length : null
  const rhr30dValues = (metrics.data ?? []).filter((d) => d.resting_hr != null)
  const rhr30dAvg = rhr30dValues.length > 0
    ? rhr30dValues.reduce((s: number, d) => s + d.resting_hr!, 0) / rhr30dValues.length : null
  const rhrElevated = rhr7dAvg != null && rhr30dAvg != null && rhr7dAvg > rhr30dAvg + 5
  const rhrTrend = todayMetrics?.resting_hr != null && rhr7dAvg != null
    ? (todayMetrics.resting_hr > rhr7dAvg + 2 ? '↑ Rising' : todayMetrics.resting_hr < rhr7dAvg - 2 ? '↓ Declining' : '→ Stable')
    : null

  const splitLoad = (acts: typeof thisWeekActivities) => {
    let gym = 0, mountain = 0, resort = 0
    for (const a of acts) {
      const dur = a.duration_seconds ?? 0
      if (a.activity_type === 'strength_training') gym += dur
      else if (SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type)) mountain += dur
      else if (MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type)) resort += dur
    }
    return { gym, mountain, resort }
  }
  const thisWeekLoad = splitLoad(thisWeekActivities)
  const lastWeekLoad = splitLoad(lastWeekActivities)
  const thisWeekElev = thisWeekActivities
    .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
    .reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
  const lastWeekElev = lastWeekActivities
    .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
    .reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
  const trainingLoad = thisWeekLoad.gym + thisWeekLoad.mountain
  const prevTrainingLoad = lastWeekLoad.gym + lastWeekLoad.mountain
  const loadChangePct = prevTrainingLoad > 0
    ? Math.round(((trainingLoad - prevTrainingLoad) / prevTrainingLoad) * 100) : null

  // ─── Coaching card decision tree (centralized in lib/coachingDecision) ───
  const decision = computeCoachingState({
    hrvStatus: todayHRV?.status,
    hrvVal,
    hrvWeeklyAvg,
    sleepHoursLastNight: sleepHours,
    sleep7dAvg,
    wellnessComposite: todayWellness?.composite_score ?? null,
    bodyBattery: bbHigh,
    trainingReadiness: readiness,
    rhrElevated,
  })
  const cardState = decision.state

  const verdictLabel = decision.label
  const verdictColor = cardState === 'green' ? 'text-accent-green' : cardState === 'amber' ? 'text-accent-yellow' : 'text-accent-red'
  const verdictBg = cardState === 'green' ? 'border-accent-green/20 bg-glow-green' : cardState === 'amber' ? 'border-accent-yellow/20 bg-glow-yellow' : 'border-accent-red/20 bg-glow-red'
  const rpeRange = todayPlanned?.workout_definition?.rpe_range
    ? `${todayPlanned.workout_definition.rpe_range[0]}-${todayPlanned.workout_definition.rpe_range[1]}`
    : deload ? '5-6' : block === 1 ? '6-7' : '7-8'

  // ─── Coaching notes ───
  const coachingPoints: { icon: string; text: string; color?: string }[] = []

  if (cardState === 'red') {
    coachingPoints.push({ icon: '🔴', text: 'Multiple recovery signals degraded — rest or mobility only', color: 'text-accent-red' })
  } else if (cardState === 'amber') {
    coachingPoints.push({ icon: '🟡', text: 'One or more signals flagged — train if warmup feels good, otherwise swap to mobility', color: 'text-accent-yellow' })
  }

  const lastGymSession = recentActivities.find((a) => a.activity_type === 'strength_training')
  const daysSinceGym = lastGymSession
    ? Math.floor((Date.now() - new Date(lastGymSession.date).getTime()) / 86400000)
    : null

  if (isGymDay && todaySession) {
    if (deload) {
      coachingPoints.push({ icon: '📉', text: 'Deload week — same weight, half sets, focus on form' })
    } else if (daysSinceGym != null && daysSinceGym > 7) {
      coachingPoints.push({ icon: '💡', text: `${daysSinceGym} days since last gym session — start conservative, RPE 6 max` })
    }
  }

  if (mountainLoad72h && isGymDay) {
    if (mountainLoad72h.category === 'heavy') {
      coachingPoints.push({ icon: '🏔', text: `Heavy mountain load: ${mountainLoad72h.elevation}m / ${mountainLoad72h.hours}h in last 72h — expect reduced performance`, color: 'text-accent-yellow' })
    } else if (mountainLoad72h.category === 'moderate') {
      coachingPoints.push({ icon: '🏔', text: `Mountain load: ${mountainLoad72h.elevation}m in last 72h — monitor how warmup feels` })
    }
  }

  if (sleepBelowCount >= 3) {
    coachingPoints.push({ icon: '😴', text: `${sleepBelowCount} nights below 6h this week — sleep is the bottleneck`, color: 'text-accent-yellow' })
  }

  if (!isGymDay) {
    const dayName = new Date().toLocaleDateString('en-US', { weekday: 'long' })
    if (dayName === 'Tuesday') coachingPoints.push({ icon: '🧘', text: 'Mobility day — foam roll, hip flexors, thoracic rotation' })
    else if (dayName === 'Saturday' || dayName === 'Sunday') coachingPoints.push({ icon: '🏔', text: 'Mountain day — your call based on conditions' })
    else coachingPoints.push({ icon: '🔋', text: 'Rest day — recover for the next session' })
  }

  if (!todayWellness && cardState === 'green') {
    coachingPoints.push({ icon: 'ℹ️', text: 'Complete wellness check-in for full assessment', color: 'text-text-muted' })
  }

  if (coachingPoints.length === 0 && isGymDay) {
    coachingPoints.push({ icon: '✅', text: 'All signals green — train as planned' })
  }

  const todayIsHome = isHomeWorkout(todayPlanned?.workout_definition)

  // Home workout preview diff
  const homePreviewDiff = useMemo(() => {
    if (!todayPlanned?.workout_definition || todayIsHome) return []
    const homeWd = buildHomeWorkout(todayPlanned.workout_definition)
    const gymExercises = todayPlanned.workout_definition.exercises ?? []
    const homeExercises = homeWd.exercises ?? []
    return gymExercises.map((gym: PlannedExercise, i: number) => {
      const home = homeExercises[i]
      if (!home || (gym.name === home.name && gym.weight_kg === home.weight_kg)) return null
      return {
        gym: `${gym.name}${gym.weight_kg != null ? ` ${gym.weight_kg}kg` : ''}`,
        home: `${home.name}${home.weight_kg != null ? ` ${home.weight_kg}kg` : ' (BW)'}`,
        note: home.note,
      }
    }).filter(Boolean) as { gym: string; home: string; note?: string }[]
  }, [todayPlanned?.workout_definition, todayIsHome])

  const handlePushToGarmin = async () => {
    if (pushing) return
    setPushing(true)
    setPushMsg(null)
    try {
      const resp = await fetch('/api/garmin-push-trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-ascent-token': import.meta.env.VITE_SUPABASE_KEY ?? '',
        },
        body: JSON.stringify({ date: todayStr }),
      })
      const data = await resp.json()
      setPushMsg(data.ok ? 'Push queued — check your watch in ~2 min' : (data.error || 'Failed'))
      setTimeout(() => setPushMsg(null), 5000)
    } catch {
      setPushMsg('Push request failed')
      setTimeout(() => setPushMsg(null), 5000)
    } finally {
      setPushing(false)
    }
  }

  const handleSwitchToHome = async () => {
    if (!todayPlanned?.workout_definition || switching) return
    setSwitching(true)
    setSwitchError(null)
    try {
      const homeWd = buildHomeWorkout(todayPlanned.workout_definition)
      const { error } = await supabase
        .from('planned_workouts')
        .update({
          workout_definition: homeWd,
          status: 'adjusted',
          adjustment_reason: 'Switched to home workout',
        })
        .eq('id', todayPlanned.id)
      if (error) throw error
      await supabase.from('coaching_log').insert({
        date: todayStr,
        type: 'adjustment',
        channel: 'app',
        message: 'Switched to home workout',
        data_context: { action: 'switch_to_home', reason: 'User requested from app' },
      })
    } catch (err) {
      setSwitchError(`Switch failed: ${err instanceof Error ? err.message : 'unknown error'}`)
      setTimeout(() => setSwitchError(null), 5000)
    } finally {
      setSwitching(false)
    }
  }

  const handleSwitchToGym = async () => {
    if (!todayPlanned?.workout_definition || switching) return
    const gymWd = restoreGymWorkout(todayPlanned.workout_definition)
    if (!gymWd) return
    setSwitching(true)
    setSwitchError(null)
    try {
      const { error } = await supabase
        .from('planned_workouts')
        .update({
          workout_definition: gymWd,
          status: 'adjusted',
          adjustment_reason: 'Switched back to gym workout',
        })
        .eq('id', todayPlanned.id)
      if (error) throw error
      await supabase.from('coaching_log').insert({
        date: todayStr,
        type: 'adjustment',
        channel: 'app',
        message: 'Switched back to gym workout',
        data_context: { action: 'switch_to_gym', reason: 'User requested from app' },
      })
    } catch (err) {
      setSwitchError(`Switch failed: ${err instanceof Error ? err.message : 'unknown error'}`)
      setTimeout(() => setSwitchError(null), 5000)
    } finally {
      setSwitching(false)
    }
  }

  return (
    <div className="space-y-3">

      {/* ═══ 1. COACHING CARD ═══ */}
      <div className={`rounded-2xl border p-5 ${verdictBg}`}>
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className={`text-xl font-bold ${verdictColor}`}>{verdictLabel}</div>
            {isGymDay && todaySessionName && (
              <div className="text-[15px] text-text-primary mt-1">
                {todaySessionName}
                {isAdjusted && <span className="ml-2 text-[11px] px-2 py-0.5 rounded-full bg-accent-yellow/20 text-accent-yellow font-semibold">Adjusted</span>}
              </div>
            )}
          </div>
          <div className="text-[12px] text-text-muted text-right leading-relaxed">
            Week {week} · Block {block}
            <br />RPE {rpeRange}{deload && ' · Deload'}
          </div>
        </div>

        {/* Coaching points */}
        <div className="space-y-2 mt-3">
          {coachingPoints.map((p, i) => (
            <div key={i} className={`text-[14px] leading-snug ${p.color ?? 'text-text-secondary'}`}>
              <span className="mr-1.5">{p.icon}</span>{p.text}
            </div>
          ))}
        </div>

        {/* Garmin proprietary signals as info note */}
        {(bbHigh != null || readiness != null) && cardState === 'green' && (
          <div className="mt-3 text-[12px] text-text-dim flex items-center gap-1.5">
            <Info size={12} />
            Garmin: BB {bbHigh ?? '—'} · Readiness {readiness ?? '—'}
            <span className="text-[10px]">(estimates)</span>
          </div>
        )}

        {/* Action buttons: Home/Gym toggle + Push to Garmin */}
        {isGymDay && todayPlanned?.workout_definition && (todayPlanned.workout_definition.exercises?.length ?? 0) > 0 && (
          <div className="mt-3 flex items-center gap-4">
            {todayIsHome ? (
              <button
                onClick={handleSwitchToGym}
                disabled={switching}
                className="flex items-center gap-1.5 text-[13px] text-text-muted hover:text-text-secondary transition-colors disabled:opacity-50"
              >
                <Dumbbell size={14} />
                {switching ? 'Switching...' : 'Switch back to gym'}
              </button>
            ) : (
              <button
                onClick={() => setShowHomePreview(true)}
                disabled={switching}
                className="flex items-center gap-1.5 text-[13px] text-accent-blue hover:text-accent-blue/80 transition-colors disabled:opacity-50"
              >
                <Home size={14} />
                Train at home
                {countSubstitutions(todayPlanned.workout_definition) > 0 && (
                  <span className="text-[10px] text-text-dim">({countSubstitutions(todayPlanned.workout_definition)} swaps)</span>
                )}
              </button>
            )}
            {todayPlanned.status !== 'pushed' && (
              <button
                onClick={handlePushToGarmin}
                disabled={pushing}
                className="flex items-center gap-1.5 text-[13px] text-accent-green hover:text-accent-green/80 transition-colors disabled:opacity-50"
              >
                <Send size={13} />
                {pushing ? 'Pushing...' : 'Push to Garmin'}
              </button>
            )}
          </div>
        )}
        {switchError && (
          <div className="mt-2 text-[12px] text-accent-red bg-accent-red/10 rounded-lg px-2.5 py-1.5">
            {switchError}
          </div>
        )}
        {pushMsg && (
          <div className={`mt-2 text-[12px] rounded-lg px-2.5 py-1.5 ${
            pushMsg.includes('queued') ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'
          }`}>
            {pushMsg}
          </div>
        )}

        {/* Home workout preview modal */}
        {showHomePreview && (
          <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50" onClick={() => setShowHomePreview(false)}>
            <div className="w-full max-w-lg bg-bg-card rounded-t-2xl p-5 pb-8 max-h-[70vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
              <div className="text-[15px] font-semibold text-text-primary mb-3">Home workout preview</div>
              {homePreviewDiff.length > 0 ? (
                <div className="space-y-2 mb-4">
                  {homePreviewDiff.map((d, i) => (
                    <div key={i} className="text-[12px] bg-bg-primary rounded-lg px-3 py-2">
                      <div className="text-text-dim line-through">{d.gym}</div>
                      <div className="text-accent-blue">{d.home}</div>
                      {d.note && <div className="text-text-dim text-[11px] mt-0.5">{d.note}</div>}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[13px] text-text-muted mb-4">No exercise changes needed — all exercises are home-compatible.</div>
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowHomePreview(false)}
                  className="flex-1 text-[13px] text-text-muted py-2.5 rounded-xl border border-border-subtle"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => { setShowHomePreview(false); await handleSwitchToHome() }}
                  disabled={switching}
                  className="flex-1 text-[13px] text-white bg-accent-blue py-2.5 rounded-xl font-semibold disabled:opacity-50"
                >
                  {switching ? 'Switching...' : 'Switch to home'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Expandable workout */}
        {isAdjusted && !todayPlanned && todayAdjustment && (
          <div className="mt-3 text-[13px] text-accent-yellow">
            Coach: {todayAdjustment.message}
          </div>
        )}

        {/* Coaching rationale — collapsible "Why?" */}
        {todayRationale && (
          <div className="mt-2">
            <button
              onClick={() => setShowRationale(!showRationale)}
              className="flex items-center gap-1 text-[11px] text-text-muted hover:text-text-secondary transition-colors"
            >
              <Info size={11} />
              {showRationale ? 'Hide rationale' : 'Why?'}
            </button>
            {showRationale && (
              <div className="mt-1.5 text-[11px] text-text-muted bg-bg-primary/50 rounded-lg px-2.5 py-2 space-y-1">
                {todayRationale.rule && (
                  <div><span className="text-text-dim">Rule:</span> {todayRationale.rule.replace(/[._]/g, ' ')}</div>
                )}
                {todayRationale.inputs && (
                  <div><span className="text-text-dim">Inputs:</span> {
                    Object.entries(todayRationale.inputs)
                      .filter(([, v]) => v != null)
                      .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`)
                      .join(' · ')
                  }</div>
                )}
                {todayRationale.kb_refs && todayRationale.kb_refs.length > 0 && (
                  <div><span className="text-text-dim">Ref:</span> {todayRationale.kb_refs.join(', ')}</div>
                )}
              </div>
            )}
          </div>
        )}

        {isGymDay && todayPlanned?.workout_definition && (
          <div className="mt-4 pt-3 border-t border-text-primary/5">
            {isAdjusted && (todayPlanned?.adjustment_reason || todayAdjustment?.message) && (
              <div className="text-[12px] text-accent-yellow mb-2">
                Coach: {todayPlanned?.adjustment_reason ?? todayAdjustment?.message}
              </div>
            )}
            <button
              onClick={() => setShowExercises(!showExercises)}
              className="flex items-center gap-1.5 text-[13px] text-text-muted hover:text-text-secondary transition-colors"
            >
              <ChevronDown size={14} className={`transition-transform ${showExercises ? 'rotate-180' : ''}`} />
              {showExercises ? 'Hide workout' : 'Show workout'}
            </button>
            {showExercises && (
              <div className="mt-3">
                {todayPlanned.workout_definition.warmup?.length > 0 && (
                  <div className="mb-3 pb-2 border-b border-text-primary/5">
                    <div className="text-[11px] text-text-dim uppercase tracking-[0.06em] font-semibold mb-2">Warm-up</div>
                    {todayPlanned.workout_definition.warmup.map((wu: WarmupExercise, i: number) => (
                      <div key={i} className="flex items-center justify-between text-[12px] py-0.5">
                        <span className="text-text-muted italic">{wu.name}</span>
                        <span className="text-text-dim font-mono text-[11px]">{wu.duration_s ? `${wu.duration_s}s` : `${wu.reps} reps`}</span>
                      </div>
                    ))}
                  </div>
                )}
                {todayIsHome && (
                  <div className="flex items-center gap-1.5 text-[12px] text-accent-blue mb-2">
                    <Home size={12} />
                    Home workout — exercises adapted for home equipment
                  </div>
                )}
                <table className="w-full text-[14px]">
                  <tbody>
                    {(todayPlanned.workout_definition?.exercises ?? []).map((ex: PlannedExercise, i: number) => (
                      <tr key={i} className="border-b border-text-primary/5 last:border-0">
                        <td className="py-2">
                          <div className="text-text-primary">{ex.name}</div>
                          {todayIsHome && ex.note && (
                            <div className="text-[11px] text-text-dim mt-0.5">{ex.note}</div>
                          )}
                        </td>
                        <td className="py-2 text-right text-text-secondary font-mono text-[13px] whitespace-nowrap align-top">
                          {ex.sets}×{ex.reps}
                        </td>
                        <td className="py-2 text-right text-text-primary font-mono text-[13px] w-20 font-semibold align-top">
                          {ex.weight_kg != null ? `${ex.weight_kg}kg` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="text-[12px] text-text-muted mt-2">
                  ~{todayPlanned.workout_definition.estimated_duration_minutes ?? (deload ? 30 : 50)} min
                  {' · '}RPE {todayPlanned.workout_definition.rpe_range?.join('-') ?? '6-7'}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ 2. WELLNESS CHECK-IN ═══ */}
      <WellnessInput
        todayWellness={todayWellness}
        onSubmit={() => setWellnessRefresh(r => r + 1)}
      />

      {/* ═══ 3. RECOVERY SIGNALS — Tiered layout ═══ */}
      <div className="grid grid-cols-2 gap-3">
        {/* HRV */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">HRV</span>
            <span className={`text-[11px] font-semibold ${hrvInfo.color}`}>{hrvInfo.label}</span>
          </div>
          <div className={`data-value-md font-data ${hrvInfo.color}`}>
            {hrvVal ?? '—'}<span className="text-[13px] font-normal text-text-muted ml-1">ms</span>
          </div>
          {hrvWeeklyAvg != null && hrvVal != null && (
            <div className="text-[12px] text-text-muted mt-1.5">
              {hrvVal >= hrvWeeklyAvg ? '↑ above' : '↓ below'} {hrvWeeklyAvg}ms avg
            </div>
          )}
        </div>

        {/* Sleep */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Sleep</span>
            {sleepBelowCount > 0 && (
              <span className="text-[11px] text-accent-red font-semibold">{sleepBelowCount}×&lt;6h</span>
            )}
          </div>
          <div className={`data-value-md font-data ${metricColor(sleepHours, 7, 6)}`}>
            {sleepHours ?? '—'}<span className="text-[13px] font-normal text-text-muted ml-1">h</span>
          </div>
          <div className="text-[12px] text-text-muted mt-1.5">Target 7-8h</div>
        </div>
      </div>

      {/* Secondary signals (Garmin estimates — visually demoted) */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3 opacity-60">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-[0.06em] font-semibold">Body Battery</span>
            <span className="text-[9px] text-text-dim">(est.)</span>
          </div>
          <div className={`text-lg font-bold font-data ${metricColor(bbHigh, 60, 30)}`}>
            {bbHigh ?? '—'}
          </div>
          <div className="text-[11px] text-text-dim">
            {todayMetrics?.body_battery_lowest != null
              ? `Low ${todayMetrics.body_battery_lowest} · Range ${(bbHigh ?? 0) - todayMetrics.body_battery_lowest}`
              : ''}
          </div>
        </div>

        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3 opacity-60">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-[0.06em] font-semibold">Readiness</span>
            <span className="text-[9px] text-text-dim">(est.)</span>
          </div>
          <div className={`text-lg font-bold font-data ${metricColor(readiness, 60, 40)}`}>
            {readiness ?? '—'}
          </div>
          <div className="text-[11px] text-text-dim">
            {readiness != null && readiness >= 60 ? 'Ready' : readiness != null && readiness >= 40 ? 'Borderline' : readiness != null ? 'Low' : ''}
          </div>
        </div>
      </div>

      {/* ═══ 4. WEEKLY LOAD ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
        <div className="flex items-center gap-2 mb-3">
          <ActivityIcon size={15} className="text-accent-purple" />
          <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Weekly Load</span>
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-[14px]">
          <div>
            <span className="text-text-primary font-semibold">{formatDuration(thisWeekLoad.gym)}</span>
            <span className="text-text-muted text-[12px] ml-1">gym</span>
          </div>
          <div>
            <span className="text-text-primary font-semibold">{formatDuration(thisWeekLoad.mountain)}</span>
            <span className="text-text-muted text-[12px] ml-1">mountain</span>
          </div>
          <div>
            <span className="text-text-primary font-semibold">{Math.round(thisWeekElev).toLocaleString()}m</span>
            <span className="text-text-muted text-[12px] ml-1">elev</span>
          </div>
          {loadChangePct != null && (
            <span className={`text-[12px] font-semibold ${
              Math.abs(loadChangePct) < 15 ? 'text-accent-green' : Math.abs(loadChangePct) < 25 ? 'text-accent-yellow' : 'text-accent-red'
            }`}>
              {loadChangePct >= 0 ? '+' : ''}{loadChangePct}% vs last wk
            </span>
          )}
        </div>
        {prevTrainingLoad > 0 && (
          <div className="text-[12px] text-text-muted mt-1.5">
            Last week: {formatDuration(lastWeekLoad.gym)} gym · {formatDuration(lastWeekLoad.mountain)} mountain · {Math.round(lastWeekElev).toLocaleString()}m
          </div>
        )}
      </div>

      {/* ═══ 5. RESTING HR ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Heart size={15} className="text-heart" />
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Resting HR</span>
            <span className="text-[15px] font-bold font-data text-text-primary">
              {todayMetrics?.resting_hr ?? '--'} bpm
            </span>
            {rhrTrend && (
              <span className={`text-[11px] font-medium ${rhrElevated ? 'text-accent-yellow' : 'text-text-muted'}`}>
                {rhrTrend}
              </span>
            )}
          </div>
          {rhr7dAvg != null && (
            <span className="text-[11px] text-text-muted">
              7d avg: {Math.round(rhr7dAvg)}bpm
            </span>
          )}
        </div>
      </div>

      {/* ═══ 6. LATEST ACTIVITY ═══ */}
      {lastActivity && (
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
          <div className="flex items-center gap-2 mb-2">
            {(lastActivity.elevation_gain ?? 0) > 0
              ? <TrendingUp size={15} className="text-mountain" />
              : <ActivityIcon size={15} className="text-gym" />
            }
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Latest Activity</span>
          </div>
          <div className="text-[16px] font-bold text-text-primary leading-tight">
            {lastActivity.activity_name || formatActivityType(lastActivity.activity_type)}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[13px] text-text-secondary">
            {lastActivity.duration_seconds && (
              <span className="flex items-center gap-1.5"><Clock size={12} className="text-text-muted" />{formatDuration(lastActivity.duration_seconds)}</span>
            )}
            {(lastActivity.elevation_gain ?? 0) > 0 && (
              <span className="flex items-center gap-1.5"><ArrowUpRight size={12} className="text-mountain" />{Math.round(lastActivity.elevation_gain!)}m</span>
            )}
            {lastActivity.calories != null && (
              <span className="flex items-center gap-1.5"><Flame size={12} className="text-accent-orange" />{lastActivity.calories} kcal</span>
            )}
            {lastActivity.avg_hr != null && (
              <span className="flex items-center gap-1.5"><Heart size={12} className="text-heart" />{lastActivity.avg_hr} bpm</span>
            )}
          </div>
        </div>
      )}

      {/* ═══ 7. POST-SESSION LOG (RPE + Exercise Feel + Wellness combined) ═══ */}
      {lastActivity && lastActivity.activity_type === 'strength_training' && todayPlanned?.workout_definition?.exercises && (
        <PostSessionLog
          activity={lastActivity}
          exercises={todayPlanned.workout_definition.exercises}
          todayWellness={todayWellness}
          onComplete={() => setWellnessRefresh(r => r + 1)}
        />
      )}

      {/* ═══ 7c. WEEKLY REFLECTION (Sundays only) ═══ */}
      {new Date().getDay() === 0 && <WeeklyReflection />}

      {/* ═══ 8. PROGRAM PROGRESS ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">
            {programEnded ? 'Program Complete' : `${block === 1 ? 'Base Rebuild' : 'Progression'} · Block ${block}`}
          </span>
          <span className="text-[15px] font-bold font-data text-accent-green">
            {programEnded ? '8/8' : <>{week}<span className="text-text-muted font-normal">/8</span></>}
          </span>
        </div>
        <div className="w-full bg-bg-elevated rounded-full h-1.5">
          <div
            className="bg-accent-green rounded-full h-1.5 transition-all duration-500"
            style={{ width: `${programEnded ? 100 : (week / 8) * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}
