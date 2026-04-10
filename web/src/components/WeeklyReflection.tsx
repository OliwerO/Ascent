import { useState, useMemo, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { format } from 'date-fns'

const ENERGY_OPTIONS = [
  { value: 'improving', label: 'Improving', color: 'bg-accent-green/20 text-accent-green border-accent-green/40' },
  { value: 'stable', label: 'Stable', color: 'bg-accent-blue/20 text-accent-blue border-accent-blue/40' },
  { value: 'declining', label: 'Declining', color: 'bg-accent-red/20 text-accent-red border-accent-red/40' },
] as const

export function WeeklyReflection() {
  const [expanded, setExpanded] = useState(false)
  const [done, setDone] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [energy, setEnergy] = useState<string | null>(null)
  const [satisfaction, setSatisfaction] = useState<number | null>(null)
  const [highlight, setHighlight] = useState('')
  const [challenge, setChallenge] = useState('')
  const [focus, setFocus] = useState('')

  const weekStart = useMemo(() => {
    const now = new Date()
    const day = now.getDay()
    const diff = now.getDate() - ((day + 6) % 7)
    const monday = new Date(now.setDate(diff))
    return format(monday, 'yyyy-MM-dd')
  }, [])

  useEffect(() => {
    (async () => {
      const { data } = await supabase
        .from('weekly_reflections')
        .select('*')
        .eq('week_start', weekStart)
        .limit(1)
      if (data && data.length > 0) {
        const r = data[0]
        if (r.training_satisfaction != null) {
          setDone(true)
        } else {
          if (r.energy_trend) setEnergy(r.energy_trend)
          if (r.training_satisfaction) setSatisfaction(r.training_satisfaction)
          if (r.top_highlight) setHighlight(r.top_highlight)
          if (r.biggest_challenge) setChallenge(r.biggest_challenge)
          if (r.next_week_focus) setFocus(r.next_week_focus)
        }
      }
      setLoaded(true)
    })()
  }, [weekStart])

  if (!loaded || done) return null

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full bg-bg-card rounded-2xl border border-accent-purple/20 p-4 text-left"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-text-primary">Weekly Reflection</div>
            <div className="text-[12px] text-text-muted mt-0.5">How was this week? (30 seconds)</div>
          </div>
          <ChevronDown size={16} className="text-text-muted" />
        </div>
      </button>
    )
  }

  const handleSubmit = async () => {
    if (!energy || !satisfaction) return
    setSaving(true)
    try {
      const { error } = await supabase
        .from('weekly_reflections')
        .upsert({
          week_start: weekStart,
          energy_trend: energy,
          training_satisfaction: satisfaction,
          top_highlight: highlight || null,
          biggest_challenge: challenge || null,
          next_week_focus: focus || null,
        }, { onConflict: 'week_start' })
      if (!error) setDone(true)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-2xl border border-border-subtle p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-text-primary">Weekly Reflection</span>
        <button onClick={() => setExpanded(false)} className="text-[11px] text-text-muted hover:text-text-secondary">Close</button>
      </div>

      {/* Energy trend */}
      <div className="mb-4">
        <div className="text-[12px] text-text-secondary font-medium mb-2">Energy trend this week</div>
        <div className="flex gap-2">
          {ENERGY_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setEnergy(opt.value)}
              className={`flex-1 py-2 rounded-xl text-[12px] font-semibold border transition-all ${
                energy === opt.value ? opt.color : 'bg-bg-primary/50 text-text-muted border-transparent'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Training satisfaction */}
      <div className="mb-4">
        <div className="text-[12px] text-text-secondary font-medium mb-2">Training satisfaction</div>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map(v => (
            <button
              key={v}
              onClick={() => setSatisfaction(v)}
              className={`flex-1 h-10 rounded-xl text-sm font-semibold transition-all ${
                satisfaction === v
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

      {/* Optional text fields */}
      <div className="space-y-3 mb-4">
        <div>
          <div className="text-[12px] text-text-dim mb-1">Week highlight (optional)</div>
          <input
            value={highlight}
            onChange={e => setHighlight(e.target.value)}
            placeholder="Best moment this week..."
            className="w-full bg-bg-primary/50 rounded-lg px-3 py-2 text-[13px] text-text-primary border border-transparent focus:border-border outline-none"
          />
        </div>
        <div>
          <div className="text-[12px] text-text-dim mb-1">Biggest challenge (optional)</div>
          <input
            value={challenge}
            onChange={e => setChallenge(e.target.value)}
            placeholder="What held you back..."
            className="w-full bg-bg-primary/50 rounded-lg px-3 py-2 text-[13px] text-text-primary border border-transparent focus:border-border outline-none"
          />
        </div>
        <div>
          <div className="text-[12px] text-text-dim mb-1">Next week focus (optional)</div>
          <input
            value={focus}
            onChange={e => setFocus(e.target.value)}
            placeholder="Priority for next week..."
            className="w-full bg-bg-primary/50 rounded-lg px-3 py-2 text-[13px] text-text-primary border border-transparent focus:border-border outline-none"
          />
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={saving || !energy || !satisfaction}
        className="w-full py-2.5 rounded-xl bg-accent-purple/15 text-accent-purple text-sm font-semibold
                   disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:bg-accent-purple/25"
      >
        {saving ? 'Saving...' : 'Submit reflection'}
      </button>
    </div>
  )
}
