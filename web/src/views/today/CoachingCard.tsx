import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Card } from '../../components/Card'
import { supabase } from '../../lib/supabase'
import { buildHomeWorkout, restoreGymWorkout, countSubstitutions } from '../../lib/homeWorkout'
import type { PlannedWorkout, WarmupExercise, PlannedExercise } from '../../lib/types'
import { ChevronDown, Info, Home, Dumbbell, Send, RefreshCw } from 'lucide-react'

interface CoachingPoint {
  icon: string
  text: string
  color?: string
}

interface Props {
  cardState: 'green' | 'amber' | 'red'
  verdictLabel: string
  isGymDay: boolean
  todaySessionName: string | null
  isAdjusted: boolean
  isRescheduled: boolean
  block: number
  week: number
  rpeRange: string
  deload: boolean
  coachingPoints: CoachingPoint[]
  bbHigh: number | null
  readiness: number | null
  todayPlanned: PlannedWorkout | null
  todayAdjustment: { message?: string } | null
  todayRationale: {
    rule?: string | null
    inputs?: Record<string, unknown> | null
    kb_refs?: string[] | null
    message?: string | null
    decision_type?: string | null
  } | null
  todayStr: string
  todayIsHome: boolean
}

const accentMap = { green: 'green' as const, amber: 'yellow' as const, red: 'red' as const }
const glowMap = { green: 'green' as const, amber: 'yellow' as const, red: 'red' as const }

