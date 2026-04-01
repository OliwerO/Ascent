import { Sparkline } from '../components/Sparkline'
import { LoadingState } from '../components/LoadingState'
import { useDailySummary, useHRV, useDailyMetrics, useActivities, useCoachingLog } from '../hooks/useSupabase'
import {
  getProgramWeek, isDeloadWeek, getSessionForDate, SESSION_NAMES,
  getPlannedWeight,
} from '../lib/program'
import { Clock, Flame, ArrowUpRight, Heart, Dumbbell, Mountain, ChevronDown } from 'lucide-react'
import { useState } from 'react'

// ─── Helpers ──────────────────────────────────────────────────────

function hrvStatus(status: string | null | undefined): { color: string; label: string } {
  if (!status) return { color: 'text-accent-yellow', label: 'Unknown' }
  const s = status.toUpperCase()
  if (s === 'BALANCED') return { color: 'text-accent-green', label: 'Balanced' }
  if (s === 'UNBALANCED') return { color: 'text-accent-yellow', label: 'Unbalanced' }
  return { color: 'text-accent-red', label: 'Low' }
}

function sleepColor(hours: number | null): string {
  if (hours == null) return 'text-text-muted'
  if (hours >= 7) return 'text-accent-green'
  if (hours >= 6) return 'text-accent-yellow'
  return 'text-accent-red'
}

function metricColor(value: number | null, green: number, yellow: number): string {
  if (value == null) return 'text-text-muted'
  if (value >= green) return 'text-accent-green'
  if (value >= yellow) return 'text-accent-yellow'
  return 'text-accent-red'
}

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatActivityType(type: string | null | undefined): string {
  if (!type) return ''
  return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// ─── Session exercise definitions ─────────────────────────────────

type SessionType = 'A' | 'B' | 'C' | 'A2' | 'B2'

const SESSION_EXERCISES: Record<SessionType, { name: string; sets: number; reps: number | string }[]> = {
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
    { name: 'Core Circuit', sets: 3, reps: '1 round' },
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
    { name: 'Overhead Press', sets: 3, reps: 10 },
    { name: 'Barbell Row', sets: 3, reps: 10 },
    { name: 'KB Swings', sets: 3, reps: 15 },
    { name: 'KB Halo', sets: 2, reps: 10 },
    { name: 'Core Circuit', sets: 3, reps: '1 round' },
  ],
  B2: [
    { name: 'Trap Bar Deadlift', sets: 3, reps: 8 },
    { name: 'KB Clean & Press', sets: 3, reps: 8 },
    { name: 'Chin-ups', sets: 3, reps: 8 },
    { name: 'Bulgarian Split Squat', sets: 2, reps: 10 },
    { name: 'KB Turkish Get-up', sets: 2, reps: 3 },
    { name: 'KB Farmer Carry', sets: 3, reps: '40m' },
  ],
}

// ─── Main Component ───────────────────────────────────────────────

