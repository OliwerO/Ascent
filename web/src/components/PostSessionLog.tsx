import { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { format } from 'date-fns'
import type { Activity, PlannedExercise, ExerciseFeedback, SubjectiveWellness } from '../lib/types'

const RPE_LABELS: Record<number, string> = {
  0: 'Rest', 1: 'Very light', 2: 'Light', 3: 'Moderate', 4: 'Somewhat hard',
  5: 'Hard', 6: '', 7: 'Very hard', 8: '', 9: '', 10: 'Maximal',
}

const FEEL_OPTIONS: { value: ExerciseFeedback['feel']; label: string; color: string }[] = [
  { value: 'light', label: 'Light', color: 'accent-green' },
  { value: 'right', label: 'Right', color: 'accent-blue' },
  { value: 'heavy', label: 'Heavy', color: 'accent-red' },
]

const WELLNESS_ITEMS = [
  { key: 'sleep_quality', label: 'Sleep', low: 'Poor', high: 'Great' },
  { key: 'energy', label: 'Energy', low: 'Low', high: 'Fresh' },
  { key: 'muscle_soreness', label: 'Soreness', low: 'Very sore', high: 'None' },
  { key: 'motivation', label: 'Motivation', low: 'None', high: 'High' },
  { key: 'stress', label: 'Stress', low: 'High', high: 'Low' },
] as const

export function PostSessionLog({ activity, exercises, todayWellness, onComplete }: {
  activity: Activity
  exercises: PlannedExercise[]
  todayWellness: SubjectiveWellness | null
  onComplete: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [alreadyLogged, setAlreadyLogged] = useState(false)
  const [loading, setLoading] = useState(true)

  // State for all three inputs
  const [rpe, setRpe] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<Record<string, ExerciseFeedback['feel']>>({})
  const [showFeedback, setShowFeedback] = useState(false)
  const [wellnessValues, setWellnessValues] = useState<Record<string, number>>({})
  const [showWellness, setShowWellness] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  // Check if already logged
  useEffect(() => {
    (async () => {
      const [rpeResult, feedbackResult] = await Promise.all([
        supabase.from('training_sessions').select('srpe').eq('date', activity.date).limit(1),
        supabase.from('exercise_feedback').select('exercise_name, feel').eq('session_date', activity.date),
      ])

      const hasRpe = rpeResult.data?.[0]?.srpe != null
      const hasFeedback = (feedbackResult.data?.length ?? 0) >= exercises.length

      if (hasRpe && hasFeedback) {
        setAlreadyLogged(true)
      } else {
        // Load existing partial data
        if (rpeResult.data?.[0]?.srpe != null) setRpe(rpeResult.data[0].srpe)
        if (feedbackResult.data && feedbackResult.data.length > 0) {
          const existing: Record<string, ExerciseFeedback['feel']> = {}
          for (const row of feedbackResult.data) {
            existing[row.exercise_name] = row.feel as ExerciseFeedback['feel']
          }
          setFeedback(existing)
        }
      }
      setLoading(false)
    })()
  }, [activity.date, exercises.length])

  if (loading || alreadyLogged) return null

  const feedbackCount = Object.keys(feedback).length
  const wellnessCount = Object.keys(wellnessValues).length
  const wellnessAlreadyDone = todayWellness != null
  const canSave = rpe != null

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-accent-purple/20 p-4 text-left"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-text-primary">Log your session</div>
            <div className="text-[12px] text-text-muted mt-0.5">
              RPE + exercise feel{!wellnessAlreadyDone ? ' + wellness' : ''} — quick combined log
            </div>
          </div>
          <ChevronDown size={16} className="text-text-muted" />
        </div>
      </button>
    )
  }

  const handleSave = async () => {
    if (rpe == null) return
    setSaving(true)
    setSaveMsg(null)

    try {
      // 1. Save RPE
      const { data: sessions } = await supabase
        .from('training_sessions')
        .select('id')
        .eq('date', activity.date)
        .limit(1)
      if (sessions && sessions.length > 0) {
        await supabase
          .from('training_sessions')
          .update({ srpe: rpe })
          .eq('id', sessions[0].id)
      }

      // 2. Save exercise feedback (if any filled)
      if (feedbackCount > 0) {
        const rows = exercises
          .filter(ex => feedback[ex.name])
          .map(ex => ({
            session_date: activity.date,
            exercise_name: ex.name,
            feel: feedback[ex.name],
          }))
        if (rows.length > 0) {
          await supabase
            .from('exercise_feedback')
            .upsert(rows, { onConflict: 'session_date,exercise_name' })
        }
      }

      // 3. Save wellness (if filled and not already done)
      if (!wellnessAlreadyDone && wellnessCount === WELLNESS_ITEMS.length) {
        const todayStr = format(new Date(), 'yyyy-MM-dd')
        await supabase.from('subjective_wellness').upsert({
          date: todayStr,
          ...wellnessValues,
        }, { onConflict: 'date' })
      }

      setSaveMsg('Logged')
      setTimeout(() => {
        setAlreadyLogged(true)
        onComplete()
      }, 1000)
    } catch {
      setSaveMsg('Save failed')
      setTimeout(() => setSaveMsg(null), 3000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-text-primary">Log your session</span>
        <button onClick={() => setExpanded(false)} className="text-[11px] text-text-muted hover:text-text-secondary">Close</button>
      </div>

      {/* RPE */}
      <div className="mb-4">
        <div className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-2">
          Session RPE
        </div>
        <div className="flex gap-1">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => (
            <button
              key={v}
              onClick={() => setRpe(v)}
              className={`flex-1 h-9 rounded-lg text-[11px] font-semibold transition-all ${
                rpe === v
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
        {rpe != null && RPE_LABELS[rpe] && (
          <div className="text-[11px] text-text-dim mt-1 text-center">{RPE_LABELS[rpe]}</div>
        )}
      </div>

      {/* Exercise Feel — collapsible */}
      {exercises.length > 0 && (
        <div className="mb-4">
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className="flex items-center gap-1.5 text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-2"
          >
            <ChevronDown size={12} className={`transition-transform ${showFeedback ? 'rotate-180' : ''}`} />
            Exercise feel {feedbackCount > 0 && `(${feedbackCount}/${exercises.length})`}
          </button>
          {showFeedback && (
            <div className="space-y-2">
              {exercises.map(ex => (
                <div key={ex.name} className="flex items-center justify-between gap-2">
                  <span className="text-[12px] text-text-secondary truncate flex-1">{ex.name}</span>
                  <div className="flex gap-1">
                    {FEEL_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setFeedback(prev => ({ ...prev, [ex.name]: opt.value }))}
                        className={`px-2 py-1 rounded-lg text-[10px] font-semibold border transition-all ${
                          feedback[ex.name] === opt.value
                            ? `bg-${opt.color}/20 text-${opt.color} border-${opt.color}/40`
                            : 'bg-bg-primary/50 text-text-muted border-transparent'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Wellness — collapsible, only if not already done */}
      {!wellnessAlreadyDone && (
        <div className="mb-4">
          <button
            onClick={() => setShowWellness(!showWellness)}
            className="flex items-center gap-1.5 text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-2"
          >
            <ChevronDown size={12} className={`transition-transform ${showWellness ? 'rotate-180' : ''}`} />
            Wellness {wellnessCount > 0 && `(${wellnessCount}/${WELLNESS_ITEMS.length})`}
          </button>
          {showWellness && (
            <div className="space-y-3">
              {WELLNESS_ITEMS.map(item => (
                <div key={item.key}>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-text-secondary">{item.label}</span>
                    <span className="text-text-dim">{item.low} → {item.high}</span>
                  </div>
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map(v => (
                      <button
                        key={v}
                        onClick={() => setWellnessValues(prev => ({ ...prev, [item.key]: v }))}
                        className={`flex-1 h-8 rounded-lg text-[12px] font-semibold transition-all ${
                          wellnessValues[item.key] === v
                            ? v >= 4 ? 'bg-accent-green/20 text-accent-green border border-accent-green/40'
                              : v === 3 ? 'bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/40'
                              : 'bg-accent-red/20 text-accent-red border border-accent-red/40'
                            : 'bg-bg-primary/50 text-text-muted border border-transparent'
                        }`}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={saving || !canSave}
        className="w-full py-2.5 rounded-xl bg-accent-purple/15 text-accent-purple text-[13px] font-semibold
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        {saving ? 'Saving...' : saveMsg === 'Logged' ? 'Logged' : 'Save session log'}
      </button>
      {saveMsg && saveMsg !== 'Logged' && (
        <p className="mt-2 text-center text-xs font-medium text-accent-red">{saveMsg}</p>
      )}
    </div>
  )
}
