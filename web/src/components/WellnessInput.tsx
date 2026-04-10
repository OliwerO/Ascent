import { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { format } from 'date-fns'
import type { SubjectiveWellness } from '../lib/types'

const WELLNESS_ITEMS = [
  { key: 'sleep_quality', label: 'Sleep quality', low: 'Poor', high: 'Great' },
  { key: 'energy', label: 'Energy level', low: 'Exhausted', high: 'Fresh' },
  { key: 'muscle_soreness', label: 'Muscle soreness', low: 'Very sore', high: 'None' },
  { key: 'motivation', label: 'Motivation', low: 'None', high: 'Fired up' },
  { key: 'stress', label: 'Stress', low: 'Very high', high: 'Very low' },
] as const

export function WellnessInput({ todayWellness, onSubmit }: {
  todayWellness: SubjectiveWellness | null
  onSubmit: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [values, setValues] = useState<Record<string, number>>({})
  const [submitting, setSubmitting] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  useEffect(() => {
    if (expanded && todayWellness) {
      const existing: Record<string, number> = {}
      for (const item of WELLNESS_ITEMS) {
        const v = todayWellness[item.key as keyof SubjectiveWellness]
        if (typeof v === 'number') existing[item.key] = v
      }
      setValues(existing)
    }
  }, [expanded, todayWellness])

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
