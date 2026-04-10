import { useState, useMemo } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import {
  useActivities,
  useTrainingSessions,
  useTrainingSets,
  useCoachingLog,
  usePlannedWorkouts,
} from '../hooks/useSupabase'
import type { Activity, TrainingSession, TrainingSet, CoachingLogEntry, PlannedWorkout, WorkoutDefinition } from '../lib/types'
import {
  getProgramWeek,
  getWeekSchedule,
  isDeloadWeek,
} from '../lib/program'
import { format, startOfWeek, endOfWeek, isWithinInterval } from 'date-fns'
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
import { formatDuration } from '../lib/format'
import { loadChangeColor } from '../lib/colors'
import { MOUNTAIN_ACTIVITY_TYPES } from '../lib/constants'
import { MountainActivityCard } from '../components/MountainActivityCard'

const darkTooltipStyle = {
  background: '#16161e',
  border: '1px solid #262636',
  borderRadius: 12,
  fontSize: 12,
  color: '#f0f0f5',
}

// ─── Helpers ───────────────────────────────────────────────────────
function fmtDate(d: Date): string {
  return format(d, 'yyyy-MM-dd')
}

function normalizeExName(name: string): string {
  return name.toLowerCase().replace(/[_\s-]+/g, ' ').replace(/&/g, 'and').trim()
}

function exerciseNameMatch(a: string, b: string): boolean {
  return normalizeExName(a) === normalizeExName(b)
}

