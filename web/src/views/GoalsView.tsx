import { useMemo } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useBodyComposition, useDailyMetrics, useActivities, useGoals } from '../hooks/useSupabase'
import type { BodyComposition, DailyMetrics, Activity, Goal } from '../lib/types'
import { getProgramWeek } from '../lib/program'
import { startOfWeek, endOfWeek, isWithinInterval, differenceInDays } from 'date-fns'
import { Target, Mountain, Dumbbell, Calendar, TrendingDown, TrendingUp, Minus } from 'lucide-react'

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="w-full bg-border rounded-full h-2 mt-2">
      <div
        className="rounded-full h-2 transition-all"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  )
}

export default function GoalsView() {
  const bodyComp = useBodyComposition(90)
  const metrics = useDailyMetrics(14)
  const activitiesHook = useActivities(14)
  const goalsHook = useGoals()

  const loading = bodyComp.loading || metrics.loading || activitiesHook.loading || goalsHook.loading
  const error = bodyComp.error || metrics.error || activitiesHook.error || goalsHook.error

  const now = new Date()
  const weekStart = startOfWeek(now, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(now, { weekStartsOn: 1 })

  const weeklyElevation = useMemo(
    () => Math.round((activitiesHook.data ?? [])
      .filter((a: Activity) => {
        const d = new Date(a.date)
        return isWithinInterval(d, { start: weekStart, end: weekEnd }) && a.activity_type !== 'hang_gliding'
      })
      .reduce((sum: number, a: Activity) => sum + (a.elevation_gain || 0), 0)),
    [activitiesHook.data, weekStart.getTime(), weekEnd.getTime()]
  )

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  // Prefer xiaomi (home scale) for weight — more accurate than gym weigh-in (clothes, food)
  const latestWeight = bodyComp.data?.find((d: BodyComposition) => d.weight_kg != null && d.source === 'xiaomi')
    ?? bodyComp.data?.find((d: BodyComposition) => d.weight_kg != null)
  // Muscle mass comes from egym body scans (xiaomi only has weight)
  const latestMuscle = bodyComp.data?.find((d: BodyComposition) => d.muscle_mass_grams != null)
  const latestBodyFat = bodyComp.data?.find((d: BodyComposition) => d.body_fat_pct != null)
  const latestVO2 = metrics.data?.find((d: DailyMetrics) => d.vo2max != null)
  const allGoals = (goalsHook.data ?? []) as Goal[]
  const bodyCompGoals = allGoals.filter((g) => g.category === 'body_composition')
  const strengthGoals = allGoals.filter((g) => g.category === 'strength')
  const enduranceGoals = allGoals.filter((g) => g.category === 'endurance')
  const milestoneGoals = allGoals
    .filter((g) => g.category === 'milestone')
    .sort((a, b) => (a.target_date ?? '').localeCompare(b.target_date ?? ''))

  const { week } = getProgramWeek(new Date())

  const STRENGTH_LABELS: Record<string, string> = {
    squat_e1rm_kg: 'Squat e1RM',
    deadlift_e1rm_kg: 'Deadlift e1RM',
    bench_e1rm_kg: 'Bench e1RM',
    ohp_e1rm_kg: 'OH Press e1RM',
    row_e1rm_kg: 'Row e1RM',
  }
  const ENDURANCE_LABELS: Record<string, { label: string; unit: string }> = {
    vo2max: { label: 'VO2max', unit: '' },
    weekly_elevation_m: { label: 'Weekly Elevation', unit: 'm' },
  }
  const enduranceCurrent = (metric: string): number | null => {
    if (metric === 'vo2max') return latestVO2?.vo2max != null ? Number(latestVO2.vo2max) : null
    if (metric === 'weekly_elevation_m') return weeklyElevation
    return null
  }
  const milestoneTitle = (g: Goal) => {
    const note = g.notes?.replace(/^\[block1-seed\]\s*/, '') ?? ''
    const [label, ...rest] = note.split('—')
    return { label: label?.trim() || g.metric, detail: rest.join('—').trim() }
  }

  return (
    <div className="space-y-3 pb-8">
      {/* Current Goals */}
      <div className="px-1">
        <h2 className="text-[14px] text-text-secondary font-semibold mb-2">Current Goals</h2>
      </div>
      <div className="space-y-3">
        {/* Body Recomp */}
        <Card>
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-accent-purple/15 text-accent-purple">
              <Target size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-[15px] font-bold text-text-primary">Body Recomposition</h3>
              {bodyCompGoals.length > 0 ? (
                <div className="mt-3 space-y-4">
                  {bodyCompGoals.map((goal: Goal) => {
                    const current = goal.metric === 'weight_kg' ? latestWeight?.weight_kg
                      : goal.metric === 'body_fat_pct' ? latestBodyFat?.body_fat_pct
                      : goal.metric === 'muscle_mass_kg' && latestMuscle?.muscle_mass_grams
                        ? latestMuscle.muscle_mass_grams / 1000 : null
                    const target = goal.target_value
                    const start = goal.current_value ?? 0
                    const isLowerBetter = goal.metric === 'weight_kg' || goal.metric === 'body_fat_pct'
                    const totalChange = Math.abs(target - start)
                    const currentChange = current != null ? Math.abs(current - start) : 0
                    const progressPct = totalChange > 0 ? Math.min(100, (currentChange / totalChange) * 100) : 0
                    const movingRight = current != null && (isLowerBetter ? current < start : current > start)
                    const daysLeft = goal.target_date ? differenceInDays(new Date(goal.target_date), new Date()) : null
                    const label = goal.metric === 'weight_kg' ? 'Weight'
                      : goal.metric === 'body_fat_pct' ? 'Body Fat'
                      : 'Muscle Mass'
                    const unit = goal.metric === 'body_fat_pct' ? '%' : 'kg'
                    const color = movingRight ? '#34d399' : current === start ? '#fbbf24' : '#f87171'

                    return (
                      <div key={goal.id}>
                        <div className="flex items-center justify-between text-[14px]">
                          <span className="text-text-secondary font-medium">{label}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-text-primary font-bold">
                              {current != null ? (goal.metric === 'body_fat_pct' ? `~${current.toFixed(0)}` : current.toFixed(1)) : '--'}{unit}
                            </span>
                            {current != null && (
                              movingRight
                                ? <TrendingDown size={13} className="text-accent-green" />
                                : current === start
                                  ? <Minus size={13} className="text-accent-yellow" />
                                  : <TrendingUp size={13} className="text-accent-red" />
                            )}
                            <span className="text-text-muted text-[12px]">→ {target}{unit}</span>
                          </div>
                        </div>
                        <ProgressBar value={movingRight ? progressPct : 0} max={100} color={color} />
                        {daysLeft != null && daysLeft > 0 && (
                          <div className="text-[11px] text-text-dim mt-1">
                            {daysLeft} days remaining · started at {start}{unit}
                          </div>
                        )}
                      </div>
                    )
                  })}
                  {bodyCompGoals[0]?.notes && (
                    <div className="text-[11px] text-text-dim mt-1">
                      {bodyCompGoals[0].metric === 'body_fat_pct' ? 'BIA has ±5% error — track direction, not absolute value' : ''}
                    </div>
                  )}
                </div>
              ) : (
                <div className="mt-2 space-y-2">
                  {latestWeight?.weight_kg && (
                    <div className="flex justify-between text-[14px]">
                      <span className="text-text-secondary">Weight</span>
                      <span className="text-text-primary font-bold">{latestWeight.weight_kg.toFixed(1)} kg</span>
                    </div>
                  )}
                  {latestBodyFat?.body_fat_pct && (
                    <div className="flex justify-between text-[14px]">
                      <span className="text-text-secondary">Body Fat</span>
                      <span className="text-text-primary font-bold">{latestBodyFat.body_fat_pct.toFixed(1)}% <span className="text-text-muted text-[12px] font-normal">(±5%)</span></span>
                    </div>
                  )}
                  {!latestWeight?.weight_kg && !latestBodyFat?.body_fat_pct && (
                    <div className="rounded-xl bg-bg-elevated border border-border px-3 py-2 text-[13px] text-text-muted">
                      Baseline needed — schedule a gym scan
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Endurance */}
        <Card>
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-mountain/15 text-mountain">
              <Mountain size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-[15px] font-bold text-text-primary">Endurance</h3>
              <div className="mt-2 space-y-3">
                {enduranceGoals.length > 0 ? enduranceGoals.map((g) => {
                  const meta = ENDURANCE_LABELS[g.metric] ?? { label: g.metric, unit: '' }
                  const current = enduranceCurrent(g.metric)
                  const pct = current != null && g.target_value > 0
                    ? Math.min(100, (current / g.target_value) * 100) : 0
                  return (
                    <div key={g.id}>
                      <div className="flex justify-between text-[14px]">
                        <span className="text-text-secondary">{meta.label}</span>
                        <span className="text-text-primary font-bold">
                          {current != null ? `${current.toLocaleString(undefined, { maximumFractionDigits: 1 })}${meta.unit}` : '--'}
                          <span className="text-text-muted text-[12px] font-normal"> / {g.target_value.toLocaleString()}{meta.unit}</span>
                        </span>
                      </div>
                      {current != null && <ProgressBar value={pct} max={100} color="#38bdf8" />}
                    </div>
                  )
                }) : (<>
                <div>
                  <div className="flex justify-between text-[14px]">
                    <span className="text-text-secondary">VO2max</span>
                    <span className="text-text-primary font-bold">
                      {latestVO2?.vo2max
                        ? Number(latestVO2.vo2max).toFixed(1)
                        : '--'}
                    </span>
                  </div>
                  {latestVO2?.vo2max && (
                    <ProgressBar value={Number(latestVO2.vo2max)} max={55} color="#38bdf8" />
                  )}
                </div>
                <div>
                  <div className="flex justify-between text-[14px]">
                    <span className="text-text-secondary">Weekly Elevation</span>
                    <span className="text-text-primary font-bold">
                      {weeklyElevation > 0
                        ? `${weeklyElevation.toLocaleString()}m`
                        : '0m'}
                    </span>
                  </div>
                </div>
                </>)}
              </div>
            </div>
          </div>
        </Card>

        {/* Strength */}
        {strengthGoals.length > 0 ? (
          <Card>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-accent-blue/15 text-accent-blue">
                <Dumbbell size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-[15px] font-bold text-text-primary">Strength</h3>
                <div className="mt-2 space-y-2 text-[14px]">
                  {strengthGoals.map((g) => {
                    const label = STRENGTH_LABELS[g.metric] ?? g.metric
                    const current = g.current_value
                    const pct = current != null && g.target_value > 0
                      ? Math.min(100, (current / g.target_value) * 100) : 0
                    return (
                      <div key={g.id}>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">{label}</span>
                          <span className="text-text-primary font-bold">
                            {current != null ? `${current.toFixed(1)}kg` : <span className="text-text-muted font-normal">awaiting data</span>}
                            <span className="text-text-muted text-[12px] font-normal"> / {g.target_value}kg</span>
                          </span>
                        </div>
                        {current != null && <ProgressBar value={pct} max={100} color="#60a5fa" />}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </Card>
        ) : week < 4 ? (
          <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-bg-card border border-border-subtle">
            <Dumbbell size={16} className="text-accent-blue shrink-0" />
            <span className="text-[14px] text-text-muted">Strength targets set after Week 4 assessment (Apr 27)</span>
          </div>
        ) : (
          <Card>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-accent-blue/15 text-accent-blue">
                <Dumbbell size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-[15px] font-bold text-text-primary">Strength</h3>
                <div className="mt-2 space-y-2 text-[14px]">
                  {['Squat e1RM', 'Deadlift e1RM', 'Bench e1RM', 'OH Press e1RM', 'Row e1RM'].map(lift => (
                    <div key={lift} className="flex justify-between">
                      <span className="text-text-secondary">{lift}</span>
                      <span className="text-text-muted">awaiting data</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Season Context */}
      <Card title="Season Context">
        <div className="space-y-4">
          {[
            { label: 'Current', value: 'Winter/Spring — Mountain Primary, transitioning to summer' },
            { label: 'Next', value: 'Summer 2026 — Hike & Fly' },
            { label: 'Transition', value: 'Mid-May 2026' },
          ].map(s => (
            <div key={s.label}>
              <div className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-1">{s.label}</div>
              <div className="text-[14px] text-text-primary font-medium">{s.value}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Milestones */}
      <Card title="Milestones">
        <div className="space-y-3">
          {milestoneGoals.length === 0 && (
            <div className="text-[13px] text-text-muted">No milestones set</div>
          )}
          {milestoneGoals.map((g) => {
            const { label, detail } = milestoneTitle(g)
            const daysLeft = g.target_date ? differenceInDays(new Date(g.target_date), new Date()) : null
            const upcoming = daysLeft == null || daysLeft >= 0
            const dateStr = g.target_date
              ? new Date(g.target_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
              : ''
            return (
              <div key={g.id} className="flex items-start gap-3">
                <div className={`p-2 rounded-xl ${upcoming ? 'bg-accent-blue/15 text-accent-blue' : 'bg-accent-green/15 text-accent-green'}`}>
                  <Calendar size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-[14px] font-semibold text-text-primary">{label}</span>
                    <span className="text-[12px] text-text-muted whitespace-nowrap">{dateStr}</span>
                  </div>
                  {detail && <div className="text-[13px] text-text-secondary mt-0.5">{detail}</div>}
                  {daysLeft != null && daysLeft >= 0 && (
                    <div className="text-[11px] text-text-dim mt-0.5">{daysLeft} days remaining</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
