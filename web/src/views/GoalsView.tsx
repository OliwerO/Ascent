import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useBodyComposition, useDailyMetrics } from '../hooks/useSupabase'
import { getProgramWeek } from '../lib/program'
import { Target, Mountain, Dumbbell, Calendar } from 'lucide-react'

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

  const loading = bodyComp.loading || metrics.loading
  const error = bodyComp.error || metrics.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const latestWeight = bodyComp.data?.find((d: any) => d.weight_kg != null)
  const latestBodyFat = bodyComp.data?.find((d: any) => d.body_fat_pct != null)
  const latestVO2 = metrics.data?.find((d: any) => d.vo2max != null)

  const { week } = getProgramWeek(new Date())

  return (
    <div className="space-y-4 pb-8">
      {/* Current Goals */}
      <div>
        <h2 className="text-sm text-text-secondary font-medium mb-2">Current Goals</h2>
        <div className="space-y-3">
          {/* Body Recomp */}
          <Card>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-accent-purple/20 text-accent-purple">
                <Target size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">Body Recomposition</h3>
                <div className="mt-2 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-secondary">Weight</span>
                    <span className="text-text-primary font-medium">
                      {latestWeight?.weight_kg
                        ? `${latestWeight.weight_kg.toFixed(1)} kg`
                        : '-- kg'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-text-secondary">Body Fat</span>
                    <span className="text-text-primary font-medium">
                      {latestBodyFat?.body_fat_pct
                        ? `${latestBodyFat.body_fat_pct.toFixed(1)}%`
                        : '--%'}
                    </span>
                  </div>
                  <div className="mt-2 rounded-lg bg-bg-card-hover border border-border px-3 py-2 text-xs text-text-muted">
                    No DEXA baseline yet. Body fat target will be set after first DEXA scan.
                    Garmin scale estimates shown above.
                  </div>
                </div>
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
                          ? `${Number(latestVO2.vo2max).toFixed(1)}`
                          : '--'}
                        <span className="text-text-muted ml-1">/ target TBD</span>
                      </span>
                    </div>
                    {latestVO2?.vo2max && (
                      <ProgressBar value={Number(latestVO2.vo2max)} max={55} color="#38bdf8" />
                    )}
                  </div>
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-text-secondary">Weekly Elevation</span>
                      <span className="text-text-muted font-medium">
                        tracking in Trends view
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Strength */}
          <Card>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-accent-blue/20 text-accent-blue">
                <Dumbbell size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">Strength</h3>
                <div className="mt-2">
                  {week < 4 ? (
                    <div className="rounded-lg bg-bg-card-hover border border-border px-3 py-2 text-xs text-text-muted">
                      e1RM targets will be set after the Week 4 assessment (working weights
                      established). Currently in Week {week} — building base.
                    </div>
                  ) : (
                    <div className="space-y-2 text-sm">
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
                  )}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

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
