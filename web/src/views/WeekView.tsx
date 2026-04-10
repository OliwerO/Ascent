import { useMemo, useState, useCallback } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import {
  useActivities, useSleep, useBodyComposition, useHRV, useDailyMetrics,
  usePlannedWorkouts, useTrainingSessions, rescheduleWorkout,
} from '../hooks/useSupabase'
import type {
  Activity, SleepRow, BodyComposition, HRVRow, DailyMetrics,
  PlannedWorkout, TrainingSession, PlannedExercise,
} from '../lib/types'
import { pairHikeAndFly, formatAirtime, formatDistance } from '../lib/flying'
import { startOfWeek, endOfWeek, format, isWithinInterval, addDays, isSameDay, isBefore, parseISO } from 'date-fns'
import { Wind, ChevronDown, ChevronUp, ArrowRightLeft } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts'
import { formatDuration, formatActivityType } from '../lib/format'
import { MountainActivityCard } from '../components/MountainActivityCard'
import { MOUNTAIN_ACTIVITY_TYPES, SELF_POWERED_MOUNTAIN_TYPES } from '../lib/activityTypes'
import { getProgramWeek, isDeloadWeek, getWeekSchedule, SESSION_NAMES } from '../lib/program'

function sleepBarColor(hours: number): string {
  if (hours >= 7) return '#4ade80'
  if (hours >= 6) return '#fbbf24'
  return '#f87171'
}

type DayStatus = 'completed' | 'adjusted' | 'skipped' | 'planned' | 'missed' | 'today' | 'rest' | 'mountain'

interface DayCell {
  date: Date
  dateStr: string
  label: string
  isToday: boolean
  planned: PlannedWorkout | null
  templateSession: string | null // fallback name from getWeekSchedule
  templateDayType: 'gym' | 'rest' | 'mobility' | 'mountain' | 'cardio' | 'intervals' | null
  activities: Activity[]
  status: DayStatus
  /** Override label when a real activity replaces the planned session for this day */
  displayLabel: string | null
}

const STATUS_BADGES: Record<DayStatus, { icon: string; label: string; color: string }> = {
  completed: { icon: 'OK', label: 'Done', color: 'text-accent-green' },
  adjusted: { icon: '~', label: 'Adjusted', color: 'text-accent-blue' },
  skipped: { icon: 'X', label: 'Skipped', color: 'text-text-muted' },
  planned: { icon: '...', label: 'Planned', color: 'text-text-secondary' },
  missed: { icon: '!', label: 'Missed', color: 'text-accent-red' },
  today: { icon: '>', label: 'Today', color: 'text-accent-green' },
  rest: { icon: '-', label: 'Rest', color: 'text-text-dim' },
  mountain: { icon: '^', label: 'Mountain', color: 'text-mountain' },
}

