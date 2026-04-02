import { useMemo, useState, useCallback } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useHRV, useBodyComposition, useActivities, useDailyMetrics } from '../hooks/useSupabase'
import { format, startOfWeek, subDays } from 'date-fns'
import { RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip, Legend,
} from 'recharts'

function CollapsibleSection({ title, defaultOpen = false, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between py-2 text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold"
      >
        {title}
        <ChevronDown size={14} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="space-y-3">{children}</div>}
    </div>
  )
}

function InfoPanel({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-1 text-[12px] text-text-dim hover:text-text-muted transition-colors">
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {title}
      </button>
      {open && (
        <div className="mt-2 text-[12px] text-text-muted leading-relaxed bg-bg-primary/50 rounded-xl px-3 py-2.5 space-y-2">
          {children}
        </div>
      )}
    </div>
  )
}

const darkTooltipStyle = {
  backgroundColor: '#16161e',
  border: '1px solid #262636',
  borderRadius: '12px',
  color: '#f0f0f5',
  fontSize: '12px',
}

const axisTickStyle = { fill: '#646478', fontSize: 11 }
const axisLineStyle = { stroke: '#262636' }

function classifyActivity(type: string | null | undefined): 'ski' | 'hike' | 'fly' | null {
  if (!type) return null
  const t = type.toLowerCase()
  if (t.includes('ski') || t.includes('snowboard') || t.includes('backcountry')) return 'ski'
  if (t.includes('hik') || t.includes('trail') || t.includes('mountaineering')) return 'hike'
  if (t.includes('hang_gliding') || t.includes('paraglid')) return 'fly'
  return null
}

const elevationColors: Record<string, string> = {
  ski: '#38bdf8',
  hike: '#22c55e',
}

export default function TrendsView() {
  const hrv = useHRV(90)
  const bodyComp = useBodyComposition(90)
  const activities = useActivities(90)
  const metrics = useDailyMetrics(90)

  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)

  const handleEgymSync = useCallback(async () => {
    setSyncing(true)
    setSyncResult(null)
    try {
      const resp = await fetch('/api/egym-sync', { method: 'POST' })
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
      .filter((d: any) => d.weight_kg != null)
      .map((d: any) => ({
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

  const fatChartData = (bodyComp.data ?? [])
    .slice()
    .reverse()
    .filter((d: any) => d.body_fat_pct != null)
    .map((d: any) => ({
      date: format(new Date(d.date), 'MMM d'),
      bodyFat: +d.body_fat_pct.toFixed(1),
    }))

  const latestComp = (bodyComp.data ?? []).find((d: any) => d.body_fat_pct != null) as any
  const bioAges = latestComp?.raw_json?.bio_age ?? null
  const rawMetrics = latestComp?.raw_json?.body_metrics ?? []

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

  const elevationTypes = ['ski', 'hike']
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
  const vo2Deduped = vo2Data.filter(
    (d: any, i: number, arr: any[]) =>
      i === 0 || i === arr.length - 1 || d.value !== arr[i - 1].value
  )

  return (
    <div className="space-y-3 pb-8">
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
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} />
              <Tooltip contentStyle={darkTooltipStyle} />
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
              <Tooltip contentStyle={darkTooltipStyle} />
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
              <Tooltip contentStyle={darkTooltipStyle} />
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
            <div className="border-t border-border pt-3">
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
                  <div className={`data-value-md mt-0.5 ${b.value <= b.threshold ? 'text-accent-green' : 'text-accent-yellow'}`}>
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
            <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border">
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Lean Mass</div>
                <div className="data-value-sm text-text-primary mt-0.5">
                  {latestComp.lean_body_mass_grams ? (latestComp.lean_body_mass_grams / 1000).toFixed(1) : '--'} <span className="text-[11px] text-text-muted font-normal">kg</span>
                </div>
              </div>
              <div>
                <div className="text-[11px] text-text-muted font-semibold">Body Water</div>
                <div className={`data-value-sm mt-0.5 ${latestComp.body_water_pct >= 55 ? 'text-accent-blue' : 'text-accent-yellow'}`}>
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
              <Tooltip contentStyle={darkTooltipStyle} />
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
      <Card title="VO2max Trend (running-derived)" subtitle="Estimates from hiking and touring are not validated and are excluded. Values have ±5 ml/kg/min uncertainty.">
        {vo2Deduped.length > 1 ? (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={vo2Deduped}>
              <XAxis dataKey="date" tick={{ ...axisTickStyle, fontSize: 10 }} axisLine={axisLineStyle} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={axisTickStyle} axisLine={false} tickLine={false} width={35} domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Line type="monotone" dataKey="value" stroke="#34d399" strokeWidth={2} dot={{ fill: '#34d399', r: 3 }} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-text-muted text-[14px]">
            {vo2Deduped.length === 1
              ? `Current VO2max: ${vo2Deduped[0].value}`
              : 'No VO2max data available'}
          </div>
        )}
      </Card>

      <Card title="e1RM Progression" subtitle="Normal variation: ±3-5% per session. Plateau = flat or declining for ≥4 weeks.">
        <div className="flex items-center justify-center h-32 text-text-muted text-[14px]">
          e1RM tracking will populate after gym sessions are completed.
        </div>
      </Card>
      </CollapsibleSection>
    </div>
  )
}
