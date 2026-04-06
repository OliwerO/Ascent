import { LoadingState } from '../components/LoadingState'
import { useDailySummary, useHRV, useDailyMetrics, useActivities, useSubjectiveWellness, usePlannedWorkouts } from '../hooks/useSupabase'
import type { Activity, SubjectiveWellness, WarmupExercise, PlannedExercise } from '../lib/types'
import {
  getProgramWeek, isDeloadWeek, getSessionForDate, SESSION_NAMES,
} from '../lib/program'
import { Clock, Flame, ArrowUpRight, Heart, ChevronDown, TrendingUp, Activity as ActivityIcon, Info } from 'lucide-react'
import { useState, useMemo, useEffect } from 'react'
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

// ─── Wellness Input Component ────────────────────────────────────

const WELLNESS_ITEMS = [
  { key: 'sleep_quality', label: 'Sleep quality', low: 'Poor', high: 'Great' },
  { key: 'energy', label: 'Energy level', low: 'Exhausted', high: 'Fresh' },
  { key: 'muscle_soreness', label: 'Muscle soreness', low: 'Very sore', high: 'None' },
  { key: 'motivation', label: 'Motivation', low: 'None', high: 'Fired up' },
  { key: 'stress', label: 'Stress', low: 'Very high', high: 'Very low' },
] as const

