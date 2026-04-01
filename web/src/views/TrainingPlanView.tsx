import { useState, useMemo } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useActivities, useTrainingSessions, useTrainingSets, useCoachingLog } from '../hooks/useSupabase'
import {
  getProgramWeek,
  getPlannedWeight,
  getWeekSchedule,
  SESSION_NAMES,
  isDeloadWeek,
  analyzeLiftProgression,
  type SessionType,
} from '../lib/program'
import { format, isSameDay, startOfWeek, endOfWeek, isWithinInterval } from 'date-fns'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  Cell,
} from 'recharts'
import { ChevronDown, ChevronRight, Mountain, Dumbbell } from 'lucide-react'

// ─── Session definitions ───────────────────────────────────────────
interface ExerciseDef {
  name: string
  sets: number
  reps: number | string
}

const SESSION_EXERCISES: Record<SessionType, ExerciseDef[]> = {
  A: [
    { name: 'Barbell Back Squat', sets: 3, reps: 8 },
    { name: 'DB Bench Press', sets: 3, reps: 10 },
    { name: 'Barbell Row', sets: 3, reps: 10 },
    { name: 'KB Swings', sets: 3, reps: 15 },
    { name: 'KB Halo', sets: 2, reps: 10 },
    { name: 'KB Turkish Get-up', sets: 2, reps: 3 },
  ],
  B: [
    { name: 'Overhead Press', sets: 3, reps: 10 },
    { name: 'Chin-ups', sets: 3, reps: 8 },
    { name: 'DB Incline Press', sets: 2, reps: 12 },
    { name: 'Cable Row', sets: 2, reps: 12 },
    { name: 'Core Circuit', sets: 3, reps: '1' },
  ],
  C: [
    { name: 'Trap Bar Deadlift', sets: 3, reps: 8 },
    { name: 'KB Clean & Press', sets: 3, reps: 8 },
    { name: 'Single-Arm DB Row', sets: 3, reps: 10 },
    { name: 'Bulgarian Split Squat', sets: 2, reps: 10 },
    { name: 'Lateral Raises', sets: 2, reps: 15 },
    { name: 'KB Farmer Carry', sets: 3, reps: '40m' },
  ],
  A2: [
    { name: 'Barbell Back Squat', sets: 3, reps: 8 },
    { name: 'DB Bench Press', sets: 3, reps: 10 },
    { name: 'Barbell Row', sets: 3, reps: 10 },
    { name: 'KB Swings', sets: 3, reps: 15 },
    { name: 'KB Halo', sets: 2, reps: 10 },
    { name: 'KB Turkish Get-up', sets: 2, reps: 3 },
  ],
  B2: [
    { name: 'Overhead Press', sets: 3, reps: 10 },
    { name: 'Chin-ups', sets: 3, reps: 8 },
    { name: 'DB Incline Press', sets: 2, reps: 12 },
    { name: 'Cable Row', sets: 2, reps: 12 },
    { name: 'Core Circuit', sets: 3, reps: '1' },
  ],
}

const MOUNTAIN_ACTIVITY_TYPES = new Set([
  'backcountry_snowboarding',
  'resort_snowboarding',
  'hiking',
  'mountaineering',
  'hang_gliding',
])

const COMPOUND_LIFTS = [
  'Barbell Back Squat',
  'DB Bench Press',
  'Barbell Row',
  'Trap Bar Deadlift',
  'Overhead Press',
]

// ─── Helpers ───────────────────────────────────────────────────────
function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatActivityType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function acwrColor(acwr: number): 'green' | 'yellow' | 'red' {
  if (acwr > 1.5) return 'red'
  if (acwr >= 0.8 && acwr <= 1.3) return 'green'
  return 'yellow'
}

function acwrBgClass(acwr: number): string {
  const c = acwrColor(acwr)
  if (c === 'green') return 'text-accent-green'
  if (c === 'yellow') return 'text-accent-yellow'
  return 'text-accent-red'
}

function acwrLabel(acwr: number): { text: string; color: string } {
  if (acwr > 1.5) return { text: 'Spike risk — high injury probability', color: 'text-accent-red' }
  if (acwr >= 1.3) return { text: 'Elevated load — monitor recovery', color: 'text-accent-yellow' }
  if (acwr >= 0.8) return { text: 'Sweet spot — optimal training zone', color: 'text-accent-green' }
  if (acwr >= 0.5) return { text: 'Detraining risk — consider increasing volume', color: 'text-accent-yellow' }
  return { text: 'Significant detraining — fitness declining', color: 'text-accent-red' }
}


function fmtDate(d: Date): string {
  return format(d, 'yyyy-MM-dd')
}

