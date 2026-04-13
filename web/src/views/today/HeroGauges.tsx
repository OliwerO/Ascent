import { useState } from 'react'
import { RadialGauge } from '../../components/RadialGauge'
import { MetricDetailSheet } from '../../components/MetricDetailSheet'
import type { DailyMetrics, SleepRow, HRVRow } from '../../lib/types'

interface Props {
  hrvVal: number | null
  hrvWeeklyAvg: number | null
  cardState: 'green' | 'amber' | 'red'
  sleepHours: number | null
  /** Rolling 7d vigorous intensity minutes */
  strain7d: number
  /** Rolling 28d average vigorous intensity minutes (per 7d window) */
  strain28d: number
  /** Detail data for sheets */
  hrvData: HRVRow[]
  sleepData: SleepRow[]
  metricsData: DailyMetrics[]
  latestActivity: { training_effect_aerobic?: number | null; training_effect_anaerobic?: number | null; activity_type?: string } | null
}

const stateColors = { green: '#34d399', amber: '#fbbf24', red: '#f87171' }

function sleepColor(h: number | null): string {
  if (h == null) return '#6a6a82'
  if (h >= 7) return '#34d399'
  if (h >= 6) return '#fbbf24'
  return '#f87171'
}

function strainColor(ratio: number | null): string {
  if (ratio == null) return '#6a6a82'
  if (ratio >= 0.8 && ratio <= 1.3) return '#fb923c' // orange — in sweet spot
  if (ratio > 1.3 && ratio <= 1.5) return '#fbbf24' // yellow — pushing
  if (ratio > 1.5) return '#f87171' // red — overreaching
  if (ratio < 0.5) return '#f87171' // red — detraining
  return '#fbbf24' // yellow — low side
}

