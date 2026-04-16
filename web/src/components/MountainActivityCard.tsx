import { useState } from 'react'
import { Mountain, ChevronDown, ChevronUp } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { formatDuration, formatActivityType } from '../lib/format'
import type { Activity, HRZone, ActivityDetails } from '../lib/types'

function trainingEffectLabel(te: number): { text: string; color: string } {
  if (te < 1.0) return { text: 'None', color: 'text-text-dim' }
  if (te < 2.0) return { text: 'Minor', color: 'text-text-muted' }
  if (te < 3.0) return { text: 'Maintaining', color: 'text-accent-blue' }
  if (te < 4.0) return { text: 'Improving', color: 'text-accent-green' }
  if (te < 5.0) return { text: 'Highly improving', color: 'text-accent-yellow' }
  return { text: 'Overreaching', color: 'text-accent-red' }
}

function formatDistance(meters: number): string {
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)}km`
  return `${Math.round(meters)}m`
}

/** Parse HR zones from the Garmin JSONB format */
function parseZones(zones: HRZone[] | null): { zone: number; seconds: number }[] {
  if (!zones || !Array.isArray(zones)) return []
  return zones
    .map((z) => ({
      zone: typeof z.zone === 'number' ? z.zone
        : typeof z.zoneNumber === 'number' ? (z.zoneNumber as number)
        : parseInt(String(z.zone || z.zoneNumber || '0'), 10),
      seconds: z.seconds ?? z.secsInZone as number ?? 0,
    }))
    .filter((z) => z.seconds > 0)
    .sort((a, b) => a.zone - b.zone)
}

const ZONE_COLORS = ['#4ade80', '#86efac', '#fbbf24', '#f97316', '#ef4444']

// ─── Split parsing (Garmin JSONB varies) ───

interface ParsedSplit {
  index: number
  duration: number | null
  elevationGain: number | null
  avgHR: number | null
  maxHR: number | null
}

function parseSplits(raw: unknown): ParsedSplit[] {
  if (!raw) return []
  const arr = Array.isArray(raw) ? raw
    : typeof raw === 'object' && raw !== null && 'activityDetailMetrics' in raw
      ? (raw as Record<string, unknown>).activityDetailMetrics as unknown[]
      : typeof raw === 'object' && raw !== null && 'lapDTOs' in raw
        ? (raw as Record<string, unknown>).lapDTOs as unknown[]
        : null
  if (!Array.isArray(arr) || arr.length === 0) return []

  return arr.map((s: Record<string, unknown>, i: number) => ({
    index: i + 1,
    duration: toNum(s.duration ?? s.elapsedDuration ?? s.movingDuration),
    elevationGain: toNum(s.elevationGain ?? s.totalAscent ?? s.gainElevation),
    avgHR: toNum(s.averageHR ?? s.averageHeartRate),
    maxHR: toNum(s.maxHR ?? s.maxHeartRate),
  })).filter((s) => s.duration != null || s.elevationGain != null)
}

function toNum(v: unknown): number | null {
  if (v == null) return null
  const n = Number(v)
  return isFinite(n) ? n : null
}

// ─── Historical comparison helpers ───

function activityVam(a: Activity): number | null {
  if (a.elevation_gain == null || a.duration_seconds == null || a.duration_seconds <= 0 || a.elevation_gain <= 0) return null
  return Math.round((a.elevation_gain / a.duration_seconds) * 3600)
}

function avgOrNull(values: number[]): number | null {
  if (values.length === 0) return null
  return Math.round(values.reduce((a, b) => a + b, 0) / values.length)
}

interface HistoricalStats {
  count: number
  avgVam: number | null
  avgHR: number | null
  avgElevation: number | null
  avgDuration: number | null
  avgTE: number | null
}

function computeStats(activities: Activity[]): HistoricalStats {
  const vams = activities.map(activityVam).filter((v): v is number => v != null)
  const hrs = activities.map((a) => a.avg_hr).filter((v): v is number => v != null)
  const elevs = activities.map((a) => a.elevation_gain).filter((v): v is number => v != null && v > 0)
  const durs = activities.map((a) => a.duration_seconds).filter((v): v is number => v != null && v > 0)
  const tes = activities.map((a) => a.training_effect_aerobic).filter((v): v is number => v != null)
  return {
    count: activities.length,
    avgVam: avgOrNull(vams),
    avgHR: avgOrNull(hrs),
    avgElevation: avgOrNull(elevs),
    avgDuration: avgOrNull(durs),
    avgTE: tes.length > 0 ? Math.round(tes.reduce((a, b) => a + b, 0) / tes.length * 10) / 10 : null,
  }
}

// Season start: November 1 of the current winter season
function getSeasonStart(): Date {
  const now = new Date()
  const year = now.getMonth() >= 10 ? now.getFullYear() : now.getFullYear() - 1
  return new Date(year, 10, 1) // Nov 1
}

export function MountainActivityCard({
  activity,
  showDate = true,
  details,
  allMountainActivities,
}: {
  activity: Activity
  showDate?: boolean
  details?: ActivityDetails | null
  allMountainActivities?: Activity[]
}) {
  const [expanded, setExpanded] = useState(false)
  const a = activity
  const zones = parseZones(a.hr_zones)
  const totalZoneSecs = zones.reduce((s, z) => s + z.seconds, 0)
  const vam = activityVam(a)
  const aerobic = a.training_effect_aerobic
  const anaerobic = a.training_effect_anaerobic

  const splits = details ? parseSplits(details.splits) : []
  const hasDetail = splits.length > 0 || (allMountainActivities && allMountainActivities.length > 1)

  // Historical comparisons (exclude this activity)
  const others = (allMountainActivities ?? []).filter((o) => o.garmin_activity_id !== a.garmin_activity_id)
  const thirtyDaysAgo = format(subDays(new Date(), 30), 'yyyy-MM-dd')
  const seasonStart = format(getSeasonStart(), 'yyyy-MM-dd')
  const last30 = others.filter((o) => o.date >= thirtyDaysAgo)
  const season = others.filter((o) => o.date >= seasonStart)
  const stats30 = computeStats(last30)
  const statsSeason = computeStats(season)

  return (
    <div className="bg-bg-primary/50 rounded-xl px-4 py-3 space-y-2">
      {/* Header */}
      <button
        onClick={() => hasDetail && setExpanded(!expanded)}
        className={`flex items-center gap-2 w-full text-left ${hasDetail ? 'cursor-pointer' : 'cursor-default'}`}
      >
        <Mountain size={14} className="text-mountain shrink-0" />
        <span className="text-[14px] font-semibold text-text-primary flex-1">
          {a.activity_name ?? formatActivityType(a.activity_type)}
        </span>
        {hasDetail && (
          expanded
            ? <ChevronUp size={14} className="text-text-muted shrink-0" />
            : <ChevronDown size={14} className="text-text-muted shrink-0" />
        )}
      </button>

      {/* Metric row */}
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[13px] text-text-muted">
        {showDate && <span>{format(new Date(a.date + 'T12:00:00'), 'EEE')}</span>}
        {a.duration_seconds != null && <span>{formatDuration(a.duration_seconds)}</span>}
        {a.distance_meters != null && a.distance_meters > 0 && (
          <span>{formatDistance(a.distance_meters)}</span>
        )}
        {a.elevation_gain != null && a.elevation_gain > 0 && (
          <span className="text-mountain">{Math.round(a.elevation_gain)}m ↑</span>
        )}
        {a.calories != null && a.calories > 0 && (
          <span>{a.calories} kcal</span>
        )}
      </div>

      {/* HR + VAM row */}
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[13px]">
        {a.avg_hr != null && (
          <span className="text-text-secondary">
            HR {a.avg_hr}
            {a.max_hr != null && <span className="text-text-dim"> / {a.max_hr} max</span>}
          </span>
        )}
        {vam != null && vam > 0 && (
          <span className="text-mountain font-medium">{vam} m/h VAM</span>
        )}
      </div>

      {/* Training effect */}
      {aerobic != null && (
        <div className="flex gap-3 text-[12px]">
          <span>
            Aerobic:{' '}
            <span className={`font-semibold ${trainingEffectLabel(aerobic).color}`}>
              {aerobic.toFixed(1)} {trainingEffectLabel(aerobic).text}
            </span>
          </span>
          {anaerobic != null && anaerobic > 0 && (
            <span>
              Anaerobic:{' '}
              <span className="font-semibold text-text-secondary">
                {anaerobic.toFixed(1)}
              </span>
            </span>
          )}
        </div>
      )}

      {/* HR zone bar */}
      {zones.length > 0 && totalZoneSecs > 0 && (
        <div>
          <div className="flex rounded-full overflow-hidden h-2.5">
            {zones.map((z) => (
              <div
                key={z.zone}
                style={{
                  width: `${(z.seconds / totalZoneSecs) * 100}%`,
                  backgroundColor: ZONE_COLORS[Math.min(z.zone - 1, 4)] ?? ZONE_COLORS[0],
                }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-1 text-[10px] text-text-dim">
            {zones.map((z) => (
              <span key={z.zone}>
                Z{z.zone} {Math.round(z.seconds / 60)}m
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ─── Expandable Deep Dive ─── */}
      {expanded && hasDetail && (
        <div className="pt-2 mt-2 border-t border-border-subtle space-y-3">
          {/* Splits table */}
          {splits.length > 0 && (
            <div>
              <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-1.5">
                Splits ({splits.length})
              </div>
              <div className="overflow-x-auto -mx-4 px-4">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="text-text-dim border-b border-border-subtle">
                      <th className="text-left py-1 font-semibold">#</th>
                      <th className="text-right py-1 font-semibold">Time</th>
                      {splits.some((s) => s.elevationGain != null) && <th className="text-right py-1 font-semibold">Elev</th>}
                      {splits.some((s) => s.elevationGain != null && s.duration != null) && <th className="text-right py-1 font-semibold">VAM</th>}
                      {splits.some((s) => s.avgHR != null) && <th className="text-right py-1 font-semibold">HR</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {splits.map((s) => {
                      const splitVam = s.elevationGain != null && s.duration != null && s.duration > 0
                        ? Math.round((s.elevationGain / (s.duration / 1000)) * 3600)
                        : null
                      return (
                        <tr key={s.index} className="border-b border-border-subtle/30 last:border-0">
                          <td className="py-1 text-text-muted">{s.index}</td>
                          <td className="py-1 text-right text-text-secondary font-data">
                            {s.duration != null ? formatDuration(Math.round(s.duration / 1000)) : '\u2014'}
                          </td>
                          {splits.some((sp) => sp.elevationGain != null) && (
                            <td className="py-1 text-right text-mountain font-data">
                              {s.elevationGain != null ? `${Math.round(s.elevationGain)}m` : '\u2014'}
                            </td>
                          )}
                          {splits.some((sp) => sp.elevationGain != null && sp.duration != null) && (
                            <td className="py-1 text-right text-mountain font-data">
                              {splitVam != null && splitVam > 0 ? splitVam : '\u2014'}
                            </td>
                          )}
                          {splits.some((sp) => sp.avgHR != null) && (
                            <td className="py-1 text-right text-text-secondary font-data">
                              {s.avgHR != null ? Math.round(s.avgHR) : '\u2014'}
                            </td>
                          )}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              <SplitPerformanceSummary splits={splits} />
            </div>
          )}

          {/* Historical comparison */}
          <HistoricalComparison
            thisActivity={a}
            thisVam={vam}
            stats30={stats30}
            statsSeason={statsSeason}
          />
        </div>
      )}

      {/* Tap hint */}
      {hasDetail && !expanded && (
        <div className="text-[10px] text-text-dim text-center pt-0.5">Tap for details</div>
      )}
    </div>
  )
}

// ─── Split Performance Summary ───

function SplitPerformanceSummary({ splits }: { splits: ParsedSplit[] }) {
  const splitsWithVam = splits.filter((s) => s.elevationGain != null && s.duration != null && s.duration > 0)
    .map((s) => ({
      ...s,
      vam: Math.round((s.elevationGain! / (s.duration! / 1000)) * 3600),
    }))
    .filter((s) => s.vam > 0)

  if (splitsWithVam.length < 2) return null

  const bestVam = Math.max(...splitsWithVam.map((s) => s.vam))
  const avgVam = Math.round(splitsWithVam.reduce((sum, s) => sum + s.vam, 0) / splitsWithVam.length)

  const mean = avgVam
  const stdDev = Math.sqrt(splitsWithVam.reduce((sum, s) => sum + (s.vam - mean) ** 2, 0) / splitsWithVam.length)
  const consistency = mean > 0 ? Math.round((1 - stdDev / mean) * 100) : null

  return (
    <div className="mt-2 pt-2 border-t border-border-subtle/50">
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-[10px] text-text-dim uppercase tracking-wider">Best VAM</div>
          <div className="text-[13px] font-bold text-mountain font-data">{bestVam}</div>
        </div>
        <div>
          <div className="text-[10px] text-text-dim uppercase tracking-wider">Avg VAM</div>
          <div className="text-[13px] font-bold text-text-secondary font-data">{avgVam}</div>
        </div>
        {consistency != null && (
          <div>
            <div className="text-[10px] text-text-dim uppercase tracking-wider">Pacing</div>
            <div className={`text-[13px] font-bold font-data ${
              consistency >= 80 ? 'text-accent-green' : consistency >= 60 ? 'text-accent-yellow' : 'text-accent-red'
            }`}>
              {consistency}%
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Historical Comparison ───

function deltaIndicator(current: number | null, avg: number | null): { text: string; color: string } | null {
  if (current == null || avg == null || avg === 0) return null
  const pct = Math.round(((current - avg) / avg) * 100)
  if (Math.abs(pct) < 2) return { text: '=', color: 'text-text-muted' }
  return {
    text: `${pct > 0 ? '+' : ''}${pct}%`,
    color: pct > 0 ? 'text-accent-green' : 'text-accent-red',
  }
}

function HistoricalComparison({
  thisActivity,
  thisVam,
  stats30,
  statsSeason,
}: {
  thisActivity: Activity
  thisVam: number | null
  stats30: HistoricalStats
  statsSeason: HistoricalStats
}) {
  // Need at least one comparison window with data
  if (stats30.count === 0 && statsSeason.count === 0) return null

  const thisHR = thisActivity.avg_hr
  const thisElev = thisActivity.elevation_gain
  const thisDur = thisActivity.duration_seconds
  const thisTE = thisActivity.training_effect_aerobic

  const rows: { label: string; thisVal: string; vs30: ReturnType<typeof deltaIndicator>; avg30: string | null; vsSeason: ReturnType<typeof deltaIndicator>; avgSeason: string | null }[] = []

  if (thisVam != null) {
    rows.push({
      label: 'VAM',
      thisVal: `${thisVam}`,
      vs30: deltaIndicator(thisVam, stats30.avgVam),
      avg30: stats30.avgVam != null ? `${stats30.avgVam}` : null,
      vsSeason: deltaIndicator(thisVam, statsSeason.avgVam),
      avgSeason: statsSeason.avgVam != null ? `${statsSeason.avgVam}` : null,
    })
  }
  if (thisHR != null) {
    rows.push({
      label: 'Avg HR',
      thisVal: `${thisHR}`,
      // For HR, lower is better (more efficient) — flip the indicator
      vs30: stats30.avgHR != null && thisHR != null ? deltaIndicator(stats30.avgHR, thisHR) : null,
      avg30: stats30.avgHR != null ? `${stats30.avgHR}` : null,
      vsSeason: statsSeason.avgHR != null && thisHR != null ? deltaIndicator(statsSeason.avgHR, thisHR) : null,
      avgSeason: statsSeason.avgHR != null ? `${statsSeason.avgHR}` : null,
    })
  }
  if (thisElev != null && thisElev > 0) {
    rows.push({
      label: 'Elevation',
      thisVal: `${Math.round(thisElev)}m`,
      vs30: deltaIndicator(thisElev, stats30.avgElevation),
      avg30: stats30.avgElevation != null ? `${stats30.avgElevation}m` : null,
      vsSeason: deltaIndicator(thisElev, statsSeason.avgElevation),
      avgSeason: statsSeason.avgElevation != null ? `${statsSeason.avgElevation}m` : null,
    })
  }
  if (thisDur != null && thisDur > 0) {
    rows.push({
      label: 'Duration',
      thisVal: formatDuration(thisDur),
      vs30: deltaIndicator(thisDur, stats30.avgDuration),
      avg30: stats30.avgDuration != null ? formatDuration(stats30.avgDuration) : null,
      vsSeason: deltaIndicator(thisDur, statsSeason.avgDuration),
      avgSeason: statsSeason.avgDuration != null ? formatDuration(statsSeason.avgDuration) : null,
    })
  }
  if (thisTE != null) {
    rows.push({
      label: 'Aero TE',
      thisVal: thisTE.toFixed(1),
      vs30: deltaIndicator(thisTE, stats30.avgTE),
      avg30: stats30.avgTE != null ? stats30.avgTE.toFixed(1) : null,
      vsSeason: deltaIndicator(thisTE, statsSeason.avgTE),
      avgSeason: statsSeason.avgTE != null ? statsSeason.avgTE.toFixed(1) : null,
    })
  }

  if (rows.length === 0) return null

  const has30 = stats30.count > 0
  const hasSeason = statsSeason.count > 0

  return (
    <div className="pt-2 border-t border-border-subtle">
      <div className="text-[11px] text-text-muted uppercase tracking-wider font-semibold mb-2">
        vs History
      </div>
      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-text-dim border-b border-border-subtle">
            <th className="text-left py-1 font-semibold"></th>
            <th className="text-right py-1 font-semibold">This</th>
            {has30 && <th className="text-right py-1 font-semibold">30d avg</th>}
            {has30 && <th className="text-right py-1 font-semibold"></th>}
            {hasSeason && <th className="text-right py-1 font-semibold">Season</th>}
            {hasSeason && <th className="text-right py-1 font-semibold"></th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-b border-border-subtle/30 last:border-0">
              <td className="py-1 text-text-muted">{r.label}</td>
              <td className="py-1 text-right text-text-primary font-data font-semibold">{r.thisVal}</td>
              {has30 && <td className="py-1 text-right text-text-dim font-data">{r.avg30 ?? '\u2014'}</td>}
              {has30 && (
                <td className={`py-1 text-right font-data font-semibold ${r.vs30?.color ?? 'text-text-dim'}`}>
                  {r.vs30?.text ?? ''}
                </td>
              )}
              {hasSeason && <td className="py-1 text-right text-text-dim font-data">{r.avgSeason ?? '\u2014'}</td>}
              {hasSeason && (
                <td className={`py-1 text-right font-data font-semibold ${r.vsSeason?.color ?? 'text-text-dim'}`}>
                  {r.vsSeason?.text ?? ''}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-[10px] text-text-dim mt-1.5">
        {has30 && <span>30d: {stats30.count} activities</span>}
        {has30 && hasSeason && <span className="mx-1.5">&middot;</span>}
        {hasSeason && <span>Season: {statsSeason.count} activities</span>}
      </div>
    </div>
  )
}
