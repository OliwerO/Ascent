import { Card } from '../components/Card'
import { StatusBadge } from '../components/StatusBadge'
import { Sparkline } from '../components/Sparkline'
import { LoadingState } from '../components/LoadingState'
import { useDailySummary, useHRV, useDailyMetrics, useActivities } from '../hooks/useSupabase'
import { getProgramWeek } from '../lib/program'

function hrvStatusColor(status: string | null | undefined): 'green' | 'yellow' | 'red' {
  if (!status) return 'yellow'
  const s = status.toUpperCase()
  if (s === 'BALANCED') return 'green'
  if (s === 'UNBALANCED') return 'yellow'
  return 'red'
}

function sleepStatusColor(hours: number): 'green' | 'yellow' | 'red' {
  if (hours >= 7) return 'green'
  if (hours >= 6) return 'yellow'
  return 'red'
}

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatActivityType(type: string | null | undefined): string {
  if (!type) return ''
  return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function TodayView() {
  const summary = useDailySummary(7)
  const hrv = useHRV(14)
  const metrics = useDailyMetrics(7)
  const activities = useActivities(7)

  const loading = summary.loading || hrv.loading || metrics.loading || activities.loading
  const error = summary.error || hrv.error || metrics.error || activities.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const today = summary.data?.[0]
  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const yesterdayActivity = activities.data?.[0]

  const sleepHours = today?.total_sleep_seconds
    ? Number((today.total_sleep_seconds / 3600).toFixed(1))
    : null

  const { block, week } = getProgramWeek(new Date())

  // Build 7-day resting HR sparkline from metrics (most recent last)
  const restingHRData = (metrics.data ?? [])
    .slice()
    .reverse()
    .filter((d: any) => d.resting_hr != null)
    .map((d: any) => ({ value: d.resting_hr }))

  return (
    <div className="space-y-4 pb-8">
      {/* Recovery Triad */}
      <div>
        <h2 className="text-sm text-text-secondary font-medium mb-2">Recovery Triad</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatusBadge
            label="HRV"
            value={todayHRV?.last_night_avg != null ? Math.round(todayHRV.last_night_avg) : null}
            unit="ms"
            status={hrvStatusColor(todayHRV?.status)}
          />
          <StatusBadge
            label="Sleep"
            value={sleepHours}
            unit="h"
            status={sleepHours != null ? sleepStatusColor(sleepHours) : null}
          />
          <StatusBadge
            label="Body Battery"
            value={todayMetrics?.body_battery_highest ?? null}
            thresholds={{ green: 60, yellow: 30 }}
          />
          <StatusBadge
            label="Readiness"
            value={todayMetrics?.training_readiness_score != null
              ? Math.round(todayMetrics.training_readiness_score)
              : null}
            thresholds={{ green: 60, yellow: 40 }}
          />
        </div>
      </div>

      {/* Resting HR */}
      <Card title="Resting HR">
        <div className="flex items-center gap-4">
          <div className="text-3xl font-bold text-text-primary">
            {todayMetrics?.resting_hr ?? '--'}
            <span className="text-sm text-text-muted ml-1">bpm</span>
          </div>
          <div className="flex-1 min-w-0">
            {restingHRData.length > 1 && (
              <Sparkline data={restingHRData} color="#f472b6" height={36} />
            )}
          </div>
        </div>
        <div className="text-xs text-text-muted mt-1">7-day trend</div>
      </Card>

      {/* Yesterday's Activity */}
      <Card title="Latest Activity">
        {yesterdayActivity ? (
          <div className="space-y-1">
            <div className="text-lg font-semibold text-text-primary">
              {yesterdayActivity.activity_name || formatActivityType(yesterdayActivity.activity_type)}
            </div>
            <div className="text-sm text-text-secondary">
              {formatActivityType(yesterdayActivity.activity_type)}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-text-secondary">
              <span>{formatDuration(yesterdayActivity.duration_seconds)}</span>
              {yesterdayActivity.elevation_gain != null && yesterdayActivity.elevation_gain > 0 && (
                <span>{Math.round(yesterdayActivity.elevation_gain)}m gain</span>
              )}
              {yesterdayActivity.calories != null && (
                <span>{yesterdayActivity.calories} kcal</span>
              )}
              {yesterdayActivity.avg_hr != null && (
                <span>Avg HR {yesterdayActivity.avg_hr}</span>
              )}
            </div>
          </div>
        ) : (
          <div className="text-text-muted text-sm">No recent activity</div>
        )}
      </Card>

      {/* Current Phase */}
      <Card title="Current Phase">
        <div className="text-lg font-semibold text-accent-blue">
          Block {block} — {block === 1 ? 'Base Rebuild' : 'Progression'}
        </div>
        <div className="text-sm text-text-secondary mt-1">
          Week {week} of 8
        </div>
        <div className="w-full bg-border rounded-full h-2 mt-3">
          <div
            className="bg-accent-blue rounded-full h-2 transition-all"
            style={{ width: `${(week / 8) * 100}%` }}
          />
        </div>
      </Card>
    </div>
  )
}
