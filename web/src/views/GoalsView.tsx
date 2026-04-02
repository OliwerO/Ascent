import { useMemo } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useBodyComposition, useDailyMetrics, useActivities, useGoals } from '../hooks/useSupabase'
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

  const weekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: any) =>
      isWithinInterval(new Date(a.date), { start: weekStart, end: weekEnd })
    )
  }, [activitiesHook.data, weekStart.getTime(), weekEnd.getTime()])

  const gymThisWeek = useMemo(
    () => weekActivities.filter((a: any) => a.activity_type === 'strength_training').length,
    [weekActivities]
  )
  const mountainDaysThisWeek = useMemo(
    () => weekActivities.filter((a: any) =>
      ['resort_snowboarding', 'backcountry_snowboarding', 'resort_skiing', 'backcountry_skiing', 'hiking', 'ski_touring', 'splitboarding'].includes(a.activity_type)
    ).length,
    [weekActivities]
  )
  const weeklyElevation = useMemo(
    () => Math.round((activitiesHook.data ?? [])
      .filter((a: any) => {
        const d = new Date(a.date)
        return isWithinInterval(d, { start: weekStart, end: weekEnd }) && a.activity_type !== 'hang_gliding'
      })
      .reduce((sum: number, a: any) => sum + (a.elevation_gain || 0), 0)),
    [activitiesHook.data, weekStart.getTime(), weekEnd.getTime()]
  )

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const latestWeight = bodyComp.data?.find((d: any) => d.weight_kg != null)
  const latestBodyFat = bodyComp.data?.find((d: any) => d.body_fat_pct != null)
  const latestVO2 = metrics.data?.find((d: any) => d.vo2max != null)
  const bodyCompGoals = (goalsHook.data ?? []).filter((g: any) => g.category === 'body_composition')

  const { week } = getProgramWeek(new Date())

  return (
    <div className="space-y-4 pb-8">
      {/* Current Goals */}
      <div>
        <h2 className="text-sm text-text-secondary font-medium mb-2">Current Goals</h2>
        <div className="space-y-3">
          {/* Body Recomp — with goals */}
          <Card>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-accent-purple/20 text-accent-purple">
                <Target size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">Body Recomposition</h3>
                {bodyCompGoals.length > 0 ? (
                  <div className="mt-3 space-y-4">
                    {bodyCompGoals.map((goal: any) => {
                      const current = goal.metric === 'weight_kg' ? latestWeight?.weight_kg
                        : goal.metric === 'body_fat_pct' ? latestBodyFat?.body_fat_pct
                        : goal.metric === 'muscle_mass_kg' && latestWeight?.muscle_mass_grams
                          ? latestWeight.muscle_mass_grams / 1000 : null
                      const target = goal.target_value
                      const start = goal.current_value
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
                      const color = movingRight ? '#34d399' : current === start ? '#f59e0b' : '#f87171'

                      return (
                        <div key={goal.id}>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-text-secondary">{label}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-text-primary font-medium">
                                {current != null ? (goal.metric === 'body_fat_pct' ? `~${current.toFixed(0)}` : current.toFixed(1)) : '--'}{unit}
                              </span>
                              {current != null && (
                                movingRight
                                  ? <TrendingDown size={12} className="text-accent-green" />
                                  : current === start
                                    ? <Minus size={12} className="text-accent-yellow" />
                                    : <TrendingUp size={12} className="text-accent-red" />
                              )}
                              <span className="text-text-muted text-xs">→ {target}{unit}</span>
                            </div>
                          </div>
                          <ProgressBar value={movingRight ? progressPct : 0} max={100} color={color} />
                          {daysLeft != null && daysLeft > 0 && (
                            <div className="text-[10px] text-text-muted mt-1">
                              {daysLeft} days remaining · started at {start}{unit}
                            </div>
                          )}
                        </div>
                      )
                    })}
                    {bodyCompGoals[0]?.notes && (
                      <div className="text-[10px] text-text-muted/60 mt-1">
                        {bodyCompGoals[0].metric === 'body_fat_pct' ? 'BIA has ±5% error — track direction, not absolute value' : ''}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 space-y-2">
                    {latestWeight?.weight_kg && (
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Weight</span>
                        <span className="text-text-primary font-medium">{latestWeight.weight_kg.toFixed(1)} kg</span>
                      </div>
                    )}
                    {latestBodyFat?.body_fat_pct && (
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Body Fat</span>
                        <span className="text-text-primary font-medium">{latestBodyFat.body_fat_pct.toFixed(1)}% <span className="text-text-muted text-xs">(±5%)</span></span>
                      </div>
                    )}
                    {!latestWeight?.weight_kg && !latestBodyFat?.body_fat_pct && (
                      <div className="rounded-lg bg-bg-card-hover border border-border px-3 py-2 text-xs text-text-muted">
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
              <div className="p-2 rounded-lg bg-mountain/20 text-mountain">
                <Mountain size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">Endurance</h3>
                <div className="mt-2 space-y-3">
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-text-secondary">VO2max</span>
                      <span className="text-text-primary font-medium">
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
                    <div className="flex justify-between text-sm">
                      <span className="text-text-secondary">Weekly Elevation</span>
                      <span className="text-text-primary font-medium">
                        {weeklyElevation > 0
                          ? `${weeklyElevation.toLocaleString()}m`
                          : '0m'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Strength */}
          {week < 4 ? (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-bg-card border border-border">
              <Dumbbell size={16} className="text-accent-blue shrink-0" />
              <span className="text-sm text-text-muted">Strength targets set after Week 4 assessment (Apr 27)</span>
            </div>
          ) : (
            <Card>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-accent-blue/20 text-accent-blue">
                  <Dumbbell size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-text-primary">Strength</h3>
                  <div className="mt-2 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Squat e1RM</span>
                      <span className="text-text-muted">awaiting data</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Deadlift e1RM</span>
                      <span className="text-text-muted">awaiting data</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Bench e1RM</span>
                      <span className="text-text-muted">awaiting data</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">OH Press e1RM</span>
                      <span className="text-text-muted">awaiting data</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Row e1RM</span>
                      <span className="text-text-muted">awaiting data</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* This Week */}
      <Card title="This Week">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2">
            <Dumbbell size={16} className="text-accent-blue shrink-0" />
            <div>
              <div className="text-lg font-bold text-text-primary">{gymThisWeek}<span className="text-sm text-text-muted font-normal">/3</span></div>
              <div className="text-xs text-text-muted">Strength sessions</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Mountain size={16} className="text-mountain shrink-0" />
            <div>
              <div className="text-lg font-bold text-text-primary">{mountainDaysThisWeek}</div>
              <div className="text-xs text-text-muted">Mountain days</div>
            </div>
          </div>
        </div>
      </Card>

      {/* Season Context */}
      <Card title="Season Context">
        <div className="space-y-4">
          <div>
            <div className="text-xs text-text-muted uppercase tracking-wider mb-1">Current</div>
            <div className="text-sm text-text-primary font-medium">
              Winter/Spring — Mountain Primary, transitioning to summer
            </div>
          </div>
          <div>
            <div className="text-xs text-text-muted uppercase tracking-wider mb-1">Next</div>
            <div className="text-sm text-text-primary font-medium">
              Summer 2026 — Hike &amp; Fly
            </div>
          </div>
          <div>
            <div className="text-xs text-text-muted uppercase tracking-wider mb-1">Transition</div>
            <div className="text-sm text-text-primary font-medium">
              Mid-May 2026
            </div>
          </div>
        </div>
      </Card>

      {/* Milestones */}
      <Card title="Milestones">
        <div className="space-y-3">
          {[
            {
              label: 'Week 4 Assessment',
              date: 'Apr 27, 2026',
              detail: 'Body comp, working weights, Opus review',
              upcoming: week < 4,
            },
            {
              label: 'Week 8 Assessment',
              date: 'May 25, 2026',
              detail: 'Full review, block comparison',
              upcoming: week < 8,
            },
            {
              label: 'Season Transition',
              date: 'Mid-May 2026',
              detail: 'Mountain primary to Hike & Fly',
              upcoming: true,
            },
          ].map((m) => (
            <div
              key={m.label}
              className="flex items-start gap-3"
            >
              <div
                className={`p-2 rounded-lg ${
                  m.upcoming
                    ? 'bg-accent-blue/20 text-accent-blue'
                    : 'bg-accent-green/20 text-accent-green'
                }`}
              >
                <Calendar size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium text-text-primary">{m.label}</span>
                  <span className="text-xs text-text-muted whitespace-nowrap">{m.date}</span>
                </div>
                <div className="text-xs text-text-secondary mt-0.5">{m.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
