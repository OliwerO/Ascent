import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import type { Activity } from '../lib/types'

const RPE_LABELS: Record<number, string> = {
  0: 'Rest', 1: 'Very light', 2: 'Light', 3: 'Moderate', 4: 'Somewhat hard',
  5: 'Hard', 6: '', 7: 'Very hard', 8: '', 9: '', 10: 'Maximal',
}

export function RPEPrompt({ activity }: { activity: Activity }) {
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
