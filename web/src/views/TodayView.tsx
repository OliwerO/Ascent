import { LoadingState, EmptyState } from '../components/LoadingState'
import { WellnessInput } from '../components/WellnessInput'
import { useDailySummary, useHRV, useDailyMetrics, useActivities, useSubjectiveWellness, usePlannedWorkouts, useCoachingLog, useSleep } from '../hooks/useSupabase'
import { getProgramWeek, isDeloadWeek, getSessionForDate, SESSION_NAMES } from '../lib/program'
import { MOUNTAIN_ACTIVITY_TYPES, SELF_POWERED_MOUNTAIN_TYPES, CYCLING_ACTIVITY_TYPES } from '../lib/activityTypes'
import { computeCoachingState } from '../lib/coachingDecision'
import { isHomeWorkout } from '../lib/homeWorkout'
import { useState, useMemo } from 'react'
import { format } from 'date-fns'
import { HeroGauges, CoachingCard, AfterTraining, SecondaryInfo } from './today'

export default function TodayView() {
  const summary = useDailySummary(7)
  const hrv = useHRV(14)
  const metrics = useDailyMetrics(28)
  const activities = useActivities(28)
  const sleepHook = useSleep(14)
  const wellness = useSubjectiveWellness(30)
  const planned = usePlannedWorkouts()
  const coachingLog = useCoachingLog(7)
  const [, setWellnessRefresh] = useState(0)

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

  // ─── Strain: EPOC-weighted load (training_effect × duration) 7d vs 28d ───
  const { strain7d, strain28d } = useMemo(() => {
    const all = recentActivities
    const now = new Date()
    const daysAgo = (d: number) => { const r = new Date(now); r.setDate(r.getDate() - d); return format(r, 'yyyy-MM-dd') }
    const d7 = daysAgo(7)
    const d28 = daysAgo(28)
    const load = (a: typeof all[0]) => (a.training_effect_aerobic ?? 0) * ((a.duration_seconds ?? 0) / 60)
    const sum7 = all.filter(a => a.date >= d7).reduce((s, a) => s + load(a), 0)
    const sum28 = all.filter(a => a.date >= d28).reduce((s, a) => s + load(a), 0)
    // 28d avg per 7-day window
    const weeks28 = Math.max(1, all.filter(a => a.date >= d28).length > 0 ? (new Date().getTime() - new Date(d28).getTime()) / (7 * 86400000) : 1)
    return { strain7d: Math.round(sum7), strain28d: Math.round(sum28 / weeks28) }
  }, [recentActivities])

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
  const todayMetrics = metrics.data?.[0] ?? null
  const lastActivity = recentActivities[0] ?? null
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const todayWellness = (wellness.data ?? []).find((w) => w.date === todayStr) ?? null

  // ─── Derived values ───
  const sleepHours = today?.total_sleep_seconds
    ? Number((today.total_sleep_seconds / 3600).toFixed(1)) : null
  const { block, week, ended: programEnded } = getProgramWeek(new Date())
  const deload = isDeloadWeek(week)
  const todayPlanned = planned.data?.find((pw) => pw.scheduled_date === todayStr) ?? null

  const todayAdjustment = (coachingLog.data ?? []).find(
    (entry) => entry.date === todayStr &&
      (entry.type === 'adjustment' || entry.type === 'daily_adjustment')
  )
  const adjustedSessionName = todayAdjustment?.data_context?.session_name as string | undefined

  const todayRationale = (coachingLog.data ?? []).find(
    (entry) => entry.date === todayStr && entry.rule != null
  )
  const todaySession = todayPlanned
    ? todayPlanned.workout_definition?.session_label
    : (adjustedSessionName ? null : getSessionForDate(new Date()))
  const isGymDay = todayPlanned != null || todayAdjustment != null || getSessionForDate(new Date()) != null
  const todaySessionName = todayPlanned?.workout_definition?.session_name
    ?? adjustedSessionName
    ?? (todaySession ? SESSION_NAMES[todaySession as keyof typeof SESSION_NAMES] : null)
  const isAdjusted = todayPlanned?.status === 'adjusted' || todayAdjustment != null
  const isRescheduled = todayPlanned?.status === 'rescheduled'
  const bbHigh = todayMetrics?.body_battery_highest ?? null
  const readiness = todayMetrics?.training_readiness_score != null
    ? Math.round(todayMetrics.training_readiness_score) : null

  // ─── HRV context ───
  const hrvVal = todayHRV?.last_night_avg != null ? Math.round(todayHRV.last_night_avg) : null
  const hrvWeeklyAvg = todayHRV?.weekly_avg != null ? Math.round(todayHRV.weekly_avg) : null

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

  // ─── Weekly load ───
  const splitLoad = (acts: typeof thisWeekActivities) => {
    let gym = 0, mountain = 0, resort = 0, cycling = 0
    for (const a of acts) {
      const dur = a.duration_seconds ?? 0
      if (a.activity_type === 'strength_training') gym += dur
      else if (SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type)) mountain += dur
      else if (MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type)) resort += dur
      else if (CYCLING_ACTIVITY_TYPES.has(a.activity_type)) cycling += dur
    }
    return { gym, mountain, resort, cycling }
  }
  const thisWeekLoad = splitLoad(thisWeekActivities)
  const lastWeekLoad = splitLoad(lastWeekActivities)
  const thisWeekElev = thisWeekActivities
    .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
    .reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
  const lastWeekElev = lastWeekActivities
    .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
    .reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
  const trainingLoad = thisWeekLoad.gym + thisWeekLoad.mountain + thisWeekLoad.cycling
  const prevTrainingLoad = lastWeekLoad.gym + lastWeekLoad.mountain + lastWeekLoad.cycling
  const loadChangePct = prevTrainingLoad > 0
    ? Math.round(((trainingLoad - prevTrainingLoad) / prevTrainingLoad) * 100) : null

  // ─── Sleep quality (deep/REM) ───
  const todaySleep = (sleepHook.data ?? []).find((s) => s.date === todayStr) ?? (sleepHook.data ?? [])[0] ?? null
  const deepSleepPct = todaySleep?.deep_sleep_seconds != null && todaySleep?.total_sleep_seconds
    ? (todaySleep.deep_sleep_seconds / todaySleep.total_sleep_seconds) * 100 : null
  const remSleepPct = todaySleep?.rem_sleep_seconds != null && todaySleep?.total_sleep_seconds
    ? (todaySleep.rem_sleep_seconds / todaySleep.total_sleep_seconds) * 100 : null

  // ─── Coaching decision ───
  const decision = computeCoachingState({
    hrvStatus: todayHRV?.status, hrvVal, hrvWeeklyAvg,
    sleepHoursLastNight: sleepHours, sleep7dAvg,
    wellnessComposite: todayWellness?.composite_score ?? null,
    bodyBattery: bbHigh, trainingReadiness: readiness, rhrElevated,
    deepSleepPct,
    remSleepPct,
    poorSleepNights7d: sleepBelowCount,
    mountainDays3d: mountainLoad72h?.days ?? 0,
    isDeload: deload,
    lastSrpe: null, // sRPE lives in training_sessions, not fetched here; CCD handles this
    soreness: todayWellness?.muscle_soreness ?? null,
  })
  const cardState = decision.state
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
  const now = Date.now() // eslint-disable-line react-hooks/purity -- stable within a render
  const daysSinceGym = lastGymSession ? Math.floor((now - new Date(lastGymSession.date).getTime()) / 86400000) : null
  if (isGymDay && todaySession) {
    if (deload) coachingPoints.push({ icon: '📉', text: 'Deload week — same weight, half sets, focus on form' })
    else if (daysSinceGym != null && daysSinceGym > 7) coachingPoints.push({ icon: '💡', text: `${daysSinceGym} days since last gym session — start conservative, RPE 6 max` })
  }
  if (mountainLoad72h && isGymDay) {
    if (mountainLoad72h.category === 'heavy') coachingPoints.push({ icon: '🏔', text: `Heavy mountain load: ${mountainLoad72h.elevation}m / ${mountainLoad72h.hours}h in last 72h — expect reduced performance`, color: 'text-accent-yellow' })
    else if (mountainLoad72h.category === 'moderate') coachingPoints.push({ icon: '🏔', text: `Mountain load: ${mountainLoad72h.elevation}m in last 72h — monitor how warmup feels` })
  }
  if (sleepBelowCount >= 3) coachingPoints.push({ icon: '😴', text: `${sleepBelowCount} nights below 6h this week — sleep is the bottleneck`, color: 'text-accent-yellow' })
  if (!isGymDay) {
    const dayName = new Date().toLocaleDateString('en-US', { weekday: 'long' })
    if (dayName === 'Tuesday') coachingPoints.push({ icon: '🧘', text: 'Mobility day — foam roll, hip flexors, thoracic rotation' })
    else if (dayName === 'Saturday' || dayName === 'Sunday') coachingPoints.push({ icon: '🏔', text: 'Mountain day — your call based on conditions' })
    else coachingPoints.push({ icon: '🔋', text: 'Rest day — recover for the next session' })
  }
  if (!todayWellness && cardState === 'green') coachingPoints.push({ icon: 'ℹ️', text: 'Complete wellness check-in for full assessment', color: 'text-text-muted' })
  if (coachingPoints.length === 0 && isGymDay) coachingPoints.push({ icon: '✅', text: 'All signals green — train as planned' })
  // Recovery tip (max 1, from coaching decision)
  if (decision.recoveryTip) coachingPoints.push({ icon: '💤', text: decision.recoveryTip, color: 'text-text-muted' })

  return (
    <div className="space-y-3">
      {/* Hero gauges: HRV / Sleep / Strain — each tappable for detail */}
      <HeroGauges
        hrvVal={hrvVal}
        hrvWeeklyAvg={hrvWeeklyAvg}
        cardState={cardState}
        sleepHours={sleepHours}
        strain7d={strain7d}
        strain28d={strain28d}
        hrvData={hrv.data ?? []}
        sleepData={sleepHook.data ?? []}
        recentActivities={recentActivities}
      />

      {/* Coaching card with accent strip */}
      <CoachingCard
        cardState={cardState}
        verdictLabel={decision.label}
        isGymDay={isGymDay}
        todaySessionName={todaySessionName ?? null}
        isAdjusted={isAdjusted}
        isRescheduled={isRescheduled}
        block={block}
        week={week}
        rpeRange={rpeRange}
        deload={deload}
        coachingPoints={coachingPoints}
        bbHigh={bbHigh}
        readiness={readiness}
        todayPlanned={todayPlanned}
        todayAdjustment={todayAdjustment ? { message: todayAdjustment.message } : null}
        todayRationale={todayRationale ?? null}
        todayStr={todayStr}
        todayIsHome={isHomeWorkout(todayPlanned?.workout_definition)}
      />

      {/* Before training: wellness check-in */}
      <div className="section-label mt-2">Before training</div>
      <WellnessInput
        todayWellness={todayWellness}
        onSubmit={() => setWellnessRefresh(r => r + 1)}
      />

      {/* After training: RPE, feedback, reflection */}
      <AfterTraining
        lastActivity={lastActivity}
        exercises={todayPlanned?.workout_definition?.exercises ?? null}
        isSunday={new Date().getDay() === 0}
      />

      {/* Collapsible secondary details */}
      <SecondaryInfo
        recovery={{
          hrvVal, hrvWeeklyAvg, hrvStatus: todayHRV?.status,
          sleepHours, sleepBelowCount, bbHigh,
          bbLowest: todayMetrics?.body_battery_lowest ?? null,
          readiness,
        }}
        weeklyLoad={{
          thisWeekLoad, lastWeekLoad,
          thisWeekElev, lastWeekElev,
          loadChangePct, prevTrainingLoad,
        }}
        todayMetrics={todayMetrics}
        rhrTrend={rhrTrend}
        rhr7dAvg={rhr7dAvg}
        rhrElevated={rhrElevated}
        lastActivity={lastActivity}
        programEnded={programEnded}
        block={block}
        week={week}
      />
    </div>
  )
}
