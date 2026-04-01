import { Sparkline } from '../components/Sparkline'
import { LoadingState } from '../components/LoadingState'
import { useDailySummary, useHRV, useDailyMetrics, useActivities, useTrainingStatus } from '../hooks/useSupabase'
import {
  getProgramWeek, isDeloadWeek, getSessionForDate, SESSION_NAMES,
  getPlannedWeight,
} from '../lib/program'
import { Clock, Flame, ArrowUpRight, Heart, ChevronDown, TrendingUp, Activity } from 'lucide-react'
import { useState } from 'react'

// ─── Helpers ──────────────────────────────────────────────────────

function hrvStatusInfo(status: string | null | undefined): { color: string; label: string } {
  if (!status) return { color: 'text-accent-yellow', label: 'Unknown' }
  const s = status.toUpperCase()
  if (s === 'BALANCED') return { color: 'text-accent-green', label: 'Balanced' }
  if (s === 'UNBALANCED') return { color: 'text-accent-yellow', label: 'Unbalanced' }
  return { color: 'text-accent-red', label: 'Low' }
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

// Training status codes from Garmin
const TRAINING_STATUS_MAP: Record<number, { label: string; color: string; desc: string }> = {
  0: { label: 'No Status', color: 'text-text-muted', desc: 'Not enough data' },
  1: { label: 'Detraining', color: 'text-accent-red', desc: 'Training load dropping — fitness declining' },
  2: { label: 'Recovery', color: 'text-accent-blue', desc: 'Light load — recovering from hard training' },
  3: { label: 'Overreaching', color: 'text-accent-yellow', desc: 'High load — back off or risk overtraining' },
  4: { label: 'Productive', color: 'text-accent-green', desc: 'Good balance — fitness improving' },
  5: { label: 'Peaking', color: 'text-accent-purple', desc: 'Peak race readiness' },
  6: { label: 'Unproductive', color: 'text-accent-red', desc: 'Training hard but fitness not improving' },
  7: { label: 'Maintaining', color: 'text-text-secondary', desc: 'Maintaining current fitness level' },
}

// ─── Session exercises ────────────────────────────────────────────

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

// ═══════════════════════════════════════════════════════════════════

export default function TodayView() {
  const summary = useDailySummary(7)
  const hrv = useHRV(14)
  const metrics = useDailyMetrics(7)
  const activities = useActivities(14)
  const trainingStatus = useTrainingStatus(3)
  const [showExercises, setShowExercises] = useState(false)

  const loading = summary.loading || hrv.loading || metrics.loading || activities.loading
  if (loading) return <LoadingState />

  const today = summary.data?.[0]
  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const recentActivities = activities.data ?? []
  const lastActivity = recentActivities[0]

  // ─── Derived values ───
  const sleepHours = today?.total_sleep_seconds
    ? Number((today.total_sleep_seconds / 3600).toFixed(1)) : null
  const { block, week } = getProgramWeek(new Date())
  const deload = isDeloadWeek(week)
  const todaySession = getSessionForDate(new Date()) as SessionType | null
  const isGymDay = todaySession != null
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
    (d: any) => d.total_sleep_seconds != null && d.total_sleep_seconds / 3600 < 6
  ).length

  // ─── Readiness ───
  const signals = [
    todayHRV?.status?.toUpperCase() === 'LOW' || todayHRV?.status?.toUpperCase() === 'UNBALANCED',
    sleepHours != null && sleepHours < 6,
    (bbHigh ?? 100) < 30,
    (readiness ?? 100) < 40,
  ]
  const degradedCount = signals.filter(Boolean).length

  // ─── Training status from Garmin ───
  const tsRaw = (trainingStatus.data ?? [])[0]?.raw_json as any
  const tsDevice = tsRaw?.mostRecentTrainingStatus?.latestTrainingStatusData
  const tsData = tsDevice ? Object.values(tsDevice)[0] as any : null
  const garminTrainingStatus = tsData?.trainingStatus as number | undefined
  const tsInfo = garminTrainingStatus != null ? TRAINING_STATUS_MAP[garminTrainingStatus] : null
  const acuteLoad = tsData?.acuteTrainingLoadDTO
  const garminACWR = acuteLoad?.dailyAcuteChronicWorkloadRatio as number | undefined

  // ─── Last session context ───
  const lastGymSession = recentActivities.find((a: any) => a.activity_type === 'strength_training')
  const daysSinceGym = lastGymSession
    ? Math.floor((Date.now() - new Date(lastGymSession.date).getTime()) / 86400000)
    : null

  // ─── Coaching note (structured, not wall of text) ───
  const coachingPoints: { icon: string; text: string; color?: string }[] = []

  if (degradedCount >= 3) {
    coachingPoints.push({ icon: '🔴', text: 'Multiple recovery signals degraded — rest or mobility only', color: 'text-accent-red' })
  } else if (degradedCount === 2) {
    coachingPoints.push({ icon: '🟡', text: 'Two signals flagged — train if warmup feels good, otherwise swap to mobility', color: 'text-accent-yellow' })
  }

  if (isGymDay && todaySession) {
    if (deload) {
      coachingPoints.push({ icon: '📉', text: 'Deload week — same weight, half sets, focus on form' })
    } else if (daysSinceGym != null && daysSinceGym > 7) {
      coachingPoints.push({ icon: '💡', text: `${daysSinceGym} days since last gym session — start conservative, RPE 6 max` })
    }
  }

  if (tsInfo && garminTrainingStatus === 3) {
    coachingPoints.push({ icon: '⚠️', text: 'Garmin flags overreaching — consider reducing volume this week', color: 'text-accent-yellow' })
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

  if (coachingPoints.length === 0 && isGymDay) {
    coachingPoints.push({ icon: '✅', text: 'All signals green — train as planned' })
  }

  const verdictColor = degradedCount === 0 ? 'text-accent-green' : degradedCount <= 1 ? 'text-accent-yellow' : 'text-accent-red'
  const verdictBg = degradedCount === 0 ? 'border-accent-green/20 bg-glow-green' : degradedCount <= 1 ? 'border-accent-yellow/20 bg-glow-yellow' : 'border-accent-red/20 bg-glow-red'
  const verdictLabel = degradedCount === 0 ? 'Good to train' : degradedCount <= 1 ? 'Train with caution' : 'Rest day'
  const rpeRange = deload ? '5-6' : block === 1 ? '6-7' : '7-8'

  return (
    <div className="space-y-3">

      {/* ═══ 1. COACHING CARD ═══ */}
      <div className={`rounded-2xl border p-5 ${verdictBg}`}>
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className={`text-lg font-semibold ${verdictColor}`}>{verdictLabel}</div>
            {isGymDay && todaySession && (
              <div className="text-sm text-text-primary">{SESSION_NAMES[todaySession]}</div>
            )}
          </div>
          <div className="text-[10px] text-text-muted text-right">
            Week {week} · Block {block}
            <br />RPE {rpeRange}{deload && ' · Deload'}
          </div>
        </div>

        {/* Coaching points — structured, not paragraph */}
        <div className="space-y-1.5 mt-3">
          {coachingPoints.map((p, i) => (
            <div key={i} className={`text-[13px] leading-snug ${p.color ?? 'text-text-secondary'}`}>
              <span className="mr-1.5">{p.icon}</span>{p.text}
            </div>
          ))}
        </div>

        {/* Expandable workout */}
        {isGymDay && todaySession && SESSION_EXERCISES[todaySession] && (
          <div className="mt-3 pt-3 border-t border-white/5">
            <button
              onClick={() => setShowExercises(!showExercises)}
              className="flex items-center gap-1.5 text-[11px] text-text-muted hover:text-text-secondary transition-colors"
            >
              <ChevronDown size={12} className={`transition-transform ${showExercises ? 'rotate-180' : ''}`} />
              {showExercises ? 'Hide workout' : 'Show workout'}
            </button>
            {showExercises && (
              <div className="mt-2 space-y-1.5">
                {SESSION_EXERCISES[todaySession].map((ex, i) => {
                  const weight = getPlannedWeight(ex.name, week)
                  const sets = deload ? Math.max(1, Math.round(ex.sets * 0.5)) : ex.sets
                  return (
                    <div key={i} className="flex items-center justify-between text-[12px]">
                      <span className="text-text-secondary">{ex.name}</span>
                      <span className="text-text-muted font-data">
                        {sets}×{ex.reps}{weight != null && <> @ {weight}kg</>}
                      </span>
                    </div>
                  )
                })}
                <div className="text-[10px] text-text-muted mt-2">
                  ~{deload ? '30' : '45-55'} min
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ 2. RECOVERY SIGNALS (2x2 grid with inline context) ═══ */}
      <div className="grid grid-cols-2 gap-2">
        {/* HRV */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">HRV</span>
            <span className={`text-[10px] font-medium ${hrvInfo.color}`}>{hrvInfo.label}</span>
          </div>
          <div className={`text-2xl font-semibold font-data ${hrvInfo.color}`}>
            {hrvVal ?? '—'}<span className="text-xs font-normal text-text-muted ml-1">ms</span>
          </div>
          {hrvWeeklyAvg != null && hrvVal != null && (
            <div className="text-[10px] text-text-muted mt-1">
              {hrvVal >= hrvWeeklyAvg ? '↑ above' : '↓ below'} {hrvWeeklyAvg}ms avg
            </div>
          )}
        </div>

        {/* Sleep */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Sleep</span>
            {sleepBelowCount > 0 && (
              <span className="text-[10px] text-accent-red">{sleepBelowCount}×&lt;6h</span>
            )}
          </div>
          <div className={`text-2xl font-semibold font-data ${metricColor(sleepHours, 7, 6)}`}>
            {sleepHours ?? '—'}<span className="text-xs font-normal text-text-muted ml-1">h</span>
          </div>
          <div className="text-[10px] text-text-muted mt-1">Target 7-8h</div>
        </div>

        {/* Body Battery */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Body Battery</span>
          </div>
          <div className={`text-2xl font-semibold font-data ${metricColor(bbHigh, 60, 30)}`}>
            {bbHigh ?? '—'}
          </div>
          <div className="text-[10px] text-text-muted mt-1">
            {todayMetrics?.body_battery_lowest != null
              ? `Low ${todayMetrics.body_battery_lowest} · Range ${(bbHigh ?? 0) - todayMetrics.body_battery_lowest}`
              : ''}
          </div>
        </div>

        {/* Readiness */}
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Readiness</span>
          </div>
          <div className={`text-2xl font-semibold font-data ${metricColor(readiness, 60, 40)}`}>
            {readiness ?? '—'}
          </div>
          <div className="text-[10px] text-text-muted mt-1">
            {readiness != null && readiness >= 60 ? 'Ready' : readiness != null && readiness >= 40 ? 'Borderline' : readiness != null ? 'Low' : ''}
          </div>
        </div>
      </div>

      {/* ═══ 3. TRAINING STATUS (replaces resting HR) ═══ */}
      {(tsInfo || garminACWR != null) && (
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-accent-purple/10 flex items-center justify-center">
                <Activity size={16} className="text-accent-purple" />
              </div>
              <div>
                <div className="text-[10px] text-text-muted uppercase tracking-wider">Training Status</div>
                {tsInfo && (
                  <div className={`text-base font-semibold ${tsInfo.color}`}>{tsInfo.label}</div>
                )}
              </div>
            </div>
            {garminACWR != null && (
              <div className="text-right">
                <div className="text-[10px] text-text-muted">ACWR</div>
                <div className={`text-lg font-semibold font-data ${
                  garminACWR > 1.5 ? 'text-accent-red' : garminACWR > 1.3 ? 'text-accent-yellow' : garminACWR >= 0.8 ? 'text-accent-green' : 'text-accent-yellow'
                }`}>
                  {garminACWR.toFixed(1)}
                </div>
              </div>
            )}
          </div>
          {tsInfo && (
            <div className="text-[11px] text-text-muted mt-2">{tsInfo.desc}</div>
          )}
          {acuteLoad && (
            <div className="flex gap-4 mt-2 text-[11px] text-text-muted">
              <span>Acute: {Math.round(acuteLoad.dailyTrainingLoadAcute)}</span>
              <span>Chronic: {Math.round(acuteLoad.dailyTrainingLoadChronic)}</span>
            </div>
          )}
        </div>
      )}

      {/* ═══ 4. RESTING HR (compact) ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart size={14} className="text-accent-red" />
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Resting HR</span>
            <span className="text-sm font-semibold font-data text-text-primary">
              {todayMetrics?.resting_hr ?? '--'} bpm
            </span>
          </div>
          <div className="w-20">
            {(metrics.data ?? []).length > 1 && (
              <Sparkline
                data={(metrics.data ?? []).slice().reverse().filter((d: any) => d.resting_hr).map((d: any) => ({ value: d.resting_hr }))}
                color="#f87171"
                height={24}
              />
            )}
          </div>
        </div>
      </div>

      {/* ═══ 5. LATEST ACTIVITY ═══ */}
      {lastActivity && (
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
          <div className="flex items-center gap-2 mb-2">
            {lastActivity.elevation_gain > 0
              ? <TrendingUp size={14} className="text-mountain" />
              : <Activity size={14} className="text-gym" />
            }
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Latest Activity</span>
          </div>
          <div className="text-base font-semibold text-text-primary leading-tight">
            {lastActivity.activity_name || formatActivityType(lastActivity.activity_type)}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[12px] text-text-secondary">
            {lastActivity.duration_seconds && (
              <span className="flex items-center gap-1"><Clock size={11} className="text-text-muted" />{formatDuration(lastActivity.duration_seconds)}</span>
            )}
            {lastActivity.elevation_gain > 0 && (
              <span className="flex items-center gap-1"><ArrowUpRight size={11} className="text-mountain" />{Math.round(lastActivity.elevation_gain)}m</span>
            )}
            {lastActivity.calories != null && (
              <span className="flex items-center gap-1"><Flame size={11} className="text-accent-orange" />{lastActivity.calories} kcal</span>
            )}
            {lastActivity.avg_hr != null && (
              <span className="flex items-center gap-1"><Heart size={11} className="text-accent-red" />{lastActivity.avg_hr} bpm</span>
            )}
          </div>
        </div>
      )}

      {/* ═══ 6. PROGRAM PROGRESS (compact) ═══ */}
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