// ─── Types for Supabase data ──────────────────────────────────────
type Activity = {
  date: string
  activity_type: string
  activity_name: string | null
  duration_seconds: number | null
  calories: number | null
  elevation_gain: number | null
  avg_hr: number | null
  max_hr: number | null
  garmin_activity_id: string | null
}

type TrainingSession = {
  id: number
  date: string
  name: string | null
  program: string | null
  duration_minutes: number | null
  total_volume_kg: number | null
  total_sets: number | null
  notes: string | null
  rating: number | null
}

type TrainingSet = {
  id: number
  session_id: number
  exercise_id: number
  set_number: number
  set_type: string
  weight_kg: number | null
  reps: number | null
  rpe: number | null
  volume_kg: number | null
  exercises: { name: string; category: string | null } | null
}

type CoachingEntry = {
  id: number
  date: string
  type: string
  message: string
}

// ═══════════════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════════════
export function TrainingPlanView() {
  const activitiesQuery = useActivities(60)
  const sessionsQuery = useTrainingSessions(60)
  const coachingQuery = useCoachingLog(7)

  const sessionIds = useMemo(
    () => (sessionsQuery.data ?? []).map((s: TrainingSession) => s.id),
    [sessionsQuery.data]
  )
  const setsQuery = useTrainingSets(sessionIds)

  const loading =
    activitiesQuery.loading || sessionsQuery.loading || coachingQuery.loading || setsQuery.loading
  const error =
    activitiesQuery.error || sessionsQuery.error || coachingQuery.error || setsQuery.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const activities = (activitiesQuery.data ?? []) as Activity[]
  const sessions = (sessionsQuery.data ?? []) as TrainingSession[]
  const sets = (setsQuery.data ?? []) as TrainingSet[]
  const coaching = (coachingQuery.data ?? []) as CoachingEntry[]

  return (
    <div className="space-y-4 pb-8">
      <ProgramOverview activities={activities} sessions={sessions} />
      <WeekGrid activities={activities} sessions={sessions} />
      <TodaySession sessions={sessions} sets={sets} coaching={coaching} />
      <LiftProgressionTracker sessions={sessions} sets={sets} />
      <EnduranceLoadTracker activities={activities} />
      <SessionHistory sessions={sessions} sets={sets} />
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 1. Program Overview
// ═══════════════════════════════════════════════════════════════════
function ProgramOverview({
  activities,
  sessions,
}: {
  activities: Activity[]
  sessions: TrainingSession[]
}) {
  const today = new Date()
  const { block, week } = getProgramWeek(today)
  const nextDeload = week <= 4 ? 4 : 8
  const rpeRange = block === 1 ? '6-7' : '7-8'
  const pctDone = (week / 8) * 100

  // Current week compliance
  const weekStart = startOfWeek(today, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(today, { weekStartsOn: 1 })

  const { gymCompleted, mountainCompleted, isConsolidated, gymTarget } = useMemo(() => {
    const inWeek = (dateStr: string) => {
      const d = new Date(dateStr + 'T12:00:00')
      return isWithinInterval(d, { start: weekStart, end: weekEnd })
    }

    const gym = sessions.filter((s) => inWeek(s.date)).length
    const mountain = activities.filter(
      (a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type) && inWeek(a.date)
    ).length
    const consolidated = mountain >= 2
    return {
      gymCompleted: gym,
      mountainCompleted: mountain,
      isConsolidated: consolidated,
      gymTarget: consolidated ? 2 : 3,
    }
  }, [activities, sessions, weekStart, weekEnd])

  return (
    <Card>
      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">
            Base Rebuild &mdash; Block {block} of 2
          </h2>
          <p className="text-sm text-text-secondary mt-0.5">
            Week {week} / 8 &middot; Apr 1 &ndash; May 26
          </p>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-border rounded-full h-2">
          <div
            className="bg-accent-blue rounded-full h-2 transition-all"
            style={{ width: `${pctDone}%` }}
          />
        </div>

        {/* Compliance stats */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span className={gymCompleted >= gymTarget ? 'text-accent-green' : 'text-text-secondary'}>
            Gym: {gymCompleted}/{gymTarget}
          </span>
          <span className={mountainCompleted > 0 ? 'text-accent-green' : 'text-text-secondary'}>
            Mountain: {mountainCompleted}
          </span>
          {isConsolidated && (
            <span className="text-accent-yellow text-xs">
              2x consolidated (A2 Wed + B2 Fri)
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-text-secondary">
          <span>{isConsolidated ? '2x/week gym (consolidated)' : '3x/week gym'} + mountain days</span>
          <span>RPE {rpeRange} &middot; Linear progression</span>
          <span>Next deload: Week {nextDeload}</span>
        </div>
      </div>
    </Card>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 2. 8-Week Grid
// ═══════════════════════════════════════════════════════════════════
function WeekGrid({
  activities,
  sessions,
}: {
  activities: Activity[]
  sessions: TrainingSession[]
}) {
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null)
  const { week: currentWeek } = getProgramWeek(new Date())
  const today = new Date()

  // Build a set of dates with completed gym sessions
  const completedDates = useMemo(() => {
    const s = new Set<string>()
    sessions.forEach((sess) => s.add(sess.date))
    return s
  }, [sessions])

  // Build a map of mountain activities by date
  const mountainByDate = useMemo(() => {
    const m = new Map<string, Activity[]>()
    activities
      .filter((a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type))
      .forEach((a) => {
        const existing = m.get(a.date) ?? []
        existing.push(a)
        m.set(a.date, existing)
      })
    return m
  }, [activities])

  // Build a map of all activities by date for overlay
  const activitiesByDate = useMemo(() => {
    const m = new Map<string, Activity[]>()
    activities.forEach((a) => {
      const existing = m.get(a.date) ?? []
      existing.push(a)
      m.set(a.date, existing)
    })
    return m
  }, [activities])

  // Detect consolidated weeks: weeks where 2+ mountain days occurred
  const consolidatedWeeks = useMemo(() => {
    const s = new Set<number>()
    for (let w = 1; w <= 8; w++) {
      const ws = getWeekSchedule(w)
      const weekDates = ws.days.map((d) => fmtDate(d.date))
      const mountainCount = weekDates.reduce(
        (count, date) => count + (mountainByDate.has(date) ? 1 : 0),
        0
      )
      if (mountainCount >= 2) s.add(w)
    }
    return s
  }, [mountainByDate])

  const weeks = useMemo(() => Array.from({ length: 8 }, (_, i) => getWeekSchedule(i + 1)), [])

  // Short pill labels
  const pillLabel = (dayType: string, session: SessionType | null, isConsolidated: boolean, dayIndex: number): string => {
    if (dayType === 'gym' && session) {
      if (isConsolidated && dayIndex === 0) return '\u2014'
      const labels: Record<string, string> = {
        B: 'Upper+Core',
        A: 'Full Body',
        C: 'Full Body V2',
        A2: 'Heavy',
        B2: 'Functional',
      }
      return labels[session] ?? session
    }
    if (dayType === 'mobility') return 'Mob'
    if (dayType === 'intervals') return 'HIIT'
    if (dayType === 'mountain') return '\u{1F3D4}'
    return '\u2014'
  }

  // Pill background color
  const pillBg = (
    dayType: string,
    _session: SessionType | null,
    completed: boolean,
    isPast: boolean,
    isToday: boolean,
    hasMountainActual: boolean,
    isConsolidated: boolean,
    dayIndex: number,
  ): string => {
    // Consolidated week: Monday gym becomes rest
    if (isConsolidated && dayType === 'gym' && dayIndex === 0)
      return 'bg-bg-primary/40 text-text-muted'

    if (dayType === 'gym') {
      if (completed) return 'bg-accent-green/20 text-accent-green'
      if (isToday) return 'bg-accent-blue/20 text-accent-blue'
      if (isPast) return 'bg-accent-red/20 text-accent-red'
      return 'bg-accent-purple/20 text-accent-purple'
    }
    if (dayType === 'mountain') {
      if (hasMountainActual) return 'bg-sky-500/20 text-sky-400'
      return 'bg-sky-500/10 text-sky-400/60'
    }
    if (dayType === 'intervals') return 'bg-orange-500/20 text-orange-400'
    // rest, mobility
    return 'bg-bg-primary/40 text-text-muted'
  }

  return (
    <Card title="8-Week Program">
      <div className="space-y-1">
        {weeks.map((ws) => {
          const isCurrent = ws.weekNum === currentWeek
          const isExpanded = expandedWeek === ws.weekNum
          const isConsolidatedWeek = consolidatedWeeks.has(ws.weekNum)

          // Compute week stats
          const weekDates = ws.days.map((d) => fmtDate(d.date))
          const gymTarget = isConsolidatedWeek ? 2 : 3
          const gymCompleted = weekDates.filter((d) => completedDates.has(d)).length
          const mountainCompleted = weekDates.filter((d) => mountainByDate.has(d)).length

          // Effective sessions per day (handles consolidation)
          const effectiveDays = ws.days.map((day, i) => {
            const effectiveDayType =
              isConsolidatedWeek && day.dayType === 'gym' && i === 0
                ? ('rest' as const)
                : day.dayType
            const effectiveSession: SessionType | null =
              isConsolidatedWeek && day.dayType === 'gym'
                ? i === 2 ? 'A2' : i === 4 ? 'B2' : null
                : day.session
            return { ...day, dayType: effectiveDayType, session: effectiveSession, origIndex: i }
          })

          return (
            <div key={ws.weekNum}>
              <button
                onClick={() => setExpandedWeek(isExpanded ? null : ws.weekNum)}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors hover:bg-bg-card-hover ${
                  isCurrent ? 'border-l-2 border-accent-blue bg-bg-card-hover/50' : ''
                }`}
              >
                {/* Top line: week number + badges + completion counts */}
                <div className="flex items-center gap-2 mb-1.5">
                  {isExpanded ? <ChevronDown size={14} className="text-text-muted shrink-0" /> : <ChevronRight size={14} className="text-text-muted shrink-0" />}
                  <span className="text-sm font-medium text-text-primary">Week {ws.weekNum}</span>
                  {isCurrent && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent-blue/20 text-accent-blue font-medium">
                      Current
                    </span>
                  )}
                  {ws.deload && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent-yellow/20 text-accent-yellow font-medium">
                      Deload
                    </span>
                  )}
                  {isConsolidatedWeek && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent-purple/20 text-accent-purple font-medium">
                      Consolidated
                    </span>
                  )}
                  <span className="ml-auto text-xs text-text-secondary">
                    <Dumbbell size={11} className="inline text-gym mr-0.5" />
                    {gymCompleted}/{gymTarget}
                    <span className="mx-1.5 text-text-muted">&middot;</span>
                    <Mountain size={11} className="inline text-mountain mr-0.5" />
                    {mountainCompleted}
                  </span>
                </div>

                {/* Pill row */}
                <div className="flex gap-1 flex-wrap ml-5">
                  {effectiveDays.map((day, i) => {
                    const dateStr = fmtDate(day.date)
                    const isPast = day.date < today && !isSameDay(day.date, today)
                    const isToday = isSameDay(day.date, today)
                    const completed = completedDates.has(dateStr)
                    const hasMountainActual = mountainByDate.has(dateStr)
                    const dayActivities = activitiesByDate.get(dateStr) ?? []

                    // Override pill for actual activity on non-gym days
                    let label = pillLabel(day.dayType, day.session, isConsolidatedWeek, i)
                    let bg = pillBg(day.dayType, day.session, completed, isPast, isToday, hasMountainActual, isConsolidatedWeek, i)

                    if ((isPast || isToday) && dayActivities.length > 0 && day.dayType !== 'gym') {
                      const hasActualMtn = dayActivities.some((a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type))
                      if (hasActualMtn) {
                        label = '\u{1F3D4}'
                        bg = 'bg-sky-500/20 text-sky-400'
                      }
                    }

                    return (
                      <span
                        key={i}
                        className={`inline-block text-[10px] px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap ${bg}`}
                        title={`${format(day.date, 'EEE d MMM')}`}
                      >
                        {label}
                      </span>
                    )
                  })}
                </div>
              </button>

              {/* Expanded detail — inline */}
              {isExpanded && (
                <div className="ml-8 mr-2 mb-2 mt-1 space-y-3">
                  {/* Gym days */}
                  {effectiveDays
                    .filter((d) => d.dayType === 'gym' && d.session)
                    .map((day) => {
                      const dateStr = fmtDate(day.date)
                      const completed = completedDates.has(dateStr)
                      const exercises = SESSION_EXERCISES[day.session!] ?? []
                      const sessionName = SESSION_NAMES[day.session!] ?? day.session
                      const rpeLabel = ws.deload ? 'Deload 50% vol' : ws.block === 1 ? 'RPE 6-7' : 'RPE 7-8'

                      return (
                        <div key={dateStr} className="bg-bg-primary/50 rounded-lg px-3 py-2">
                          <div className="flex items-center gap-2 mb-1">
                            <Dumbbell size={13} className="text-gym shrink-0" />
                            <span className="text-sm font-medium text-text-primary">
                              {sessionName}
                            </span>
                            {completed && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent-green/20 text-accent-green font-medium">
                                Done
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-text-secondary mb-2">
                            {format(day.date, 'EEE')} &middot; {rpeLabel}
                          </div>
                          <div className="space-y-0.5">
                            {exercises.map((ex) => {
                              const weight = getPlannedWeight(ex.name, ws.weekNum)
                              const setsReps = ws.deload
                                ? `${Math.ceil(ex.sets / 2)}\u00D7${ex.reps}`
                                : `${ex.sets}\u00D7${ex.reps}`
                              return (
                                <div
                                  key={ex.name}
                                  className="flex justify-between text-xs font-mono"
                                >
                                  <span className="text-text-secondary">{ex.name}</span>
                                  <span className="text-text-muted">
                                    {setsReps}
                                    {weight != null && weight > 0 ? ` @ ${weight}kg` : ''}
                                  </span>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}

                  {/* Mountain activities (actual from Garmin) */}
                  {ws.days
                    .filter((d) => {
                      const dateStr = fmtDate(d.date)
                      return mountainByDate.has(dateStr)
                    })
                    .flatMap((d) => {
                      const dateStr = fmtDate(d.date)
                      return (mountainByDate.get(dateStr) ?? []).map((a, ai) => (
                        <div key={`${dateStr}-${ai}`} className="bg-bg-primary/50 rounded-lg px-3 py-2">
                          <div className="flex items-center gap-2 mb-1">
                            <Mountain size={13} className="text-mountain shrink-0" />
                            <span className="text-sm font-medium text-text-primary">
                              {a.activity_name ?? formatActivityType(a.activity_type)}
                            </span>
                          </div>
                          <div className="text-xs text-text-secondary">
                            {format(new Date(a.date + 'T12:00:00'), 'EEE')}
                            {a.duration_seconds != null && <span> &middot; {formatDuration(a.duration_seconds)}</span>}
                            {a.elevation_gain != null && a.elevation_gain > 0 && (
                              <span> &middot; {Math.round(a.elevation_gain)}m &uarr;</span>
                            )}
                            {a.avg_hr != null && <span> &middot; HR {a.avg_hr}</span>}
                          </div>
                        </div>
                      ))
                    })}

                  {/* Empty state */}
                  {effectiveDays.filter((d) => d.dayType === 'gym' && d.session).length === 0 &&
                    ws.days.every((d) => !mountainByDate.has(fmtDate(d.date))) && (
                    <div className="text-xs text-text-muted py-1">No recorded sessions this week</div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 3. Today's Session
// ═══════════════════════════════════════════════════════════════════
function TodaySession({
  sessions,
  sets,
  coaching,
}: {
  sessions: TrainingSession[]
  sets: TrainingSet[]
  coaching: CoachingEntry[]
}) {
  const today = new Date()
  const { block, week } = getProgramWeek(today)
  const todaySchedule = getWeekSchedule(week)
  const dayOfWeek = today.getDay() // 0=Sun
  // Map to our 0-indexed days array (Mon=0 ... Sun=6)
  const dayIndex = dayOfWeek === 0 ? 6 : dayOfWeek - 1
  const todayDay = todaySchedule.days[dayIndex]

  if (!todayDay || todayDay.dayType !== 'gym' || !todayDay.session) return null

  const sessionType = todayDay.session
  const exercises = SESSION_EXERCISES[sessionType] ?? []
  const rpeTarget = block === 1 ? '6-7' : '7-8'
  const estDuration = exercises.length <= 5 ? '45-55 min' : '55-65 min'

  // Check if there's an actual session logged today
  const todayStr = fmtDate(today)
  const todaySession = sessions.find((s) => s.date === todayStr)
  const todaySets = todaySession ? sets.filter((s) => s.session_id === todaySession.id) : []

  // Coaching notes for today
  const todayNotes = coaching.filter((c) => c.date === todayStr)

  return (
    <Card>
      <div className="space-y-3">
        <div>
          <div className="flex items-center gap-2">
            <Dumbbell size={16} className="text-gym" />
            <h3 className="text-sm font-semibold text-text-primary">Today's Session</h3>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-xs text-text-secondary">
            <span className="text-gym font-medium">{SESSION_NAMES[sessionType]}</span>
            <span>
              Block {block} / Week {week}
            </span>
            <span>RPE {rpeTarget}</span>
            <span>~{estDuration}</span>
          </div>
        </div>

        {/* Exercise table */}
        <div className="overflow-x-auto -mx-4 px-4">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-text-muted border-b border-border">
                <th className="text-left py-1 font-medium">Exercise</th>
                <th className="text-left py-1 font-medium">Target</th>
                <th className="text-left py-1 font-medium">Actual</th>
              </tr>
            </thead>
            <tbody>
              {exercises.map((ex) => {
                const plannedWt = getPlannedWeight(ex.name, week)
                const targetStr = plannedWt
                  ? `${ex.sets}\u00D7${ex.reps} @ ${plannedWt}kg`
                  : `${ex.sets}\u00D7${ex.reps}`

                // Find actual sets for this exercise
                const actualSetsForExercise = todaySets.filter(
                  (s) => s.exercises?.name === ex.name && s.set_type === 'working'
                )

                let actualStr = '\u2014'
                if (actualSetsForExercise.length > 0) {
                  const weights = [
                    ...new Set(actualSetsForExercise.map((s) => s.weight_kg).filter(Boolean)),
                  ]
                  const reps = actualSetsForExercise.map((s) => s.reps).filter(Boolean)
                  if (weights.length === 1) {
                    actualStr = `${actualSetsForExercise.length}\u00D7${reps.join('/')} @ ${weights[0]}kg`
                  } else if (weights.length > 0) {
                    actualStr = actualSetsForExercise
                      .map((s) => `${s.reps}@${s.weight_kg}`)
                      .join(', ')
                  }
                }

                return (
                  <tr key={ex.name} className="border-b border-border/50">
                    <td className="py-1.5 text-text-primary">{ex.name}</td>
                    <td className="py-1.5 text-text-secondary">{targetStr}</td>
                    <td
                      className={`py-1.5 ${
                        actualStr !== '\u2014' ? 'text-accent-green' : 'text-text-muted'
                      }`}
                    >
                      {actualStr}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Coach notes */}
        {todayNotes.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] text-text-muted font-medium uppercase tracking-wide">
              Coach Notes
            </div>
            {todayNotes.map((n) => (
              <div key={n.id} className="text-xs text-text-secondary bg-bg-primary/50 rounded px-2 py-1">
                {n.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 4. Lift Progression Tracker
// ═══════════════════════════════════════════════════════════════════

const statusColors: Record<string, string> = {
  on_track: 'text-accent-green',
  ahead: 'text-accent-blue',
  stalled: 'text-accent-red',
  behind: 'text-accent-yellow',
  no_data: 'text-text-muted',
}

const trendArrows: Record<string, string> = {
  up: '\u2197',  // ↗
  flat: '\u2192', // →
  down: '\u2198', // ↘
}

function LiftProgressionTracker({
  sessions,
  sets,
}: {
  sessions: TrainingSession[]
  sets: TrainingSet[]
}) {
  const [selectedLift, setSelectedLift] = useState(COMPOUND_LIFTS[0])
  const { week: currentWeek } = getProgramWeek(new Date())

  // Build actual weights by week for all lifts
  const actualWeightsByWeek = useMemo(() => {
    const map = new Map<number, number>()
    for (let w = 1; w <= 8; w++) {
      const weekSchedule = getWeekSchedule(w)
      const weekDates = new Set(weekSchedule.days.map((d) => fmtDate(d.date)))
      const weekSessionIds = new Set(
        sessions.filter((s) => weekDates.has(s.date)).map((s) => s.id)
      )
      const weekSets = sets.filter(
        (s) =>
          weekSessionIds.has(s.session_id) &&
          s.exercises?.name === selectedLift &&
          s.set_type === 'working' &&
          s.weight_kg != null
      )
      if (weekSets.length > 0) {
        map.set(w, Math.max(...weekSets.map((s) => s.weight_kg!)))
      }
    }
    return map
  }, [selectedLift, sessions, sets])

  // Analyze progression
  const analysis = useMemo(
    () => analyzeLiftProgression(selectedLift, currentWeek, actualWeightsByWeek),
    [selectedLift, currentWeek, actualWeightsByWeek]
  )

  const chartData = useMemo(() => {
    return Array.from({ length: 8 }, (_, i) => {
      const weekNum = i + 1
      return {
        week: `Wk${weekNum}`,
        planned: getPlannedWeight(selectedLift, weekNum),
        actual: actualWeightsByWeek.get(weekNum) ?? null,
        deload: isDeloadWeek(weekNum),
        isCurrent: weekNum === currentWeek,
      }
    })
  }, [selectedLift, currentWeek, actualWeightsByWeek])

  return (
    <Card>
      <div className="space-y-4">
        {/* Header with analysis */}
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider mb-1">Lift Progression</div>
            <div className="text-base font-semibold text-text-primary">{selectedLift}</div>
          </div>
          <div className="text-right">
            <div className={`text-sm font-medium ${statusColors[analysis.status]}`}>
              {analysis.trend && trendArrows[analysis.trend]} {analysis.statusLabel}
            </div>
            {analysis.lastActualWeight != null && (
              <div className="text-[11px] text-text-muted mt-0.5">
                Last: {analysis.lastActualWeight}kg
                {analysis.nextTargetWeight != null && (
                  <> &rarr; Next: <span className="text-text-secondary">{analysis.nextTargetWeight}kg</span></>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Lift selector */}
        <div className="flex gap-1.5 flex-wrap">
          {COMPOUND_LIFTS.map((lift) => (
            <button
              key={lift}
              onClick={() => setSelectedLift(lift)}
              className={`text-[11px] px-3 py-1.5 rounded-full border transition-colors ${
                selectedLift === lift
                  ? 'bg-gym/15 text-gym border-gym/30'
                  : 'text-text-muted border-border-subtle hover:text-text-secondary hover:border-border'
              }`}
            >
              {lift.replace('Barbell ', '').replace('DB ', '')}
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <XAxis
                dataKey="week"
                tick={{ fontSize: 10, fill: '#5a5a6e' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#5a5a6e' }}
                axisLine={false}
                tickLine={false}
                domain={['auto', 'auto']}
                width={40}
                unit="kg"
              />
              <Tooltip
                contentStyle={{
                  background: '#1c1c24',
                  border: '1px solid #2a2a36',
                  borderRadius: 12,
                  fontSize: 11,
                  color: '#ececf0',
                }}
              />
              <Line
                type="monotone"
                dataKey="planned"
                stroke="#5a5a6e"
                strokeDasharray="4 4"
                strokeWidth={1.5}
                dot={false}
                name="Planned"
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#a78bfa"
                strokeWidth={2.5}
                dot={{ r: 5, fill: '#a78bfa', stroke: '#1c1c24', strokeWidth: 2 }}
                connectNulls={false}
                name="Actual"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Legend + stall warning */}
        <div className="flex items-center justify-between">
          <div className="flex gap-4 text-[10px] text-text-muted">
            <span className="flex items-center gap-1.5">
              <span className="w-5 h-px inline-block" style={{ borderTop: '1.5px dashed #5a5a6e' }} />
              Baseline plan
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-gym inline-block" />
              Your lifts
            </span>
          </div>
          {analysis.weeksAtSameWeight >= 2 && (
            <div className="text-[10px] text-accent-red">
              {analysis.weeksAtSameWeight >= 3
                ? 'Drop 10% & rebuild recommended'
                : 'Hold weight, focus on reps'}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 5. Endurance Load Tracker (ACWR)
// ═══════════════════════════════════════════════════════════════════
function EnduranceLoadTracker({ activities }: { activities: Activity[] }) {
  const mountainActivities = useMemo(
    () => activities.filter((a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type)),
    [activities]
  )

  // Aggregate weekly data for 8 weeks
  const weeklyData = useMemo(() => {
    return Array.from({ length: 8 }, (_, i) => {
      const weekNum = i + 1
      const ws = getWeekSchedule(weekNum)
      const weekDates = new Set(ws.days.map((d) => fmtDate(d.date)))

      const weekActivities = mountainActivities.filter((a) => weekDates.has(a.date))
      const elevation = weekActivities.reduce((sum, a) => sum + (a.elevation_gain ?? 0), 0)
      const duration = weekActivities.reduce((sum, a) => sum + (a.duration_seconds ?? 0), 0)

      return { weekNum, elevation: Math.round(elevation), duration }
    })
  }, [mountainActivities])

  // Current week values
  const { week: currentWeek } = getProgramWeek(new Date())
  const currentIdx = currentWeek - 1
  const thisWeekElev = weeklyData[currentIdx]?.elevation ?? 0
  const thisWeekDur = weeklyData[currentIdx]?.duration ?? 0

  // 4-week rolling average (previous 4 weeks, or available weeks)
  const fourWeekAvgElev = useMemo(() => {
    const start = Math.max(0, currentIdx - 4)
    const end = currentIdx
    const weeks = weeklyData.slice(start, end)
    if (weeks.length === 0) return 0
    return weeks.reduce((sum, w) => sum + w.elevation, 0) / weeks.length
  }, [weeklyData, currentIdx])

  const fourWeekAvgDur = useMemo(() => {
    const start = Math.max(0, currentIdx - 4)
    const end = currentIdx
    const weeks = weeklyData.slice(start, end)
    if (weeks.length === 0) return 0
    return weeks.reduce((sum, w) => sum + w.duration, 0) / weeks.length
  }, [weeklyData, currentIdx])

  const acwrElev = fourWeekAvgElev > 0 ? thisWeekElev / fourWeekAvgElev : 0
  const acwrDur = fourWeekAvgDur > 0 ? thisWeekDur / fourWeekAvgDur : 0

  return (
    <Card title="Endurance Load (ACWR)">
      <div className="space-y-4">
        {/* ACWR badges */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-bg-primary/50 rounded-lg p-2">
            <div className="text-[10px] text-text-muted">Weekly Vertical Gain</div>
            <div className="text-sm font-semibold text-text-primary">
              {thisWeekElev.toLocaleString()}m
            </div>
            <div className="text-[10px] text-text-muted">
              4wk avg: {Math.round(fourWeekAvgElev).toLocaleString()}m
            </div>
            <div className={`text-xs font-semibold mt-1 ${acwrBgClass(acwrElev)}`}>
              ACWR {acwrElev.toFixed(2)}
            </div>
            <div className={`text-[10px] mt-0.5 ${acwrLabel(acwrElev).color}`}>
              {acwrLabel(acwrElev).text}
            </div>
          </div>
          <div className="bg-bg-primary/50 rounded-lg p-2">
            <div className="text-[10px] text-text-muted">Weekly Mountain Duration</div>
            <div className="text-sm font-semibold text-text-primary">
              {formatDuration(thisWeekDur)}
            </div>
            <div className="text-[10px] text-text-muted">
              4wk avg: {formatDuration(Math.round(fourWeekAvgDur))}
            </div>
            <div className={`text-xs font-semibold mt-1 ${acwrBgClass(acwrDur)}`}>
              ACWR {acwrDur.toFixed(2)}
            </div>
            <div className={`text-[10px] mt-0.5 ${acwrLabel(acwrDur).color}`}>
              {acwrLabel(acwrDur).text}
            </div>
          </div>
        </div>

        {/* This week vs plan context */}
        <div className="bg-bg-primary/50 rounded-lg p-2">
          <div className="text-[10px] text-text-muted mb-1">This week vs typical</div>
          <div className="text-xs text-text-secondary">
            {fourWeekAvgElev > 0 ? (
              <>
                Vertical: {thisWeekElev.toLocaleString()}m vs {Math.round(fourWeekAvgElev).toLocaleString()}m avg
                <span className={`ml-1 font-semibold ${
                  thisWeekElev > fourWeekAvgElev * 1.3
                    ? 'text-accent-red'
                    : thisWeekElev < fourWeekAvgElev * 0.7
                      ? 'text-accent-yellow'
                      : 'text-accent-green'
                }`}>
                  ({thisWeekElev > fourWeekAvgElev
                    ? `+${Math.round(((thisWeekElev - fourWeekAvgElev) / fourWeekAvgElev) * 100)}%`
                    : `${Math.round(((thisWeekElev - fourWeekAvgElev) / fourWeekAvgElev) * 100)}%`})
                </span>
              </>
            ) : (
              <span className="text-text-muted">Not enough history for comparison</span>
            )}
          </div>
        </div>

        {/* 8-week elevation bar chart */}
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weeklyData} margin={{ top: 5, right: 5, left: -15, bottom: 0 }}>
              <XAxis
                dataKey="weekNum"
                tick={{ fontSize: 10, fill: '#555570' }}
                tickFormatter={(w) => `Wk${w}`}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#555570' }}
                axisLine={false}
                tickLine={false}
                width={45}
                tickFormatter={(v) => `${v}m`}
              />
              <Tooltip
                contentStyle={{
                  background: '#1a1a2e',
                  border: '1px solid #2a2a4a',
                  borderRadius: 8,
                  fontSize: 11,
                  color: '#e4e4ef',
                }}
                formatter={(value: unknown) => [`${Number(value).toLocaleString()}m`, 'Elevation']}
                labelFormatter={(w: unknown) => `Week ${w}`}
              />
              <Bar dataKey="elevation" radius={[4, 4, 0, 0]}>
                {weeklyData.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={idx === currentIdx ? '#38bdf8' : '#2a2a4a'}
                    opacity={idx === currentIdx ? 1 : 0.7}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 6. Session History
// ═══════════════════════════════════════════════════════════════════
function SessionHistory({
  sessions,
  sets,
}: {
  sessions: TrainingSession[]
  sets: TrainingSet[]
}) {
  const recentSessions = sessions.slice(0, 10)

  if (recentSessions.length === 0) {
    return (
      <Card title="Session History">
        <div className="text-sm text-text-muted py-2">No sessions logged yet</div>
      </Card>
    )
  }

  return (
    <Card title="Session History">
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {recentSessions.map((session) => {
          const sessionSets = sets.filter((s) => s.session_id === session.id)
          const exerciseNames = [
            ...new Set(sessionSets.map((s) => s.exercises?.name).filter(Boolean)),
          ]

          return (
            <div
              key={session.id}
              className="bg-bg-primary/50 rounded-lg px-3 py-2 space-y-1"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Dumbbell size={12} className="text-gym shrink-0" />
                  <span className="text-xs font-medium text-text-primary">
                    {session.name ?? 'Session'}
                  </span>
                </div>
                <span className="text-[10px] text-text-muted">{session.date}</span>
              </div>

              <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-text-secondary">
                {session.duration_minutes != null && <span>{session.duration_minutes} min</span>}
                {session.total_volume_kg != null && (
                  <span>{Math.round(session.total_volume_kg).toLocaleString()}kg volume</span>
                )}
                {session.total_sets != null && <span>{session.total_sets} sets</span>}
              </div>

              {exerciseNames.length > 0 && (
                <div className="text-[10px] text-text-muted truncate">
                  {exerciseNames.join(' \u00B7 ')}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default TrainingPlanView