// ═══════════════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════════════
export function TrainingPlanView() {
  const activitiesQuery = useActivities(60)
  const sessionsQuery = useTrainingSessions(60)
  const coachingQuery = useCoachingLog(7)
  const plannedQuery = usePlannedWorkouts()

  const sessionIds = useMemo(
    () => (sessionsQuery.data ?? []).map((s: TrainingSession) => s.id),
    [sessionsQuery.data]
  )
  const setsQuery = useTrainingSets(sessionIds)

  const loading =
    activitiesQuery.loading || sessionsQuery.loading || coachingQuery.loading || setsQuery.loading || plannedQuery.loading
  const error =
    activitiesQuery.error || sessionsQuery.error || coachingQuery.error || setsQuery.error || plannedQuery.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const activities = (activitiesQuery.data ?? []) as Activity[]
  const sessions = (sessionsQuery.data ?? []) as TrainingSession[]
  const sets = (setsQuery.data ?? []) as TrainingSet[]
  const coaching = (coachingQuery.data ?? []) as CoachingLogEntry[]
  const planned = (plannedQuery.data ?? []) as PlannedWorkout[]

  return (
    <div className="space-y-3 pb-8">
      <ProgramOverview activities={activities} sessions={sessions} planned={planned} />
      <WeekGrid activities={activities} planned={planned} />
      <TodaySession sessions={sessions} sets={sets} coaching={coaching} planned={planned} />
      <LiftProgressionTracker sessions={sessions} sets={sets} planned={planned} />
      <EnduranceLoadTracker activities={activities} />
      <SessionHistory sessions={sessions} sets={sets} />
      <SystemArchitecture />
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 1. Program Overview
// ═══════════════════════════════════════════════════════════════════
function ProgramOverview({
  activities,
  sessions,
  planned,
}: {
  activities: Activity[]
  sessions: TrainingSession[]
  planned: PlannedWorkout[]
}) {
  const today = new Date()
  const { block, week } = getProgramWeek(today)
  const nextDeload = week <= 4 ? 4 : 8
  const pctDone = (week / 8) * 100

  const weekStart = startOfWeek(today, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(today, { weekStartsOn: 1 })

  const { gymCompleted, mountainCompleted, isConsolidated, gymTarget, rpeRange } = useMemo(() => {
    const inWeek = (dateStr: string) => {
      const d = new Date(dateStr + 'T12:00:00')
      return isWithinInterval(d, { start: weekStart, end: weekEnd })
    }

    const gym = sessions.filter((s) => inWeek(s.date)).length
    const mountain = activities.filter(
      (a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type) && inWeek(a.date)
    ).length

    const thisWeekPlanned = planned.filter((pw) => pw.week_number === week)
    const target = thisWeekPlanned.length || (block === 1 ? 3 : 3)

    const consolidated = thisWeekPlanned.some(
      (pw) => pw.workout_definition?.session_label === 'A2' || pw.workout_definition?.session_label === 'B2'
    )

    let rpe = block === 1 ? '6-7' : '7-8'
    if (thisWeekPlanned.length > 0 && thisWeekPlanned[0].workout_definition?.rpe_range) {
      const r = thisWeekPlanned[0].workout_definition.rpe_range
      rpe = `${r[0]}-${r[1]}`
    }

    return { gymCompleted: gym, mountainCompleted: mountain, isConsolidated: consolidated, gymTarget: target, rpeRange: rpe }
  }, [activities, sessions, planned, weekStart, weekEnd, week, block])

  return (
    <Card>
      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-bold text-text-primary">
            Base Rebuild &mdash; Block {block} of 2
          </h2>
          <p className="text-[14px] text-text-secondary mt-0.5">
            Week {week} / 8 &middot; Apr 1 &ndash; May 26
          </p>
        </div>

        <div className="w-full bg-border rounded-full h-2">
          <div className="bg-accent-blue rounded-full h-2 transition-all" style={{ width: `${pctDone}%` }} />
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[14px]">
          <span className={gymCompleted >= gymTarget ? 'text-accent-green font-semibold' : 'text-text-secondary'}>
            Gym: {gymCompleted}/{gymTarget}
          </span>
          <span className={mountainCompleted > 0 ? 'text-accent-green font-semibold' : 'text-text-secondary'}>
            Mountain: {mountainCompleted}
          </span>
          {isConsolidated && (
            <span className="text-accent-yellow text-[13px] font-semibold">
              2x consolidated (A2 Wed + B2 Fri)
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-text-muted">
          <span>{isConsolidated ? '2x/week gym (consolidated)' : `${gymTarget}x/week gym`} + mountain days</span>
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

function statusPillBg(status: PlannedWorkout['status'], scheduledDate: string): string {
  const today = new Date()
  const todayStr = format(today, 'yyyy-MM-dd')

  switch (status) {
    case 'completed':
      return 'bg-accent-green/25 text-accent-green'
    case 'adjusted':
      return 'bg-accent-yellow/25 text-accent-yellow'
    case 'skipped':
      return 'bg-bg-primary/40 text-text-dim line-through'
    case 'planned':
      if (scheduledDate === todayStr) return 'bg-accent-blue/25 text-accent-blue'
      if (scheduledDate < todayStr) return 'bg-accent-red/25 text-accent-red'
      return 'bg-accent-purple/20 text-accent-purple'
    default:
      return 'bg-bg-primary/40 text-text-dim'
  }
}

function WeekGrid({ activities, planned }: { activities: Activity[]; planned: PlannedWorkout[] }) {
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null)
  const { week: currentWeek } = getProgramWeek(new Date())

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

  const plannedByWeek = useMemo(() => {
    const m = new Map<number, PlannedWorkout[]>()
    planned.forEach((pw) => {
      const existing = m.get(pw.week_number) ?? []
      existing.push(pw)
      m.set(pw.week_number, existing)
    })
    return m
  }, [planned])

  const consolidatedWeeks = useMemo(() => {
    const s = new Set<number>()
    planned.forEach((pw) => {
      const label = pw.workout_definition?.session_label
      if (label === 'A2' || label === 'B2') s.add(pw.week_number)
    })
    return s
  }, [planned])

  const weeks = useMemo(() => Array.from({ length: 8 }, (_, i) => i + 1), [])

  return (
    <Card title="8-Week Program">
      <div className="space-y-1">
        {weeks.map((weekNum) => {
          const isCurrent = weekNum === currentWeek
          const isExpanded = expandedWeek === weekNum
          const isConsolidatedWeek = consolidatedWeeks.has(weekNum)
          const weekPlanned = plannedByWeek.get(weekNum) ?? []
          const deload = isDeloadWeek(weekNum)

          const ws = getWeekSchedule(weekNum)
          const allWeekDates = ws.days.map((d) => fmtDate(d.date))
          const mountainDates = new Set(allWeekDates.filter((d) => mountainByDate.has(d)))
          const mountainCompleted = mountainDates.size
          // Exclude gym sessions replaced by mountain days
          const activeGymPlanned = weekPlanned.filter(
            (pw) => !(mountainDates.has(pw.scheduled_date) &&
              (pw.status === 'skipped' || pw.status === 'adjusted'))
          )
          const gymTarget = activeGymPlanned.length || 3
          const gymCompleted = activeGymPlanned.filter((pw) => pw.status === 'completed').length

          return (
            <div key={weekNum}>
              <button
                onClick={() => setExpandedWeek(isExpanded ? null : weekNum)}
                className={`w-full text-left px-3 py-2.5 rounded-xl transition-colors hover:bg-bg-card-hover ${
                  isCurrent ? 'border-l-2 border-accent-blue bg-bg-card-hover/50' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  {isExpanded ? <ChevronDown size={14} className="text-text-dim shrink-0" /> : <ChevronRight size={14} className="text-text-dim shrink-0" />}
                  <span className="text-[14px] font-semibold text-text-primary">Week {weekNum}</span>
                  {isCurrent && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent-blue/25 text-accent-blue font-semibold">
                      Current
                    </span>
                  )}
                  {deload && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent-yellow/25 text-accent-yellow font-semibold">
                      Deload
                    </span>
                  )}
                  {isConsolidatedWeek && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent-purple/20 text-accent-purple font-semibold">
                      Consolidated
                    </span>
                  )}
                  <span className="ml-auto text-[12px] text-text-secondary font-medium">
                    <Dumbbell size={11} className="inline text-gym mr-0.5" />
                    {gymCompleted}/{gymTarget}
                    <span className="mx-1.5 text-text-dim">&middot;</span>
                    <Mountain size={11} className="inline text-mountain mr-0.5" />
                    {mountainCompleted}
                  </span>
                </div>

                <div className="flex gap-1.5 flex-wrap ml-5">
                  {activeGymPlanned.map((pw) => {
                    const shortLabel = pw.workout_definition?.session_name
                      ? pw.workout_definition.session_name.replace(/^Strength [A-Z]: /, '')
                      : pw.session_name
                    const bg = statusPillBg(pw.status, pw.scheduled_date)

                    return (
                      <span
                        key={pw.id}
                        className={`inline-block text-[11px] px-2 py-0.5 rounded-full font-semibold whitespace-nowrap ${bg}`}
                        title={`${pw.scheduled_date} — ${shortLabel}`}
                      >
                        {shortLabel}
                      </span>
                    )
                  })}
                  {allWeekDates
                    .filter((d) => mountainByDate.has(d))
                    .map((d) => (
                      <span
                        key={`mtn-${d}`}
                        className="inline-block text-[11px] px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap bg-sky-500/20 text-sky-400"
                        title={d}
                      >
                        {'\u{1F3D4}'}
                      </span>
                    ))}
                </div>
              </button>

              {isExpanded && (
                <WeekExpanded
                  weekPlanned={weekPlanned}
                  mountainByDate={mountainByDate}
                  allWeekDates={allWeekDates}
                  deload={deload}
                />
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}

// ─── Week Expanded: merged & date-sorted gym + mountain items ───
function WeekExpanded({
  weekPlanned,
  mountainByDate,
  allWeekDates,
  deload,
}: {
  weekPlanned: PlannedWorkout[]
  mountainByDate: Map<string, Activity[]>
  allWeekDates: string[]
  deload: boolean
}) {
  // Build a unified list sorted by date
  type Item =
    | { kind: 'gym'; date: string; pw: PlannedWorkout }
    | { kind: 'mountain'; date: string; activity: Activity; idx: number }

  const items: Item[] = []

  // Dates that have a mountain activity (used to suppress skipped gym sessions)
  const mountainDates = new Set(allWeekDates.filter((d) => mountainByDate.has(d)))

  weekPlanned.forEach((pw) => {
    // Don't show gym sessions that were replaced by mountain days
    if (mountainDates.has(pw.scheduled_date) &&
        (pw.status === 'skipped' || pw.status === 'adjusted')) return
    items.push({ kind: 'gym', date: pw.scheduled_date, pw })
  })

  allWeekDates
    .filter((d) => mountainByDate.has(d))
    .forEach((dateStr) => {
      (mountainByDate.get(dateStr) ?? []).forEach((a, ai) => {
        items.push({ kind: 'mountain', date: dateStr, activity: a, idx: ai })
      })
    })

  items.sort((a, b) => a.date.localeCompare(b.date))

  if (items.length === 0) {
    return (
      <div className="ml-2 mr-1 mb-2 mt-1">
        <div className="text-[13px] text-text-dim py-1">No planned sessions this week</div>
      </div>
    )
  }

  return (
    <div className="ml-2 mr-1 mb-2 mt-1 space-y-3">
      {items.map((item) => {
        if (item.kind === 'mountain') {
          return (
            <MountainActivityCard
              key={`mtn-${item.date}-${item.idx}`}
              activity={item.activity}
            />
          )
        }

        const pw = item.pw
        const def = pw.workout_definition as WorkoutDefinition | null
        const exercises = def?.exercises ?? []
        const warmup = def?.warmup ?? []
        const rpeLabel = deload
          ? 'Deload 50% vol'
          : def?.rpe_range
            ? `RPE ${def.rpe_range[0]}-${def.rpe_range[1]}`
            : ''
        const sessionLabel = def?.session_name ?? pw.session_name

        return (
          <div key={pw.id} className="bg-bg-primary/50 rounded-xl px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
              <Dumbbell size={15} className="text-gym shrink-0" />
              <span className="text-[15px] font-semibold text-text-primary">
                {sessionLabel}
              </span>
              {pw.status === 'completed' && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent-green/25 text-accent-green font-semibold">
                  Done
                </span>
              )}
              {pw.status === 'adjusted' && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent-yellow/25 text-accent-yellow font-semibold">
                  Adjusted
                </span>
              )}
              {pw.status === 'skipped' && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-bg-primary/60 text-text-dim font-semibold">
                  Skipped
                </span>
              )}
            </div>
            <div className="text-[13px] text-text-muted mb-2">
              {pw.scheduled_date} &middot; {rpeLabel}
              {def?.estimated_duration_minutes && (
                <span> &middot; ~{def.estimated_duration_minutes} min</span>
              )}
            </div>

            {pw.status === 'adjusted' && pw.adjustment_reason && (
              <div className="text-[13px] text-accent-yellow bg-accent-yellow/10 rounded-lg px-3 py-2 mb-3">
                {pw.adjustment_reason}
              </div>
            )}

            {warmup.length > 0 && <WarmupSection warmup={warmup} />}

            <table className="w-full text-[14px]">
              <thead>
                <tr className="text-text-muted border-b border-border">
                  <th className="text-left py-2 font-semibold pr-2 text-[12px] uppercase tracking-wider">Exercise</th>
                  <th className="text-right py-2 font-semibold px-2 whitespace-nowrap text-[12px] uppercase tracking-wider">Sets×Reps</th>
                  <th className="text-right py-2 font-semibold pl-2 w-20 text-[12px] uppercase tracking-wider">Weight</th>
                </tr>
              </thead>
              <tbody>
                {exercises.map((ex) => {
                  const setsReps = deload
                    ? `${Math.ceil(ex.sets / 2)}\u00D7${ex.reps}`
                    : `${ex.sets}\u00D7${ex.reps}`
                  return (
                    <tr key={ex.name} className="border-b border-border-subtle last:border-0">
                      <td className="py-2 pr-2 text-text-primary">
                        {ex.name}
                        {ex.note && <span className="text-text-dim ml-1.5 text-[12px]">({ex.note})</span>}
                      </td>
                      <td className="py-2 px-2 text-right font-mono text-text-secondary whitespace-nowrap">{setsReps}</td>
                      <td className="py-2 pl-2 text-right font-mono text-text-primary font-semibold w-20">
                        {ex.weight_kg != null && ex.weight_kg > 0 ? `${ex.weight_kg}kg` : '\u2014'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}

// ─── Warmup collapsible section ──────────────────────────────────
function WarmupSection({ warmup }: { warmup: { name: string; reps: number | null; duration_s: number | null }[] }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mb-3 border-b border-border-subtle pb-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-[11px] text-text-dim hover:text-text-muted transition-colors"
      >
        {open ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
        Warmup ({warmup.length} exercises)
      </button>
      {open && (
        <div className="mt-1.5 ml-3 space-y-0.5">
          {warmup.map((w) => (
            <div key={w.name} className="flex justify-between text-[11px] font-mono text-text-dim">
              <span className="italic">{w.name}</span>
              <span>
                {w.reps != null ? `${w.reps} reps` : ''}
                {w.duration_s != null ? `${w.duration_s}s` : ''}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// 3. Today's Session
// ═══════════════════════════════════════════════════════════════════
function TodaySession({
  sessions,
  sets,
  coaching,
  planned,
}: {
  sessions: TrainingSession[]
  sets: TrainingSet[]
  coaching: CoachingLogEntry[]
  planned: PlannedWorkout[]
}) {
  const today = new Date()
  const todayStr = fmtDate(today)
  const { block, week } = getProgramWeek(today)

  const todayPlanned = planned.find((pw) => pw.scheduled_date === todayStr)
  if (!todayPlanned) return null

  const def = todayPlanned.workout_definition as WorkoutDefinition | null
  const exercises = def?.exercises ?? []
  const warmup = def?.warmup ?? []
  const rpeTarget = def?.rpe_range ? `${def.rpe_range[0]}-${def.rpe_range[1]}` : block === 1 ? '6-7' : '7-8'
  const estDuration = def?.estimated_duration_minutes ? `~${def.estimated_duration_minutes} min` : ''
  const sessionName = def?.session_name ?? todayPlanned.session_name

  const todaySession = sessions.find((s) => s.date === todayStr)
  const todaySets = todaySession ? sets.filter((s) => s.session_id === todaySession.id) : []
  const todayNotes = coaching.filter((c) => c.date === todayStr && c.type !== 'heartbeat')

  return (
    <Card>
      <div className="space-y-3">
        <div>
          <div className="flex items-center gap-2">
            <Dumbbell size={16} className="text-gym" />
            <h3 className="text-[14px] font-bold text-text-primary">Today's Session</h3>
            {todayPlanned.status === 'adjusted' && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-accent-yellow/20 text-accent-yellow font-semibold">
                Adjusted
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5 text-[13px] text-text-muted">
            <span className="text-gym font-semibold">{sessionName}</span>
            <span>Block {block} / Week {week}</span>
            <span>RPE {rpeTarget}</span>
            {estDuration && <span>{estDuration}</span>}
          </div>
        </div>

        {todayPlanned.status === 'adjusted' && todayPlanned.adjustment_reason && (
          <div className="text-[13px] text-accent-yellow bg-accent-yellow/10 rounded-lg px-3 py-2">
            {todayPlanned.adjustment_reason}
          </div>
        )}

        {warmup.length > 0 && <WarmupSection warmup={warmup} />}

        <div className="overflow-x-auto -mx-4 px-4">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-text-muted border-b border-border">
                <th className="text-left py-1.5 font-semibold text-[11px] uppercase tracking-wider">Exercise</th>
                <th className="text-left py-1.5 font-semibold text-[11px] uppercase tracking-wider">Target</th>
                <th className="text-left py-1.5 font-semibold text-[11px] uppercase tracking-wider">Actual</th>
              </tr>
            </thead>
            <tbody>
              {exercises.map((ex) => {
                const targetStr = ex.weight_kg
                  ? `${ex.sets}\u00D7${ex.reps} @ ${ex.weight_kg}kg`
                  : `${ex.sets}\u00D7${ex.reps}`

                const actualSetsForExercise = todaySets.filter(
                  (s) => s.exercises?.name != null && exerciseNameMatch(s.exercises.name, ex.name) && s.set_type === 'working'
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
                  <tr key={ex.name} className="border-b border-border-subtle last:border-0">
                    <td className="py-2 text-text-primary">
                      {ex.name}
                      {ex.note && <span className="text-text-dim ml-1.5 text-[11px]">({ex.note})</span>}
                    </td>
                    <td className="py-2 text-text-secondary font-mono">{targetStr}</td>
                    <td className={`py-2 font-mono font-semibold ${actualStr !== '\u2014' ? 'text-accent-green' : 'text-text-dim'}`}>
                      {actualStr}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {todayNotes.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-[11px] text-text-muted font-semibold uppercase tracking-wider">
              Coach Notes
            </div>
            {todayNotes.map((n) => (
              <div key={n.id} className="text-[13px] text-text-secondary bg-bg-primary/50 rounded-lg px-3 py-2">
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

function LiftProgressionTracker({
  sessions,
  sets,
  planned,
}: {
  sessions: TrainingSession[]
  sets: TrainingSet[]
  planned: PlannedWorkout[]
}) {
  const { week: currentWeek } = getProgramWeek(new Date())

  const barbellLifts = useMemo(() => {
    const names = new Set<string>()
    planned.forEach((pw) => {
      const def = pw.workout_definition as WorkoutDefinition | null
      if (!def?.exercises) return
      def.exercises.forEach((ex) => {
        if (ex.weight_kg != null && ex.weight_kg > 0) names.add(ex.name)
      })
    })
    return Array.from(names)
  }, [planned])

  const exercisesWithData = useMemo(() => {
    const names = new Set<string>()
    sets.forEach((s) => {
      if (s.exercises?.name && s.set_type === 'working' && s.weight_kg != null && s.weight_kg > 0) {
        names.add(s.exercises.name)
      }
    })
    return names
  }, [sets])

  const hasActualData = (plannedName: string): boolean => {
    for (const dbName of exercisesWithData) {
      if (exerciseNameMatch(dbName, plannedName)) return true
    }
    return false
  }

  const liftOptions = useMemo(() => {
    const withData: string[] = []
    const noData: string[] = []

    for (const name of barbellLifts) {
      if (hasActualData(name)) withData.push(name)
      else noData.push(name)
    }
    const allPlannedNames = new Set<string>()
    planned.forEach((pw) => {
      const def = pw.workout_definition as WorkoutDefinition | null
      if (!def?.exercises) return
      def.exercises.forEach((ex) => allPlannedNames.add(ex.name))
    })
    exercisesWithData.forEach((dbName) => {
      const alreadyIncluded = barbellLifts.some((bl) => exerciseNameMatch(bl, dbName))
      if (!alreadyIncluded) {
        for (const plannedName of allPlannedNames) {
          if (exerciseNameMatch(dbName, plannedName)) {
            withData.push(plannedName)
            break
          }
        }
      }
    })

    return { withData, noData }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exercisesWithData, barbellLifts, planned])

  const defaultLift = liftOptions.withData[0] ?? liftOptions.noData[0] ?? 'Barbell Back Squat'
  const [selectedLift, setSelectedLift] = useState(defaultLift)
  const [showAll, setShowAll] = useState(false)

  const plannedWeightsByWeek = useMemo(() => {
    const map = new Map<number, number>()
    planned.forEach((pw) => {
      const def = pw.workout_definition as WorkoutDefinition | null
      if (!def?.exercises) return
      const ex = def.exercises.find((e) => e.name === selectedLift)
      if (ex?.weight_kg != null) {
        const existing = map.get(pw.week_number)
        if (existing == null || ex.weight_kg > existing) {
          map.set(pw.week_number, ex.weight_kg)
        }
      }
    })
    return map
  }, [planned, selectedLift])

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
          s.exercises?.name != null &&
          exerciseNameMatch(s.exercises.name, selectedLift) &&
          s.set_type === 'working' &&
          s.weight_kg != null
      )
      if (weekSets.length > 0) {
        map.set(w, Math.max(...weekSets.map((s) => s.weight_kg!)))
      }
    }
    return map
  }, [selectedLift, sessions, sets])

  const analysis = useMemo(() => {
    let lastActualWeight: number | null = null
    let lastActualWeek: number | null = null
    for (let w = currentWeek; w >= 1; w--) {
      if (actualWeightsByWeek.has(w)) {
        lastActualWeight = actualWeightsByWeek.get(w)!
        lastActualWeek = w
        break
      }
    }

    if (lastActualWeight === null) {
      return {
        status: 'no_data' as const,
        statusLabel: 'No sessions yet',
        lastActualWeight: null,
        trend: null as 'up' | 'flat' | 'down' | null,
        weeksAtSameWeight: 0,
      }
    }

    let weeksAtSameWeight = 0
    for (let w = lastActualWeek!; w >= 1; w--) {
      const wt = actualWeightsByWeek.get(w)
      if (wt === lastActualWeight) weeksAtSameWeight++
      else break
    }

    const recentWeights: number[] = []
    for (let w = lastActualWeek!; w >= 1 && recentWeights.length < 3; w--) {
      if (actualWeightsByWeek.has(w)) recentWeights.unshift(actualWeightsByWeek.get(w)!)
    }
    let trend: 'up' | 'flat' | 'down' | null = null
    if (recentWeights.length >= 2) {
      const last = recentWeights[recentWeights.length - 1]
      const prev = recentWeights[recentWeights.length - 2]
      if (last > prev) trend = 'up'
      else if (last < prev) trend = 'down'
      else trend = 'flat'
    }

    const plannedForLastWeek = plannedWeightsByWeek.get(lastActualWeek!)
    let status: 'on_track' | 'ahead' | 'stalled' | 'behind' | 'no_data' = 'on_track'
    let statusLabel = 'On track'

    if (plannedForLastWeek != null) {
      if (lastActualWeight > plannedForLastWeek) {
        status = 'ahead'
        statusLabel = 'Ahead of plan'
      } else if (lastActualWeight >= plannedForLastWeek) {
        status = 'on_track'
        statusLabel = 'On track'
      } else {
        status = 'behind'
        statusLabel = 'Behind plan'
      }
    }

    if (status !== 'ahead') {
      if (weeksAtSameWeight >= 3) {
        status = 'stalled'
        statusLabel = `Stalled ${weeksAtSameWeight} weeks`
      } else if (weeksAtSameWeight >= 2 && status !== 'on_track') {
        status = 'stalled'
        statusLabel = `Same weight for ${weeksAtSameWeight} weeks`
      }
    }

    return { status, statusLabel, lastActualWeight, trend, weeksAtSameWeight }
  }, [selectedLift, currentWeek, actualWeightsByWeek, plannedWeightsByWeek])

  const statusColors: Record<string, string> = {
    on_track: 'text-accent-green',
    ahead: 'text-accent-blue',
    stalled: 'text-accent-red',
    behind: 'text-accent-yellow',
    no_data: 'text-text-dim',
  }

  const trendArrows: Record<string, string> = {
    up: '\u2197',
    flat: '\u2192',
    down: '\u2198',
  }

  const chartData = useMemo(() => {
    return Array.from({ length: 8 }, (_, i) => {
      const weekNum = i + 1
      return {
        week: `Wk${weekNum}`,
        planned: plannedWeightsByWeek.get(weekNum) ?? null,
        actual: actualWeightsByWeek.get(weekNum) ?? null,
        deload: isDeloadWeek(weekNum),
        isCurrent: weekNum === currentWeek,
      }
    })
  }, [plannedWeightsByWeek, actualWeightsByWeek, currentWeek])

  return (
    <Card>
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-1">Lift Progression</div>
            <div className="text-[16px] font-bold text-text-primary">{selectedLift}</div>
          </div>
          <div className="text-right">
            <div className={`text-[14px] font-semibold ${statusColors[analysis.status]}`}>
              {analysis.trend && trendArrows[analysis.trend]} {analysis.statusLabel}
            </div>
            {analysis.lastActualWeight != null && (
              <div className="text-[12px] text-text-muted mt-0.5">
                Last: {analysis.lastActualWeight}kg
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-1.5 flex-wrap">
          {liftOptions.withData.map((lift) => (
            <button
              key={lift}
              onClick={() => setSelectedLift(lift)}
              className={`text-[12px] px-3 py-1.5 rounded-full border transition-colors ${
                selectedLift === lift
                  ? 'bg-gym/15 text-gym border-gym/30 font-semibold'
                  : 'text-text-secondary border-border hover:text-text-primary hover:border-border'
              }`}
            >
              {lift.replace('Barbell ', '').replace('Dumbbell ', '').replace('KB ', '')}
            </button>
          ))}
          {showAll && liftOptions.noData.map((lift) => (
            <button
              key={lift}
              onClick={() => setSelectedLift(lift)}
              className={`text-[12px] px-3 py-1.5 rounded-full border transition-colors ${
                selectedLift === lift
                  ? 'bg-gym/15 text-gym border-gym/30 font-semibold'
                  : 'text-text-dim border-border hover:text-text-muted'
              }`}
            >
              {lift.replace('Barbell ', '').replace('Dumbbell ', '').replace('KB ', '')}
            </button>
          ))}
          {liftOptions.noData.length > 0 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-[11px] px-2 py-1.5 text-text-dim hover:text-text-muted"
            >
              {showAll ? 'less' : `+${liftOptions.noData.length} more`}
            </button>
          )}
        </div>

        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: 5, bottom: 0 }}>
              <XAxis dataKey="week" tick={{ fontSize: 11, fill: '#646478' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#646478' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} width={52} unit="kg" />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Line type="monotone" dataKey="planned" stroke="#646478" strokeDasharray="4 4" strokeWidth={1.5} dot={false} name="Planned" />
              <Line type="monotone" dataKey="actual" stroke="#a78bfa" strokeWidth={2.5} dot={{ r: 5, fill: '#a78bfa', stroke: '#16161e', strokeWidth: 2 }} connectNulls={false} name="Actual" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex gap-4 text-[11px] text-text-muted">
            <span className="flex items-center gap-1.5">
              <span className="w-5 h-px inline-block" style={{ borderTop: '1.5px dashed #646478' }} />
              Planned (DB)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-gym inline-block" />
              Your lifts
            </span>
          </div>
          {analysis.weeksAtSameWeight >= 2 && (
            <div className="text-[11px] text-accent-red font-semibold">
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
// 5. Endurance Load Tracker
// ═══════════════════════════════════════════════════════════════════
function EnduranceLoadTracker({ activities }: { activities: Activity[] }) {
  const mountainActivities = useMemo(
    () => activities.filter((a) => MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type)),
    [activities]
  )

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

  const { week: currentWeek } = getProgramWeek(new Date())
  const currentIdx = currentWeek - 1
  const thisWeekElev = weeklyData[currentIdx]?.elevation ?? 0
  const thisWeekDur = weeklyData[currentIdx]?.duration ?? 0

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

  const elevPctChange = fourWeekAvgElev > 0 ? Math.round(((thisWeekElev - fourWeekAvgElev) / fourWeekAvgElev) * 100) : null
  const durPctChange = fourWeekAvgDur > 0 ? Math.round(((thisWeekDur - fourWeekAvgDur) / fourWeekAvgDur) * 100) : null

  const zeroElevWeeks = useMemo(() => {
    let count = 0
    for (let i = currentIdx; i >= 0; i--) {
      if (weeklyData[i]?.elevation === 0) count++
      else break
    }
    return count
  }, [weeklyData, currentIdx])

  return (
    <Card title="Mountain Load">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-bg-primary/50 rounded-xl p-3">
            <div className="text-[11px] text-text-muted font-semibold uppercase tracking-wider">Weekly Vertical Gain</div>
            <div className="text-[15px] font-bold text-text-primary mt-1">
              {thisWeekElev.toLocaleString()}m
            </div>
            <div className="text-[11px] text-text-muted mt-0.5">
              4wk avg: {Math.round(fourWeekAvgElev).toLocaleString()}m
            </div>
            {elevPctChange != null && (
              <div className={`text-[12px] font-semibold mt-1 ${loadChangeColor(elevPctChange)}`}>
                {elevPctChange >= 0 ? '+' : ''}{elevPctChange}% vs avg
              </div>
            )}
          </div>
          <div className="bg-bg-primary/50 rounded-xl p-3">
            <div className="text-[11px] text-text-muted font-semibold uppercase tracking-wider">Weekly Mountain Duration</div>
            <div className="text-[15px] font-bold text-text-primary mt-1">
              {formatDuration(thisWeekDur)}
            </div>
            <div className="text-[11px] text-text-muted mt-0.5">
              4wk avg: {formatDuration(Math.round(fourWeekAvgDur))}
            </div>
            {durPctChange != null && (
              <div className={`text-[12px] font-semibold mt-1 ${loadChangeColor(durPctChange)}`}>
                {durPctChange >= 0 ? '+' : ''}{durPctChange}% vs avg
              </div>
            )}
          </div>
        </div>

        {elevPctChange != null && elevPctChange > 15 && (
          <div className="text-[13px] font-semibold text-accent-yellow bg-accent-yellow/10 rounded-xl px-3 py-2">
            Vertical gain increased &gt;15% vs 4-week average — monitor recovery
          </div>
        )}

        {zeroElevWeeks >= 3 && (
          <div className="text-[13px] font-semibold text-accent-red bg-accent-red/10 rounded-xl px-3 py-2">
            No mountain activity for {zeroElevWeeks} consecutive weeks during mountain-primary season
          </div>
        )}

        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weeklyData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <XAxis dataKey="weekNum" tick={{ fontSize: 11, fill: '#646478' }} tickFormatter={(w) => `Wk${w}`} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#646478' }} axisLine={false} tickLine={false} width={45} tickFormatter={(v) => `${v}m`} />
              <Tooltip contentStyle={darkTooltipStyle} formatter={(value: unknown) => [`${Number(value).toLocaleString()}m`, 'Elevation']} labelFormatter={(w: unknown) => `Week ${w}`} />
              <Bar dataKey="elevation" radius={[4, 4, 0, 0]}>
                {weeklyData.map((_, idx) => (
                  <Cell key={idx} fill={idx === currentIdx ? '#38bdf8' : '#262636'} opacity={idx === currentIdx ? 1 : 0.7} />
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
function SessionHistory({ sessions, sets }: { sessions: TrainingSession[]; sets: TrainingSet[] }) {
  const recentSessions = sessions.slice(0, 10)

  if (recentSessions.length === 0) {
    return (
      <Card title="Session History">
        <div className="text-[14px] text-text-muted py-2">No sessions logged yet</div>
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
            <div key={session.id} className="bg-bg-primary/50 rounded-xl px-4 py-2.5 space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Dumbbell size={13} className="text-gym shrink-0" />
                  <span className="text-[13px] font-semibold text-text-primary">
                    {session.name ?? 'Session'}
                  </span>
                </div>
                <span className="text-[11px] text-text-muted">{session.date}</span>
              </div>

              <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-text-secondary">
                {session.duration_minutes != null && <span>{session.duration_minutes} min</span>}
                {session.total_volume_kg != null && (
                  <span>{Math.round(session.total_volume_kg).toLocaleString()}kg volume</span>
                )}
                {session.total_sets != null && <span>{session.total_sets} sets</span>}
              </div>

              {exerciseNames.length > 0 && (
                <div className="text-[11px] text-text-dim truncate">
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

// ═══════════════════════════════════════════════════════════════════
// 7. System Architecture (collapsible)
// ═══════════════════════════════════════════════════════════════════
function SystemArchitecture() {
  const [open, setOpen] = useState(false)

  return (
    <Card>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full text-left"
      >
        {open ? <ChevronDown size={14} className="text-text-dim" /> : <ChevronRight size={14} className="text-text-dim" />}
        <span className="text-[11px] font-semibold text-text-dim uppercase tracking-wider">System</span>
      </button>
      {open && (
        <pre className="mt-3 text-[11px] leading-relaxed font-mono text-text-dim bg-bg-primary/50 rounded-xl px-4 py-3 overflow-x-auto whitespace-pre">{`Data Flow:
  coaching-program.md (Opus) -> workout_generator.py -> planned_workouts table -> This app

Coaching Cycle:
  Sunday: Generate next week's plan -> Push to Calendar
  Daily: Check recovery -> Push workout to Garmin (if green)
  Post-workout: Garmin sync -> mark_completed -> compliance score

Adjustment Flow:
  Jarvis detects mountain day -> Updates planned_workouts (status='adjusted')
  -> App reflects change immediately

Weight Progression:
  progression_engine.py -> exercise_progression table -> workout_definition weights

Scripts:
  garmin_sync.py       - Pull Garmin data -> Supabase (daily 09:00)
  scale_sync.py        - Pull Xiaomi weight -> Supabase (daily 10:00)
  workout_generator.py - Populate/update planned_workouts
  workout_push.py      - Push workout to Garmin watch
  morning_briefing.py  - Daily Slack briefing (10:05)`}</pre>
      )}
    </Card>
  )
}

export default TrainingPlanView
