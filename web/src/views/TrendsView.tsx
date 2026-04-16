import { useMemo, useState, useCallback } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { CollapsibleSection } from '../components/CollapsibleSection'
import { InfoPanel } from '../components/InfoPanel'
import { SectionErrorBoundary } from '../components/SectionErrorBoundary'
import { glassTooltipStyle, axisTickStyle, axisLineStyle } from '../lib/chartConfig'
import { useHRV, useBodyComposition, useActivities, useDailyMetrics, useSleep, usePerformanceScores } from '../hooks/useSupabase'
import type { HRVRow, BodyComposition, DailyMetrics, SleepRow, PerformanceScore } from '../lib/types'
import { format, startOfWeek, subDays } from 'date-fns'
import { formatActivityType } from '../lib/format'
import { RefreshCw } from 'lucide-react'
import { correlateLagged, loadImpact, describeR, type DayPoint } from '../lib/correlations'
import { MOUNTAIN_ACTIVITY_TYPES, SELF_POWERED_MOUNTAIN_TYPES, CYCLING_ACTIVITY_TYPES } from '../lib/activityTypes'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip, Legend,
} from 'recharts'

function classifyActivity(type: string | null | undefined): 'ski' | 'hike' | 'fly' | 'bike' | null {
  if (!type) return null
  const t = type.toLowerCase()
  if (t.includes('ski') || t.includes('snowboard') || t.includes('backcountry')) return 'ski'
  if (t.includes('hik') || t.includes('trail') || t.includes('mountaineering')) return 'hike'
  if (t.includes('hang_gliding') || t.includes('paraglid')) return 'fly'
  if (CYCLING_ACTIVITY_TYPES.has(type)) return 'bike'
  return null
}

const elevationColors: Record<string, string> = {
  ski: '#38bdf8',
  hike: '#22c55e',
  bike: '#f59e0b',
}

