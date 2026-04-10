import { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { supabase } from '../lib/supabase'
import type { PlannedExercise, ExerciseFeedback } from '../lib/types'

const FEEL_OPTIONS: { value: ExerciseFeedback['feel']; label: string; activeClass: string }[] = [
  { value: 'light', label: 'Light', activeClass: 'bg-accent-green/20 text-accent-green border-accent-green/40' },
  { value: 'right', label: 'Right', activeClass: 'bg-accent-blue/20 text-accent-blue border-accent-blue/40' },
  { value: 'heavy', label: 'Heavy', activeClass: 'bg-accent-red/20 text-accent-red border-accent-red/40' },
]

export function ExerciseFeedbackPrompt({ exercises, sessionDate }: {
  exercises: PlannedExercise[]
  sessionDate: string
}) {
  const [expanded, setExpanded] = useState(false)
  const [feedback, setFeedback] = useState<Record<string, ExerciseFeedback['feel']>>({})
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    (async () => {
      const { data } = await supabase
        .from('exercise_feedback')
        .select('exercise_name, feel')
        .eq('session_date', sessionDate)
      if (data && data.length > 0) {
        if (data.length >= exercises.length) {
          setDone(true)
        } else {
          const existing: Record<string, ExerciseFeedback['feel']> = {}
          for (const row of data) {
            existing[row.exercise_name] = row.feel as ExerciseFeedback['feel']
          }
          setFeedback(existing)
        }
      }
      setLoaded(true)
    })()
  }, [sessionDate, exercises.length])

  if (!loaded || done) return null

  const filledCount = Object.keys(feedback).length
  const allFilled = filledCount >= exercises.length

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-accent-blue/20 p-4 text-left"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-text-primary">How did each exercise feel?</div>
            <div className="text-[12px] text-text-muted mt-0.5">
              {filledCount > 0 ? `${filledCount}/${exercises.length} rated` : 'Quick per-exercise feedback'}
            </div>
          </div>
          <ChevronDown size={16} className="text-text-muted" />
        </div>
      </button>
    )
  }

  const handleSubmit = async () => {
    if (!allFilled) return
    setSaving(true)
    try {
      const rows = exercises.map(ex => ({
        session_date: sessionDate,
        exercise_name: ex.name,
        feel: feedback[ex.name],
      }))
      const { error } = await supabase
        .from('exercise_feedback')
        .upsert(rows, { onConflict: 'session_date,exercise_name' })
      if (!error) setDone(true)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-text-primary">Exercise feel</span>
        <button onClick={() => setExpanded(false)} className="text-[11px] text-text-muted hover:text-text-secondary">Close</button>
      </div>
      <div className="space-y-2.5">
        {exercises.map(ex => (
          <div key={ex.name} className="flex items-center justify-between gap-2">
            <span className="text-[13px] text-text-secondary truncate flex-1">{ex.name}</span>
            <div className="flex gap-1.5">
              {FEEL_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setFeedback(prev => ({ ...prev, [ex.name]: opt.value }))}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                    feedback[ex.name] === opt.value
                      ? opt.activeClass
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
      <button
        onClick={handleSubmit}
        disabled={saving || !allFilled}
        className="mt-3 w-full py-2 rounded-xl bg-accent-blue/15 text-accent-blue text-[13px] font-semibold
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        {saving ? 'Saving...' : `Save feedback (${filledCount}/${exercises.length})`}
      </button>
    </div>
  )
}
