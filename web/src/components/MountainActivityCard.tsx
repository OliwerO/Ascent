import { Mountain } from 'lucide-react'
import { format } from 'date-fns'
import { formatDuration, formatActivityType } from '../lib/format'
import type { Activity, HRZone } from '../lib/types'

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

export function MountainActivityCard({ activity, showDate = true }: { activity: Activity; showDate?: boolean }) {
  const a = activity
  const zones = parseZones(a.hr_zones)
  const totalZoneSecs = zones.reduce((s, z) => s + z.seconds, 0)
  const vam = a.elevation_gain != null && a.duration_seconds != null && a.duration_seconds > 0
    ? Math.round((a.elevation_gain / a.duration_seconds) * 3600)
    : null
  const aerobic = a.training_effect_aerobic
  const anaerobic = a.training_effect_anaerobic

  return (
    <div className="bg-bg-primary/50 rounded-xl px-4 py-3 space-y-2">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Mountain size={14} className="text-mountain shrink-0" />
        <span className="text-[14px] font-semibold text-text-primary">
          {a.activity_name ?? formatActivityType(a.activity_type)}
        </span>
      </div>

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
    </div>
  )
}