export default function WeekView() {
  const activitiesHook = useActivities(14)
  const sleepHook = useSleep(14)
  const bodyCompHook = useBodyComposition(30)
  const hrvHook = useHRV(14)
  const metricsHook = useDailyMetrics(14)
  const plannedHook = usePlannedWorkouts()
  const sessionsHook = useTrainingSessions(14)

  const [activitiesExpanded, setActivitiesExpanded] = useState(false)
  const [expandedDay, setExpandedDay] = useState<string | null>(null)
  const [rescheduleSource, setRescheduleSource] = useState<DayCell | null>(null)
  const [rescheduleLoading, setRescheduleLoading] = useState(false)

  const loading = activitiesHook.loading || sleepHook.loading || bodyCompHook.loading
    || hrvHook.loading || metricsHook.loading || plannedHook.loading
  const error = activitiesHook.error || sleepHook.error || bodyCompHook.error
    || hrvHook.error || metricsHook.error || plannedHook.error

  const now = new Date()
  const today = useMemo(() => {
    const t = new Date()
    t.setHours(0, 0, 0, 0)
    return t
  }, [])
  const weekStart = useMemo(() => startOfWeek(now, { weekStartsOn: 1 }), [now.toDateString()])
  const weekEnd = useMemo(() => endOfWeek(now, { weekStartsOn: 1 }), [now.toDateString()])

  const prevWeekStart = useMemo(() => addDays(weekStart, -7), [weekStart])
  const prevWeekEnd = useMemo(() => addDays(weekEnd, -7), [weekEnd])

  const { block, week, ended } = useMemo(() => getProgramWeek(now), [now.toDateString()])
  const deload = isDeloadWeek(week)

  // ─── Filter activities to weeks ───
  const weekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: Activity) =>
      isWithinInterval(new Date(a.date), { start: weekStart, end: weekEnd })
    )
  }, [activitiesHook.data, weekStart, weekEnd])

  const prevWeekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: Activity) =>
      isWithinInterval(new Date(a.date), { start: prevWeekStart, end: prevWeekEnd })
    )
  }, [activitiesHook.data, prevWeekStart, prevWeekEnd])

  // ─── Filter planned workouts to current week ───
  const weekPlanned = useMemo(() => {
    if (!plannedHook.data) return []
    return plannedHook.data.filter((p: PlannedWorkout) =>
      isWithinInterval(parseISO(p.scheduled_date), { start: weekStart, end: weekEnd })
    )
  }, [plannedHook.data, weekStart, weekEnd])

  // ─── Build 7-day grid ───
  const weekTemplate = useMemo(() => getWeekSchedule(week), [week])

  const dayCells: DayCell[] = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const date = addDays(weekStart, i)
      const dateStr = format(date, 'yyyy-MM-dd')
      const planned = weekPlanned.find((p) => p.scheduled_date === dateStr) ?? null
      const templateDay = weekTemplate.days[i]
      const templateSession = templateDay?.session
        ? SESSION_NAMES[templateDay.session]
        : null
      const dayActivities = weekActivities.filter((a) => a.date === dateStr)
      const isToday = isSameDay(date, today)
      const isPast = isBefore(date, today) && !isToday

      // Reality wins over plan: if a self-powered mountain activity happened
      // this day, surface it regardless of what was planned. The DB will be
      // reconciled by the daily coach_adjust pass; this is the view-time fix.
      const mountainAct = dayActivities.find((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))

      let status: DayStatus
      let displayLabel: string | null = null
      if (mountainAct) {
        status = 'mountain'
        displayLabel = mountainAct.activity_name || formatActivityType(mountainAct.activity_type)
      } else if (planned) {
        if (planned.status === 'completed') status = 'completed'
        else if (planned.status === 'adjusted') status = 'adjusted'
        else if (planned.status === 'skipped') status = 'skipped'
        else if (isPast) status = 'missed'
        else if (isToday) status = 'today'
        else status = 'planned'
      } else if (dayActivities.some((a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type))) {
        // Resort/lift-served mountain — not a self-powered tour, but still mountain context
        status = 'mountain'
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

      return {
        date,
        dateStr,
        label: format(date, 'EEE'),
        isToday,
        planned,
        templateSession,
        templateDayType: templateDay?.dayType ?? null,
        activities: dayActivities,
        status,
        displayLabel,
      }
    })
  }, [weekStart, weekPlanned, weekTemplate, weekActivities, today])

  // ─── Reschedule handler ───
  const canReschedule = (cell: DayCell) =>
    cell.planned && (cell.status === 'planned' || cell.status === 'today' || cell.status === 'adjusted')

  const handleReschedule = useCallback(async (targetDateStr: string) => {
    if (!rescheduleSource?.planned) return
    setRescheduleLoading(true)
    try {
      const targetPlanned = weekPlanned.find((p) => p.scheduled_date === targetDateStr) ?? undefined
      await rescheduleWorkout(rescheduleSource.planned.id, targetDateStr, targetPlanned)
    } catch (err) {
      console.error('Reschedule failed:', err)
    } finally {
      setRescheduleLoading(false)
      setRescheduleSource(null)
    }
  }, [rescheduleSource, weekPlanned])

  // ─── Compliance summary ───
  const compliance = useMemo(() => {
    const completed = dayCells.filter((d) => d.status === 'completed').length
    const adjusted = dayCells.filter((d) => d.status === 'adjusted').length
    const skipped = dayCells.filter((d) => d.status === 'skipped').length
    const missed = dayCells.filter((d) => d.status === 'missed').length
    const scheduled = dayCells.filter((d) => d.planned != null || (d.templateSession != null && d.templateDayType === 'gym')).length
    const lastAdjustment = weekPlanned
      .filter((p) => p.adjustment_reason)
      .sort((a, b) => b.scheduled_date.localeCompare(a.scheduled_date))[0]
    return { completed, adjusted, skipped, missed, scheduled, lastAdjustment }
  }, [dayCells, weekPlanned])

  // ─── Load accumulation ───
  const strengthVolume = useMemo(() => {
    if (!sessionsHook.data) return 0
    return sessionsHook.data
      .filter((s: TrainingSession) =>
        isWithinInterval(parseISO(s.date), { start: weekStart, end: weekEnd }))
      .reduce((sum: number, s: TrainingSession) => sum + (s.total_volume_kg ?? 0), 0)
  }, [sessionsHook.data, weekStart, weekEnd])

  const prevStrengthVolume = useMemo(() => {
    if (!sessionsHook.data) return 0
    return sessionsHook.data
      .filter((s: TrainingSession) =>
        isWithinInterval(parseISO(s.date), { start: prevWeekStart, end: prevWeekEnd }))
      .reduce((sum: number, s: TrainingSession) => sum + (s.total_volume_kg ?? 0), 0)
  }, [sessionsHook.data, prevWeekStart, prevWeekEnd])

  // Elevation and training hours count strength + self-powered mountain only.
  // Resort skiing/snowboarding is recovery context, not training load.
  const isTrainingActivity = (a: Activity) =>
    a.activity_type === 'strength_training' || SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type)

  const totalElevation = useMemo(
    () => weekActivities
      .filter((a: Activity) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
      .reduce((sum: number, a: Activity) => sum + (a.elevation_gain || 0), 0),
    [weekActivities]
  )
  const prevElevation = useMemo(
    () => prevWeekActivities
      .filter((a: Activity) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type))
      .reduce((sum: number, a: Activity) => sum + (a.elevation_gain || 0), 0),
    [prevWeekActivities]
  )

  const trainingHours = useMemo(
    () => weekActivities.filter(isTrainingActivity).reduce((s: number, a: Activity) => s + (a.duration_seconds ?? 0), 0) / 3600,
    [weekActivities]
  )
  const prevTrainingHours = useMemo(
    () => prevWeekActivities.filter(isTrainingActivity).reduce((s: number, a: Activity) => s + (a.duration_seconds ?? 0), 0) / 3600,
    [prevWeekActivities]
  )

  const pctChange = (curr: number, prev: number) => {
    if (prev === 0) return null
    return Math.round(((curr - prev) / prev) * 100)
  }

  const deltaColor = (pct: number | null) => {
    if (pct == null) return 'text-text-muted'
    if (Math.abs(pct) > 15) return 'text-accent-yellow'
    return 'text-accent-green'
  }

  // ─── Recovery snapshot ───
  const weekSleep = useMemo(() => {
    if (!sleepHook.data) return { avg: null as number | null, count: 0 }
    const inWeek = sleepHook.data.filter((s: SleepRow) =>
      isWithinInterval(parseISO(s.date), { start: weekStart, end: weekEnd }))
    const valid = inWeek.filter((s: SleepRow) => s.total_sleep_seconds != null)
    if (valid.length === 0) return { avg: null, count: 0 }
    const avg = valid.reduce((sum: number, s: SleepRow) => sum + (s.total_sleep_seconds! / 3600), 0) / valid.length
    return { avg: Number(avg.toFixed(1)), count: valid.length }
  }, [sleepHook.data, weekStart, weekEnd])

  const weekHRV = useMemo(() => {
    if (!hrvHook.data) return { avg: null as number | null, baseline: null as number | null, status: null as string | null }
    const inWeek = hrvHook.data.filter((h: HRVRow) =>
      isWithinInterval(parseISO(h.date), { start: weekStart, end: weekEnd }))
    const valid = inWeek.filter((h: HRVRow) => h.last_night_avg != null)
    if (valid.length === 0) return { avg: null, baseline: null, status: hrvHook.data[0]?.status ?? null }
    const avg = valid.reduce((sum: number, h: HRVRow) => sum + h.last_night_avg!, 0) / valid.length
    const baseline = valid[0]?.weekly_avg ?? null
    return { avg: Math.round(avg), baseline: baseline ? Math.round(baseline) : null, status: valid[0]?.status ?? null }
  }, [hrvHook.data, weekStart, weekEnd])

  const rhrTrend = useMemo(() => {
    if (!metricsHook.data) return null
    const valid = metricsHook.data.filter((d: DailyMetrics) => d.resting_hr != null)
    if (valid.length < 4) return null
    const recent = valid.slice(0, 3).reduce((s: number, d: DailyMetrics) => s + d.resting_hr!, 0) / 3
    const prior = valid.slice(3, 10).reduce((s: number, d: DailyMetrics) => s + d.resting_hr!, 0) / Math.min(7, valid.length - 3)
    return { recent: Math.round(recent), delta: Math.round(recent - prior) }
  }, [metricsHook.data])

  // ─── Sleep chart (existing) ───
  const sleepBars = useMemo(() => {
    if (!sleepHook.data) return []
    return sleepHook.data
      .slice()
      .reverse()
      .map((d: SleepRow) => {
        const hours = d.total_sleep_seconds ? d.total_sleep_seconds / 3600 : 0
        return {
          date: format(new Date(d.date), 'MM/dd'),
          hours: Number(hours.toFixed(1)),
        }
      })
  }, [sleepHook.data])

  // ─── Body comp (kept compact for activity log section) ───
  const bodyComp = useMemo(() => {
    if (!bodyCompHook.data || bodyCompHook.data.length === 0) return null
    const withWeight = bodyCompHook.data.filter((d: BodyComposition) => d.weight_kg != null)
    const latest = withWeight[0]
    if (!latest) return null
    return {
      weight: latest.weight_kg,
      date: latest.date,
    }
  }, [bodyCompHook.data])

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const hasPlannedWorkouts = weekPlanned.length > 0
  const elevPct = pctChange(totalElevation, prevElevation)
  const volumePct = pctChange(strengthVolume, prevStrengthVolume)
  const hoursPct = pctChange(trainingHours, prevTrainingHours)

  return (
    <div className="space-y-3 pb-8">
      {/* ═══ 1. WEEK HEADER ═══ */}
      <div className="px-1">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-bold text-text-primary">
            Week {week} <span className="text-text-muted text-sm font-normal">of 8</span>
          </h2>
          <div className="flex items-center gap-2">
            {deload && (
              <span className="text-[10px] uppercase tracking-wider font-bold text-accent-yellow bg-accent-yellow/15 px-2 py-0.5 rounded">
                Deload
              </span>
            )}
            <span className="text-[10px] uppercase tracking-wider font-semibold text-text-muted">
              Block {block}
            </span>
          </div>
        </div>
        <p className="text-[13px] text-text-muted mt-0.5">
          {format(weekStart, 'MMM d')} – {format(weekEnd, 'MMM d, yyyy')}
        </p>
        {ended && (
          <div className="mt-2 text-[12px] text-accent-green font-semibold">
            Program complete — time for an Opus session to plan the next block
          </div>
        )}
      </div>

      {/* ═══ 2. COMPLIANCE SUMMARY ═══ */}
      {compliance.scheduled > 0 && (
        <Card glow={compliance.missed > 0 ? 'red' : compliance.adjusted > 0 ? 'yellow' : 'green'}>
          <div className="flex items-baseline justify-between mb-2">
            <div>
              <span className="text-2xl font-bold text-text-primary font-data">
                {compliance.completed + compliance.adjusted}
              </span>
              <span className="text-sm text-text-muted ml-1">
                / {compliance.scheduled} sessions
              </span>
            </div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">
              Compliance
            </div>
          </div>
          <div className="flex gap-3 text-[12px]">
            {compliance.completed > 0 && (
              <span className="text-accent-green">✓ {compliance.completed} done</span>
            )}
            {compliance.adjusted > 0 && (
              <span className="text-accent-blue">~ {compliance.adjusted} adjusted</span>
            )}
            {compliance.skipped > 0 && (
              <span className="text-text-muted">– {compliance.skipped} skipped</span>
            )}
            {compliance.missed > 0 && (
              <span className="text-accent-red">! {compliance.missed} missed</span>
            )}
          </div>
          {compliance.lastAdjustment?.adjustment_reason && (
            <div className="mt-2 pt-2 border-t border-border-subtle text-[11px] text-text-muted">
              <span className="text-text-secondary font-medium">
                {format(parseISO(compliance.lastAdjustment.scheduled_date), 'EEE')}:
              </span>{' '}
              {compliance.lastAdjustment.adjustment_reason}
            </div>
          )}
        </Card>
      )}

      {/* ═══ 3. 7-DAY PLAN GRID ═══ */}
      <Card title="Schedule">
        {!hasPlannedWorkouts && (
          <div className="text-[11px] text-text-dim mb-3 italic">
            Showing template — sessions not yet generated for this week
          </div>
        )}
        <div className="space-y-1.5">
          {dayCells.map((cell) => {
            const badge = STATUS_BADGES[cell.status]
            const hasMountainActivity = cell.status === 'mountain' && cell.activities.length > 0
            const isExpandable = cell.planned?.workout_definition?.exercises?.length || hasMountainActivity
            const isExpanded = expandedDay === cell.dateStr
            const sessionName = cell.displayLabel
              ?? cell.planned?.workout_definition?.session_name
              ?? cell.templateSession
              ?? (cell.templateDayType === 'mobility' ? 'Mobility'
                : cell.templateDayType === 'mountain' ? 'Mountain day'
                : cell.templateDayType === 'cardio' ? 'Cardio'
                : cell.templateDayType === 'intervals' ? 'Intervals'
                : 'Rest')

            const completedActivity = cell.activities.find((a) =>
              cell.planned?.actual_garmin_activity_id
                ? a.garmin_activity_id === cell.planned.actual_garmin_activity_id
                : false
            ) ?? cell.activities[0]

            return (
              <div
                key={cell.dateStr}
                className={`rounded-xl border px-3 py-2 ${
                  cell.isToday
                    ? 'border-accent-green/40 bg-accent-green/5'
                    : 'border-border-subtle bg-bg-surface'
                }`}
              >
                <button
                  onClick={() => isExpandable && setExpandedDay(isExpanded ? null : cell.dateStr)}
                  className={`w-full flex items-center gap-3 text-left ${isExpandable ? 'cursor-pointer' : 'cursor-default'}`}
                >
                  <div className="w-10 shrink-0">
                    <div className={`text-[10px] uppercase tracking-wider font-semibold ${cell.isToday ? 'text-accent-green' : 'text-text-muted'}`}>
                      {cell.label}
                    </div>
                    <div className={`text-base font-bold font-data ${cell.isToday ? 'text-text-primary' : 'text-text-secondary'}`}>
                      {format(cell.date, 'd')}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-semibold text-text-primary truncate">
                      {sessionName}
                    </div>
                    {completedActivity && (
                      <div className="text-[11px] text-text-muted truncate">
                        {formatDuration(completedActivity.duration_seconds)}
                        {completedActivity.elevation_gain != null && completedActivity.elevation_gain > 0 && (
                          <span className="text-mountain ml-2">{Math.round(completedActivity.elevation_gain)}m</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="shrink-0 flex items-center gap-2">
                    <span className={`text-[11px] font-semibold ${badge.color}`}>
                      {badge.label}
                    </span>
                    {isExpandable ? (
                      isExpanded ? <ChevronUp size={14} className="text-text-muted" /> : <ChevronDown size={14} className="text-text-muted" />
                    ) : null}
                  </div>
                </button>

                {isExpanded && cell.planned?.workout_definition && (
                  <div className="mt-3 pt-3 border-t border-border-subtle space-y-1.5">
                    {cell.planned.workout_definition.warmup?.length > 0 && (
                      <div className="text-[11px] text-text-muted mb-2">
                        Warmup: {cell.planned.workout_definition.warmup.map((w) => w.name).join(', ')}
                      </div>
                    )}
                    {(cell.planned.workout_definition.exercises ?? []).map((ex: PlannedExercise, i: number) => (
                      <div key={i} className="flex items-baseline justify-between text-[12px]">
                        <span className="text-text-primary truncate pr-2">{ex.name}</span>
                        <span className="text-text-muted shrink-0 font-data">
                          {ex.sets}×{ex.reps}
                          {ex.weight_kg != null && ` @ ${ex.weight_kg}kg`}
                        </span>
                      </div>
                    ))}
                    {cell.planned.workout_definition.rpe_range && (
                      <div className="text-[11px] text-text-dim mt-2">
                        Target RPE: {cell.planned.workout_definition.rpe_range[0]}–{cell.planned.workout_definition.rpe_range[1]}
                      </div>
                    )}
                    {cell.planned.adjustment_reason && (
                      <div className="text-[11px] text-accent-blue mt-2 italic">
                        Adjusted: {cell.planned.adjustment_reason}
                      </div>
                    )}
                    {canReschedule(cell) && (
                      <button
                        onClick={(e) => { e.stopPropagation(); setRescheduleSource(cell) }}
                        className="mt-3 pt-2 border-t border-border-subtle flex items-center gap-1.5 text-[12px] text-accent-blue font-medium w-full"
                      >
                        <ArrowRightLeft size={13} />
                        Move to another day
                      </button>
                    )}
                  </div>
                )}

                {isExpanded && hasMountainActivity && !cell.planned?.workout_definition && (
                  <div className="mt-3 pt-3 border-t border-border-subtle">
                    {cell.activities
                      .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type) || MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type))
                      .map((a, i) => (
                        <MountainActivityCard key={a.garmin_activity_id ?? i} activity={a} showDate={false} />
                      ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      {/* ═══ 4. LOAD ACCUMULATION ═══ */}
      <Card title="Load this week">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Strength</div>
            <div className="text-lg font-bold text-text-primary font-data mt-1">
              {Math.round(strengthVolume).toLocaleString()}
              <span className="text-[11px] text-text-muted ml-1 font-normal">kg</span>
            </div>
            {volumePct != null && (
              <div className={`text-[11px] font-semibold ${deltaColor(volumePct)}`}>
                {volumePct >= 0 ? '↑' : '↓'} {volumePct >= 0 ? '+' : ''}{volumePct}%
              </div>
            )}
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Elevation</div>
            <div className="text-lg font-bold text-text-primary font-data mt-1">
              {Math.round(totalElevation)}
              <span className="text-[11px] text-text-muted ml-1 font-normal">m</span>
            </div>
            {elevPct != null && (
              <div className={`text-[11px] font-semibold ${deltaColor(elevPct)}`}>
                {elevPct >= 0 ? '↑' : '↓'} {elevPct >= 0 ? '+' : ''}{elevPct}%
              </div>
            )}
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Hours</div>
            <div className="text-lg font-bold text-text-primary font-data mt-1">
              {trainingHours.toFixed(1)}
              <span className="text-[11px] text-text-muted ml-1 font-normal">h</span>
            </div>
            {hoursPct != null && (
              <div className={`text-[11px] font-semibold ${deltaColor(hoursPct)}`}>
                {hoursPct >= 0 ? '↑' : '↓'} {hoursPct >= 0 ? '+' : ''}{hoursPct}%
              </div>
            )}
          </div>
        </div>
        <div className="text-[10px] text-text-dim mt-3">vs previous week</div>
      </Card>

      {/* ═══ 5. RECOVERY SNAPSHOT ═══ */}
      <Card title="Recovery snapshot">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Sleep avg</div>
            <div className={`text-lg font-bold font-data mt-1 ${
              weekSleep.avg == null ? 'text-text-muted'
                : weekSleep.avg >= 7 ? 'text-accent-green'
                : weekSleep.avg >= 6 ? 'text-accent-yellow'
                : 'text-accent-red'
            }`}>
              {weekSleep.avg != null ? `${weekSleep.avg}h` : '—'}
            </div>
            <div className="text-[10px] text-text-dim mt-0.5">{weekSleep.count} nights</div>
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">HRV</div>
            <div className={`text-lg font-bold font-data mt-1 ${
              weekHRV.status?.toUpperCase() === 'BALANCED' ? 'text-accent-green'
                : weekHRV.status?.toUpperCase() === 'UNBALANCED' ? 'text-accent-yellow'
                : weekHRV.status?.toUpperCase() === 'LOW' ? 'text-accent-red'
                : 'text-text-muted'
            }`}>
              {weekHRV.avg != null ? `${weekHRV.avg}` : '—'}
              <span className="text-[11px] text-text-muted ml-1 font-normal">ms</span>
            </div>
            <div className="text-[10px] text-text-dim mt-0.5">
              {weekHRV.baseline != null ? `baseline ${weekHRV.baseline}` : weekHRV.status ?? '—'}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">RHR</div>
            <div className="text-lg font-bold font-data mt-1 text-text-primary">
              {rhrTrend?.recent ?? '—'}
              <span className="text-[11px] text-text-muted ml-1 font-normal">bpm</span>
            </div>
            <div className={`text-[10px] mt-0.5 ${
              rhrTrend == null ? 'text-text-dim'
                : rhrTrend.delta > 2 ? 'text-accent-yellow'
                : rhrTrend.delta < -2 ? 'text-accent-green'
                : 'text-text-dim'
            }`}>
              {rhrTrend == null ? '—'
                : rhrTrend.delta > 2 ? `↑ +${rhrTrend.delta} vs 7d`
                : rhrTrend.delta < -2 ? `↓ ${rhrTrend.delta} vs 7d`
                : 'stable'}
            </div>
          </div>
        </div>
      </Card>

      {/* ═══ 6. SLEEP TREND CHART (kept) ═══ */}
      <Card title="Sleep Trend (14d)" subtitle="Total duration is the reliable number; stage breakdown is approximate.">
        {sleepBars.length > 0 ? (
          <ResponsiveContainer width="100%" height={130}>
            <BarChart data={sleepBars} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#646478' }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 10]} tick={{ fontSize: 10, fill: '#646478' }} tickLine={false} axisLine={false} width={35} />
              <Bar dataKey="hours" radius={[3, 3, 0, 0]}>
                {sleepBars.map((entry, index) => (
                  <Cell key={index} fill={sleepBarColor(entry.hours)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-[14px] text-text-muted">Not enough data</div>
        )}
      </Card>

      {/* ═══ 7. ACTIVITY LOG (collapsed) ═══ */}
      <button
        onClick={() => setActivitiesExpanded(!activitiesExpanded)}
        className="w-full bg-bg-card border border-border-subtle rounded-2xl p-4 text-left"
      >
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
              <div
                key={a.garmin_activity_id || i}
                className="flex items-center justify-between border-b border-border-subtle last:border-0 py-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold text-text-primary truncate">
                    {a.activity_name || formatActivityType(a.activity_type)}
                  </div>
                  <div className="text-[11px] text-text-muted mt-0.5">
                    {format(new Date(a.date), 'EEE, MMM d')}
                  </div>
                </div>
                <div className="flex gap-2 text-[11px] text-text-secondary shrink-0 ml-3 font-medium">
                  <span>{formatDuration(a.duration_seconds)}</span>
                  {a.elevation_gain != null && a.elevation_gain > 0 && (
                    <span className="text-mountain">{Math.round(a.elevation_gain)}m</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </button>

      {/* ═══ 8. FLYING (existing) ═══ */}
      <WeekFlights activities={weekActivities} />

      {/* ═══ RESCHEDULE MODAL ═══ */}
      {rescheduleSource && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/60"
          onClick={() => !rescheduleLoading && setRescheduleSource(null)}
        >
          <div
            className="w-full max-w-lg bg-bg-card border-t border-border-subtle rounded-t-2xl p-5 pb-8 animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-text-primary">
                Move session
              </h3>
              <button
                onClick={() => !rescheduleLoading && setRescheduleSource(null)}
                className="text-text-muted text-sm px-2 py-1"
              >
                Cancel
              </button>
            </div>
            <div className="text-[13px] text-text-secondary mb-4">
              <span className="font-semibold text-text-primary">
                {rescheduleSource.planned?.workout_definition?.session_name
                  ?? rescheduleSource.planned?.session_name
                  ?? rescheduleSource.templateSession}
              </span>
              {' '}from {format(rescheduleSource.date, 'EEEE, MMM d')}
            </div>
            <div className="grid grid-cols-7 gap-1.5">
              {dayCells.map((cell) => {
                const isSource = cell.dateStr === rescheduleSource.dateStr
                const isPast = isBefore(cell.date, today) && !cell.isToday
                const isCompleted = cell.status === 'completed'
                const disabled = isSource || isPast || isCompleted || rescheduleLoading
                const hasWorkout = cell.planned != null
                return (
                  <button
                    key={cell.dateStr}
                    disabled={disabled}
                    onClick={() => handleReschedule(cell.dateStr)}
                    className={`flex flex-col items-center py-2.5 rounded-xl border transition-colors ${
                      isSource
                        ? 'border-accent-blue/40 bg-accent-blue/10 opacity-50'
                        : disabled
                          ? 'border-border-subtle bg-bg-surface opacity-30 cursor-not-allowed'
                          : hasWorkout
                            ? 'border-accent-yellow/40 bg-accent-yellow/5 active:bg-accent-yellow/15'
                            : 'border-border-subtle bg-bg-surface active:bg-accent-green/10 active:border-accent-green/40'
                    }`}
                  >
                    <div className={`text-[10px] uppercase tracking-wider font-semibold ${
                      cell.isToday ? 'text-accent-green' : 'text-text-muted'
                    }`}>
                      {cell.label}
                    </div>
                    <div className={`text-base font-bold font-data ${
                      isSource ? 'text-accent-blue' : 'text-text-primary'
                    }`}>
                      {format(cell.date, 'd')}
                    </div>
                    {!isSource && hasWorkout && !disabled && (
                      <div className="text-[9px] text-accent-yellow font-semibold mt-0.5">swap</div>
                    )}
                    {isSource && (
                      <div className="text-[9px] text-accent-blue font-semibold mt-0.5">from</div>
                    )}
                  </button>
                )
              })}
            </div>
            {rescheduleLoading && (
              <div className="text-[12px] text-text-muted text-center mt-3">Moving...</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function WeekFlights({ activities }: { activities: Activity[] }) {
  const flights = useMemo(() => {
    const flyActivities = activities.filter((a: Activity) => a.activity_type === 'hang_gliding')
    if (!flyActivities.length) return []
    return pairHikeAndFly(flyActivities, activities)
  }, [activities])

  if (!flights.length) return null

  const totalAirtime = flights.reduce((s, f) => s + f.airtime, 0)
  const totalDistance = flights.reduce((s, f) => s + f.distance, 0)
  const xcFlights = flights.filter(f => f.flightType === 'xc').length

  const typeLabel = (type: string) => {
    switch (type) {
      case 'xc': return 'XC'
      case 'soaring': return 'Soaring'
      case 'glide_down': return 'Glide'
      case 'hike_and_fly': return 'H&F'
      default: return type
    }
  }

  const typeColor = (type: string) => {
    switch (type) {
      case 'xc': return 'text-accent-orange'
      case 'soaring': return 'text-accent-yellow'
      case 'hike_and_fly': return 'text-accent-green'
      default: return 'text-text-muted'
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2 mb-3">
        <Wind size={15} className="text-accent-orange" />
        <span className="text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold">Flying this week</span>
      </div>
      <div className="flex gap-4 text-[14px] mb-3">
        <div>
          <span className="text-text-primary font-bold">{flights.length}</span>
          <span className="text-text-muted text-[12px] ml-1">flight{flights.length !== 1 ? 's' : ''}</span>
        </div>
        <div>
          <span className="text-text-primary font-bold">{formatAirtime(totalAirtime)}</span>
          <span className="text-text-muted text-[12px] ml-1">airtime</span>
        </div>
        {totalDistance > 0 && (
          <div>
            <span className="text-text-primary font-bold">{formatDistance(totalDistance)}</span>
            <span className="text-text-muted text-[12px] ml-1">distance</span>
          </div>
        )}
        {xcFlights > 0 && (
          <div>
            <span className="text-accent-orange font-bold">{xcFlights}</span>
            <span className="text-text-muted text-[12px] ml-1">XC</span>
          </div>
        )}
      </div>
      <div className="space-y-2">
        {flights.map((f, i) => (
          <div key={i} className="flex items-center justify-between text-[13px]">
            <div className="flex items-center gap-2">
              <span className={`font-semibold ${typeColor(f.flightType)}`}>{typeLabel(f.flightType)}</span>
              <span className="text-text-secondary">{format(new Date(f.date), 'EEE')}</span>
            </div>
            <div className="flex gap-3 text-text-muted">
              <span>{formatAirtime(f.airtime)}</span>
              {f.distance > 100 && <span>{formatDistance(f.distance)}</span>}
              {f.maxAltitude != null && f.maxAltitude > 0 && <span>{Math.round(f.maxAltitude)}m</span>}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
