import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import {
  useHRV, useSleep, useDailyMetrics, useActivities, useSubjectiveWellness,
} from '../hooks/useSupabase'
import { format } from 'date-fns'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip,
} from 'recharts'
import { AlertTriangle, CheckCircle } from 'lucide-react'
import { computeCoachingState } from '../lib/coachingDecision'
import { MOUNTAIN_ACTIVITY_TYPES } from '../lib/activityTypes'

const darkTooltipStyle = {
  backgroundColor: '#16161e',
  border: '1px solid #262636',
  borderRadius: '12px',
  color: '#f0f0f5',
  fontSize: '12px',
}

export default function RecoveryView() {
  const hrv = useHRV(14)
  const sleep = useSleep(14)
  const metrics = useDailyMetrics(14)
  const activities = useActivities(14)
  const wellness = useSubjectiveWellness(14)
  const loading = hrv.loading || sleep.loading || metrics.loading || activities.loading
  const error = hrv.error || sleep.error || metrics.error || activities.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  const todayHRV = hrv.data?.[0]
  const todayMetrics = metrics.data?.[0]
  const todaySleep = sleep.data?.[0]
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const todayWellness = (wellness.data ?? []).find((w) => w.date === todayStr) ?? null

  const bodyBattery = todayMetrics?.body_battery_highest ?? null
  const trainingReadiness = todayMetrics?.training_readiness_score
    ? Math.round(todayMetrics.training_readiness_score)
    : null

  // --- HRV trend chart data ---
  const hrvChartData = (hrv.data ?? [])
    .slice()
    .reverse()
    .map((d) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: d.last_night_avg ? Math.round(d.last_night_avg) : null,
      baselineLow: d.baseline_balanced_low ? Math.round(d.baseline_balanced_low) : null,
      baselineHigh: d.baseline_balanced_upper ? Math.round(d.baseline_balanced_upper) : null,
    }))

  // --- Sleep trend chart data ---
  const sleepChartData = (sleep.data ?? [])
    .slice()
    .reverse()
    .map((d) => ({
      date: format(new Date(d.date), 'MMM d'),
      deep: d.deep_sleep_seconds ? +(d.deep_sleep_seconds / 3600).toFixed(1) : 0,
      rem: d.rem_sleep_seconds ? +(d.rem_sleep_seconds / 3600).toFixed(1) : 0,
      light: d.light_sleep_seconds ? +(d.light_sleep_seconds / 3600).toFixed(1) : 0,
    }))

  // --- Resting HR trend chart data ---
  const restingHRData = (metrics.data ?? [])
    .slice()
    .reverse()
    .filter((d) => d.resting_hr != null)
    .map((d) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: d.resting_hr,
    }))

  // Detect rising resting HR trend
  const recentHR3 = restingHRData.slice(-3)
  const previousHR7 = restingHRData.slice(Math.max(0, restingHRData.length - 10), Math.max(0, restingHRData.length - 3))
  const recentHRAvg = recentHR3.length > 0
    ? recentHR3.reduce((s: number, d) => s + d.value!, 0) / recentHR3.length : null
  const previousHRAvg = previousHR7.length > 0
    ? previousHR7.reduce((s: number, d) => s + d.value!, 0) / previousHR7.length : null
  const hrRiseDelta = recentHRAvg != null && previousHRAvg != null
    ? Math.round((recentHRAvg - previousHRAvg) * 10) / 10 : null
  const risingHR = hrRiseDelta != null && hrRiseDelta > 3

  // --- HRV trend context ---
  const currentHRVStatus = todayHRV?.status?.toUpperCase() ?? null
  const hrvDegraded = currentHRVStatus === 'LOW' || currentHRVStatus === 'UNBALANCED'
  let hrvConsecutiveDays = 0
  if (currentHRVStatus && hrv.data) {
    for (const d of hrv.data ?? []) {
      if (d.status?.toUpperCase() === currentHRVStatus) hrvConsecutiveDays++
      else break
    }
  }
  const hrv14DayValues = (hrv.data ?? []).filter((d) => d.last_night_avg != null)
  const hrv14DayAvg = hrv14DayValues.length > 0
    ? hrv14DayValues.reduce((s: number, d) => s + d.last_night_avg!, 0) / hrv14DayValues.length
    : null
  const hrvPctChange = todayHRV?.last_night_avg != null && hrv14DayAvg != null && hrv14DayAvg > 0
    ? Math.round(((todayHRV.last_night_avg - hrv14DayAvg) / hrv14DayAvg) * 100)
    : null

  // --- Sleep trend context ---
  const sleep7Days = (sleep.data ?? []).slice(0, 7).filter((d) => d.total_sleep_seconds != null)
  const sleepWeeklyAvg = sleep7Days.length > 0
    ? sleep7Days.reduce((s: number, d) => s + d.total_sleep_seconds! / 3600, 0) / sleep7Days.length
    : null
  const nightsBelow6h = sleep7Days.filter((d) => d.total_sleep_seconds! / 3600 < 6).length

  // --- Fatigue flags ---
  const hrvValues = (hrv.data ?? []).slice(0, 7).filter((d) => d.last_night_avg != null)
  const hrvAvg =
    hrvValues.length > 0
      ? hrvValues.reduce((s: number, d) => s + d.last_night_avg!, 0) / hrvValues.length
      : null
  const hrvSuppressedDays = hrvAvg
    ? hrvValues.filter((d) => d.last_night_avg! < hrvAvg * 0.9).length
    : 0
  const flagHRVSuppressed = hrvSuppressedDays >= 3

  const restingHRValues = (metrics.data ?? [])
    .slice(0, 7)
    .filter((d) => d.resting_hr != null)
  const restingHRAvg =
    restingHRValues.length > 0
      ? restingHRValues.reduce((s: number, d) => s + d.resting_hr!, 0) / restingHRValues.length
      : null
  const hrElevatedDays = restingHRAvg
    ? restingHRValues.filter((d) => d.resting_hr! > restingHRAvg + 5).length
    : 0
  const flagHRElevated = hrElevatedDays >= 3

  const sleepValues = (sleep.data ?? [])
    .slice(0, 7)
    .filter((d) => d.total_sleep_seconds != null)
  const sleepAvgHours =
    sleepValues.length > 0
      ? sleepValues.reduce((s: number, d) => s + d.total_sleep_seconds! / 3600, 0) /
        sleepValues.length
      : null
  const flagSleepLow = sleepAvgHours != null && sleepAvgHours < 6.5

  const flagBBLow = bodyBattery != null && bodyBattery < 30
  const flagTRLow = trainingReadiness != null && trainingReadiness < 40

  // --- Primary recovery signals ---
  const primaryFlags = [
    {
      label: flagHRVSuppressed
        ? `HRV suppressed: ${hrvSuppressedDays} of 7 days >10% below avg${hrvAvg ? ` (avg ${Math.round(hrvAvg)}ms)` : ''}`
        : `HRV stable${hrvAvg ? ` (${Math.round(hrvAvg)}ms 7d avg)` : ''}`,
      active: flagHRVSuppressed,
    },
    {
      label: flagSleepLow
        ? `Sleep low: ${sleepAvgHours != null ? sleepAvgHours.toFixed(1) : '?'}h avg this week (<6.5h threshold)`
        : `Sleep adequate${sleepAvgHours != null ? ` (${sleepAvgHours.toFixed(1)}h avg)` : ''}`,
      active: flagSleepLow,
    },
    {
      label: flagHRElevated
        ? `Resting HR elevated: ${hrElevatedDays} of 7 days >5bpm above avg${restingHRAvg ? ` (avg ${Math.round(restingHRAvg)})` : ''}`
        : `Resting HR normal${restingHRAvg ? ` (${Math.round(restingHRAvg)}bpm 7d avg)` : ''}`,
      active: flagHRElevated,
    },
  ]
  const primaryFlagCount = primaryFlags.filter((f) => f.active).length

  // --- Garmin indicators ---
  const garminIndicators = [
    { label: `Body Battery: ${bodyBattery ?? '—'}`, active: flagBBLow },
    { label: `Training Readiness: ${trainingReadiness ?? '—'}`, active: flagTRLow },
  ]

  // --- HRV 14d trend direction ---
  const hrvFirst7 = (hrv.data ?? []).slice(7, 14).filter((d) => d.last_night_avg != null)
  const hrvLast7 = (hrv.data ?? []).slice(0, 7).filter((d) => d.last_night_avg != null)
  const hrvFirst7Avg = hrvFirst7.length > 0 ? hrvFirst7.reduce((s: number, d) => s + d.last_night_avg!, 0) / hrvFirst7.length : null
  const hrvLast7Avg = hrvLast7.length > 0 ? hrvLast7.reduce((s: number, d) => s + d.last_night_avg!, 0) / hrvLast7.length : null
  const hrv14dPctChange = hrvFirst7Avg != null && hrvLast7Avg != null && hrvFirst7Avg > 0
    ? Math.round(((hrvLast7Avg - hrvFirst7Avg) / hrvFirst7Avg) * 100) : null
  const hrvTrendLabel = hrv14dPctChange != null
    ? hrv14dPctChange > 3 ? `↑ Improving +${hrv14dPctChange}% over 14 days`
      : hrv14dPctChange < -3 ? `↓ Declining ${hrv14dPctChange}% over 14 days`
      : `→ Stable around ${hrvLast7Avg != null ? Math.round(hrvLast7Avg) : '--'}ms`
    : null

  // --- Sleep 14d trend direction ---
  const sleepFirst7 = (sleep.data ?? []).slice(7, 14).filter((d) => d.total_sleep_seconds != null)
  const sleepLast7 = (sleep.data ?? []).slice(0, 7).filter((d) => d.total_sleep_seconds != null)
  const sleepFirst7Avg = sleepFirst7.length > 0 ? sleepFirst7.reduce((s: number, d) => s + d.total_sleep_seconds! / 3600, 0) / sleepFirst7.length : null
  const sleepLast7Avg = sleepLast7.length > 0 ? sleepLast7.reduce((s: number, d) => s + d.total_sleep_seconds! / 3600, 0) / sleepLast7.length : null
  const sleep14dPctChange = sleepFirst7Avg != null && sleepLast7Avg != null && sleepFirst7Avg > 0
    ? Math.round(((sleepLast7Avg - sleepFirst7Avg) / sleepFirst7Avg) * 100) : null
  const sleepTrendLabel = sleep14dPctChange != null
    ? sleep14dPctChange > 5 ? `↑ Improving +${sleep14dPctChange}% over 14 days`
      : sleep14dPctChange < -5 ? `↓ Declining ${sleep14dPctChange}% over 14 days`
      : `→ Stable around ${sleepLast7Avg != null ? sleepLast7Avg.toFixed(1) : '--'}h`
    : null

  // --- Resting HR 14d trend direction ---
  const hrFirst7 = restingHRData.slice(0, Math.floor(restingHRData.length / 2))
  const hrLater7 = restingHRData.slice(Math.floor(restingHRData.length / 2))
  const hrFirst7Avg = hrFirst7.length > 0 ? hrFirst7.reduce((s: number, d) => s + d.value!, 0) / hrFirst7.length : null
  const hrLater7Avg = hrLater7.length > 0 ? hrLater7.reduce((s: number, d) => s + d.value!, 0) / hrLater7.length : null
  const hr14dPctChange = hrFirst7Avg != null && hrLater7Avg != null && hrFirst7Avg > 0
    ? Math.round(((hrLater7Avg - hrFirst7Avg) / hrFirst7Avg) * 100) : null
  const hrTrendLabel = hr14dPctChange != null
    ? hr14dPctChange > 3 ? `↑ Rising +${hr14dPctChange}% over 14 days — monitor closely`
      : hr14dPctChange < -3 ? `↓ Dropping ${hr14dPctChange}% over 14 days`
      : `→ Stable around ${hrLater7Avg != null ? Math.round(hrLater7Avg) : '--'}bpm`
    : null

  const axisTickStyle = { fill: '#646478', fontSize: 11 }
  const axisLineStyle = { stroke: '#262636' }

  // ─── Coaching recommendation ───
  const sleepHoursLastNight = todaySleep?.total_sleep_seconds
    ? todaySleep.total_sleep_seconds / 3600
    : null
  const decision = computeCoachingState({
    hrvStatus: todayHRV?.status,
    hrvVal: todayHRV?.last_night_avg ?? null,
    hrvWeeklyAvg: todayHRV?.weekly_avg ?? null,
    sleepHoursLastNight,
    sleep7dAvg: sleepWeeklyAvg,
    wellnessComposite: todayWellness?.composite_score ?? null,
    bodyBattery,
    trainingReadiness,
    rhrElevated: flagHRElevated,
  })

  // ─── Days since last rest day ───
  // A "rest day" = a day with no strength_training and no MOUNTAIN activity in the last 14 days.
  const daysSinceRest = (() => {
    const acts = activities.data ?? []
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    for (let i = 0; i < 14; i++) {
      const d = new Date(today)
      d.setDate(today.getDate() - i)
      const dStr = format(d, 'yyyy-MM-dd')
      const dayHasLoad = acts.some((a) =>
        a.date === dStr && (
          a.activity_type === 'strength_training' ||
          MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type)
        )
      )
      if (!dayHasLoad) return i
    }
    return 14 // capped
  })()

  const decisionGlow = decision.state === 'red' ? 'red' : decision.state === 'amber' ? 'yellow' : 'green'
  const decisionTextColor =
    decision.state === 'red' ? 'text-accent-red'
    : decision.state === 'amber' ? 'text-accent-yellow'
    : 'text-accent-green'

  return (
    <div className="space-y-3 pb-8">
      {/* Coach's Recommendation */}
      <Card glow={decisionGlow}>
        <div className="text-[10px] uppercase tracking-wider font-semibold text-text-muted mb-1">
          Coach's recommendation
        </div>
        <div className={`text-lg font-bold ${decisionTextColor}`}>{decision.label}</div>
        <p className="text-[13px] text-text-secondary mt-2 leading-relaxed">
          {decision.recommendation}
        </p>
        {decision.reasons.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border-subtle">
            <div className="text-[10px] uppercase tracking-wider text-text-dim mb-1">Signals</div>
            <ul className="text-[12px] text-text-muted space-y-0.5">
              {decision.reasons.map((r) => (
                <li key={r}>• {r}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-3 pt-3 border-t border-border-subtle flex items-center justify-between text-[12px]">
          <span className="text-text-muted">Days since last rest day</span>
          <span className={`font-bold font-data ${
            daysSinceRest >= 7 ? 'text-accent-red'
            : daysSinceRest >= 4 ? 'text-accent-yellow'
            : 'text-text-secondary'
          }`}>
            {daysSinceRest === 14 ? '14+' : daysSinceRest}
          </span>
        </div>
      </Card>

      {/* Recovery Signals */}
      <Card title="Recovery Signals">
        <div className="space-y-2.5">
          {primaryFlags.map((flag) => (
            <div key={flag.label} className="flex items-start gap-2.5 text-[14px]">
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
          className={`mt-4 rounded-xl px-4 py-2.5 text-[14px] font-semibold ${
            primaryFlagCount >= 2
              ? 'bg-accent-red/10 text-accent-red'
              : 'bg-bg-elevated text-text-secondary'
          }`}
        >
          {primaryFlagCount} / {primaryFlags.length} signals flagged
          {primaryFlagCount >= 2 && ' — consider rest or light session'}
        </div>

        {/* Garmin Indicators */}
        <details className="mt-3 pt-3 border-t border-border">
          <summary className="text-[12px] text-text-dim cursor-pointer hover:text-text-muted">
            Show Garmin indicators (estimates)
          </summary>
          <div className="mt-2.5 space-y-2 opacity-60">
            {garminIndicators.map((ind) => (
              <div key={ind.label} className="flex items-start gap-2 text-[13px]">
                {ind.active ? (
                  <AlertTriangle size={13} className="text-accent-yellow mt-0.5 shrink-0" />
                ) : (
                  <CheckCircle size={13} className="text-accent-green/60 mt-0.5 shrink-0" />
                )}
                <span className="text-text-muted">{ind.label}</span>
              </div>
            ))}
          </div>
        </details>
      </Card>

      {/* HRV Trend (14d) */}
      <Card title="HRV Trend (14d)">
        {hrvTrendLabel && (
          <div className="text-[13px] font-semibold text-text-secondary mb-1">{hrvTrendLabel}</div>
        )}
        {currentHRVStatus && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3 text-[13px] text-text-secondary">
            <span>
              Status: <span className={hrvDegraded ? 'text-accent-yellow font-semibold' : 'text-accent-green font-semibold'}>
                {currentHRVStatus.toLowerCase()}
              </span>
              {hrvConsecutiveDays > 1 && <> ({hrvConsecutiveDays} days)</>}
            </span>
            {hrvPctChange != null && (
              <span>
                vs 14d avg: <span className={`font-semibold ${hrvPctChange < -10 ? 'text-accent-red' : hrvPctChange < 0 ? 'text-accent-yellow' : 'text-accent-green'}`}>
                  {hrvPctChange > 0 ? '+' : ''}{hrvPctChange}%
                </span>
              </span>
            )}
            {hrv14DayAvg != null && (
              <span>{Math.round(hrv14DayAvg)}ms 14d avg</span>
            )}
          </div>
        )}
        {hrvChartData.length > 0 ? (
          <>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={hrvChartData}>
              <defs>
                <linearGradient id="hrvGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#34d399" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#34d399" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={axisTickStyle} axisLine={axisLineStyle} tickLine={false} />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} domain={['dataMin - 10', 'dataMax + 10']} />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Area type="monotone" dataKey="baselineHigh" stroke="none" fill="url(#baselineGrad)" fillOpacity={1} stackId="baseline" connectNulls />
              <Area type="monotone" dataKey="baselineLow" stroke="none" fill="#0a0a0f" fillOpacity={1} stackId="baseline" connectNulls />
              <Area type="monotone" dataKey="value" stroke="#60a5fa" fill="url(#hrvGrad)" strokeWidth={2} dot={{ fill: '#60a5fa', r: 3, strokeWidth: 0 }} connectNulls />
            </AreaChart>
          </ResponsiveContainer>
          <div className="text-[11px] text-text-dim mt-1.5">Green band = balanced baseline range</div>
          </>
        ) : (
          <div className="text-text-muted text-[14px]">No HRV data available</div>
        )}
      </Card>

      {/* Sleep Trend (14d) */}
      <Card title="Sleep Trend (14d)" subtitle="Stage breakdown is approximate (±45 min per stage). Total duration is the reliable number.">
        {sleepTrendLabel && (
          <div className="text-[13px] font-semibold text-text-secondary mb-1">{sleepTrendLabel}</div>
        )}
        {sleepWeeklyAvg != null && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3 text-[13px] text-text-secondary">
            <span>
              7d avg: <span className={`font-semibold ${sleepWeeklyAvg >= 7 ? 'text-accent-green' : sleepWeeklyAvg >= 6 ? 'text-accent-yellow' : 'text-accent-red'}`}>
                {sleepWeeklyAvg.toFixed(1)}h
              </span>
              <span className="text-text-dim"> / 7-8h target</span>
            </span>
            {nightsBelow6h > 0 && (
              <span className="text-accent-red font-semibold">
                {nightsBelow6h} night{nightsBelow6h > 1 ? 's' : ''} &lt;6h this week
              </span>
            )}
            {nightsBelow6h === 0 && (
              <span className="text-accent-green font-medium">No short nights this week</span>
            )}
          </div>
        )}
        {sleepChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={sleepChartData}>
              <XAxis dataKey="date" tick={axisTickStyle} axisLine={axisLineStyle} tickLine={false} />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={30} unit="h" />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Bar dataKey="deep" stackId="sleep" fill="#1e3a5f" radius={[0, 0, 0, 0]} name="Deep" />
              <Bar dataKey="rem" stackId="sleep" fill="#7c3aed" radius={[0, 0, 0, 0]} name="REM" />
              <Bar dataKey="light" stackId="sleep" fill="#4a4a5c" radius={[2, 2, 0, 0]} name="Light" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-[14px]">No sleep data available</div>
        )}
      </Card>

      {/* Resting HR Trend (14d) */}
      <Card title="Resting HR Trend (14d)">
        {hrTrendLabel && (
          <div className="text-[13px] font-semibold text-text-secondary mb-1">{hrTrendLabel}</div>
        )}
        {restingHRData.length > 0 ? (
          <>
            {risingHR && hrRiseDelta != null && (
              <div className="mb-3 space-y-1">
                <div className="flex items-center gap-2 text-accent-yellow text-[13px] font-semibold">
                  <AlertTriangle size={15} />
                  <span>Rising trend: +{hrRiseDelta.toFixed(1)}bpm (3d avg vs prior 7d avg)</span>
                </div>
                <div className="text-[13px] text-accent-yellow/80 ml-[23px]">
                  → Prioritize sleep and consider reducing volume
                </div>
              </div>
            )}
            {!risingHR && recentHRAvg != null && previousHRAvg != null && (
              <div className="text-[13px] text-text-muted mb-2">
                3d avg {Math.round(recentHRAvg)}bpm &middot; 7d avg {Math.round(previousHRAvg)}bpm
              </div>
            )}
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={restingHRData}>
                <XAxis dataKey="date" tick={axisTickStyle} axisLine={axisLineStyle} tickLine={false} />
                <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={30} domain={['dataMin - 3', 'dataMax + 3']} unit=" bpm" />
                <Tooltip contentStyle={darkTooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={risingHR ? '#fbbf24' : '#fb7185'}
                  strokeWidth={2}
                  dot={{ fill: risingHR ? '#fbbf24' : '#fb7185', r: 3, strokeWidth: 0 }}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </>
        ) : (
          <div className="text-text-muted text-[14px]">No resting HR data available</div>
        )}
      </Card>
    </div>
  )
}
