import { Card } from '../components/Card'
import { StatusBadge } from '../components/StatusBadge'
import { LoadingState } from '../components/LoadingState'
import { useHRV, useSleep, useDailyMetrics, useDailySummary } from '../hooks/useSupabase'
import { format } from 'date-fns'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip,
} from 'recharts'
import { AlertTriangle, CheckCircle } from 'lucide-react'

function hrvStatusColor(status: string | null | undefined): 'green' | 'yellow' | 'red' {
  if (!status) return 'yellow'
  const s = status.toUpperCase()
  if (s === 'BALANCED') return 'green'
  if (s === 'UNBALANCED') return 'yellow'
  return 'red'
}

const darkTooltipStyle = {
  backgroundColor: '#1a1a2e',
  border: '1px solid #2a2a4a',
  borderRadius: '8px',
  color: '#e4e4ef',
}

export default function RecoveryView() {
  const hrv = useHRV(14)
  const sleep = useSleep(14)
  const metrics = useDailyMetrics(14)
  const summary = useDailySummary(7)

  const loading = hrv.loading || sleep.loading || metrics.loading || summary.loading
  const error = hrv.error || sleep.error || metrics.error || summary.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const todayHRV = hrv.data?.[0]
  const todaySleep = sleep.data?.[0]
  const todayMetrics = metrics.data?.[0]

  const sleepHours = todaySleep?.total_sleep_seconds
    ? Number((todaySleep.total_sleep_seconds / 3600).toFixed(1))
    : null
  const bodyBattery = todayMetrics?.body_battery_highest ?? null
  const trainingReadiness = todayMetrics?.training_readiness_score
    ? Math.round(todayMetrics.training_readiness_score)
    : null

  // --- Degraded signal count ---
  const hrvStatus = todayHRV?.status?.toUpperCase()
  const hrvDegraded = hrvStatus === 'LOW' || hrvStatus === 'UNBALANCED'
  const sleepDegraded = sleepHours != null && sleepHours < 6
  const bbDegraded = bodyBattery != null && bodyBattery < 30
  const trDegraded = trainingReadiness != null && trainingReadiness < 40
  const degradedCount = [hrvDegraded, sleepDegraded, bbDegraded, trDegraded].filter(Boolean).length

  // --- HRV trend chart data ---
  const hrvChartData = (hrv.data ?? [])
    .slice()
    .reverse()
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: d.last_night_avg ? Math.round(d.last_night_avg) : null,
      baselineLow: d.baseline_balanced_low ? Math.round(d.baseline_balanced_low) : null,
      baselineHigh: d.baseline_balanced_upper ? Math.round(d.baseline_balanced_upper) : null,
    }))

  // --- Sleep trend chart data ---
  const sleepChartData = (sleep.data ?? [])
    .slice()
    .reverse()
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      deep: d.deep_sleep_seconds ? +(d.deep_sleep_seconds / 3600).toFixed(1) : 0,
      rem: d.rem_sleep_seconds ? +(d.rem_sleep_seconds / 3600).toFixed(1) : 0,
      light: d.light_sleep_seconds ? +(d.light_sleep_seconds / 3600).toFixed(1) : 0,
    }))

  // --- Resting HR trend chart data ---
  const restingHRData = (metrics.data ?? [])
    .slice()
    .reverse()
    .filter((d: any) => d.resting_hr != null)
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: d.resting_hr,
    }))

  // Detect rising resting HR trend (last 3 values increasing)
  const risingHR =
    restingHRData.length >= 3 &&
    restingHRData[restingHRData.length - 1].value > restingHRData[restingHRData.length - 2].value &&
    restingHRData[restingHRData.length - 2].value > restingHRData[restingHRData.length - 3].value

  // --- Fatigue flags ---
  const hrvValues = (hrv.data ?? []).slice(0, 7).filter((d: any) => d.last_night_avg != null)
  const hrvAvg =
    hrvValues.length > 0
      ? hrvValues.reduce((s: number, d: any) => s + d.last_night_avg, 0) / hrvValues.length
      : null
  const hrvSuppressedDays = hrvAvg
    ? hrvValues.filter((d: any) => d.last_night_avg < hrvAvg * 0.9).length
    : 0
  const flagHRVSuppressed = hrvSuppressedDays >= 3

  const restingHRValues = (metrics.data ?? [])
    .slice(0, 7)
    .filter((d: any) => d.resting_hr != null)
  const restingHRAvg =
    restingHRValues.length > 0
      ? restingHRValues.reduce((s: number, d: any) => s + d.resting_hr, 0) / restingHRValues.length
      : null
  const hrElevatedDays = restingHRAvg
    ? restingHRValues.filter((d: any) => d.resting_hr > restingHRAvg + 5).length
    : 0
  const flagHRElevated = hrElevatedDays >= 3

  const sleepValues = (sleep.data ?? [])
    .slice(0, 7)
    .filter((d: any) => d.total_sleep_seconds != null)
  const sleepAvgHours =
    sleepValues.length > 0
      ? sleepValues.reduce((s: number, d: any) => s + d.total_sleep_seconds / 3600, 0) /
        sleepValues.length
      : null
  const flagSleepLow = sleepAvgHours != null && sleepAvgHours < 6.5

  const flagBBLow = bodyBattery != null && bodyBattery < 30
  const flagTRLow = trainingReadiness != null && trainingReadiness < 40

  const fatigueFlags = [
    { label: 'HRV suppressed (>10% below avg for 3+ days)', active: flagHRVSuppressed },
    { label: 'Resting HR elevated (+5bpm for 3+ days)', active: flagHRElevated },
    { label: 'Sleep avg <6.5h this week', active: flagSleepLow },
    { label: 'Body Battery <30', active: flagBBLow },
    { label: 'Training Readiness <40', active: flagTRLow },
  ]
  const activeFlagCount = fatigueFlags.filter((f) => f.active).length

  return (
    <div className="space-y-4 pb-8">
      {/* Today's Readiness */}
      <div>
        <h2 className="text-sm text-text-secondary font-medium mb-2">Today&apos;s Readiness</h2>
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
            status={
              sleepHours != null
                ? sleepHours >= 7
                  ? 'green'
                  : sleepHours >= 6
                    ? 'yellow'
                    : 'red'
                : null
            }
          />
          <StatusBadge
            label="Body Battery"
            value={bodyBattery}
            thresholds={{ green: 60, yellow: 30 }}
          />
          <StatusBadge
            label="Training Readiness"
            value={trainingReadiness}
            thresholds={{ green: 60, yellow: 40 }}
          />
        </div>

        {/* Verdict */}
        <div
          className={`mt-3 rounded-lg border px-4 py-3 text-center font-semibold ${
            degradedCount === 0
              ? 'bg-accent-green/10 border-accent-green/30 text-accent-green'
              : degradedCount <= 2
                ? 'bg-accent-yellow/10 border-accent-yellow/30 text-accent-yellow'
                : 'bg-accent-red/10 border-accent-red/30 text-accent-red'
          }`}
        >
          {degradedCount === 0
            ? `TRAIN AS PLANNED (${degradedCount}/4 degraded)`
            : degradedCount <= 2
              ? `TRAIN WITH CAUTION (${degradedCount}/4 degraded)`
              : `REST DAY (${degradedCount}/4 degraded)`}
        </div>
      </div>

      {/* HRV Trend (14d) */}
      <Card title="HRV Trend (14d)">
        {hrvChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={hrvChartData}>
              <defs>
                <linearGradient id="hrvGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={{ stroke: '#2a2a4a' }}
                tickLine={false}
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
                fill="url(#baselineGrad)"
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
                fill="url(#hrvGrad)"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 3 }}
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-sm">No HRV data available</div>
        )}
      </Card>

      {/* Sleep Trend (14d) */}
      <Card title="Sleep Trend (14d)">
        {sleepChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={sleepChartData}>
              <XAxis
                dataKey="date"
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={{ stroke: '#2a2a4a' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#555570', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={30}
                unit="h"
              />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Bar dataKey="deep" stackId="sleep" fill="#1e3a5f" radius={[0, 0, 0, 0]} name="Deep" />
              <Bar dataKey="rem" stackId="sleep" fill="#7c3aed" radius={[0, 0, 0, 0]} name="REM" />
              <Bar dataKey="light" stackId="sleep" fill="#555570" radius={[2, 2, 0, 0]} name="Light" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-sm">No sleep data available</div>
        )}
      </Card>

      {/* Resting HR Trend (14d) */}
      <Card title="Resting HR Trend (14d)">
        {restingHRData.length > 0 ? (
          <>
            {risingHR && (
              <div className="flex items-center gap-2 mb-2 text-accent-yellow text-xs">
                <AlertTriangle size={14} />
                <span>Rising trend detected</span>
              </div>
            )}
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={restingHRData}>
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#555570', fontSize: 11 }}
                  axisLine={{ stroke: '#2a2a4a' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#555570', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={30}
                  domain={['dataMin - 3', 'dataMax + 3']}
                  unit=" bpm"
                />
                <Tooltip contentStyle={darkTooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={risingHR ? '#eab308' : '#f472b6'}
                  strokeWidth={2}
                  dot={{ fill: risingHR ? '#eab308' : '#f472b6', r: 3 }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        ) : (
          <div className="text-text-muted text-sm">No resting HR data available</div>
        )}
      </Card>

      {/* Fatigue Flags */}
      <Card title="Fatigue Flags">
        <div className="space-y-2">
          {fatigueFlags.map((flag) => (
            <div key={flag.label} className="flex items-start gap-2 text-sm">
              {flag.active ? (
                <AlertTriangle size={16} className="text-accent-red mt-0.5 shrink-0" />
              ) : (
                <CheckCircle size={16} className="text-accent-green mt-0.5 shrink-0" />
              )}
              <span className={flag.active ? 'text-text-primary' : 'text-text-muted'}>
                {flag.label}
              </span>
            </div>
          ))}
        </div>
        <div
          className={`mt-3 rounded-lg px-3 py-2 text-sm font-medium ${
            activeFlagCount >= 2
              ? 'bg-accent-red/10 text-accent-red'
              : 'bg-bg-card-hover text-text-secondary'
          }`}
        >
          {activeFlagCount} / 5 flags active
          {activeFlagCount >= 2 && ' — auto rest override recommended'}
        </div>
      </Card>
    </div>
  )
}
