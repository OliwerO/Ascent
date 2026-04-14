import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Card } from '../../components/Card'
import { supabase } from '../../lib/supabase'
import { buildHomeWorkout, restoreGymWorkout, countSubstitutions } from '../../lib/homeWorkout'
import type { PlannedWorkout, WarmupExercise, PlannedExercise } from '../../lib/types'
import { ChevronDown, Info, Home, Dumbbell, Send } from 'lucide-react'

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
  todayRationale: { rule?: string | null; inputs?: Record<string, unknown> | null; kb_refs?: string[] | null } | null
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
            {showRationale ? 'Hide rationale' : 'Why?'}
          </button>
          {showRationale && (
            <div className="mt-1.5 text-[11px] text-text-muted bg-bg-inset rounded-lg px-2.5 py-2 space-y-1">
              {todayRationale.rule && (
                <div><span className="text-text-dim">Rule:</span> {todayRationale.rule.replace(/[._]/g, ' ')}</div>
              )}
              {todayRationale.inputs && (
                <div><span className="text-text-dim">Inputs:</span> {
                  Object.entries(todayRationale.inputs)
                    .filter(([, v]) => v != null)
                    .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`)
                    .join(' · ')
                }</div>
              )}
              {todayRationale.kb_refs && todayRationale.kb_refs.length > 0 && (
                <div><span className="text-text-dim">Ref:</span> {todayRationale.kb_refs.join(', ')}</div>
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
