import { LoadingState } from '../components/LoadingState'
import { useDailySummary, useHRV, useDailyMetrics, useActivities, useSubjectiveWellness } from '../hooks/useSupabase'
import {
  getProgramWeek, isDeloadWeek, getSessionForDate, SESSION_NAMES,
  getPlannedWeight,
} from '../lib/program'
import { Clock, Flame, ArrowUpRight, Heart, ChevronDown, TrendingUp, Activity, Info } from 'lucide-react'
import { useState, useMemo } from 'react'
import { supabase } from '../lib/supabase'
import { format } from 'date-fns'

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

// ─── Wellness Input Component ────────────────────────────────────

const WELLNESS_ITEMS = [
  { key: 'sleep_quality', label: 'Sleep quality', low: 'Poor', high: 'Great' },
  { key: 'energy', label: 'Energy level', low: 'Exhausted', high: 'Fresh' },
  { key: 'muscle_soreness', label: 'Muscle soreness', low: 'Very sore', high: 'None' },
  { key: 'motivation', label: 'Motivation', low: 'None', high: 'Fired up' },
  { key: 'stress', label: 'Stress', low: 'Very high', high: 'Very low' },
] as const

function WellnessInput({ todayWellness, onSubmit }: {
  todayWellness: any | null
  onSubmit: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [values, setValues] = useState<Record<string, number>>({})
  const [submitting, setSubmitting] = useState(false)

  const composite = todayWellness?.composite_score

  if (todayWellness && !expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-border-subtle p-3 text-left"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Wellness</span>
            <span className={`text-sm font-semibold font-data ${
              composite >= 3.5 ? 'text-accent-green' : composite >= 2.5 ? 'text-accent-yellow' : 'text-accent-red'
            }`}>
              {composite.toFixed(1)}/5
            </span>
          </div>
          <span className="text-[10px] text-text-muted">Tap to view</span>
        </div>
      </button>
    )
  }

  if (!expanded && !todayWellness) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-accent-green/20 p-3 text-left animate-pulse-subtle"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-text-primary">How are you feeling?</div>
            <div className="text-[10px] text-text-muted">30-second daily check-in</div>
          </div>
          <ChevronDown size={14} className="text-text-muted" />
        </div>
      </button>
    )
  }

  const handleSubmit = async () => {
    const allFilled = WELLNESS_ITEMS.every(item => values[item.key] != null)
    if (!allFilled) return
    setSubmitting(true)
    try {
      const todayStr = format(new Date(), 'yyyy-MM-dd')
      const { error } = await supabase.from('subjective_wellness').upsert({
        date: todayStr,
        ...values,
      }, { onConflict: 'date' })
      if (error) {
        console.warn('Wellness save failed (table may not exist yet):', error.message)
      }
      onSubmit()
      setExpanded(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-text-primary">How are you feeling?</span>
        <button onClick={() => setExpanded(false)} className="text-[10px] text-text-muted">Close</button>
      </div>
      <div className="space-y-3">
        {WELLNESS_ITEMS.map(item => (
          <div key={item.key}>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-text-secondary">{item.label}</span>
              <span className="text-text-muted">{item.low} → {item.high}</span>
            </div>
            <div className="flex gap-1.5">
              {[1, 2, 3, 4, 5].map(v => (
                <button
                  key={v}
                  onClick={() => setValues(prev => ({ ...prev, [item.key]: v }))}
                  className={`flex-1 h-8 rounded-lg text-xs font-semibold transition-all ${
                    values[item.key] === v
                      ? v >= 4 ? 'bg-accent-green/20 text-accent-green border border-accent-green/40'
                        : v === 3 ? 'bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/40'
                        : 'bg-accent-red/20 text-accent-red border border-accent-red/40'
                      : 'bg-bg-primary/50 text-text-muted border border-transparent hover:border-border-subtle'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={handleSubmit}
        disabled={submitting || !WELLNESS_ITEMS.every(item => values[item.key] != null)}
        className="mt-3 w-full py-2 rounded-lg bg-accent-green/20 text-accent-green text-sm font-medium
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:bg-accent-green/30"
      >
        {submitting ? 'Saving...' : 'Submit'}
      </button>
    </div>
  )
}

// ─── RPE Prompt Component ─────────────────────────────────────────

const RPE_LABELS: Record<number, string> = {
  0: 'Rest', 1: 'Very light', 2: 'Light', 3: 'Moderate', 4: 'Somewhat hard',
  5: 'Hard', 6: '', 7: 'Very hard', 8: '', 9: '', 10: 'Maximal',
}

function RPEPrompt({ activity }: { activity: any }) {
  const [rated, setRated] = useState(false)
  const [selectedRPE, setSelectedRPE] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)

  if (rated) return null

  const handleSubmit = async () => {
    if (selectedRPE == null) return
    setSaving(true)
    try {
      // Find the matching training_session and update srpe
      const dateStr = activity.date
      try {
        const { data: sessions } = await supabase
          .from('training_sessions')
          .select('id')
          .eq('date', dateStr)
          .limit(1)
        if (sessions && sessions.length > 0) {
          await supabase
            .from('training_sessions')
            .update({ srpe: selectedRPE })
            .eq('id', sessions[0].id)
        }
      } catch (e) {
        console.warn('RPE save failed:', e)
      }
      setRated(true)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-accent-purple/20 p-4">
      <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2">Session RPE</div>
      <div className="text-xs text-text-secondary mb-3">
        How hard was {activity.activity_name || 'your session'}? (0-10)
      </div>
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => (
          <button
            key={v}
            onClick={() => setSelectedRPE(v)}
            className={`flex-1 h-8 rounded text-[10px] font-semibold transition-all ${
              selectedRPE === v
                ? v >= 8 ? 'bg-accent-red/20 text-accent-red border border-accent-red/40'
                  : v >= 5 ? 'bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/40'
                  : 'bg-accent-green/20 text-accent-green border border-accent-green/40'
                : 'bg-bg-primary/50 text-text-muted border border-transparent'
            }`}
          >
            {v}
          </button>
        ))}
      </div>
      {selectedRPE != null && RPE_LABELS[selectedRPE] && (
        <div className="text-[10px] text-text-muted mt-1 text-center">{RPE_LABELS[selectedRPE]}</div>
      )}
      <button
        onClick={handleSubmit}
        disabled={saving || selectedRPE == null}
        className="mt-2 w-full py-1.5 rounded-lg bg-accent-purple/20 text-accent-purple text-xs font-medium
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        {saving ? 'Saving...' : 'Log RPE'}
      </button>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════

export default function TodayView() {
  const summary = useDailySummary(7)
  const hrv = useHRV(14)
  const metrics = useDailyMetrics(14)
  const activities = useActivities(14)
  const wellness = useSubjectiveWellness(30)
  const [showExercises, setShowExercises] = useState(false)
  const [, setWellnessRefresh] = useState(0)

  const loading = summary.loading || hrv.loading || metrics.loading || activities.loading
  if (loading) return <LoadingState />

  const today = summary.data?.[0]
  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const recentActivities = activities.data ?? []
  const lastActivity = recentActivities[0]
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const todayWellness = (wellness.data ?? []).find((w: any) => w.date === todayStr)

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
  const sleep7dAvg = useMemo(() => {
    const valid = sleepDays.filter((d: any) => d.total_sleep_seconds != null)
    if (valid.length === 0) return null
    return valid.reduce((s: number, d: any) => s + d.total_sleep_seconds / 3600, 0) / valid.length
  }, [sleepDays])

  // ─── Resting HR context ───
  const rhrValues = (metrics.data ?? []).slice(0, 7).filter((d: any) => d.resting_hr != null)
  const rhr7dAvg = rhrValues.length > 0
    ? rhrValues.reduce((s: number, d: any) => s + d.resting_hr, 0) / rhrValues.length : null
  const rhr30dValues = (metrics.data ?? []).filter((d: any) => d.resting_hr != null)
  const rhr30dAvg = rhr30dValues.length > 0
    ? rhr30dValues.reduce((s: number, d: any) => s + d.resting_hr, 0) / rhr30dValues.length : null
  const rhrElevated = rhr7dAvg != null && rhr30dAvg != null && rhr7dAvg > rhr30dAvg + 5
  const rhrTrend = todayMetrics?.resting_hr != null && rhr7dAvg != null
    ? (todayMetrics.resting_hr > rhr7dAvg + 2 ? '↑ Rising' : todayMetrics.resting_hr < rhr7dAvg - 2 ? '↓ Declining' : '→ Stable')
    : null

  // ─── Weekly load (replaces ACWR) ───
  const thisWeekActivities = useMemo(() => {
    const now = new Date()
    const dayOfWeek = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7))
    monday.setHours(0, 0, 0, 0)
    return recentActivities.filter((a: any) => new Date(a.date) >= monday)
  }, [recentActivities])

  const lastWeekActivities = useMemo(() => {
    const now = new Date()
    const dayOfWeek = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7))
    const prevMonday = new Date(monday)
    prevMonday.setDate(monday.getDate() - 7)
    return recentActivities.filter((a: any) => {
      const d = new Date(a.date)
      return d >= prevMonday && d < monday
    })
  }, [recentActivities])

  const thisWeekDuration = thisWeekActivities.reduce((s: number, a: any) => s + (a.duration_seconds ?? 0), 0)
  const lastWeekDuration = lastWeekActivities.reduce((s: number, a: any) => s + (a.duration_seconds ?? 0), 0)
  const thisWeekElev = thisWeekActivities.reduce((s: number, a: any) => s + (a.elevation_gain ?? 0), 0)
  const lastWeekElev = lastWeekActivities.reduce((s: number, a: any) => s + (a.elevation_gain ?? 0), 0)
  const loadChangePct = lastWeekDuration > 0 ? Math.round(((thisWeekDuration - lastWeekDuration) / lastWeekDuration) * 100) : null

  // ─── Coaching card decision tree (evidence-based) ───
  // Uses only validated signals: HRV, sleep, resting HR, subjective wellness
  // Body Battery and Readiness are EXCLUDED from this logic
  const hrvDegraded = todayHRV?.status?.toUpperCase() === 'LOW'
  const hrvLow = hrvVal != null && hrvWeeklyAvg != null && hrvVal < hrvWeeklyAvg * 0.85
  const sleepPoor = sleep7dAvg != null && sleep7dAvg < 6.5
  const wellnessLow = todayWellness?.composite_score != null && todayWellness.composite_score < 2.5

  let cardState: 'green' | 'amber' | 'red' = 'green'
  if (wellnessLow) {
    cardState = 'red'
  } else if (hrvDegraded && (sleepPoor || rhrElevated)) {
    cardState = 'red'
  } else if (hrvDegraded || hrvLow) {
    cardState = 'amber'
  } else if (sleep7dAvg != null && sleep7dAvg < 7) {
    cardState = 'amber'
  } else if (rhrElevated) {
    cardState = 'amber'
  }

  const verdictLabel = cardState === 'green' ? 'Good to train' : cardState === 'amber' ? 'Train with caution' : 'Consider rest or light session'
  const verdictColor = cardState === 'green' ? 'text-accent-green' : cardState === 'amber' ? 'text-accent-yellow' : 'text-accent-red'
  const verdictBg = cardState === 'green' ? 'border-accent-green/20 bg-glow-green' : cardState === 'amber' ? 'border-accent-yellow/20 bg-glow-yellow' : 'border-accent-red/20 bg-glow-red'
  const rpeRange = deload ? '5-6' : block === 1 ? '6-7' : '7-8'

  // ─── Coaching notes ───
  const coachingPoints: { icon: string; text: string; color?: string }[] = []

  if (cardState === 'red') {
    coachingPoints.push({ icon: '🔴', text: 'Multiple recovery signals degraded — rest or mobility only', color: 'text-accent-red' })
  } else if (cardState === 'amber') {
    coachingPoints.push({ icon: '🟡', text: 'One or more signals flagged — train if warmup feels good, otherwise swap to mobility', color: 'text-accent-yellow' })
  }

  // ─── Last session context ───
  const lastGymSession = recentActivities.find((a: any) => a.activity_type === 'strength_training')
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

        {/* Coaching points */}
        <div className="space-y-1.5 mt-3">
          {coachingPoints.map((p, i) => (
            <div key={i} className={`text-[13px] leading-snug ${p.color ?? 'text-text-secondary'}`}>
              <span className="mr-1.5">{p.icon}</span>{p.text}
            </div>
          ))}
        </div>

        {/* Garmin proprietary signals as info note (never override card color) */}
        {(bbHigh != null || readiness != null) && cardState === 'green' && (
          <div className="mt-2 text-[11px] text-text-muted/60 flex items-center gap-1">
            <Info size={10} />
            Garmin: BB {bbHigh ?? '—'} · Readiness {readiness ?? '—'}
            <span className="text-[9px]">(estimates)</span>
          </div>
        )}

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

      {/* ═══ 2. WELLNESS CHECK-IN ═══ */}
      <WellnessInput
        todayWellness={todayWellness}
        onSubmit={() => setWellnessRefresh(r => r + 1)}
      />

      {/* ═══ 3. RECOVERY SIGNALS — Tiered layout ═══ */}
      {/* Primary signals (evidence-backed) */}
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
      </div>

      {/* Secondary signals (Garmin estimates — visually demoted) */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-bg-card rounded-2xl border border-border-subtle p-2.5 opacity-70">
          <div className="flex items-center gap-1 mb-0.5">
            <span className="text-[9px] text-text-muted uppercase tracking-wider">Body Battery</span>
            <span className="text-[8px] text-text-muted/50">(est.)</span>
          </div>
          <div className={`text-lg font-semibold font-data ${metricColor(bbHigh, 60, 30)}`}>
            {bbHigh ?? '—'}
          </div>
          <div className="text-[9px] text-text-muted">
            {todayMetrics?.body_battery_lowest != null
              ? `Low ${todayMetrics.body_battery_lowest} · Range ${(bbHigh ?? 0) - todayMetrics.body_battery_lowest}`
              : ''}
          </div>
        </div>

        <div className="bg-bg-card rounded-2xl border border-border-subtle p-2.5 opacity-70">
          <div className="flex items-center gap-1 mb-0.5">
            <span className="text-[9px] text-text-muted uppercase tracking-wider">Readiness</span>
            <span className="text-[8px] text-text-muted/50">(est.)</span>
          </div>
          <div className={`text-lg font-semibold font-data ${metricColor(readiness, 60, 40)}`}>
            {readiness ?? '—'}
          </div>
          <div className="text-[9px] text-text-muted">
            {readiness != null && readiness >= 60 ? 'Ready' : readiness != null && readiness >= 40 ? 'Borderline' : readiness != null ? 'Low' : ''}
          </div>
        </div>
      </div>

      {/* ═══ 4. WEEKLY LOAD (replaces Training Status / ACWR) ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
        <div className="flex items-center gap-2 mb-2">
          <Activity size={14} className="text-accent-purple" />
          <span className="text-[10px] text-text-muted uppercase tracking-wider">Weekly Load</span>
        </div>
        <div className="flex gap-4 text-sm">
          <div>
            <span className="text-text-secondary">{formatDuration(thisWeekDuration)}</span>
            <span className="text-text-muted text-xs ml-1">gym</span>
          </div>
          <div>
            <span className="text-text-secondary">{Math.round(thisWeekElev).toLocaleString()}m</span>
            <span className="text-text-muted text-xs ml-1">elev</span>
          </div>
          {loadChangePct != null && (
            <span className={`text-xs font-medium ${
              Math.abs(loadChangePct) < 15 ? 'text-accent-green' : Math.abs(loadChangePct) < 25 ? 'text-accent-yellow' : 'text-accent-red'
            }`}>
              {loadChangePct >= 0 ? '+' : ''}{loadChangePct}% vs last wk
            </span>
          )}
        </div>
        {lastWeekDuration > 0 && (
          <div className="text-[10px] text-text-muted mt-1">
            Last week: {formatDuration(lastWeekDuration)} · {Math.round(lastWeekElev).toLocaleString()}m
          </div>
        )}
      </div>

      {/* ═══ 5. RESTING HR (compact with trend) ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart size={14} className="text-accent-red" />
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Resting HR</span>
            <span className="text-sm font-semibold font-data text-text-primary">
              {todayMetrics?.resting_hr ?? '--'} bpm
            </span>
            {rhrTrend && (
              <span className={`text-[10px] ${rhrElevated ? 'text-accent-yellow' : 'text-text-muted'}`}>
                {rhrTrend}
              </span>
            )}
          </div>
          {rhr7dAvg != null && (
            <span className="text-[10px] text-text-muted">
              7d avg: {Math.round(rhr7dAvg)}bpm
            </span>
          )}
        </div>
      </div>

      {/* ═══ 6. LATEST ACTIVITY ═══ */}
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

      {/* ═══ 7. SESSION RPE PROMPT ═══ */}
      {lastActivity && lastActivity.activity_type === 'strength_training' && (
        <RPEPrompt activity={lastActivity} />
      )}

      {/* ═══ 8. PROGRAM PROGRESS (compact) ═══ */}
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