export default function TrendsView() {
  const hrv = useHRV(90)
  const bodyComp = useBodyComposition(90)
  const activities = useActivities(90)
  const metrics = useDailyMetrics(90)
  const sleep = useSleep(90)
  const perfScores = usePerformanceScores(90)

  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)

  const handleEgymSync = useCallback(async () => {
    setSyncing(true)
    setSyncResult(null)
    try {
      const resp = await fetch('/api/egym-sync', { method: 'POST' })
      if (!resp.ok) {
        setSyncResult(`Sync failed (HTTP ${resp.status})`)
        return
      }
      const data = await resp.json()
      if (data.ok) {
        setSyncResult('Sync queued — data arrives in ~5 min')
        setTimeout(() => setSyncResult(null), 5000)
      } else {
        setSyncResult(data.error || data.message || 'Sync failed')
      }
    } catch (e) {
      setSyncResult(`Error: ${e}`)
    } finally {
      setSyncing(false)
    }
  }, [])

  const massChartData = useMemo(() => {
    const raw = (bodyComp.data ?? [])
      .slice()
      .reverse()
      .filter((d: BodyComposition) => d.weight_kg != null)
      .map((d: BodyComposition) => ({
        date: format(new Date(d.date), 'MMM d'),
        weight: d.weight_kg ? +d.weight_kg.toFixed(1) : null,
        muscleMass: d.muscle_mass_grams ? +(d.muscle_mass_grams / 1000).toFixed(1) : null,
      }))
    const alpha = 0.25
    let ewma: number | null = null
    return raw.map(d => {
      if (d.weight != null) {
        ewma = ewma == null ? d.weight : +(alpha * d.weight + (1 - alpha) * ewma).toFixed(1)
      }
      return { ...d, weightEWMA: ewma }
    })
  }, [bodyComp.data])

  const loading = hrv.loading || bodyComp.loading || activities.loading || metrics.loading || sleep.loading || perfScores.loading
  const error = hrv.error || bodyComp.error || activities.error || metrics.error || sleep.error || perfScores.error

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red p-4">{error}</div>

  // --- HRV 90-day ---
  const hrvChartData = (hrv.data ?? [])
    .slice()
    .reverse()
    .map((d: HRVRow) => ({
      date: format(new Date(d.date), 'MMM d'),
      value: d.last_night_avg ? Math.round(d.last_night_avg) : null,
      baselineLow: d.baseline_balanced_low ? Math.round(d.baseline_balanced_low) : null,
      baselineHigh: d.baseline_balanced_upper ? Math.round(d.baseline_balanced_upper) : null,
    }))

  const fatChartData = (bodyComp.data ?? [])
    .slice()
    .reverse()
    .filter((d: BodyComposition) => d.body_fat_pct != null)
    .map((d: BodyComposition) => ({
      date: format(new Date(d.date), 'MMM d'),
      bodyFat: d.body_fat_pct != null ? +d.body_fat_pct.toFixed(1) : 0,
    }))

  const latestComp = (bodyComp.data ?? []).find((d: BodyComposition) => d.body_fat_pct != null) ?? null
  const rawJson = latestComp?.raw_json as Record<string, unknown> | null
  const bioAges = (rawJson?.bio_age as { totalBioAge?: number; muscleBioAge?: number; metabolicAge?: number; cardioAge?: number } | undefined) ?? null
  const rawMetrics = (rawJson?.body_metrics as Array<{ type: string; value: number | null }>) ?? []

  const rawByType: Record<string, number> = {}
  for (const m of rawMetrics) {
    if (m.value != null) rawByType[m.type] = m.value
  }
  const phaseAngle = rawByType['BODY_PHASE_ANGLE']
  const phaseAngleRange = { low: rawByType['BODY_PHASE_ANGLE_LOW'], top: rawByType['BODY_PHASE_ANGLE_TOP'] }
  const ecwTbw = rawByType['ECW_TBW_PERCENT']
  const segmental = {
    leftArm: rawByType['SEGMENTAL_MUSCLE_LEFT_ARM_KG'],
    rightArm: rawByType['SEGMENTAL_MUSCLE_RIGHT_ARM_KG'],
    leftLeg: rawByType['SEGMENTAL_MUSCLE_LEFT_LEG_KG'],
    rightLeg: rawByType['SEGMENTAL_MUSCLE_RIGHT_LEG_KG'],
    trunk: rawByType['SEGMENTAL_MUSCLE_TRUNK_KG'],
  }
  const hasSegmental = segmental.leftArm != null

  // --- Weekly Elevation (12 weeks) ---
  const twelveWeeksAgo = subDays(new Date(), 84)
  const weeklyElevation: Record<string, { total: number; byType: Record<string, number> }> = {}

  const weekDates: Record<string, Date> = {}
  for (const a of activities.data ?? []) {
    const actDate = new Date(a.date)
    if (actDate < twelveWeeksAgo || !a.elevation_gain) continue
    const actType = classifyActivity(a.activity_type)
    if (!actType || actType === 'fly') continue
    const ws = startOfWeek(actDate, { weekStartsOn: 1 })
    const weekKey = format(ws, 'MMM d')
    if (!weeklyElevation[weekKey]) {
      weeklyElevation[weekKey] = { total: 0, byType: {} }
      weekDates[weekKey] = ws
    }
    weeklyElevation[weekKey].total += a.elevation_gain
    weeklyElevation[weekKey].byType[actType] =
      (weeklyElevation[weekKey].byType[actType] || 0) + a.elevation_gain
  }

  const elevationTypes = ['ski', 'hike', 'bike']
  const elevationChartData = Object.entries(weeklyElevation)
    .sort(([a], [b]) => (weekDates[a]?.getTime() ?? 0) - (weekDates[b]?.getTime() ?? 0))
    .map(([week, data]) => ({
      week,
      total: Math.round(data.total),
      ...Object.fromEntries(
        elevationTypes.map((t) => [t, Math.round(data.byType[t] || 0)])
      ),
    }))

  // --- Hill Score + Endurance Score trends ---
  const fitnessScoreData = (perfScores.data ?? [])
    .filter((d: PerformanceScore) => d.hill_score != null || d.endurance_score != null)
    .map((d: PerformanceScore) => ({
      date: format(new Date(d.date), 'MMM d'),
      hill: d.hill_score,
      endurance: d.endurance_score,
    }))

  // Deduplicate consecutive identical values to reduce chart noise
  const fitnessScoreDeduped = fitnessScoreData.filter(
    (d, i, arr) =>
      i === 0 || i === arr.length - 1 ||
      d.hill !== arr[i - 1].hill || d.endurance !== arr[i - 1].endurance
  )

  const latestScores = (() => {
    const scores = perfScores.data ?? []
    const withHill = scores.filter((d: PerformanceScore) => d.hill_score != null)
    const withEnd = scores.filter((d: PerformanceScore) => d.endurance_score != null)
    const hillVal = withHill.length > 0 ? withHill[withHill.length - 1].hill_score : null
    const endVal = withEnd.length > 0 ? withEnd[withEnd.length - 1].endurance_score : null
    const ageVal = scores.length > 0 ? scores[scores.length - 1].fitness_age : null
    return {
      hill: typeof hillVal === 'number' ? hillVal : null,
      endurance: typeof endVal === 'number' ? endVal : null,
      fitnessAge: typeof ageVal === 'number' ? ageVal : null,
    }
  })()

  // --- VAM trend (vertical ascent rate from mountain activities) ---
  const vamData = (activities.data ?? [])
    .filter((a) =>
      MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type) &&
      a.elevation_gain != null && a.elevation_gain > 200 &&
      a.duration_seconds != null && a.duration_seconds > 1800
    )
    .slice()
    .reverse()
    .map((a) => ({
      date: format(new Date(a.date), 'MMM d'),
      vam: Math.round(((a.elevation_gain ?? 0) / (a.duration_seconds ?? 1)) * 3600),
      name: String(a.activity_name ?? a.activity_type),
    }))

  // --- Mountain Trends (deep analysis) ---
  const mountainActivities = useMemo(() =>
    (activities.data ?? [])
      .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type) && a.elevation_gain != null && a.elevation_gain > 0)
      .slice()
      .reverse()
  , [activities.data])

  const mountainTrends = useMemo(() => {
    if (mountainActivities.length < 2) return null

    const withVam = mountainActivities.filter((a) => a.duration_seconds != null && a.duration_seconds > 0)
    const vams = withVam.map((a) => Math.round(((a.elevation_gain ?? 0) / (a.duration_seconds ?? 1)) * 3600))
    const hrs = mountainActivities.map((a) => a.avg_hr).filter((v): v is number => v != null)
    const elevations = mountainActivities.map((a) => a.elevation_gain).filter((v): v is number => v != null)
    const durations = mountainActivities.map((a) => (a.duration_seconds ?? 0) / 3600).filter((v) => v > 0)
    const tes = mountainActivities.map((a) => a.training_effect_aerobic).filter((v): v is number => v != null)

    // Split into halves for trend direction
    const half = Math.floor(withVam.length / 2)
    const recentVams = vams.slice(half)
    const olderVams = vams.slice(0, half)
    const recentHRs = hrs.slice(Math.floor(hrs.length / 2))
    const olderHRs = hrs.slice(0, Math.floor(hrs.length / 2))

    const avg = (arr: number[]) => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : null
    const max = (arr: number[]) => arr.length > 0 ? Math.max(...arr) : null

    const avgVam = avg(vams)
    const avgVamRecent = avg(recentVams)
    const avgVamOlder = avg(olderVams)
    const vamTrendPct = avgVamOlder && avgVamRecent ? Math.round(((avgVamRecent - avgVamOlder) / avgVamOlder) * 100) : null

    const avgHR = avg(hrs)
    const avgHRRecent = avg(recentHRs)
    const avgHROlder = avg(olderHRs)
    const hrTrendPct = avgHROlder && avgHRRecent ? Math.round(((avgHRRecent - avgHROlder) / avgHROlder) * 100) : null

    // Efficiency: VAM per HR beat (higher = fitter)
    const efficiencies = withVam
      .filter((a) => a.avg_hr != null && a.avg_hr > 0)
      .map((a) => Math.round(((a.elevation_gain ?? 0) / (a.duration_seconds ?? 1)) * 3600) / a.avg_hr!)
    const effRecent = avg(efficiencies.slice(Math.floor(efficiencies.length / 2)))
    const effOlder = avg(efficiencies.slice(0, Math.floor(efficiencies.length / 2)))
    const effTrendPct = effOlder && effRecent ? Math.round(((effRecent - effOlder) / effOlder) * 100) : null

    // Per-activity chart data with VAM + HR + efficiency
    const chartData = withVam
      .filter((a) => a.avg_hr != null)
      .map((a) => {
        const v = Math.round(((a.elevation_gain ?? 0) / (a.duration_seconds ?? 1)) * 3600)
        return {
          date: format(new Date(a.date), 'MMM d'),
          vam: v,
          hr: a.avg_hr!,
          efficiency: a.avg_hr! > 0 ? +(v / a.avg_hr!).toFixed(2) : null,
          name: a.activity_name ?? formatActivityType(a.activity_type),
          elev: Math.round(a.elevation_gain ?? 0),
        }
      })

    return {
      count: mountainActivities.length,
      totalElevation: Math.round(elevations.reduce((a, b) => a + b, 0)),
      totalHours: Math.round(durations.reduce((a, b) => a + b, 0) * 10) / 10,
      avgVam: avgVam != null ? Math.round(avgVam) : null,
      bestVam: max(vams),
      vamTrendPct,
      avgHR: avgHR != null ? Math.round(avgHR) : null,
      hrTrendPct,
      avgTE: avg(tes) != null ? Math.round(avg(tes)! * 10) / 10 : null,
      avgElev: avg(elevations) != null ? Math.round(avg(elevations)!) : null,
      avgDuration: avg(durations) != null ? Math.round(avg(durations)! * 10) / 10 : null,
      effTrendPct,
      chartData,
    }
  }, [mountainActivities])

  // --- Cycling performance ---
  const cyclingData = (activities.data ?? [])
    .filter((a) =>
      CYCLING_ACTIVITY_TYPES.has(a.activity_type) &&
      (a.duration_seconds ?? 0) > 300 &&
      (a.distance_meters ?? 0) > 1000
    )
    .slice()
    .reverse()
    .map((a) => {
      const speedKmh = (a.avg_speed ?? 0) * 3.6
      const elevGain = a.elevation_gain ?? 0
      const durH = (a.duration_seconds ?? 1) / 3600
      const vam = elevGain > 0 ? Math.round(elevGain / durH) : null
      const hrEff = a.avg_hr && a.avg_hr > 0 ? +(speedKmh / a.avg_hr).toFixed(3) : null
      return {
        date: format(new Date(a.date), 'MMM d'),
        speed: +speedKmh.toFixed(1),
        vam,
        hrEff,
        name: String(a.activity_name ?? a.activity_type),
        distKm: +((a.distance_meters ?? 0) / 1000).toFixed(1),
        elevGain: Math.round(elevGain),
      }
    })

  // --- Insights / correlations ---
  const hrvSeries: DayPoint[] = (hrv.data ?? []).map((d: HRVRow) => ({ date: d.date, value: d.last_night_avg }))
  const sleepSeries: DayPoint[] = (sleep.data ?? []).map((d: SleepRow) => ({
    date: d.date,
    value: d.total_sleep_seconds != null ? d.total_sleep_seconds / 3600 : null,
  }))
  const readinessSeries: DayPoint[] = (metrics.data ?? []).map((d: DailyMetrics) => ({
    date: d.date,
    value: d.training_readiness_score != null ? Number(d.training_readiness_score) : null,
  }))

  const mountainLoadByDate = new Map<string, number>()
  const strengthLoadByDate = new Map<string, number>()
  for (const a of activities.data ?? []) {
    if (MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type) && a.elevation_gain) {
      mountainLoadByDate.set(a.date, (mountainLoadByDate.get(a.date) ?? 0) + a.elevation_gain)
    }
    if (a.activity_type === 'strength_training' && a.duration_seconds) {
      strengthLoadByDate.set(a.date, (strengthLoadByDate.get(a.date) ?? 0) + a.duration_seconds / 60)
    }
  }

  const mountainImpact = loadImpact(mountainLoadByDate, hrvSeries, 600, 1)
  const sleepReadiness = correlateLagged(sleepSeries, readinessSeries, 0)
  const strengthHrv = loadImpact(strengthLoadByDate, hrvSeries, 45, 1)

  type Insight = { headline: string; detail: string; tone: 'green' | 'amber' | 'red' | 'neutral' }
  const insights: Insight[] = []

  if (mountainImpact && Math.abs(mountainImpact.delta) >= 1) {
    const drop = mountainImpact.delta < 0
    insights.push({
      headline: `Big mountain days ${drop ? 'lower' : 'raise'} next-day HRV by ${Math.abs(mountainImpact.delta).toFixed(0)} ms`,
      detail: `After days with ≥600 m elevation gain (n=${mountainImpact.nHigh}) vs other days (n=${mountainImpact.nBase}). ${drop ? 'Worth pairing with an easy day after big tours.' : 'Your system tolerates these well.'}`,
      tone: drop ? 'amber' : 'green',
    })
  }

  if (sleepReadiness && sleepReadiness.n >= 7) {
    const desc = describeR(sleepReadiness.r)
    if (desc.strength !== 'no clear') {
      insights.push({
        headline: `Sleep duration shows a ${desc.strength} ${desc.direction} link to training readiness`,
        detail: `Pearson r = ${sleepReadiness.r.toFixed(2)} across ${sleepReadiness.n} matched days. ${desc.direction === 'positive' ? 'More sleep tends to lift next-day readiness.' : 'Readiness looks driven by something other than sleep length right now.'}`,
        tone: desc.direction === 'positive' ? 'green' : 'neutral',
      })
    }
  }

  if (strengthHrv && Math.abs(strengthHrv.delta) >= 1) {
    const drop = strengthHrv.delta < 0
    insights.push({
      headline: `HRV ${drop ? 'dips' : 'climbs'} ${Math.abs(strengthHrv.delta).toFixed(0)} ms the day after strength sessions`,
      detail: `Comparing days after ≥45-min strength sessions (n=${strengthHrv.nHigh}) vs others (n=${strengthHrv.nBase}). ${drop ? 'Recovery cost is real — keep heavy sessions away from big mountain days.' : 'You bounce back fast.'}`,
      tone: drop ? 'amber' : 'green',
    })
  }

  const toneClasses: Record<Insight['tone'], string> = {
    green: 'border-accent-green/30 bg-accent-green/5',
    amber: 'border-accent-yellow/30 bg-accent-yellow/5',
    red: 'border-accent-red/30 bg-accent-red/5',
    neutral: 'border-border bg-bg-primary/40',
  }

  return (
    <div className="space-y-3 pb-8">
      {/* Insights */}
      <Card title="Insights">
        {insights.length === 0 ? (
          <div className="text-text-muted text-[13px]">
            Not enough overlapping data yet — insights appear once we have ~2 weeks of training plus recovery data.
          </div>
        ) : (
          <div className="space-y-2">
            {insights.map((ins, i) => (
              <div key={i} className={`rounded-xl border px-3 py-2 ${toneClasses[ins.tone]}`}>
                <div className="text-[13px] text-text-primary font-semibold">{ins.headline}</div>
                <div className="text-[12px] text-text-muted mt-0.5 leading-relaxed">{ins.detail}</div>
              </div>
            ))}
          </div>
        )}
        <div className="text-[10px] text-text-dim mt-2">
          Observational only — correlation, not causation. Use as a hypothesis to discuss with your coach.
        </div>
      </Card>

      {/* Recovery & Readiness */}
      <CollapsibleSection title="Recovery & Readiness" defaultOpen>
      <Card title="HRV (90 days)">
        {hrvChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={hrvChartData}>
              <defs>
                <linearGradient id="hrvGrad90" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="baselineGrad90" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#34d399" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#34d399" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} domain={['dataMin - 10', 'dataMax + 10']} />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Area type="monotone" dataKey="baselineHigh" stroke="none" fill="url(#baselineGrad90)" fillOpacity={1} stackId="baseline" connectNulls />
              <Area type="monotone" dataKey="baselineLow" stroke="none" fill="#0a0a0f" fillOpacity={1} stackId="baseline" connectNulls />
              <Area type="monotone" dataKey="value" stroke="#60a5fa" fill="url(#hrvGrad90)" strokeWidth={2} dot={false} connectNulls />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-[14px]">No HRV data available</div>
        )}
      </Card>
      </CollapsibleSection>

      {/* Body Composition */}
      <CollapsibleSection title="Body Composition" defaultOpen>
      <Card>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold">Body Composition</span>
          <button
            onClick={handleEgymSync}
            disabled={syncing}
            className="flex items-center gap-1.5 text-[12px] text-accent-green hover:text-accent-green/80 disabled:opacity-50 transition-colors font-medium"
          >
            <RefreshCw size={12} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing...' : 'Sync eGym'}
          </button>
        </div>
        {syncResult && (
          <div className={`text-[12px] mb-2 px-3 py-1.5 rounded-xl ${syncResult.startsWith('Synced') ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'}`}>
            {syncResult}
          </div>
        )}

        {latestComp ? (
          <>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Weight</div>
                <div className="data-value-md text-text-primary mt-0.5">
                  {latestComp.weight_kg?.toFixed(1) ?? '--'}
                  <span className="text-[11px] text-text-muted ml-0.5 font-normal">kg</span>
                </div>
              </div>
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Body Fat <span className="text-text-dim font-normal">(±5%)</span></div>
                <div className="data-value-md text-accent-purple mt-0.5">
                  ~{latestComp.body_fat_pct?.toFixed(0) ?? '--'}
                  <span className="text-[11px] text-text-muted ml-0.5 font-normal">%</span>
                </div>
              </div>
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Muscle</div>
                <div className="data-value-md text-accent-green mt-0.5">
                  {latestComp.muscle_mass_grams ? (latestComp.muscle_mass_grams / 1000).toFixed(1) : '--'}
                  <span className="text-[11px] text-text-muted ml-0.5 font-normal">kg</span>
                </div>
              </div>
            </div>

            {latestComp.date && (
              <div className="text-[11px] text-text-dim mb-1">
                Last scan: {format(new Date(latestComp.date), 'MMM d, yyyy')}
              </div>
            )}

            <InfoPanel title="What do these mean?">
              <p><strong className="text-text-secondary">Body Fat %</strong> — Percentage of total weight that is fat. 12-18% is athletic for men. Lower = more defined, but below 10% is hard to sustain.</p>
              <p><strong className="text-text-secondary">Skeletal Muscle Mass</strong> — Weight of muscles attached to bones (the ones you train). The primary metric for tracking strength gains. More muscle = higher metabolism + better performance.</p>
              <p><strong className="text-text-secondary">Recomp goal:</strong> Muscle up + fat down simultaneously. Track both — weight alone is misleading since muscle is denser than fat.</p>
            </InfoPanel>
          </>
        ) : (
          <div className="text-text-muted text-[14px]">No body composition data available</div>
        )}
      </Card>

      {/* Weight & Muscle Mass trend */}
      {massChartData.length > 1 && (
        <Card title="Weight & Muscle (90d)" subtitle="Bold line = 7-day smoothed trend. Dots = daily readings (±1-3 kg normal noise).">
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={massChartData}>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis yAxisId="w" tick={axisTickStyle} axisLine={false} tickLine={false} width={40} unit=" kg" domain={['dataMin - 1', 'dataMax + 1']} />
              <YAxis yAxisId="m" orientation="right" tick={axisTickStyle} axisLine={false} tickLine={false} width={40} unit=" kg" domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Legend wrapperStyle={{ color: '#a0a0b8', fontSize: 11 }} />
              <Line yAxisId="w" type="monotone" dataKey="weight" stroke="none" dot={{ fill: '#60a5fa', r: 2, opacity: 0.3 }} name="Daily weight" connectNulls legendType="none" />
              <Line yAxisId="w" type="monotone" dataKey="weightEWMA" stroke="#60a5fa" strokeWidth={2.5} dot={false} name="Weight (trend)" connectNulls />
              <Line yAxisId="m" type="monotone" dataKey="muscleMass" stroke="#34d399" strokeWidth={2} dot={{ fill: '#34d399', r: 3 }} name="Skeletal Muscle" connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Body Fat % trend */}
      {fatChartData.length > 1 && (
        <Card title="Body Fat % (90d)" subtitle="BIA body fat has ±5-7% error vs. DEXA. Track direction, not absolute value.">
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={fatChartData}>
              <defs>
                <linearGradient id="bfGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a78bfa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a78bfa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} unit="%" domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Area type="monotone" dataKey="bodyFat" stroke="#a78bfa" fill="url(#bfGrad)" strokeWidth={2} dot={{ fill: '#a78bfa', r: 3 }} name="Body Fat %" connectNulls />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}
      </CollapsibleSection>

      {/* Body Scan Detail */}
      <CollapsibleSection title="Body Scan Detail">
      {(phaseAngle != null || hasSegmental) && (
        <Card title="Muscle Quality & Balance">
          <div className="grid grid-cols-2 gap-4 mb-4">
            {phaseAngle != null && (
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Phase Angle</div>
                <div className="data-value-md text-text-primary mt-0.5">
                  {phaseAngle.toFixed(1)}<span className="text-[11px] text-text-muted ml-0.5 font-normal">°</span>
                </div>
                <div className="text-[11px] text-text-dim mt-0.5">
                  Range: {phaseAngleRange.low?.toFixed(1)}–{phaseAngleRange.top?.toFixed(1)}°
                  {phaseAngle > (phaseAngleRange.top ?? 6) && (
                    <span className="text-accent-green ml-1 font-medium">above avg</span>
                  )}
                </div>
              </div>
            )}
            {ecwTbw != null && (
              <div>
                <div className="text-[11px] text-text-muted font-semibold">ECW/TBW Ratio</div>
                <div className={`data-value-md mt-0.5 ${ecwTbw <= 40 ? 'text-accent-green' : 'text-accent-yellow'}`}>
                  {ecwTbw.toFixed(1)}<span className="text-[11px] text-text-muted ml-0.5 font-normal">%</span>
                </div>
                <div className="text-[11px] text-text-dim mt-0.5">
                  {ecwTbw <= 39.5 ? 'Healthy' : ecwTbw <= 40 ? 'Normal' : 'Elevated — check recovery'}
                </div>
              </div>
            )}
          </div>

          {hasSegmental && (
            <div className="border-t border-border-subtle pt-3">
              <div className="text-[11px] text-text-muted mb-2.5 uppercase tracking-[0.06em] font-semibold">Segmental Muscle Mass</div>
              <div className="space-y-2.5">
                {/* Arms */}
                <div className="flex items-center gap-2 text-[13px]">
                  <span className="w-14 text-text-muted text-right font-medium">Arms</span>
                  <div className="flex-1 flex items-center gap-1.5">
                    <span className="text-text-secondary w-12 text-right font-mono">{segmental.leftArm?.toFixed(2)}</span>
                    <div className="flex-1 flex h-3 rounded-full overflow-hidden bg-bg-primary">
                      <div className="bg-accent-blue/50 h-full" style={{ width: `${(segmental.leftArm ?? 0) / ((segmental.leftArm ?? 0) + (segmental.rightArm ?? 0)) * 100}%` }} />
                      <div className="bg-accent-blue h-full" style={{ width: `${(segmental.rightArm ?? 0) / ((segmental.leftArm ?? 0) + (segmental.rightArm ?? 0)) * 100}%` }} />
                    </div>
                    <span className="text-text-secondary w-12 font-mono">{segmental.rightArm?.toFixed(2)}</span>
                  </div>
                  {segmental.leftArm != null && segmental.rightArm != null && (
                    <span className={`text-[11px] w-8 font-semibold ${Math.abs(segmental.leftArm - segmental.rightArm) / Math.max(segmental.leftArm, segmental.rightArm) > 0.05 ? 'text-accent-yellow' : 'text-accent-green'}`}>
                      {Math.abs(((segmental.rightArm - segmental.leftArm) / Math.max(segmental.leftArm, segmental.rightArm)) * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                {/* Legs */}
                <div className="flex items-center gap-2 text-[13px]">
                  <span className="w-14 text-text-muted text-right font-medium">Legs</span>
                  <div className="flex-1 flex items-center gap-1.5">
                    <span className="text-text-secondary w-12 text-right font-mono">{segmental.leftLeg?.toFixed(2)}</span>
                    <div className="flex-1 flex h-3 rounded-full overflow-hidden bg-bg-primary">
                      <div className="bg-accent-green/50 h-full" style={{ width: `${(segmental.leftLeg ?? 0) / ((segmental.leftLeg ?? 0) + (segmental.rightLeg ?? 0)) * 100}%` }} />
                      <div className="bg-accent-green h-full" style={{ width: `${(segmental.rightLeg ?? 0) / ((segmental.leftLeg ?? 0) + (segmental.rightLeg ?? 0)) * 100}%` }} />
                    </div>
                    <span className="text-text-secondary w-12 font-mono">{segmental.rightLeg?.toFixed(2)}</span>
                  </div>
                  {segmental.leftLeg != null && segmental.rightLeg != null && (
                    <span className={`text-[11px] w-8 font-semibold ${Math.abs(segmental.leftLeg - segmental.rightLeg) / Math.max(segmental.leftLeg, segmental.rightLeg) > 0.05 ? 'text-accent-yellow' : 'text-accent-green'}`}>
                      {Math.abs(((segmental.rightLeg - segmental.leftLeg) / Math.max(segmental.leftLeg, segmental.rightLeg)) * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                {/* Trunk */}
                {segmental.trunk != null && (
                  <div className="flex items-center gap-2 text-[13px]">
                    <span className="w-14 text-text-muted text-right font-medium">Trunk</span>
                    <span className="text-text-secondary font-semibold">{segmental.trunk.toFixed(1)} kg</span>
                  </div>
                )}
              </div>
              <div className="text-[10px] text-text-dim mt-2">L / R shown · {'>'} 5% asymmetry flagged yellow</div>
            </div>
          )}

          <InfoPanel title="Why these matter">
            <p><strong className="text-text-secondary">Phase Angle</strong> — Measures cell membrane integrity and muscle quality. Higher = healthier cells, better hydration of muscle tissue. Rising phase angle during training confirms quality muscle gain, not just mass. Range 6.5-8.0° is excellent for athletes.</p>
            <p><strong className="text-text-secondary">ECW/TBW Ratio</strong> — Extracellular water vs total body water. Below 40% is healthy. Elevated values can indicate inflammation, overtraining, or poor recovery. Track after hard training blocks.</p>
            <p><strong className="text-text-secondary">L/R Balance</strong> — Asymmetric sports (snowboarding, one-sided carries) can create imbalances. {'>'} 5% difference increases injury risk. Address with unilateral exercises (Bulgarian split squats, single-arm rows).</p>
          </InfoPanel>
        </Card>
      )}

      {/* Bio Age + Secondary Metrics */}
      {(bioAges || latestComp) && (
        <Card title="Health Markers">
          {bioAges && (
            <div className="grid grid-cols-4 gap-3 mb-3">
              {[
                { label: 'Total', value: bioAges.totalBioAge, threshold: 28 },
                { label: 'Muscle', value: bioAges.muscleBioAge, threshold: 28 },
                { label: 'Metabolic', value: bioAges.metabolicAge, threshold: 30 },
                { label: 'Cardio', value: bioAges.cardioAge, threshold: 28 },
              ].filter(b => b.value != null).map(b => (
                <div key={b.label}>
                  <div className="text-[11px] text-text-muted font-semibold">{b.label}</div>
                  <div className={`data-value-md mt-0.5 ${b.value! <= b.threshold ? 'text-accent-green' : 'text-accent-yellow'}`}>
                    {b.value}
                  </div>
                  <div className="text-[10px] text-text-dim">bio age</div>
                </div>
              ))}
            </div>
          )}
          {bioAges?.metabolicAge != null && bioAges.metabolicAge > 28 && (
            <div className="text-[13px] text-accent-yellow bg-accent-yellow/10 px-3 py-2 rounded-xl mb-3 font-medium">
              Metabolic age {bioAges.metabolicAge} is above actual age (28) — recomp will improve this
            </div>
          )}
          <InfoPanel title="About bio ages">
            <p><strong className="text-text-secondary">Bio Age</strong> — eGym's composite score comparing your fitness to population averages. Lower than actual age = better than average for your age group.</p>
            <p><strong className="text-text-secondary">Muscle bio age</strong> — Based on strength testing across all machines. Improve with progressive overload.</p>
            <p><strong className="text-text-secondary">Metabolic bio age</strong> — Driven by body fat %, visceral fat, and BMI. The hardest to improve — responds to sustained caloric deficit + training consistency over months.</p>
            <p><strong className="text-text-secondary">Cardio bio age</strong> — Based on resting HR and cardio performance. Your 44 bpm resting HR is excellent. Mountain sports keep this low.</p>
          </InfoPanel>

          {latestComp && (
            <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border-subtle">
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Lean Mass</div>
                <div className="data-value-sm text-text-primary mt-0.5">
                  {latestComp.lean_body_mass_grams ? (latestComp.lean_body_mass_grams / 1000).toFixed(1) : '--'} <span className="text-[11px] text-text-muted font-normal">kg</span>
                </div>
              </div>
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Body Water</div>
                <div className={`data-value-sm mt-0.5 ${(latestComp.body_water_pct ?? 0) >= 55 ? 'text-accent-blue' : 'text-accent-yellow'}`}>
                  {latestComp.body_water_pct?.toFixed(1) ?? '--'}<span className="text-[11px] text-text-muted font-normal">%</span>
                </div>
              </div>
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Visceral Fat</div>
                <div className={`data-value-sm mt-0.5 ${(latestComp.visceral_fat_rating ?? 0) <= 10 ? 'text-accent-green' : 'text-accent-yellow'}`}>
                  {latestComp.visceral_fat_rating ?? '--'}
                </div>
              </div>
            </div>
          )}
        </Card>
      )}
      </CollapsibleSection>

      {/* Activity Volume */}
      <CollapsibleSection title="Activity Volume">
      <Card title="Weekly Elevation (12 weeks)">
        {elevationChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={elevationChartData}>
              <XAxis dataKey="week" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={45} unit="m" />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Legend wrapperStyle={{ color: '#a0a0b8', fontSize: 12 }} />
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
          <div className="text-text-muted text-[14px]">No elevation data available</div>
        )}
      </Card>
      </CollapsibleSection>

      {/* Performance */}
      <CollapsibleSection title="Performance">
      <SectionErrorBoundary name="Mountain Fitness">
      {/* Hill Score + Endurance Score */}
      <Card title="Mountain Fitness (90d)" subtitle="Hill Score measures climbing ability. Endurance Score captures aerobic base. Both update from all activities.">
        {latestScores.hill != null && (
          <div className="flex gap-4 mb-3">
            <div>
              <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Hill Score</div>
              <div className="text-2xl font-bold text-mountain font-data">{latestScores.hill}</div>
            </div>
            {latestScores.endurance != null && (
              <div>
                <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Endurance</div>
                <div className="text-2xl font-bold text-accent-green font-data">{latestScores.endurance}</div>
              </div>
            )}
            {latestScores.fitnessAge != null && (
              <div>
                <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">Fitness Age</div>
                <div className="text-2xl font-bold text-text-primary font-data">{latestScores.fitnessAge}</div>
              </div>
            )}
          </div>
        )}
        {fitnessScoreDeduped.length > 1 ? (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={fitnessScoreDeduped}>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} domain={['dataMin - 5', 'dataMax + 5']} />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="hill" name="Hill Score" stroke="#38bdf8" strokeWidth={2} dot={false} connectNulls />
              <Line type="monotone" dataKey="endurance" name="Endurance" stroke="#34d399" strokeWidth={2} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-[14px]">
            {latestScores.hill != null
              ? 'Not enough data points for trend chart yet'
              : 'No performance score data — check Garmin sync'}
          </div>
        )}
        <InfoPanel title="What these scores mean">
          <p><strong>Hill Score</strong> reflects your ability to sustain effort on steep terrain. It updates from ski touring, hiking, and any uphill activity. Higher = better climbing fitness.</p>
          <p><strong>Endurance Score</strong> reflects your aerobic base across all activities. Consistent training (gym + mountain) drives it up.</p>
          <p>Both are computed by Garmin from your HR response during activity relative to your personal baseline. Expect slow changes — meaningful shifts happen over 4-8 weeks.</p>
        </InfoPanel>
      </Card>

      {/* VAM trend */}
      <Card title="Vertical Ascent Rate (VAM)" subtitle="Average m/h across entire mountain activities (>200m gain, >30min). Higher at same HR = better fitness.">
        {vamData.length > 1 ? (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={vamData}>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={40} />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Bar dataKey="vam" name="VAM (m/h)" radius={[4, 4, 0, 0]} fill="#38bdf8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-[14px]">
            {vamData.length === 1
              ? `Latest VAM: ${vamData[0].vam} m/h (${vamData[0].name})`
              : 'Not enough mountain activities for VAM trend'}
          </div>
        )}
        <InfoPanel title="How to read VAM">
          <p>VAM (Velocit&agrave; Ascensionale Media) is your average climbing speed in meters per hour. It{"'"}s influenced by terrain, snow conditions, and pack weight — so individual values vary.</p>
          <p>The trend matters more than single values. If you see VAM increasing while HR stays the same (or drops), your mountain fitness is improving.</p>
        </InfoPanel>
      </Card>

      {/* Mountain Trends Analysis */}
      {mountainTrends != null && (
        <Card title="Mountain Performance Analysis" subtitle={`${mountainTrends.count} activities over 90 days — ${mountainTrends.totalElevation.toLocaleString()}m total elevation, ${mountainTrends.totalHours}h`}>
          {/* Key metrics grid */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div>
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Avg VAM</div>
              <div className="text-lg font-bold text-mountain font-data">{mountainTrends.avgVam ?? '\u2014'}<span className="text-[11px] text-text-muted ml-0.5 font-normal">m/h</span></div>
              {mountainTrends.vamTrendPct != null && (
                <div className={`text-[11px] font-semibold ${mountainTrends.vamTrendPct > 0 ? 'text-accent-green' : mountainTrends.vamTrendPct < -5 ? 'text-accent-red' : 'text-text-muted'}`}>
                  {mountainTrends.vamTrendPct > 0 ? '+' : ''}{mountainTrends.vamTrendPct}% trend
                </div>
              )}
            </div>
            <div>
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Avg HR</div>
              <div className="text-lg font-bold text-text-secondary font-data">{mountainTrends.avgHR ?? '\u2014'}<span className="text-[11px] text-text-muted ml-0.5 font-normal">bpm</span></div>
              {mountainTrends.hrTrendPct != null && (
                <div className={`text-[11px] font-semibold ${mountainTrends.hrTrendPct < 0 ? 'text-accent-green' : mountainTrends.hrTrendPct > 3 ? 'text-accent-red' : 'text-text-muted'}`}>
                  {mountainTrends.hrTrendPct > 0 ? '+' : ''}{mountainTrends.hrTrendPct}% trend
                </div>
              )}
            </div>
            <div>
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Efficiency</div>
              <div className="text-lg font-bold text-accent-blue font-data">
                {mountainTrends.effTrendPct != null ? (
                  <span className={mountainTrends.effTrendPct > 0 ? 'text-accent-green' : mountainTrends.effTrendPct < -5 ? 'text-accent-red' : 'text-text-secondary'}>
                    {mountainTrends.effTrendPct > 0 ? '+' : ''}{mountainTrends.effTrendPct}%
                  </span>
                ) : '\u2014'}
              </div>
              <div className="text-[10px] text-text-dim">VAM/HR trend</div>
            </div>
          </div>

          {/* Secondary stats */}
          <div className="grid grid-cols-4 gap-2 mb-4 pt-3 border-t border-border-subtle">
            <div className="text-center">
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Best VAM</div>
              <div className="text-[14px] font-bold text-mountain font-data">{mountainTrends.bestVam ?? '\u2014'}</div>
            </div>
            <div className="text-center">
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Avg Elev</div>
              <div className="text-[14px] font-bold text-text-secondary font-data">{mountainTrends.avgElev ?? '\u2014'}m</div>
            </div>
            <div className="text-center">
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Avg Duration</div>
              <div className="text-[14px] font-bold text-text-secondary font-data">{mountainTrends.avgDuration ?? '\u2014'}h</div>
            </div>
            <div className="text-center">
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Avg TE</div>
              <div className={`text-[14px] font-bold font-data ${(mountainTrends.avgTE ?? 0) >= 3 ? 'text-accent-green' : 'text-text-secondary'}`}>
                {mountainTrends.avgTE ?? '\u2014'}
              </div>
            </div>
          </div>

          {/* VAM + HR dual-axis chart */}
          {mountainTrends.chartData.length > 2 && (
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-2">VAM vs HR per Activity</div>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={mountainTrends.chartData}>
                  <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 9 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
                  <YAxis yAxisId="vam" tick={axisTickStyle} axisLine={false} tickLine={false} width={38} />
                  <YAxis yAxisId="hr" orientation="right" tick={axisTickStyle} axisLine={false} tickLine={false} width={38} />
                  <Tooltip contentStyle={glassTooltipStyle} />
                  <Legend wrapperStyle={{ color: '#a0a0b8', fontSize: 11 }} />
                  <Line yAxisId="vam" type="monotone" dataKey="vam" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3, fill: '#38bdf8' }} name="VAM (m/h)" />
                  <Line yAxisId="hr" type="monotone" dataKey="hr" stroke="#ef4444" strokeWidth={1.5} dot={{ r: 2, fill: '#ef4444' }} name="Avg HR" strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
              <div className="text-[10px] text-text-dim mt-1 text-center">VAM rising while HR drops or stays flat = improving mountain fitness</div>
            </div>
          )}

          {/* Efficiency chart */}
          {mountainTrends.chartData.filter((d) => d.efficiency != null).length > 2 && (
            <div className="mt-3 pt-3 border-t border-border-subtle">
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-2">Cardiac Efficiency (VAM / HR)</div>
              <ResponsiveContainer width="100%" height={120}>
                <AreaChart data={mountainTrends.chartData.filter((d) => d.efficiency != null)}>
                  <defs>
                    <linearGradient id="effGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 9 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
                  <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} />
                  <Tooltip contentStyle={glassTooltipStyle} />
                  <Area type="monotone" dataKey="efficiency" stroke="#34d399" fill="url(#effGrad)" strokeWidth={2} dot={{ fill: '#34d399', r: 3 }} name="Efficiency" connectNulls />
                </AreaChart>
              </ResponsiveContainer>
              <div className="text-[10px] text-text-dim mt-1 text-center">Higher = more elevation per heartbeat — the best single fitness indicator</div>
            </div>
          )}

          <InfoPanel title="Reading these trends">
            <p><strong>VAM trend</strong> compares your recent half of activities against the older half. Positive = you{"'"}re climbing faster.</p>
            <p><strong>HR trend</strong> same comparison for average HR. Negative = your heart works less for similar effort — fitter.</p>
            <p><strong>Efficiency (VAM/HR)</strong> combines both. Rising efficiency is the clearest signal of improving mountain fitness, because it normalises for route difficulty.</p>
            <p>Context matters: cold temps, heavy packs, and technical terrain all lower VAM without meaning you{"'"}re less fit.</p>
          </InfoPanel>
        </Card>
      )}

      {/* Cycling Performance */}
      <Card title="Cycling Performance" subtitle="Avg speed trend across rides (>5 min, >1 km). Increasing speed at same HR = better fitness.">
        {cyclingData.length > 1 ? (
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={cyclingData}>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={40} unit=" km/h" />
              <Tooltip contentStyle={glassTooltipStyle} />
              <Line type="monotone" dataKey="speed" name="Avg speed (km/h)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3, fill: '#f59e0b' }} />
            </LineChart>
          </ResponsiveContainer>
        ) : cyclingData.length === 1 ? (
          <div className="space-y-1 text-[13px]">
            <div className="text-text-primary font-semibold">{cyclingData[0].name}</div>
            <div className="text-text-muted">
              {cyclingData[0].distKm} km · {cyclingData[0].speed} km/h avg
              {cyclingData[0].elevGain > 0 && <span className="ml-2">{cyclingData[0].elevGain}m elev</span>}
              {cyclingData[0].vam != null && <span className="ml-2">VAM {cyclingData[0].vam} m/h</span>}
            </div>
          </div>
        ) : (
          <div className="text-text-muted text-[14px]">No cycling activities yet</div>
        )}
      </Card>

      </SectionErrorBoundary>

      {/* e1RM Progression (kept) */}
      <Card title="e1RM Progression" subtitle="Normal variation: ±3-5% per session. Plateau = flat or declining for ≥4 weeks.">
        <div className="flex items-center justify-center h-32 text-text-muted text-[14px]">
          e1RM tracking will populate after gym sessions are completed.
        </div>
      </Card>
      </CollapsibleSection>
    </div>
  )
}
