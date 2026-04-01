import { Card } from '../components/Card'
import { StatusBadge } from '../components/StatusBadge'
import { Sparkline } from '../components/Sparkline'
import { LoadingState } from '../components/LoadingState'
import { useDailySummary, useHRV, useDailyMetrics, useActivities } from '../hooks/useSupabase'
import { getProgramWeek, isDeloadWeek } from '../lib/program'
import { Clock, Flame, ArrowUpRight, Heart } from 'lucide-react'

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
  const deload = isDeloadWeek(week)

  const restingHRData = (metrics.data ?? [])
    .slice()
    .reverse()
    .filter((d: any) => d.resting_hr != null)
    .map((d: any) => ({ value: d.resting_hr }))

  // --- Trend context calculations ---
  const hrvWeeklyAvg = todayHRV?.weekly_avg != null ? Math.round(todayHRV.weekly_avg) : null

  const sleepDays = (summary.data ?? []).slice(0, 7)
  const sleepBelowCount = sleepDays.filter(
    (d: any) => d.total_sleep_seconds != null && d.total_sleep_seconds / 3600 < 6
  ).length
  const sleepAvgHours = sleepDays.filter((d: any) => d.total_sleep_seconds != null).length > 0
    ? sleepDays
        .filter((d: any) => d.total_sleep_seconds != null)
        .reduce((s: number, d: any) => s + d.total_sleep_seconds / 3600, 0) /
      sleepDays.filter((d: any) => d.total_sleep_seconds != null).length
    : null

  const bbHigh = todayMetrics?.body_battery_highest ?? null
  const bbLow = todayMetrics?.body_battery_lowest ?? null

  const yesterdayMetrics = metrics.data?.[1]
  const todayReadiness = todayMetrics?.training_readiness_score != null
    ? Math.round(todayMetrics.training_readiness_score) : null
  const yesterdayReadiness = yesterdayMetrics?.training_readiness_score != null
    ? Math.round(yesterdayMetrics.training_readiness_score) : null
  const readinessDelta = todayReadiness != null && yesterdayReadiness != null
    ? todayReadiness - yesterdayReadiness : null

  // Determine overall readiness
  const degradedCount = [
    todayHRV?.status?.toUpperCase() === 'LOW' || todayHRV?.status?.toUpperCase() === 'UNBALANCED',
    sleepHours != null && sleepHours < 6,
    (todayMetrics?.body_battery_highest ?? 100) < 30,
    (todayMetrics?.training_readiness_score ?? 100) < 40,
  ].filter(Boolean).length

  const verdictColor = degradedCount === 0 ? 'text-accent-green' : degradedCount <= 1 ? 'text-accent-yellow' : 'text-accent-red'
  const verdictText = degradedCount === 0 ? 'Good to train' : degradedCount <= 1 ? 'Train with caution' : 'Consider rest'

  return (
    <div className="space-y-4">
      {/* Readiness verdict */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">Recovery</h2>
          <p className={`text-sm font-medium ${verdictColor}`}>{verdictText}</p>
        </div>
        <div className="text-right">
          <div className="text-[11px] text-text-muted uppercase tracking-wider">Signals</div>
          <div className={`text-lg font-semibold font-data ${verdictColor}`}>
            {4 - degradedCount}/4
          </div>
        </div>
      </div>

      {/* Recovery Triad */}
      <div className="grid grid-cols-2 gap-3">
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
      <div className="text-[11px] text-text-muted mt-2 space-y-0.5">
        {todayHRV?.status && (
          <div>
            HRV {todayHRV.status.toLowerCase()}
            {hrvWeeklyAvg != null && <> &middot; {hrvWeeklyAvg}ms weekly avg</>}
          </div>
        )}
        {bbHigh != null && bbLow != null && (
          <div>Body Battery high {bbHigh} &middot; low {bbLow}</div>
        )}
        {sleepBelowCount > 0 ? (
          <div>{sleepBelowCount} night{sleepBelowCount > 1 ? 's' : ''} below 6h this week</div>
        ) : sleepAvgHours != null && sleepAvgHours >= 7 ? (
          <div>Sleep on target &middot; {sleepAvgHours.toFixed(1)}h avg</div>
        ) : sleepAvgHours != null ? (
          <div>Sleep avg {sleepAvgHours.toFixed(1)}h &middot; below 7h target</div>
        ) : null}
        {readinessDelta != null && readinessDelta !== 0 && (
          <div>
            Readiness {readinessDelta > 0 ? '\u2191' : '\u2193'}{Math.abs(readinessDelta)} vs yesterday
          </div>
        )}
      </div>

      {/* Resting HR */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-accent-red/10 flex items-center justify-center">
              <Heart size={18} className="text-accent-red" />
            </div>
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider">Resting HR</div>
              <div className="text-2xl font-semibold font-data text-text-primary">
                {todayMetrics?.resting_hr ?? '--'}
                <span className="text-sm text-text-muted ml-1 font-normal">bpm</span>
              </div>
            </div>
          </div>
          <div className="w-28">
            {restingHRData.length > 1 && (
              <Sparkline data={restingHRData} color="#f87171" height={32} />
            )}
          </div>
        </div>
      </Card>

      {/* Latest Activity */}
      <Card>
        <div className="text-[11px] text-text-muted uppercase tracking-wider mb-3">Latest Activity</div>
        {yesterdayActivity ? (
          <div>
            <div className="text-lg font-semibold text-text-primary leading-tight">
              {yesterdayActivity.activity_name || formatActivityType(yesterdayActivity.activity_type)}
            </div>
            <div className="text-xs text-text-muted mt-0.5 mb-3">
              {formatActivityType(yesterdayActivity.activity_type)}
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {yesterdayActivity.duration_seconds && (
                <div className="flex items-center gap-2">
                  <Clock size={14} className="text-text-muted" />
                  <span className="text-sm text-text-secondary">{formatDuration(yesterdayActivity.duration_seconds)}</span>
                </div>
              )}
              {yesterdayActivity.elevation_gain != null && yesterdayActivity.elevation_gain > 0 && (
                <div className="flex items-center gap-2">
                  <ArrowUpRight size={14} className="text-mountain" />
                  <span className="text-sm text-text-secondary">{Math.round(yesterdayActivity.elevation_gain)}m</span>
                </div>
              )}
              {yesterdayActivity.calories != null && (
                <div className="flex items-center gap-2">
                  <Flame size={14} className="text-accent-orange" />
                  <span className="text-sm text-text-secondary">{yesterdayActivity.calories} kcal</span>
                </div>
              )}
              {yesterdayActivity.avg_hr != null && (
                <div className="flex items-center gap-2">
                  <Heart size={14} className="text-accent-red" />
                  <span className="text-sm text-text-secondary">{yesterdayActivity.avg_hr} bpm</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-text-muted text-sm">No recent activity</div>
        )}
      </Card>

      {/* Current Phase */}
      <Card glow="green">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider mb-1">Current Block</div>
            <div className="text-lg font-semibold text-text-primary">
              {block === 1 ? 'Base Rebuild' : 'Progression'}
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold font-data text-accent-green">
              {week}<span className="text-base text-text-muted font-normal">/8</span>
            </div>
            <div className="text-[11px] text-text-muted">
              {deload ? 'Deload week' : `Block ${block}`}
            </div>
          </div>
        </div>
        <div className="w-full bg-bg-elevated rounded-full h-1.5">
          <div
            className="bg-accent-green rounded-full h-1.5 transition-all duration-500"
            style={{ width: `${(week / 8) * 100}%` }}
          />
        </div>
      </Card>
    </div>
  )
}