function WellnessInput({ todayWellness, onSubmit }: {
  todayWellness: SubjectiveWellness | null
  onSubmit: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [values, setValues] = useState<Record<string, number>>({})
  const [submitting, setSubmitting] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  const composite = todayWellness?.composite_score ?? null

  if (todayWellness && !expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-border-subtle p-4 text-left"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Wellness</span>
            <span className={`text-base font-bold font-data ${
              (composite ?? 0) >= 3.5 ? 'text-accent-green' : (composite ?? 0) >= 2.5 ? 'text-accent-yellow' : 'text-accent-red'
            }`}>
              {composite != null ? composite.toFixed(1) : '?'}/5
            </span>
          </div>
          <span className="text-[11px] text-text-dim">Tap to view</span>
        </div>
      </button>
    )
  }

  if (!expanded && !todayWellness) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-accent-green/20 p-4 text-left animate-pulse-subtle"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-text-primary">How are you feeling?</div>
            <div className="text-[12px] text-text-muted mt-0.5">30-second daily check-in</div>
          </div>
          <ChevronDown size={16} className="text-text-muted" />
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
        setSaveMsg('Save failed')
        setTimeout(() => setSaveMsg(null), 3000)
        return
      }
      setSaveMsg('Saved')
      setTimeout(() => setSaveMsg(null), 2000)
      onSubmit()
      setExpanded(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-text-primary">How are you feeling?</span>
        <button onClick={() => setExpanded(false)} className="text-[11px] text-text-muted hover:text-text-secondary">Close</button>
      </div>
      <div className="space-y-4">
        {WELLNESS_ITEMS.map(item => (
          <div key={item.key}>
            <div className="flex justify-between text-[12px] mb-1.5">
              <span className="text-text-secondary font-medium">{item.label}</span>
              <span className="text-text-dim">{item.low} → {item.high}</span>
            </div>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map(v => (
                <button
                  key={v}
                  onClick={() => setValues(prev => ({ ...prev, [item.key]: v }))}
                  className={`flex-1 h-10 rounded-xl text-sm font-semibold transition-all ${
                    values[item.key] === v
                      ? v >= 4 ? 'bg-accent-green/20 text-accent-green border border-accent-green/40'
                        : v === 3 ? 'bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/40'
                        : 'bg-accent-red/20 text-accent-red border border-accent-red/40'
                      : 'bg-bg-primary/50 text-text-muted border border-transparent hover:border-border'
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
        className="mt-4 w-full py-2.5 rounded-xl bg-accent-green/15 text-accent-green text-sm font-semibold
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:bg-accent-green/25"
      >
        {submitting ? 'Saving...' : 'Submit'}
      </button>
      {saveMsg && (
        <p className={`mt-2 text-center text-xs font-medium ${
          saveMsg === 'Saved' ? 'text-accent-green' : 'text-accent-red'
        }`}>{saveMsg}</p>
      )}
    </div>
  )
}

// ─── RPE Prompt Component ─────────────────────────────────────────

const RPE_LABELS: Record<number, string> = {
  0: 'Rest', 1: 'Very light', 2: 'Light', 3: 'Moderate', 4: 'Somewhat hard',
  5: 'Hard', 6: '', 7: 'Very hard', 8: '', 9: '', 10: 'Maximal',
}

function RPEPrompt({ activity }: { activity: Activity }) {
  const [rated, setRated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [selectedRPE, setSelectedRPE] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [rpeMsg, setRpeMsg] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      const { data } = await supabase
        .from('training_sessions')
        .select('srpe')
        .eq('date', activity.date)
        .limit(1)
      if (data?.[0]?.srpe != null) setRated(true)
      setLoading(false)
    })()
  }, [activity.date])

  if (loading || rated) return null

  const handleSubmit = async () => {
    if (selectedRPE == null) return
    setSaving(true)
    try {
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
          setRpeMsg('RPE logged')
          setTimeout(() => setRpeMsg(null), 2000)
        }
      } catch {
        setRpeMsg('Save failed')
        setTimeout(() => setRpeMsg(null), 3000)
      }
      setRated(true)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-accent-purple/20 p-4">
      <div className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-2">Session RPE</div>
      <div className="text-[13px] text-text-secondary mb-3">
        How hard was {activity.activity_name || 'your session'}? (0-10)
      </div>
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => (
          <button
            key={v}
            onClick={() => setSelectedRPE(v)}
            className={`flex-1 h-9 rounded-lg text-[11px] font-semibold transition-all ${
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
        <div className="text-[11px] text-text-dim mt-1.5 text-center">{RPE_LABELS[selectedRPE]}</div>
      )}
      <button
        onClick={handleSubmit}
        disabled={saving || selectedRPE == null}
        className="mt-3 w-full py-2 rounded-xl bg-accent-purple/15 text-accent-purple text-[13px] font-semibold
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        {saving ? 'Saving...' : 'Log RPE'}
      </button>
      {rpeMsg && (
        <p className={`mt-2 text-center text-xs font-medium ${
          rpeMsg === 'RPE logged' ? 'text-accent-purple' : 'text-accent-red'
        }`}>{rpeMsg}</p>
      )}
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
  const planned = usePlannedWorkouts()
  const [showExercises, setShowExercises] = useState(false)
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

  const loading = summary.loading || hrv.loading || metrics.loading || activities.loading
  if (loading) return <LoadingState />

  const today = summary.data?.[0]
  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const lastActivity = recentActivities[0]
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const todayWellness = (wellness.data ?? []).find((w) => w.date === todayStr) ?? null

  // ─── Derived values ───
  const sleepHours = today?.total_sleep_seconds
    ? Number((today.total_sleep_seconds / 3600).toFixed(1)) : null
  const { block, week } = getProgramWeek(new Date())
  const deload = isDeloadWeek(week)
  const todayPlanned = planned.data?.find((pw) => pw.scheduled_date === todayStr) ?? null
  const todaySession = todayPlanned ? todayPlanned.workout_definition?.session_label : getSessionForDate(new Date())
  const isGymDay = todayPlanned != null || getSessionForDate(new Date()) != null
  const todaySessionName = todayPlanned?.workout_definition?.session_name ?? (todaySession ? SESSION_NAMES[todaySession as keyof typeof SESSION_NAMES] : null)
  const isAdjusted = todayPlanned?.status === 'adjusted'
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

  const thisWeekDuration = thisWeekActivities.reduce((s: number, a) => s + (a.duration_seconds ?? 0), 0)
  const lastWeekDuration = lastWeekActivities.reduce((s: number, a) => s + (a.duration_seconds ?? 0), 0)
  const thisWeekElev = thisWeekActivities.reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
  const lastWeekElev = lastWeekActivities.reduce((s: number, a) => s + (a.elevation_gain ?? 0), 0)
  const loadChangePct = lastWeekDuration > 0 ? Math.round(((thisWeekDuration - lastWeekDuration) / lastWeekDuration) * 100) : null

  // ─── Coaching card decision tree (evidence-based) ───
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

        {/* Expandable workout */}
        {isGymDay && todayPlanned?.workout_definition && (
          <div className="mt-4 pt-3 border-t border-text-primary/5">
            {isAdjusted && todayPlanned.adjustment_reason && (
              <div className="text-[12px] text-accent-yellow mb-2">
                Coach: {todayPlanned.adjustment_reason}
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
                <table className="w-full text-[14px]">
                  <tbody>
                    {todayPlanned.workout_definition.exercises.map((ex: PlannedExercise, i: number) => (
                      <tr key={i} className="border-b border-text-primary/5 last:border-0">
                        <td className="py-2 text-text-primary">{ex.name}</td>
                        <td className="py-2 text-right text-text-secondary font-mono text-[13px] whitespace-nowrap">
                          {ex.sets}×{ex.reps}
                        </td>
                        <td className="py-2 text-right text-text-primary font-mono text-[13px] w-20 font-semibold">
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
        <div className="flex gap-5 text-[14px]">
          <div>
            <span className="text-text-primary font-semibold">{formatDuration(thisWeekDuration)}</span>
            <span className="text-text-muted text-[12px] ml-1">gym</span>
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
        {lastWeekDuration > 0 && (
          <div className="text-[12px] text-text-muted mt-1.5">
            Last week: {formatDuration(lastWeekDuration)} · {Math.round(lastWeekElev).toLocaleString()}m
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

      {/* ═══ 7. SESSION RPE PROMPT ═══ */}
      {lastActivity && lastActivity.activity_type === 'strength_training' && (
        <RPEPrompt activity={lastActivity} />
      )}

      {/* ═══ 8. PROGRAM PROGRESS ═══ */}
      <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">
            {block === 1 ? 'Base Rebuild' : 'Progression'} · Block {block}
          </span>
          <span className="text-[15px] font-bold font-data text-accent-green">
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