export default function TodayView() {
  const summary = useDailySummary(7)
  const hrv = useHRV(14)
  const metrics = useDailyMetrics(7)
  const activities = useActivities(7)
  const coaching = useCoachingLog(1)
  const [showExercises, setShowExercises] = useState(false)

  const loading = summary.loading || hrv.loading || metrics.loading || activities.loading
  const error = summary.error || hrv.error || metrics.error || activities.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const today = summary.data?.[0]
  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const yesterdayActivity = activities.data?.[0]

  // ─── Derived values ───
  const sleepHours = today?.total_sleep_seconds
    ? Number((today.total_sleep_seconds / 3600).toFixed(1))
    : null

  const { block, week } = getProgramWeek(new Date())
  const deload = isDeloadWeek(week)
  const todaySession = getSessionForDate(new Date()) as SessionType | null
  const isGymDay = todaySession != null

  const bbHigh = todayMetrics?.body_battery_highest ?? null
  const bbLow = todayMetrics?.body_battery_lowest ?? null
  const readiness = todayMetrics?.training_readiness_score != null
    ? Math.round(todayMetrics.training_readiness_score) : null
  const restingHR = todayMetrics?.resting_hr ?? null

  // ─── Trend context ───
  const hrvWeeklyAvg = todayHRV?.weekly_avg != null ? Math.round(todayHRV.weekly_avg) : null
  const hrvVal = todayHRV?.last_night_avg != null ? Math.round(todayHRV.last_night_avg) : null
  const hrvStatusInfo = hrvStatus(todayHRV?.status)

  const sleepDays = (summary.data ?? []).slice(0, 7)
  const sleepBelowCount = sleepDays.filter(
    (d: any) => d.total_sleep_seconds != null && d.total_sleep_seconds / 3600 < 6
  ).length

  const yesterdayMetricsData = metrics.data?.[1]
  const readinessDelta = readiness != null && yesterdayMetricsData?.training_readiness_score != null
    ? readiness - Math.round(yesterdayMetricsData.training_readiness_score) : null

  const restingHRData = (metrics.data ?? [])
    .slice().reverse()
    .filter((d: any) => d.resting_hr != null)
    .map((d: any) => ({ value: d.resting_hr }))

  // ─── Readiness assessment ───
  const signals = [
    { degraded: todayHRV?.status?.toUpperCase() === 'LOW' || todayHRV?.status?.toUpperCase() === 'UNBALANCED' },
    { degraded: sleepHours != null && sleepHours < 6 },
    { degraded: (bbHigh ?? 100) < 30 },
    { degraded: (readiness ?? 100) < 40 },
  ]
  const degradedCount = signals.filter(s => s.degraded).length

  // ─── Coaching note (generated from data) ───
  const coachNote = (() => {
    if (degradedCount >= 3) return 'Multiple signals degraded. Rest or light mobility only — your body needs recovery.'
    if (degradedCount === 2) return 'Two recovery signals flagged. Train if you feel good after warmup, otherwise swap to mobility.'

    // Check coaching_log for today's entry
    const todayLog = (coaching.data ?? []).find((c: any) =>
      c.date === new Date().toISOString().split('T')[0] && c.type === 'daily_plan'
    )
    if (todayLog) return todayLog.message?.split('\n')[0] ?? ''

    if (!isGymDay) {
      const dayName = new Date().toLocaleDateString('en-US', { weekday: 'long' })
      if (dayName === 'Saturday' || dayName === 'Sunday') return 'Mountain day or rest — your call based on conditions and energy.'
      if (dayName === 'Tuesday') return 'Mobility day. Foam roll, hip flexor stretches, thoracic rotation, shoulder CARs.'
      return 'Rest day. Light walk, hydrate, recover for the next session.'
    }

    if (deload) return 'Deload week — same exercises, same weight, half the sets. Focus on movement quality.'
    if (degradedCount === 1) return 'One signal borderline. Train as planned but listen to your body — drop RPE by 1 if you feel off.'
    return 'All signals green. Train as planned — focus on controlled movement and hitting your RPE targets.'
  })()

  const verdictColor = degradedCount === 0 ? 'text-accent-green' : degradedCount <= 1 ? 'text-accent-yellow' : 'text-accent-red'
  const verdictBg = degradedCount === 0 ? 'border-accent-green/20 bg-glow-green' : degradedCount <= 1 ? 'border-accent-yellow/20 bg-glow-yellow' : 'border-accent-red/20 bg-glow-red'
  const verdictLabel = degradedCount === 0 ? 'Good to train' : degradedCount <= 1 ? 'Train with caution' : 'Rest day'

  const rpeRange = deload ? '5-6' : block === 1 ? '6-7' : '7-8'

  return (
    <div className="space-y-3">

      {/* ═══ 1. COACHING CARD (Hero) ═══ */}
      <div className={`rounded-2xl border p-5 ${verdictBg}`}>
        {/* Verdict + session */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className={`text-lg font-semibold ${verdictColor}`}>{verdictLabel}</div>
            {isGymDay && todaySession && (
              <div className="text-sm text-text-primary mt-0.5">
                {SESSION_NAMES[todaySession]}
              </div>
            )}
            {!isGymDay && (
              <div className="text-sm text-text-secondary mt-0.5">
                {new Date().toLocaleDateString('en-US', { weekday: 'long' })}
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-[10px] text-text-muted uppercase tracking-wider">Week {week}</div>
            <div className="text-[10px] text-text-muted">
              {deload ? 'Deload' : `Block ${block}`} · RPE {rpeRange}
            </div>
          </div>
        </div>

        {/* Coaching note */}
        <p className="text-[13px] text-text-secondary leading-relaxed">{coachNote}</p>

        {/* Today's exercises (expandable, gym days only) */}
        {isGymDay && todaySession && SESSION_EXERCISES[todaySession] && (
          <div className="mt-3">
            <button
              onClick={() => setShowExercises(!showExercises)}
              className="flex items-center gap-1.5 text-[11px] text-text-muted hover:text-text-secondary transition-colors"
            >
              <ChevronDown size={12} className={`transition-transform ${showExercises ? 'rotate-180' : ''}`} />
              {showExercises ? 'Hide workout' : 'Show workout'}
            </button>
            {showExercises && (
              <div className="mt-2 space-y-1.5 bg-bg-primary/40 rounded-xl p-3">
                {SESSION_EXERCISES[todaySession].map((ex, i) => {
                  const weight = getPlannedWeight(ex.name, week)
                  const sets = deload ? Math.max(1, Math.round(ex.sets * 0.5)) : ex.sets
                  return (
                    <div key={i} className="flex items-center justify-between text-[12px]">
                      <span className="text-text-secondary">{ex.name}</span>
                      <span className="text-text-muted font-data">
                        {sets}×{ex.reps}
                        {weight != null && <> @ {weight}kg</>}
                      </span>
                    </div>
                  )
                })}
                <div className="text-[10px] text-text-muted mt-2 pt-2 border-t border-border-subtle">
                  ~{deload ? '30' : '45-55'} min · {deload ? 'Deload: same weight, half sets' : `RPE ${rpeRange}`}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ 2. RECOVERY SIGNALS ═══ */}
      <div className="grid grid-cols-2 gap-2">
        {/* HRV */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">HRV</span>
            <span className={`text-[10px] font-medium ${hrvStatusInfo.color}`}>{hrvStatusInfo.label}</span>
          </div>
          <div className={`text-2xl font-semibold font-data ${hrvStatusInfo.color}`}>
            {hrvVal ?? '—'}<span className="text-xs font-normal text-text-muted ml-1">ms</span>
          </div>
          {hrvWeeklyAvg != null && (
            <div className="text-[10px] text-text-muted mt-1">
              {hrvVal != null && hrvWeeklyAvg > 0
                ? hrvVal >= hrvWeeklyAvg ? `↑ above` : `↓ below`
                : ''} {hrvWeeklyAvg}ms avg
            </div>
          )}
        </div>

        {/* Sleep */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Sleep</span>
            {sleepBelowCount > 0 && (
              <span className="text-[10px] text-accent-red">{sleepBelowCount} night{sleepBelowCount > 1 ? 's' : ''} &lt;6h</span>
            )}
          </div>
          <div className={`text-2xl font-semibold font-data ${sleepColor(sleepHours)}`}>
            {sleepHours ?? '—'}<span className="text-xs font-normal text-text-muted ml-1">h</span>
          </div>
          <div className="text-[10px] text-text-muted mt-1">
            Target 7-8h
          </div>
        </div>

        {/* Body Battery */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Body Battery</span>
          </div>
          <div className={`text-2xl font-semibold font-data ${metricColor(bbHigh, 60, 30)}`}>
            {bbHigh ?? '—'}
          </div>
          {bbLow != null && (
            <div className="text-[10px] text-text-muted mt-1">
              Low {bbLow} · Range {(bbHigh ?? 0) - bbLow}
            </div>
          )}
        </div>

        {/* Readiness */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Readiness</span>
            {readinessDelta != null && readinessDelta !== 0 && (
              <span className={`text-[10px] ${readinessDelta > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                {readinessDelta > 0 ? '↑' : '↓'}{Math.abs(readinessDelta)}
              </span>
            )}
          </div>
          <div className={`text-2xl font-semibold font-data ${metricColor(readiness, 60, 40)}`}>
            {readiness ?? '—'}
          </div>
          <div className="text-[10px] text-text-muted mt-1">
            {readiness != null && readiness >= 60 ? 'Ready to train' : readiness != null && readiness >= 40 ? 'Borderline' : readiness != null ? 'Recovery needed' : ''}
          </div>
        </div>
      </div>

      {/* ═══ 3. RESTING HR ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-red/10 flex items-center justify-center">
              <Heart size={16} className="text-accent-red" />
            </div>
            <div>
              <div className="text-[10px] text-text-muted uppercase tracking-wider">Resting HR</div>
              <div className="text-xl font-semibold font-data text-text-primary">
                {restingHR ?? '--'}
                <span className="text-xs text-text-muted ml-1 font-normal">bpm</span>
              </div>
            </div>
          </div>
          <div className="w-24">
            {restingHRData.length > 1 && (
              <Sparkline data={restingHRData} color="#f87171" height={28} />
            )}
          </div>
        </div>
      </div>

      {/* ═══ 4. LATEST ACTIVITY ═══ */}
      {yesterdayActivity && (
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
          <div className="flex items-center gap-2 mb-2">
            {yesterdayActivity.elevation_gain > 0
              ? <Mountain size={14} className="text-mountain" />
              : <Dumbbell size={14} className="text-gym" />
            }
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Latest Activity</span>
          </div>
          <div className="text-base font-semibold text-text-primary leading-tight">
            {yesterdayActivity.activity_name || formatActivityType(yesterdayActivity.activity_type)}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[12px] text-text-secondary">
            {yesterdayActivity.duration_seconds && (
              <span className="flex items-center gap-1.5">
                <Clock size={12} className="text-text-muted" />
                {formatDuration(yesterdayActivity.duration_seconds)}
              </span>
            )}
            {yesterdayActivity.elevation_gain != null && yesterdayActivity.elevation_gain > 0 && (
              <span className="flex items-center gap-1.5">
                <ArrowUpRight size={12} className="text-mountain" />
                {Math.round(yesterdayActivity.elevation_gain)}m
              </span>
            )}
            {yesterdayActivity.calories != null && (
              <span className="flex items-center gap-1.5">
                <Flame size={12} className="text-accent-orange" />
                {yesterdayActivity.calories} kcal
              </span>
            )}
            {yesterdayActivity.avg_hr != null && (
              <span className="flex items-center gap-1.5">
                <Heart size={12} className="text-accent-red" />
                {yesterdayActivity.avg_hr} bpm
              </span>
            )}
          </div>
        </div>
      )}

      {/* ═══ 5. PROGRAM PROGRESS ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] text-text-muted uppercase tracking-wider">
            {block === 1 ? 'Base Rebuild' : 'Progression'} · Block {block}
          </span>
          <span className="text-sm font-semibold font-data text-accent-green">
            {week}<span className="text-text-muted font-normal">/8</span>
          </span>
        </div>
        <div className="w-full bg-bg-elevated rounded-full h-1.5">
          <div
            className="bg-accent-green rounded-full h-1.5 transition-all duration-500"
            style={{ width: `${(week / 8) * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}