export function HeroGauges({
  hrvVal, hrvWeeklyAvg, cardState, sleepHours,
  strain7d, strain28d, hrvData, sleepData, metricsData, latestActivity,
}: Props) {
  const [activeSheet, setActiveSheet] = useState<'hrv' | 'sleep' | 'strain' | null>(null)

  const hrvMax = hrvWeeklyAvg != null ? Math.round(hrvWeeklyAvg * 1.3) : 150
  const strainRatio = strain28d > 0 ? strain7d / strain28d : null
  const strainPct = strainRatio != null ? Math.round(strainRatio * 100) : null

  // HRV detail data
  const hrvStatus = hrvData[0]?.status?.toLowerCase() ?? null
  const hrvBaseline = hrvData[0]?.baseline_balanced_low != null && hrvData[0]?.baseline_balanced_upper != null
    ? `${Math.round(hrvData[0].baseline_balanced_low!)}–${Math.round(hrvData[0].baseline_balanced_upper!)} ms`
    : null
  const hrv7dValues = hrvData.slice(0, 7).filter(d => d.last_night_avg != null)
  const hrv7dAvg = hrv7dValues.length > 0
    ? Math.round(hrv7dValues.reduce((s, d) => s + d.last_night_avg!, 0) / hrv7dValues.length)
    : null
  let hrvConsecutive = 0
  const firstStatus = hrvData[0]?.status?.toUpperCase()
  if (firstStatus) {
    for (const d of hrvData) {
      if (d.status?.toUpperCase() === firstStatus) hrvConsecutive++
      else break
    }
  }

  // Sleep detail data
  const lastSleep = sleepData[0]
  const sleep7d = sleepData.slice(0, 7).filter(d => d.total_sleep_seconds != null)
  const sleep7dAvg = sleep7d.length > 0
    ? (sleep7d.reduce((s, d) => s + d.total_sleep_seconds! / 3600, 0) / sleep7d.length).toFixed(1)
    : null
  const nightsBelow6 = sleep7d.filter(d => d.total_sleep_seconds! / 3600 < 6).length

  return (
    <>
      <div className="grid grid-cols-3 gap-2">
        <div className="glass-card flex items-center justify-center py-3">
          <RadialGauge
            value={hrvVal}
            max={hrvMax}
            label="HRV"
            color={stateColors[cardState]}
            size="hero"
            unit="ms"
            onClick={() => setActiveSheet('hrv')}
          />
        </div>
        <div className="glass-card flex items-center justify-center py-3">
          <RadialGauge
            value={sleepHours}
            max={9}
            label="Sleep"
            color={sleepColor(sleepHours)}
            size="hero"
            unit="h"
            onClick={() => setActiveSheet('sleep')}
          />
        </div>
        <div className="glass-card flex items-center justify-center py-3">
          <RadialGauge
            value={strainPct}
            max={150}
            label="Strain"
            color={strainColor(strainRatio)}
            size="hero"
            unit="%"
            onClick={() => setActiveSheet('strain')}
          />
        </div>
      </div>

      {/* HRV Detail Sheet */}
      <MetricDetailSheet title="HRV" open={activeSheet === 'hrv'} onClose={() => setActiveSheet(null)}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Last night</div>
              <div className={`text-2xl font-bold font-data mt-1 ${stateColors[cardState] === '#34d399' ? 'text-accent-green' : stateColors[cardState] === '#fbbf24' ? 'text-accent-yellow' : 'text-accent-red'}`}>
                {hrvVal ?? '—'} <span className="text-[13px] font-normal text-text-muted">ms</span>
              </div>
            </div>
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Status</div>
              <div className="text-lg font-[590] text-text-primary mt-1 capitalize">{hrvStatus ?? '—'}</div>
              {hrvConsecutive > 1 && <div className="text-[12px] text-text-muted">{hrvConsecutive} days</div>}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">7d avg</div>
              <div className="text-lg font-bold font-data text-text-primary mt-1">{hrv7dAvg ?? '—'} ms</div>
            </div>
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Baseline</div>
              <div className="text-lg font-bold font-data text-text-primary mt-1">{hrvBaseline ?? '—'}</div>
            </div>
          </div>
          {/* 7d values */}
          <div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-2">Last 7 nights</div>
            <div className="flex gap-1.5">
              {hrvData.slice(0, 7).reverse().map((d, i) => {
                const v = d.last_night_avg != null ? Math.round(d.last_night_avg) : null
                const isLow = d.status?.toUpperCase() === 'LOW'
                return (
                  <div key={i} className="flex-1 text-center">
                    <div className={`text-[12px] font-bold font-data ${isLow ? 'text-accent-red' : 'text-text-primary'}`}>
                      {v ?? '—'}
                    </div>
                    <div className="text-[9px] text-text-dim">{d.date.slice(5)}</div>
                  </div>
                )
              })}
            </div>
          </div>
          <div className="text-[12px] text-text-muted leading-relaxed bg-bg-inset rounded-xl px-3 py-2.5">
            <strong className="text-text-secondary">What this means:</strong> HRV (Heart Rate Variability) reflects your autonomic nervous system's recovery state. Higher values within your personal baseline indicate good recovery. Sustained drops below baseline suggest accumulated fatigue — consider reducing training intensity.
          </div>
        </div>
      </MetricDetailSheet>

      {/* Sleep Detail Sheet */}
      <MetricDetailSheet title="Sleep" open={activeSheet === 'sleep'} onClose={() => setActiveSheet(null)}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">Last night</div>
              <div className={`text-2xl font-bold font-data mt-1 ${sleepColor(sleepHours).includes('34d399') ? 'text-accent-green' : sleepColor(sleepHours).includes('fbbf24') ? 'text-accent-yellow' : 'text-accent-red'}`}>
                {sleepHours ?? '—'} <span className="text-[13px] font-normal text-text-muted">hours</span>
              </div>
            </div>
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">7d avg</div>
              <div className="text-lg font-bold font-data text-text-primary mt-1">{sleep7dAvg ?? '—'}h</div>
              <div className="text-[12px] text-text-muted">Target 7–8h</div>
            </div>
          </div>
          {/* Stage breakdown */}
          {lastSleep && (
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-2">Stage breakdown</div>
              <div className="space-y-2">
                {[
                  { label: 'Deep', seconds: lastSleep.deep_sleep_seconds, color: 'bg-[#1e3a5f]' },
                  { label: 'REM', seconds: lastSleep.rem_sleep_seconds, color: 'bg-accent-purple' },
                  { label: 'Light', seconds: lastSleep.light_sleep_seconds, color: 'bg-text-dim' },
                ].map(stage => {
                  const hours = stage.seconds ? (stage.seconds / 3600).toFixed(1) : '—'
                  const pct = stage.seconds && lastSleep.total_sleep_seconds
                    ? Math.round((stage.seconds / lastSleep.total_sleep_seconds) * 100) : 0
                  return (
                    <div key={stage.label} className="flex items-center gap-3">
                      <span className="text-[12px] text-text-muted w-10">{stage.label}</span>
                      <div className="flex-1 h-2 bg-bg-inset rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${stage.color}`} style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-[12px] text-text-secondary font-data w-10 text-right">{hours}h</span>
                    </div>
                  )
                })}
              </div>
              <div className="text-[10px] text-text-dim mt-1.5">Stage accuracy is ±45 min — track total duration, not stages</div>
            </div>
          )}
          {nightsBelow6 > 0 && (
            <div className="text-[13px] text-accent-red font-medium">
              {nightsBelow6} night{nightsBelow6 > 1 ? 's' : ''} below 6h this week
            </div>
          )}
          <div className="text-[12px] text-text-muted leading-relaxed bg-bg-inset rounded-xl px-3 py-2.5">
            <strong className="text-text-secondary">What this means:</strong> Sleep is the primary recovery driver. Below 7h consistently degrades HRV, training readiness, and strength gains. Deep sleep is when growth hormone peaks. The 7–8h target assumes training; non-training days need less.
          </div>
        </div>
      </MetricDetailSheet>

      {/* Strain Detail Sheet */}
      <MetricDetailSheet title="Strain" open={activeSheet === 'strain'} onClose={() => setActiveSheet(null)}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">7-day load</div>
              <div className="text-2xl font-bold font-data text-accent-orange mt-1">
                {strain7d} <span className="text-[13px] font-normal text-text-muted">min</span>
              </div>
            </div>
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold">28-day avg</div>
              <div className="text-lg font-bold font-data text-text-primary mt-1">
                {strain28d > 0 ? Math.round(strain28d) : '—'} <span className="text-[13px] font-normal text-text-muted">min/wk</span>
              </div>
            </div>
          </div>
          <div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-1">Load ratio</div>
            <div className={`text-xl font-bold font-data ${strainRatio != null ? (strainRatio >= 0.8 && strainRatio <= 1.3 ? 'text-accent-green' : strainRatio > 1.5 || strainRatio < 0.5 ? 'text-accent-red' : 'text-accent-yellow') : 'text-text-muted'}`}>
              {strainRatio != null ? `${strainRatio.toFixed(2)}x` : '—'}
            </div>
            <div className="flex gap-1 mt-2 text-[10px]">
              <span className="px-2 py-0.5 rounded-full bg-accent-red/15 text-accent-red">&lt;0.5x detraining</span>
              <span className="px-2 py-0.5 rounded-full bg-accent-green/15 text-accent-green">0.8–1.3x optimal</span>
              <span className="px-2 py-0.5 rounded-full bg-accent-red/15 text-accent-red">&gt;1.5x overreach</span>
            </div>
          </div>
          {latestActivity && (latestActivity.training_effect_aerobic != null || latestActivity.training_effect_anaerobic != null) && (
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-1">Last activity training effect</div>
              <div className="flex gap-4 text-[14px]">
                {latestActivity.training_effect_aerobic != null && (
                  <div>
                    <span className="text-text-primary font-bold">{latestActivity.training_effect_aerobic.toFixed(1)}</span>
                    <span className="text-text-muted text-[12px] ml-1">aerobic</span>
                  </div>
                )}
                {latestActivity.training_effect_anaerobic != null && (
                  <div>
                    <span className="text-text-primary font-bold">{latestActivity.training_effect_anaerobic.toFixed(1)}</span>
                    <span className="text-text-muted text-[12px] ml-1">anaerobic</span>
                  </div>
                )}
              </div>
            </div>
          )}
          {/* Daily intensity breakdown */}
          <div>
            <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-2">Daily intensity (7d)</div>
            <div className="flex gap-1">
              {metricsData.slice(0, 7).reverse().map((d, i) => {
                const v = (d.vigorous_intensity_minutes ?? 0) + (d.moderate_intensity_minutes ?? 0)
                const maxH = 40
                const h = Math.min(maxH, Math.max(2, (v / 120) * maxH))
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                    <div className="w-full flex items-end justify-center" style={{ height: maxH }}>
                      <div className="w-full rounded-t bg-accent-orange/60" style={{ height: h }} />
                    </div>
                    <span className="text-[9px] text-text-dim">{d.date.slice(5)}</span>
                  </div>
                )
              })}
            </div>
          </div>
          <div className="text-[12px] text-text-muted leading-relaxed bg-bg-inset rounded-xl px-3 py-2.5">
            <strong className="text-text-secondary">What this means:</strong> Strain shows your recent training load (vigorous + moderate intensity minutes) compared to your 4-week baseline. The 0.8–1.3x range is the sweet spot — enough stimulus for adaptation without overreaching. Below 0.5x risks detraining; above 1.5x increases injury and fatigue risk.
          </div>
        </div>
      </MetricDetailSheet>
    </>
  )
}