export function CoachingCard({
  cardState, verdictLabel, isGymDay, todaySessionName, isAdjusted, isRescheduled,
  block, week, rpeRange, deload, coachingPoints, bbHigh, readiness,
  todayPlanned, todayAdjustment, todayRationale, todayStr, todayIsHome,
}: Props) {
  const [showExercises, setShowExercises] = useState(false)
  const [showRationale, setShowRationale] = useState(false)
  const [switching, setSwitching] = useState(false)
  const [switchError, setSwitchError] = useState<string | null>(null)
  const [showHomePreview, setShowHomePreview] = useState(false)
  const [pushing, setPushing] = useState(false)
  const [pushMsg, setPushMsg] = useState<string | null>(null)
  const [evaluating, setEvaluating] = useState(false)
  const [evalMsg, setEvalMsg] = useState<string | null>(null)

  const verdictColor = cardState === 'green' ? 'text-accent-green' : cardState === 'amber' ? 'text-accent-yellow' : 'text-accent-red'

  // Home workout preview diff
  const homePreviewDiff = (() => {
    if (!todayPlanned?.workout_definition?.exercises || todayIsHome) return []
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
  })()

  const handlePushToGarmin = async () => {
    if (pushing) return
    setPushing(true)
    setPushMsg(null)
    try {
      const resp = await fetch('/api/garmin-push-trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-ascent-token': import.meta.env.VITE_SUPABASE_KEY ?? '' },
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

  const handleEvaluate = async () => {
    if (evaluating) return
    setEvaluating(true)
    setEvalMsg(null)
    try {
      const resp = await fetch('/api/coach-trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-ascent-token': import.meta.env.VITE_SUPABASE_KEY ?? '' },
        body: JSON.stringify({ date: todayStr }),
      })
      const data = await resp.json()
      setEvalMsg(data.ok ? 'Evaluation queued — refresh in ~30s' : (data.error || 'Failed'))
      setTimeout(() => setEvalMsg(null), 8000)
    } catch {
      setEvalMsg('Evaluation request failed')
      setTimeout(() => setEvalMsg(null), 5000)
    } finally {
      setEvaluating(false)
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
        .update({ workout_definition: homeWd, status: 'adjusted', adjustment_reason: 'Switched to home workout' })
        .eq('id', todayPlanned.id)
      if (error) throw error
      await supabase.from('coaching_log').insert({
        date: todayStr, type: 'adjustment', channel: 'app',
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
        .update({ workout_definition: gymWd, status: 'adjusted', adjustment_reason: 'Switched back to gym workout' })
        .eq('id', todayPlanned.id)
      if (error) throw error
      await supabase.from('coaching_log').insert({
        date: todayStr, type: 'adjustment', channel: 'app',
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
    <Card accentStrip={accentMap[cardState]} glow={glowMap[cardState]} className="pl-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className={`text-xl font-[590] ${verdictColor}`}>{verdictLabel}</div>
          {isGymDay && todaySessionName && (
            <div className="text-[15px] text-text-primary mt-1 font-[510]">
              {todaySessionName}
              {isRescheduled && <span className="ml-2 text-[11px] px-2 py-0.5 rounded-full bg-accent-purple/20 text-accent-purple font-semibold">Moved</span>}
              {isAdjusted && !isRescheduled && <span className="ml-2 text-[11px] px-2 py-0.5 rounded-full bg-accent-yellow/20 text-accent-yellow font-semibold">Adjusted</span>}
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

      {/* Garmin estimates info note */}
      {(bbHigh != null || readiness != null) && cardState === 'green' && (
        <div className="mt-3 text-[12px] text-text-dim flex items-center gap-1.5">
          <Info size={12} />
          Garmin: BB {bbHigh ?? '—'} · Readiness {readiness ?? '—'}
          <span className="text-[10px]">(estimates)</span>
        </div>
      )}

      {/* Action buttons */}
      {isGymDay && todayPlanned?.workout_definition && (todayPlanned.workout_definition.exercises?.length ?? 0) > 0 && (
        <div className="mt-3 flex items-center gap-4">
          {todayIsHome ? (
            <button onClick={handleSwitchToGym} disabled={switching}
              className="flex items-center gap-1.5 text-[13px] text-text-muted hover:text-text-secondary transition-colors disabled:opacity-50">
              <Dumbbell size={14} />
              {switching ? 'Switching...' : 'Switch back to gym'}
            </button>
          ) : (
            <button onClick={() => setShowHomePreview(true)} disabled={switching}
              className="flex items-center gap-1.5 text-[13px] text-accent-blue hover:text-accent-blue/80 transition-colors disabled:opacity-50">
              <Home size={14} />
              Train at home
              {countSubstitutions(todayPlanned.workout_definition) > 0 && (
                <span className="text-[10px] text-text-dim">({countSubstitutions(todayPlanned.workout_definition)} swaps)</span>
              )}
            </button>
          )}
          {todayPlanned.status !== 'pushed' && (
            <button onClick={handlePushToGarmin} disabled={pushing}
              className="flex items-center gap-1.5 text-[13px] text-accent-green hover:text-accent-green/80 transition-colors disabled:opacity-50">
              <Send size={13} />
              {pushing ? 'Pushing...' : 'Push to Garmin'}
            </button>
          )}
        </div>
      )}
      {switchError && (
        <div className="mt-2 text-[12px] text-accent-red bg-accent-red/10 rounded-lg px-2.5 py-1.5">{switchError}</div>
      )}
      {pushMsg && (
        <div className={`mt-2 text-[12px] rounded-lg px-2.5 py-1.5 ${pushMsg.includes('queued') ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'}`}>
          {pushMsg}
        </div>
      )}

      {/* Re-evaluate button — always available */}
      <div className="mt-2 flex items-center gap-3">
        <button onClick={handleEvaluate} disabled={evaluating}
          className="flex items-center gap-1.5 text-[12px] text-text-muted hover:text-text-secondary transition-colors disabled:opacity-50">
          <RefreshCw size={12} className={evaluating ? 'animate-spin' : ''} />
          {evaluating ? 'Evaluating...' : 'Re-evaluate'}
        </button>
      </div>
      {evalMsg && (
        <div className={`mt-1.5 text-[12px] rounded-lg px-2.5 py-1.5 ${evalMsg.includes('queued') ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'}`}>
          {evalMsg}
        </div>
      )}

      {/* Home workout preview modal — rendered via portal-like fixed overlay */}
      {showHomePreview && (
        <HomePreviewModal
          diffs={homePreviewDiff}
          switching={switching}
          onClose={() => setShowHomePreview(false)}
          onConfirm={async () => { setShowHomePreview(false); await handleSwitchToHome() }}
        />
      )}

      {/* Adjustment note */}
      {isAdjusted && !todayPlanned && todayAdjustment && (
        <div className="mt-3 text-[13px] text-accent-yellow">Coach: {todayAdjustment.message}</div>
      )}

      {/* Coaching rationale — "Why?" */}
      {todayRationale && (
        <div className="mt-2">
          <button onClick={() => setShowRationale(!showRationale)}
            className="flex items-center gap-1 text-[11px] text-text-muted hover:text-text-secondary transition-colors">
            <Info size={11} />
            {showRationale ? 'Hide rationale' : 'Why this decision?'}
          </button>
          {showRationale && (
            <div className="mt-1.5 text-[12px] bg-bg-inset rounded-lg px-3 py-2.5 space-y-2">
              {/* Primary: the coaching message (human-written by the daily agent) */}
              {todayRationale.message && (
                <div className="text-text-secondary leading-relaxed">{todayRationale.message}</div>
              )}

              {/* Signal pills — compact recovery snapshot */}
              {todayRationale.inputs && (
                <div className="flex flex-wrap gap-1.5">
                  <RationalePills inputs={todayRationale.inputs} />
                </div>
              )}

              {/* Rule + KB refs — compact footer */}
              {(todayRationale.rule || (todayRationale.kb_refs && todayRationale.kb_refs.length > 0)) && (
                <div className="text-[10px] text-text-dim pt-1 border-t border-border-subtle">
                  {todayRationale.rule && <span>{formatRuleId(todayRationale.rule)}</span>}
                  {todayRationale.rule && todayRationale.kb_refs && todayRationale.kb_refs.length > 0 && <span> · </span>}
                  {todayRationale.kb_refs && todayRationale.kb_refs.length > 0 && (
                    <span>{todayRationale.kb_refs.map(formatKbRef).join(', ')}</span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Expandable workout */}
      {isGymDay && todayPlanned?.workout_definition && (
        <div className="mt-4 pt-3 border-t border-border-subtle">
          {isAdjusted && (todayPlanned?.adjustment_reason || todayAdjustment?.message) && (
            <div className="text-[12px] text-accent-yellow mb-2">
              Coach: {todayPlanned?.adjustment_reason ?? todayAdjustment?.message}
            </div>
          )}
          <button onClick={() => setShowExercises(!showExercises)}
            className="flex items-center gap-1.5 text-[13px] text-text-muted hover:text-text-secondary transition-colors">
            <ChevronDown size={14} className={`transition-transform ${showExercises ? 'rotate-180' : ''}`} />
            {showExercises ? 'Hide workout' : 'Show workout'}
          </button>
          {showExercises && (
            <div className="mt-3">
              {todayPlanned.workout_definition.warmup?.length > 0 && (
                <div className="mb-3 pb-2 border-b border-border-subtle">
                  <div className="section-label mb-2">Warm-up</div>
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
                    <tr key={i} className="border-b border-border-subtle last:border-0">
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
    </Card>
  )
}

/** Map rule IDs like "all_green.train_as_planned" or "R-TAP" to readable labels */
function formatRuleId(rule: string): string {
  const map: Record<string, string> = {
    'R-TAP': 'Train as planned',
    'all_green.train_as_planned': 'All signals green',
    'recovery.hrv_low.rest': 'HRV low → rest',
    'recovery.hrv_low.lighten': 'HRV low → lighten',
    'recovery.sleep_short.lighten': 'Short sleep → lighten',
    'recovery.unbalanced_sleep_short.rest': 'Unbalanced + short sleep → rest',
    'recovery.bb_low.rest': 'Body battery low → rest',
    'recovery.tr_low.rest': 'Training readiness low → rest',
    'recovery.multi_signal.rest': 'Multiple signals degraded → rest',
    'mountain.monday_cap': 'Post-mountain Monday RPE cap',
    'mountain.2x_consolidation': 'Mountain week → consolidated template',
  }
  return map[rule] ?? rule.replace(/[._-]/g, ' ')
}

/** Make KB refs like "domain-1.1" more readable */
function formatKbRef(ref: string): string {
  if (ref.startsWith('domain-')) return `KB ${ref.replace('domain-', '§')}`
  return ref.replace(/-/g, ' ')
}

/** Signal indicator colors */
function signalColor(key: string, value: unknown): string {
  if (key === 'body_battery_highest') {
    const n = Number(value)
    if (n >= 70) return 'bg-accent-green/15 text-accent-green'
    if (n >= 30) return 'bg-accent-yellow/15 text-accent-yellow'
    return 'bg-accent-red/15 text-accent-red'
  }
  if (key === 'training_readiness_score') {
    const n = Number(value)
    if (n >= 60) return 'bg-accent-green/15 text-accent-green'
    if (n >= 40) return 'bg-accent-yellow/15 text-accent-yellow'
    return 'bg-accent-red/15 text-accent-red'
  }
  if (key === 'sleep_hours') {
    const n = Number(value)
    if (n >= 7) return 'bg-accent-green/15 text-accent-green'
    if (n >= 6) return 'bg-accent-yellow/15 text-accent-yellow'
    return 'bg-accent-red/15 text-accent-red'
  }
  if (key === 'hrv_status') {
    const s = String(value).toUpperCase()
    if (s === 'BALANCED') return 'bg-accent-green/15 text-accent-green'
    if (s === 'UNBALANCED') return 'bg-accent-yellow/15 text-accent-yellow'
    if (s === 'LOW') return 'bg-accent-red/15 text-accent-red'
    return 'bg-bg-card text-text-dim'
  }
  if (key === 'mountain_days_3d') {
    return Number(value) > 0 ? 'bg-accent-blue/15 text-accent-blue' : 'bg-bg-card text-text-dim'
  }
  if (key === 'hard_override') {
    return value ? 'bg-accent-red/15 text-accent-red' : 'bg-bg-card text-text-dim'
  }
  return 'bg-bg-card text-text-muted'
}

/** Format a signal key-value pair as a compact label */
function signalLabel(key: string, value: unknown): string | null {
  if (value == null) return null
  switch (key) {
    case 'body_battery_highest': return `BB ${value}`
    case 'training_readiness_score': return `TR ${value}`
    case 'sleep_hours': return `${value}h sleep`
    case 'hrv_status': {
      const s = String(value).toUpperCase()
      return s === 'NONE' ? null : `HRV ${s.toLowerCase()}`
    }
    case 'hrv_avg': return `HRV ${value}`
    case 'hrv_weekly_avg': return null // shown with hrv_avg
    case 'mountain_days_3d': return Number(value) > 0 ? `${value}d mountain` : null
    case 'last_srpe': return `sRPE ${value}`
    case 'hard_override': return value ? `Override: ${value}` : null
    case 'recovery_action': return value ? `→ ${value}` : null
    case 'garmin_auth_ok': return null // internal, not useful to athlete
    case 'sleep_score': return value ? `Sleep score ${value}` : null
    default: return null
  }
}

/** Render compact signal pills from coaching inputs */
function RationalePills({ inputs }: { inputs: Record<string, unknown> }) {
  // Ordered for readability: HRV → sleep → battery → readiness → mountain → sRPE → override
  const order = [
    'hrv_status', 'hrv_avg', 'sleep_hours', 'sleep_score',
    'body_battery_highest', 'training_readiness_score',
    'mountain_days_3d', 'last_srpe', 'hard_override', 'recovery_action',
  ]
  const pills: { label: string; color: string }[] = []
  for (const key of order) {
    if (!(key in inputs)) continue
    const label = signalLabel(key, inputs[key])
    if (!label) continue
    pills.push({ label, color: signalColor(key, inputs[key]) })
  }
  if (pills.length === 0) return null
  return (
    <>
      {pills.map((p, i) => (
        <span key={i} className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-medium ${p.color}`}>
          {p.label}
        </span>
      ))}
    </>
  )
}

function HomePreviewModal({ diffs, switching, onClose, onConfirm }: {
  diffs: { gym: string; home: string; note?: string }[]
  switching: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/60" onClick={onClose}>
      <div
        className="w-full max-w-[480px] bg-bg-secondary border-t border-border rounded-t-[20px] p-5 pb-8 max-h-[70vh] overflow-auto animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-[15px] font-[590] text-text-primary mb-3">Home workout preview</div>
        {diffs.length > 0 ? (
          <div className="space-y-2 mb-4">
            {diffs.map((d, i) => (
              <div key={i} className="text-[12px] bg-bg-inset rounded-lg px-3 py-2">
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
          <button onClick={onClose}
            className="flex-1 text-[13px] text-text-muted py-2.5 rounded-xl border border-border">Cancel</button>
          <button onClick={onConfirm} disabled={switching}
            className="flex-1 text-[13px] text-white bg-accent-blue py-2.5 rounded-xl font-semibold disabled:opacity-50">
            {switching ? 'Switching...' : 'Switch to home'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
