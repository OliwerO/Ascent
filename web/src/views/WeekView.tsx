import { useMemo } from 'react'
import { Card } from '../components/Card'
import { Sparkline } from '../components/Sparkline'
import { LoadingState } from '../components/LoadingState'
import { useHRV, useActivities, useSleep } from '../hooks/useSupabase'
import { startOfWeek, endOfWeek, format, isWithinInterval } from 'date-fns'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts'

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

function sleepBarColor(hours: number): string {
  if (hours >= 7) return '#4ade80'   // green
  if (hours >= 6) return '#facc15'   // yellow
  return '#f87171'                    // red
}

export default function WeekView() {
  const activitiesHook = useActivities(14)
  const hrvHook = useHRV(14)
  const sleepHook = useSleep(14)

  const loading = activitiesHook.loading || hrvHook.loading || sleepHook.loading
  const error = activitiesHook.error || hrvHook.error || sleepHook.error

  const now = new Date()
  const weekStart = startOfWeek(now, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(now, { weekStartsOn: 1 })

  // Filter activities to current week
  const weekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: any) =>
      isWithinInterval(new Date(a.date), { start: weekStart, end: weekEnd })
    )
  }, [activitiesHook.data, weekStart.getTime(), weekEnd.getTime()])

  // Quick stats
  const totalElevation = useMemo(
    () => weekActivities.reduce((sum: number, a: any) => sum + (a.elevation_gain || 0), 0),
    [weekActivities]
  )
  const gymSessions = useMemo(
    () => weekActivities.filter((a: any) => a.activity_type === 'strength_training').length,
    [weekActivities]
  )
  const totalCalories = useMemo(
    () => weekActivities.reduce((sum: number, a: any) => sum + (a.calories || 0), 0),
    [weekActivities]
  )

  // HRV sparkline data (14d, chronological)
  const hrvSparkline = useMemo(() => {
    if (!hrvHook.data) return []
    return hrvHook.data
      .slice()
      .reverse()
      .filter((d: any) => d.last_night_avg != null)
      .map((d: any) => ({ value: d.last_night_avg }))
  }, [hrvHook.data])

  // HRV baseline for reference band
  const hrvBaseline = useMemo(() => {
    if (!hrvHook.data?.[0]) return undefined
    const latest = hrvHook.data[0]
    if (latest.baseline_balanced_low != null && latest.baseline_balanced_upper != null) {
      return { low: latest.baseline_balanced_low, high: latest.baseline_balanced_upper }
    }
    return undefined
  }, [hrvHook.data])

  // Sleep bar chart data (14d, chronological)
  const sleepBars = useMemo(() => {
    if (!sleepHook.data) return []
    return sleepHook.data
      .slice()
      .reverse()
      .map((d: any) => {
        const hours = d.total_sleep_seconds ? d.total_sleep_seconds / 3600 : 0
        return {
          date: format(new Date(d.date), 'MM/dd'),
          hours: Number(hours.toFixed(1)),
        }
      })
  }, [sleepHook.data])

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  return (
    <div className="space-y-4 pb-8">
      {/* Week Header */}
      <div>
        <h2 className="text-xl font-bold text-text-primary">This Week</h2>
        <p className="text-sm text-text-muted">
          {format(weekStart, 'MMM d')} — {format(weekEnd, 'MMM d, yyyy')}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-2">
        <Card>
          <div className="text-xs text-text-muted">Elevation</div>
          <div className="text-xl font-bold text-text-primary">
            {Math.round(totalElevation)}
            <span className="text-xs text-text-muted ml-1">m</span>
          </div>
        </Card>
        <Card>
          <div className="text-xs text-text-muted">Gym</div>
          <div className="text-xl font-bold text-text-primary">
            {gymSessions}
            <span className="text-xs text-text-muted ml-1">sessions</span>
          </div>
        </Card>
        <Card>
          <div className="text-xs text-text-muted">Calories</div>
          <div className="text-xl font-bold text-text-primary">
            {totalCalories.toLocaleString()}
            <span className="text-xs text-text-muted ml-1">kcal</span>
          </div>
        </Card>
      </div>

      {/* Activity Log */}
      <Card title="Activity Log">
        {weekActivities.length > 0 ? (
          <div className="space-y-3">
            {weekActivities.map((a: any, i: number) => (
              <div
                key={a.garmin_activity_id || i}
                className="flex items-center justify-between border-b border-border last:border-0 pb-2 last:pb-0"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-text-primary truncate">
                    {a.activity_name || formatActivityType(a.activity_type)}
                  </div>
                  <div className="text-xs text-text-muted">
                    {format(new Date(a.date), 'EEE, MMM d')}
                  </div>
                </div>
                <div className="flex gap-3 text-xs text-text-secondary shrink-0 ml-3">
                  <span>{formatDuration(a.duration_seconds)}</span>
                  {a.elevation_gain != null && a.elevation_gain > 0 && (
                    <span>{Math.round(a.elevation_gain)}m</span>
                  )}
                  {a.avg_hr != null && (
                    <span>{a.avg_hr} bpm</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-text-muted">No activities this week yet</div>
        )}
      </Card>

      {/* HRV Trend */}
      <Card title="HRV Trend (14d)">
        {hrvSparkline.length > 1 ? (
          <Sparkline
            data={hrvSparkline}
            color="#818cf8"
            height={60}
            baseline={hrvBaseline}
          />
        ) : (
          <div className="text-sm text-text-muted">Not enough data</div>
        )}
      </Card>

      {/* Sleep Trend */}
      <Card title="Sleep Trend (14d)">
        {sleepBars.length > 0 ? (
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={sleepBars} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: '#888899' }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={[0, 10]}
                tick={{ fontSize: 10, fill: '#888899' }}
                tickLine={false}
                axisLine={false}
                width={35}
              />
              <Bar dataKey="hours" radius={[3, 3, 0, 0]}>
                {sleepBars.map((entry, index) => (
                  <Cell key={index} fill={sleepBarColor(entry.hours)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-sm text-text-muted">Not enough data</div>
        )}
      </Card>
    </div>
  )
}
