import { useMemo, useState, useCallback } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import {
  useActivities, useSleep, useBodyComposition, useHRV, useDailyMetrics,
  usePlannedWorkouts, useTrainingSessions, useTrainingSets, useActivityDetails,
  rescheduleWorkout, markWorkoutCompleted, logSrpe,
} from '../hooks/useSupabase'
import type {
  Activity, SleepRow, BodyComposition, HRVRow, DailyMetrics,
  PlannedWorkout, TrainingSession,
} from '../lib/types'
import { startOfWeek, endOfWeek, format, isWithinInterval, addDays, isSameDay, isBefore, parseISO } from 'date-fns'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts'
import { formatDuration, formatActivityType } from '../lib/format'
import { MOUNTAIN_ACTIVITY_TYPES, SELF_POWERED_MOUNTAIN_TYPES, CYCLING_ACTIVITY_TYPES } from '../lib/constants'
import { getProgramWeek, isDeloadWeek, getWeekSchedule, SESSION_NAMES } from '../lib/program'
import { sleepBarColor } from '../lib/colors'
import { ScheduleGrid, RescheduleModal, FlyingSection } from './week'
import type { DayCell } from './week'

export default function WeekView() {
  const activitiesHook = useActivities(14)
  const allActivitiesHook = useActivities(180) // season-wide for mountain comparison
  const sleepHook = useSleep(14)
  const bodyCompHook = useBodyComposition(30)
  const hrvHook = useHRV(14)
  const metricsHook = useDailyMetrics(14)
  const plannedHook = usePlannedWorkouts()
  const sessionsHook = useTrainingSessions(14)

  const [activitiesExpanded, setActivitiesExpanded] = useState(false)
  const [rescheduleSource, setRescheduleSource] = useState<DayCell | null>(null)
  const [rescheduleTarget, setRescheduleTarget] = useState<string | null>(null)
  const [rescheduleLoading, setRescheduleLoading] = useState(false)
  const [markDoneLoading, setMarkDoneLoading] = useState<number | null>(null)
  const [logSrpeLoading, setLogSrpeLoading] = useState<string | null>(null)

  const loading = activitiesHook.loading || sleepHook.loading || bodyCompHook.loading
    || hrvHook.loading || metricsHook.loading || plannedHook.loading
  const error = activitiesHook.error || sleepHook.error || bodyCompHook.error
    || hrvHook.error || metricsHook.error || plannedHook.error

  const now = new Date()
  const todayStr = now.toDateString()
  const today = useMemo(() => { const t = new Date(); t.setHours(0, 0, 0, 0); return t }, [])
  const weekStart = useMemo(() => startOfWeek(now, { weekStartsOn: 1 }), [todayStr]) // eslint-disable-line react-hooks/exhaustive-deps
  const weekEnd = useMemo(() => endOfWeek(now, { weekStartsOn: 1 }), [todayStr]) // eslint-disable-line react-hooks/exhaustive-deps
  const prevWeekStart = useMemo(() => addDays(weekStart, -7), [weekStart])
  const prevWeekEnd = useMemo(() => addDays(weekEnd, -7), [weekEnd])
  const { block, week, ended } = useMemo(() => getProgramWeek(now), [todayStr]) // eslint-disable-line react-hooks/exhaustive-deps
  const deload = isDeloadWeek(week)

  const weekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: Activity) => isWithinInterval(new Date(a.date), { start: weekStart, end: weekEnd }))
  }, [activitiesHook.data, weekStart, weekEnd])

  const prevWeekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: Activity) => isWithinInterval(new Date(a.date), { start: prevWeekStart, end: prevWeekEnd }))
  }, [activitiesHook.data, prevWeekStart, prevWeekEnd])

  const weekPlanned = useMemo(() => {
    if (!plannedHook.data) return []
    return plannedHook.data.filter((p: PlannedWorkout) => isWithinInterval(parseISO(p.scheduled_date), { start: weekStart, end: weekEnd }))
  }, [plannedHook.data, weekStart, weekEnd])

  const weekTemplate = useMemo(() => getWeekSchedule(week), [week])

  const dayCells: DayCell[] = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const date = addDays(weekStart, i)
      const dateStr = format(date, 'yyyy-MM-dd')
      const planned = weekPlanned.find((p) => p.scheduled_date === dateStr) ?? null
      const templateDay = weekTemplate.days[i]
      const templateSession = templateDay?.session ? SESSION_NAMES[templateDay.session] : null
      const dayActivities = weekActivities.filter((a) => a.date === dateStr)
      const isToday = isSameDay(date, today)
      const isPast = isBefore(date, today) && !isToday
      const movedAway = (plannedHook.data ?? []).some((p) => p.adjustment_reason?.includes(`from ${dateStr}`))
      const mountainAct = dayActivities.find((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
      const cyclingAct = dayActivities.find((a) => CYCLING_ACTIVITY_TYPES.has(a.activity_type))

      let status: DayCell['status']
      let displayLabel: string | null = null
      if (mountainAct) {
        status = 'mountain'
        displayLabel = mountainAct.activity_name || formatActivityType(mountainAct.activity_type)
      } else if (cyclingAct && !planned) {
        status = 'cycling'
        displayLabel = cyclingAct.activity_name || formatActivityType(cyclingAct.activity_type)
      } else if (planned) {
        if (planned.status === 'completed') status = 'completed'
        else if (planned.status === 'adjusted') status = 'adjusted'
        else if (planned.status === 'rescheduled') status = 'rescheduled'
        else if (planned.status === 'skipped') status = 'skipped'
        else if (isPast) status = 'missed'
        else if (isToday) status = 'today'
        else status = 'planned'
      } else if (dayActivities.some((a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type))) {
        status = 'mountain'
      } else if (movedAway) {
        status = 'rest'; displayLabel = 'Moved'
      } else if (templateDay?.dayType === 'rest') {
        status = 'rest'
      } else if (isToday) {
        status = 'today'
      } else if (templateSession && isPast) {
        status = 'missed'
      } else if (templateSession) {
        status = 'planned'
      } else {
        status = 'rest'
      }
      return { date, dateStr, label: format(date, 'EEE'), isToday, planned, templateSession, templateDayType: templateDay?.dayType ?? null, activities: dayActivities, status, displayLabel }
    })
  }, [weekStart, weekPlanned, weekTemplate, weekActivities, today, plannedHook.data])

  const canReschedule = (cell: DayCell) => cell.planned != null && ['planned', 'today', 'adjusted', 'rescheduled', 'missed'].includes(cell.status)
  const canMarkDone = (cell: DayCell) => cell.planned != null && ['planned', 'today', 'adjusted', 'pushed', 'rescheduled', 'missed'].includes(cell.status)

  const handleMarkDone = useCallback(async (cell: DayCell, srpe: number) => {
    if (!cell.planned) return
    setMarkDoneLoading(cell.planned.id)
    try {
      await markWorkoutCompleted(cell.planned.id, srpe)
      plannedHook.refetch?.()
    } catch (err) { console.error('Mark done failed:', err) }
    finally { setMarkDoneLoading(null) }
  }, [plannedHook])

  const handleLogSrpe = useCallback(async (cell: DayCell, srpe: number) => {
    setLogSrpeLoading(cell.dateStr)
    try {
      await logSrpe(cell.dateStr, cell.planned?.session_name ?? null, srpe)
      sessionsHook.refetch?.()
    } catch (err) { console.error('Log sRPE failed:', err) }
    finally { setLogSrpeLoading(null) }
  }, [sessionsHook])

  const handleRescheduleConfirm = useCallback(async () => {
    if (!rescheduleSource?.planned || !rescheduleTarget) return
    setRescheduleLoading(true)
    try {
      const targetPlanned = weekPlanned.find((p) => p.scheduled_date === rescheduleTarget && p.status !== 'skipped' && p.status !== 'completed') ?? undefined
      await rescheduleWorkout(rescheduleSource.planned.id, rescheduleTarget, targetPlanned)
      plannedHook.refetch?.()
    } catch (err) { console.error('Reschedule failed:', err) }
    finally { setRescheduleLoading(false); setRescheduleSource(null); setRescheduleTarget(null) }
  }, [rescheduleSource, rescheduleTarget, weekPlanned, plannedHook])

  // ─── Compliance ───
  const compliance = useMemo(() => {
    const isPastOrToday = (d: DayCell) => !isBefore(today, d.date)
    const done = dayCells.filter((d) => d.status === 'completed' || d.status === 'mountain' || (['adjusted', 'rescheduled'].includes(d.status) && isPastOrToday(d) && d.dateStr !== format(today, 'yyyy-MM-dd'))).length
    const planned = dayCells.filter((d) => ['planned', 'today', 'adjusted', 'rescheduled'].includes(d.status) && d.dateStr >= format(today, 'yyyy-MM-dd') && d.planned != null).length
    const missed = dayCells.filter((d) => d.status === 'missed').length
    const scheduled = done + planned + missed
    const lastAdjustment = weekPlanned.filter((p) => p.adjustment_reason).sort((a, b) => b.scheduled_date.localeCompare(a.scheduled_date))[0]
    return { completed: done, missed, scheduled, lastAdjustment, planned }
  }, [dayCells, weekPlanned, today])

  // ─── Sessions for sRPE lookup ───
  const weekSessions = useMemo(() => {
    if (!sessionsHook.data) return []
    return sessionsHook.data.filter((s: TrainingSession) => isWithinInterval(parseISO(s.date), { start: weekStart, end: weekEnd }))
  }, [sessionsHook.data, weekStart, weekEnd])

  // ─── Training sets for actual vs planned comparison ───
  const weekSessionIds = useMemo(() => weekSessions.map((s) => s.id), [weekSessions])
  const setsHook = useTrainingSets(weekSessionIds)

  // ─── Activity details for mountain deep dive ───
  const mountainActivityIds = useMemo(() => {
    return weekActivities
      .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type) && a.garmin_activity_id != null)
      .map((a) => a.garmin_activity_id!)
  }, [weekActivities])
  const activityDetailsHook = useActivityDetails(mountainActivityIds)

  // All mountain activities for historical comparison
  const allMountainActivities = useMemo(() => {
    if (!allActivitiesHook.data) return []
    return allActivitiesHook.data.filter((a: Activity) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
  }, [allActivitiesHook.data])

  // ─── Load ───
  const isTrainingActivity = (a: Activity) => a.activity_type === 'strength_training' || SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type) || CYCLING_ACTIVITY_TYPES.has(a.activity_type)
  const strengthVolume = useMemo(() => (sessionsHook.data ?? []).filter((s: TrainingSession) => isWithinInterval(parseISO(s.date), { start: weekStart, end: weekEnd })).reduce((sum: number, s: TrainingSession) => sum + (s.total_volume_kg ?? 0), 0), [sessionsHook.data, weekStart, weekEnd])
  const prevStrengthVolume = useMemo(() => (sessionsHook.data ?? []).filter((s: TrainingSession) => isWithinInterval(parseISO(s.date), { start: prevWeekStart, end: prevWeekEnd })).reduce((sum: number, s: TrainingSession) => sum + (s.total_volume_kg ?? 0), 0), [sessionsHook.data, prevWeekStart, prevWeekEnd])
  const totalElevation = useMemo(() => weekActivities.filter((a: Activity) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type)).reduce((sum: number, a: Activity) => sum + (a.elevation_gain || 0), 0), [weekActivities])
  const prevElevation = useMemo(() => prevWeekActivities.filter((a: Activity) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type)).reduce((sum: number, a: Activity) => sum + (a.elevation_gain || 0), 0), [prevWeekActivities])
  const trainingHours = useMemo(() => weekActivities.filter(isTrainingActivity).reduce((s: number, a: Activity) => s + (a.duration_seconds ?? 0), 0) / 3600, [weekActivities])
  const prevTrainingHours = useMemo(() => prevWeekActivities.filter(isTrainingActivity).reduce((s: number, a: Activity) => s + (a.duration_seconds ?? 0), 0) / 3600, [prevWeekActivities])

  const pctChange = (curr: number, prev: number) => prev === 0 ? null : Math.round(((curr - prev) / prev) * 100)
  const deltaColor = (pct: number | null) => pct == null ? 'text-text-muted' : Math.abs(pct) > 15 ? 'text-accent-yellow' : 'text-accent-green'

  // ─── Recovery ───
  const weekSleep = useMemo(() => {
    if (!sleepHook.data) return { avg: null as number | null, count: 0 }
    const valid = sleepHook.data.filter((s: SleepRow) => isWithinInterval(parseISO(s.date), { start: weekStart, end: weekEnd }) && s.total_sleep_seconds != null)
    if (valid.length === 0) return { avg: null, count: 0 }
    return { avg: Number((valid.reduce((sum: number, s: SleepRow) => sum + (s.total_sleep_seconds! / 3600), 0) / valid.length).toFixed(1)), count: valid.length }
  }, [sleepHook.data, weekStart, weekEnd])

  const weekHRV = useMemo(() => {
    if (!hrvHook.data) return { avg: null as number | null, baseline: null as number | null, status: null as string | null }
    const valid = hrvHook.data.filter((h: HRVRow) => isWithinInterval(parseISO(h.date), { start: weekStart, end: weekEnd }) && h.last_night_avg != null)
    if (valid.length === 0) return { avg: null, baseline: null, status: hrvHook.data[0]?.status ?? null }
    return { avg: Math.round(valid.reduce((sum: number, h: HRVRow) => sum + h.last_night_avg!, 0) / valid.length), baseline: valid[0]?.weekly_avg ? Math.round(valid[0].weekly_avg) : null, status: valid[0]?.status ?? null }
  }, [hrvHook.data, weekStart, weekEnd])

  const rhrTrend = useMemo(() => {
    if (!metricsHook.data) return null
    const valid = metricsHook.data.filter((d: DailyMetrics) => d.resting_hr != null)
    if (valid.length < 4) return null
    const recent = valid.slice(0, 3).reduce((s: number, d: DailyMetrics) => s + d.resting_hr!, 0) / 3
    const prior = valid.slice(3, 10).reduce((s: number, d: DailyMetrics) => s + d.resting_hr!, 0) / Math.min(7, valid.length - 3)
    return { recent: Math.round(recent), delta: Math.round(recent - prior) }
  }, [metricsHook.data])

  const sleepBars = useMemo(() => {
    if (!sleepHook.data) return []
    return sleepHook.data.slice().reverse().map((d: SleepRow) => ({
      date: format(new Date(d.date), 'MM/dd'),
      hours: Number((d.total_sleep_seconds ? d.total_sleep_seconds / 3600 : 0).toFixed(1)),
    }))
  }, [sleepHook.data])

  const bodyComp = useMemo(() => {
    const withWeight = (bodyCompHook.data ?? []).filter((d: BodyComposition) => d.weight_kg != null)
    return withWeight[0] ? { weight: withWeight[0].weight_kg, date: withWeight[0].date } : null
  }, [bodyCompHook.data])

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const hasPlannedWorkouts = weekPlanned.length > 0
  const elevPct = pctChange(totalElevation, prevElevation)
  const volumePct = pctChange(strengthVolume, prevStrengthVolume)
  const hoursPct = pctChange(trainingHours, prevTrainingHours)

  return (
    <div className="space-y-3 pb-8">
      {/* Week header */}
      <div className="px-1">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-[590] text-text-primary">
            Week {week} <span className="text-text-muted text-sm font-normal">of 8</span>
          </h2>
          <div className="flex items-center gap-2">
            {deload && <span className="text-[10px] uppercase tracking-wider font-bold text-accent-yellow bg-accent-yellow/15 px-2 py-0.5 rounded">Deload</span>}
            <span className="text-[10px] uppercase tracking-wider font-semibold text-text-muted">Block {block}</span>
          </div>
        </div>
        <p className="text-[13px] text-text-muted mt-0.5">{format(weekStart, 'MMM d')} – {format(weekEnd, 'MMM d, yyyy')}</p>
        {ended && <div className="mt-2 text-[12px] text-accent-green font-semibold">Program complete — time for an Opus session to plan the next block</div>}
      </div>

      {/* Compliance */}
      {compliance.scheduled > 0 && (
        <Card glow={compliance.missed > 0 ? 'red' : compliance.planned > 0 ? 'yellow' : 'green'}>
          <div className="flex items-baseline justify-between mb-2">
            <div>
              <span className="text-2xl font-bold text-text-primary font-data">{compliance.completed}</span>
              <span className="text-sm text-text-muted ml-1">/ {compliance.scheduled} sessions</span>
            </div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Compliance</div>
          </div>
          <div className="flex gap-3 text-[12px]">
            {compliance.completed > 0 && <span className="text-accent-green">✓ {compliance.completed} done</span>}
            {compliance.planned > 0 && <span className="text-accent-blue">→ {compliance.planned} planned</span>}
            {compliance.missed > 0 && <span className="text-accent-red">! {compliance.missed} missed</span>}
          </div>
          {compliance.lastAdjustment?.adjustment_reason && (
            <div className="mt-2 pt-2 border-t border-border-subtle text-[11px] text-text-muted">
              <span className="text-text-secondary font-medium">{format(parseISO(compliance.lastAdjustment.scheduled_date), 'EEE')}:</span>{' '}
              {compliance.lastAdjustment.adjustment_reason}
            </div>
          )}
        </Card>
      )}

      {/* Schedule grid */}
      <ScheduleGrid dayCells={dayCells} hasPlannedWorkouts={hasPlannedWorkouts} weekSessions={weekSessions} trainingSets={setsHook.data ?? []} activityDetails={activityDetailsHook.data ?? []} allMountainActivities={allMountainActivities} canReschedule={canReschedule} onReschedule={setRescheduleSource} canMarkDone={canMarkDone} onMarkDone={handleMarkDone} markDoneLoading={markDoneLoading} onLogSrpe={handleLogSrpe} logSrpeLoading={logSrpeLoading} />

      {/* Load */}
      <Card title="Load this week">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Strength</div>
            <div className="text-lg font-bold text-text-primary font-data mt-1">{Math.round(strengthVolume).toLocaleString()}<span className="text-[11px] text-text-muted ml-1 font-normal">kg</span></div>
            {volumePct != null && <div className={`text-[11px] font-semibold ${deltaColor(volumePct)}`}>{volumePct >= 0 ? '↑' : '↓'} {volumePct >= 0 ? '+' : ''}{volumePct}%</div>}
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Elevation</div>
            <div className="text-lg font-bold text-text-primary font-data mt-1">{Math.round(totalElevation)}<span className="text-[11px] text-text-muted ml-1 font-normal">m</span></div>
            {elevPct != null && <div className={`text-[11px] font-semibold ${deltaColor(elevPct)}`}>{elevPct >= 0 ? '↑' : '↓'} {elevPct >= 0 ? '+' : ''}{elevPct}%</div>}
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Hours</div>
            <div className="text-lg font-bold text-text-primary font-data mt-1">{trainingHours.toFixed(1)}<span className="text-[11px] text-text-muted ml-1 font-normal">h</span></div>
            {hoursPct != null && <div className={`text-[11px] font-semibold ${deltaColor(hoursPct)}`}>{hoursPct >= 0 ? '↑' : '↓'} {hoursPct >= 0 ? '+' : ''}{hoursPct}%</div>}
          </div>
        </div>
        <div className="text-[10px] text-text-dim mt-3">vs previous week</div>
      </Card>

      {/* Recovery snapshot */}
      <Card title="Recovery snapshot">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Sleep avg</div>
            <div className={`text-lg font-bold font-data mt-1 ${weekSleep.avg == null ? 'text-text-muted' : weekSleep.avg >= 7 ? 'text-accent-green' : weekSleep.avg >= 6 ? 'text-accent-yellow' : 'text-accent-red'}`}>
              {weekSleep.avg != null ? `${weekSleep.avg}h` : '—'}
            </div>
            <div className="text-[10px] text-text-dim mt-0.5">{weekSleep.count} nights</div>
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">HRV</div>
            <div className={`text-lg font-bold font-data mt-1 ${weekHRV.status?.toUpperCase() === 'BALANCED' ? 'text-accent-green' : weekHRV.status?.toUpperCase() === 'UNBALANCED' ? 'text-accent-yellow' : weekHRV.status?.toUpperCase() === 'LOW' ? 'text-accent-red' : 'text-text-muted'}`}>
              {weekHRV.avg != null ? `${weekHRV.avg}` : '—'}<span className="text-[11px] text-text-muted ml-1 font-normal">ms</span>
            </div>
            <div className="text-[10px] text-text-dim mt-0.5">{weekHRV.baseline != null ? `baseline ${weekHRV.baseline}` : weekHRV.status ?? '—'}</div>
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">RHR</div>
            <div className="text-lg font-bold font-data mt-1 text-text-primary">{rhrTrend?.recent ?? '—'}<span className="text-[11px] text-text-muted ml-1 font-normal">bpm</span></div>
            <div className={`text-[10px] mt-0.5 ${rhrTrend == null ? 'text-text-dim' : rhrTrend.delta > 2 ? 'text-accent-yellow' : rhrTrend.delta < -2 ? 'text-accent-green' : 'text-text-dim'}`}>
              {rhrTrend == null ? '—' : rhrTrend.delta > 2 ? `↑ +${rhrTrend.delta} vs 7d` : rhrTrend.delta < -2 ? `↓ ${rhrTrend.delta} vs 7d` : 'stable'}
            </div>
          </div>
        </div>
      </Card>

      {/* Sleep trend */}
      <Card title="Sleep Trend (14d)" subtitle="Total duration is the reliable number; stage breakdown is approximate.">
        {sleepBars.length > 0 ? (
          <div className="bg-bg-inset rounded-xl p-2">
            <ResponsiveContainer width="100%" height={130}>
              <BarChart data={sleepBars} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6a6a82' }} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 10]} tick={{ fontSize: 10, fill: '#6a6a82' }} tickLine={false} axisLine={false} width={35} />
                <Bar dataKey="hours" radius={[3, 3, 0, 0]}>
                  {sleepBars.map((entry, index) => (
                    <Cell key={index} fill={sleepBarColor(entry.hours)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-[14px] text-text-muted">Not enough data</div>
        )}
      </Card>

      {/* Activity log */}
      <button onClick={() => setActivitiesExpanded(!activitiesExpanded)} className="w-full glass-card text-left">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold">All activities this week</div>
            <div className="text-[13px] text-text-secondary mt-0.5">
              {weekActivities.length} activit{weekActivities.length === 1 ? 'y' : 'ies'}
              {bodyComp && ` · ${bodyComp.weight?.toFixed(1)}kg ${format(parseISO(bodyComp.date), 'MMM d')}`}
            </div>
          </div>
          {activitiesExpanded ? <ChevronUp size={16} className="text-text-muted" /> : <ChevronDown size={16} className="text-text-muted" />}
        </div>
        {activitiesExpanded && weekActivities.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border-subtle space-y-0">
            {weekActivities.map((a: Activity, i: number) => (
              <div key={a.garmin_activity_id || i} className="flex items-center justify-between border-b border-border-subtle last:border-0 py-2">
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold text-text-primary truncate">{a.activity_name || formatActivityType(a.activity_type)}</div>
                  <div className="text-[11px] text-text-muted mt-0.5">{format(new Date(a.date), 'EEE, MMM d')}</div>
                </div>
                <div className="flex gap-2 text-[11px] text-text-secondary shrink-0 ml-3 font-medium">
                  <span>{formatDuration(a.duration_seconds)}</span>
                  {CYCLING_ACTIVITY_TYPES.has(a.activity_type) ? (
                    <>
                      {a.distance_meters != null && a.distance_meters > 0 && <span>{(a.distance_meters / 1000).toFixed(1)}km</span>}
                      {a.avg_speed != null && a.avg_speed > 0 && <span>{(a.avg_speed * 3.6).toFixed(1)}km/h</span>}
                    </>
                  ) : (
                    a.elevation_gain != null && a.elevation_gain > 0 && <span className="text-mountain">{Math.round(a.elevation_gain)}m</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </button>

      {/* Flying */}
      <FlyingSection activities={weekActivities} />

      {/* Reschedule modal */}
      {rescheduleSource && (
        <RescheduleModal
          source={rescheduleSource}
          dayCells={dayCells}
          today={today}
          target={rescheduleTarget}
          loading={rescheduleLoading}
          onTargetChange={setRescheduleTarget}
          onConfirm={handleRescheduleConfirm}
          onClose={() => { setRescheduleSource(null); setRescheduleTarget(null) }}
        />
      )}
    </div>
  )
}
