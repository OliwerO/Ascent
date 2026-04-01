import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useHRV, useBodyComposition, useActivities, useDailyMetrics } from '../hooks/useSupabase'
import { format, startOfWeek, subDays } from 'date-fns'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip, Legend,
} from 'recharts'

const darkTooltipStyle = {
  backgroundColor: '#1a1a2e',
  border: '1px solid #2a2a4a',
  borderRadius: '8px',
  color: '#e4e4ef',
}

function classifyActivity(type: string | null | undefined): string | null {
  if (!type) return null
  const t = type.toLowerCase()
  if (t.includes('ski') || t.includes('snowboard') || t.includes('backcountry')) return 'ski'
  if (t.includes('hik') || t.includes('trail') || t.includes('mountaineering')) return 'hike'
  if (t.includes('hang_gliding') || t.includes('paraglid')) return 'fly'
  if (t.includes('run')) return 'run'
  if (t.includes('cycling') || t.includes('biking') || t.includes('ride')) return 'cycle'
  return null
}

const elevationColors: Record<string, string> = {
  ski: '#38bdf8',
  hike: '#22c55e',
  fly: '#fb923c',
  run: '#eab308',
  cycle: '#a855f7',
}

export default function TrendsView() {
  const hrv = useHRV(90)
  const bodyComp = useBodyComposition(90)
  const activities = useActivities(90)
  const metrics = useDailyMetrics(90)

  const loading = hrv.loading || bodyComp.loading || activities.loading || metrics.loading
  const error = hrv.error || bodyComp.error || activities.error || metrics.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  // --- HRV 90-day ---
  const hrvChartData = (hrv.data ?? [])
    .slice()
    .reverse()
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: d.last_night_avg ? Math.round(d.last_night_avg) : null,
      baselineLow: d.baseline_balanced_low ? Math.round(d.baseline_balanced_low) : null,
      baselineHigh: d.baseline_balanced_upper ? Math.round(d.baseline_balanced_upper) : null,
    }))

  // --- Body Composition ---
  const bodyCompData = (bodyComp.data ?? [])
    .slice()
    .reverse()
    .filter((d: any) => d.weight_kg != null)
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      weight: d.weight_kg ? +d.weight_kg.toFixed(1) : null,
      bodyFat: d.body_fat_pct ? +d.body_fat_pct.toFixed(1) : null,
    }))

  // --- Weekly Elevation (12 weeks) ---
  const twelveWeeksAgo = subDays(new Date(), 84)
  const weeklyElevation: Record<string, { total: number; byType: Record<string, number> }> = {}

  const weekDates: Record<string, Date> = {}
  for (const a of activities.data ?? []) {
    const actDate = new Date(a.date)
    if (actDate < twelveWeeksAgo || !a.elevation_gain) continue
    const actType = classifyActivity(a.activity_type)
    if (!actType) continue // skip gym, yoga, etc.
    const weekStart = startOfWeek(actDate, { weekStartsOn: 1 })
    const weekKey = format(weekStart, 'MMM d')
    if (!weeklyElevation[weekKey]) {
      weeklyElevation[weekKey] = { total: 0, byType: {} }
      weekDates[weekKey] = weekStart
    }
    weeklyElevation[weekKey].total += a.elevation_gain
    weeklyElevation[weekKey].byType[actType] =
      (weeklyElevation[weekKey].byType[actType] || 0) + a.elevation_gain
  }

  const elevationTypes = ['ski', 'hike', 'fly', 'run', 'cycle']
  const elevationChartData = Object.entries(weeklyElevation)
    .sort(([a], [b]) => (weekDates[a]?.getTime() ?? 0) - (weekDates[b]?.getTime() ?? 0))
    .map(([week, data]) => ({
      week,
      total: Math.round(data.total),
      ...Object.fromEntries(
        elevationTypes.map((t) => [t, Math.round(data.byType[t] || 0)])
      ),
    }))

  // --- VO2max Trend ---
  const vo2Data = (metrics.data ?? [])
    .slice()
    .reverse()
    .filter((d: any) => d.vo2max != null)
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: +d.vo2max.toFixed(1),
    }))
  // Deduplicate consecutive identical VO2max values (only keep changes + first/last)
  const vo2Deduped = vo2Data.filter(
    (d: any, i: number, arr: any[]) =>
      i === 0 || i === arr.length - 1 || d.value !== arr[i - 1].value
  )

  return (
    <div className="space-y-4 pb-8">
      {/* HRV 90-day */}
      <Card title="HRV (90 days)">
        {hrvChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={hrvChartData}>
              <defs>
                <linearGradient id="hrvGrad90" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="baselineGrad90" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fill: '#555570', fontSize: 10 }}
                axisLine={{ stroke: '#2a2a4a' }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={35}
              />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Area
                type="monotone"
                dataKey="baselineHigh"
                stroke="none"
                fill="url(#baselineGrad90)"
                fillOpacity={1}
                stackId="baseline"
                connectNulls
              />
              <Area
                type="monotone"
                dataKey="baselineLow"
                stroke="none"
                fill="#0a0a0f"
                fillOpacity={1}
                stackId="baseline"
                connectNulls
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                fill="url(#hrvGrad90)"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-sm">No HRV data available</div>
        )}
      </Card>

      {/* Body Composition */}
      <Card title="Body Composition">
        {bodyCompData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={bodyCompData}>
              <XAxis
                dataKey="date"
                tick={{ fill: '#555570', fontSize: 10 }}
                axisLine={{ stroke: '#2a2a4a' }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                yAxisId="weight"
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={40}
                unit=" kg"
                domain={['dataMin - 1', 'dataMax + 1']}
              />
              <YAxis
                yAxisId="bf"
                orientation="right"
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={40}
                unit="%"
                domain={['dataMin - 2', 'dataMax + 2']}
              />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Legend
                wrapperStyle={{ color: '#8888a8', fontSize: 12 }}
              />
              <Line
                yAxisId="weight"
                type="monotone"
                dataKey="weight"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="Weight (kg)"
                connectNulls
              />
              <Line
                yAxisId="bf"
                type="monotone"
                dataKey="bodyFat"
                stroke="#a855f7"
                strokeWidth={2}
                dot={false}
                name="Body Fat %"
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-sm">No body composition data available</div>
        )}
      </Card>

      {/* Weekly Elevation */}
      <Card title="Weekly Elevation (12 weeks)">
        {elevationChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={elevationChartData}>
              <XAxis
                dataKey="week"
                tick={{ fill: '#555570', fontSize: 10 }}
                axisLine={{ stroke: '#2a2a4a' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={45}
                unit="m"
              />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Legend wrapperStyle={{ color: '#8888a8', fontSize: 12 }} />
              {elevationTypes.map((type) => (
                <Bar
                  key={type}
                  dataKey={type}
                  stackId="elev"
                  fill={elevationColors[type]}
                  name={type === 'fly' ? 'Paragliding' : type.charAt(0).toUpperCase() + type.slice(1)}
                  radius={type === 'other' ? [2, 2, 0, 0] : [0, 0, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-sm">No elevation data available</div>
        )}
      </Card>

      {/* VO2max Trend */}
      <Card title="VO2max Trend">
        {vo2Deduped.length > 1 ? (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={vo2Deduped}>
              <XAxis
                dataKey="date"
                tick={{ fill: '#555570', fontSize: 10 }}
                axisLine={{ stroke: '#2a2a4a' }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={35}
                domain={['dataMin - 1', 'dataMax + 1']}
              />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ fill: '#22c55e', r: 3 }}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-sm">
            {vo2Deduped.length === 1
              ? `Current VO2max: ${vo2Deduped[0].value}`
              : 'No VO2max data available'}
          </div>
        )}
      </Card>

      {/* e1RM Progression */}
      <Card title="e1RM Progression">
        <div className="flex items-center justify-center h-32 text-text-muted text-sm">
          e1RM tracking will populate after gym sessions are completed.
        </div>
      </Card>
    </div>
  )
}
