import { useMemo } from 'react'
import { Card } from '../components/Card'
import { LoadingState } from '../components/LoadingState'
import { useActivities, useSleep, useBodyComposition } from '../hooks/useSupabase'
import { pairHikeAndFly, formatAirtime, formatDistance } from '../lib/flying'
import { startOfWeek, endOfWeek, format, isWithinInterval } from 'date-fns'
import { Wind } from 'lucide-react'
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
  const sleepHook = useSleep(14)
  const bodyCompHook = useBodyComposition(30)

  const loading = activitiesHook.loading || sleepHook.loading || bodyCompHook.loading
  const error = activitiesHook.error || sleepHook.error || bodyCompHook.error

  const now = new Date()
  const weekStart = startOfWeek(now, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(now, { weekStartsOn: 1 })

  const prevWeekStart = new Date(weekStart)
  prevWeekStart.setDate(prevWeekStart.getDate() - 7)
  const prevWeekEnd = new Date(weekEnd)
  prevWeekEnd.setDate(prevWeekEnd.getDate() - 7)

  // Filter activities to current week
  const weekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: any) =>
      isWithinInterval(new Date(a.date), { start: weekStart, end: weekEnd })
    )
  }, [activitiesHook.data, weekStart.getTime(), weekEnd.getTime()])

  // Filter activities to previous week
  const prevWeekActivities = useMemo(() => {
    if (!activitiesHook.data) return []
    return activitiesHook.data.filter((a: any) =>
      isWithinInterval(new Date(a.date), { start: prevWeekStart, end: prevWeekEnd })
    )
  }, [activitiesHook.data, prevWeekStart.getTime(), prevWeekEnd.getTime()])

  // Quick stats
  const totalElevation = useMemo(
    () => weekActivities
      .filter((a: any) => a.activity_type !== 'hang_gliding') // exclude paragliding from fitness elevation
      .reduce((sum: number, a: any) => sum + (a.elevation_gain || 0), 0),
    [weekActivities]
  )
  const gymSessions = useMemo(
    () => weekActivities.filter((a: any) => a.activity_type === 'strength_training').length,
    [weekActivities]
  )
  // Latest body composition data — show last available regardless of week
  const bodyComp = useMemo(() => {
    if (!bodyCompHook.data || bodyCompHook.data.length === 0) return null
    // Find latest with weight
    const withWeight = bodyCompHook.data.filter((d: any) => d.weight_kg != null)
    const withFat = bodyCompHook.data.filter((d: any) => d.body_fat_pct != null)
    const withMuscle = bodyCompHook.data.filter((d: any) => d.muscle_mass_grams != null)
    const latest = withWeight[0] as any ?? withFat[0] as any
    if (!latest) return null
    const prev = withWeight.length > 1 ? withWeight[1] as any : null
    return {
      weight: latest.weight_kg,
      bodyFat: withFat[0]?.body_fat_pct ?? null,
      muscleMass: withMuscle[0]?.muscle_mass_grams ? withMuscle[0].muscle_mass_grams / 1000 : null,
      date: latest.date,
      bodyFatDate: withFat[0]?.date ?? null,
      prevWeight: prev?.weight_kg ?? null,
    }
  }, [bodyCompHook.data])

  // Previous week stats for comparison
  const prevElevation = useMemo(
    () => prevWeekActivities
      .filter((a: any) => a.activity_type !== 'hang_gliding')
      .reduce((sum: number, a: any) => sum + (a.elevation_gain || 0), 0),
    [prevWeekActivities]
  )
  const prevGymSessions = useMemo(
    () => prevWeekActivities.filter((a: any) => a.activity_type === 'strength_training').length,
    [prevWeekActivities]
  )
  // Calories card removed — replaced by body comp

  // Comparison helper
  const pctChange = (curr: number, prev: number) => {
    if (prev === 0) return null
    return Math.round(((curr - prev) / prev) * 100)
  }

  // Weekly activity summary
  const weeklySummary = useMemo(() => {
    const strength = weekActivities.filter((a: any) => a.activity_type === 'strength_training').length
    const mountain = weekActivities.filter((a: any) =>
      ['resort_snowboarding', 'backcountry_snowboarding', 'resort_skiing', 'backcountry_skiing', 'hiking', 'ski_touring', 'splitboarding'].includes(a.activity_type)
    ).length
    const other = weekActivities.length - strength - mountain

    if (weekActivities.length === 0) return null

    const parts: string[] = []
    if (strength > 0) parts.push(`${strength} strength session${strength > 1 ? 's' : ''}`)
    if (mountain > 0) parts.push(`${mountain} mountain day${mountain > 1 ? 's' : ''}`)
    if (other > 0) parts.push(`${other} other`)

    const total = weekActivities.length
    const label = total >= 4 ? 'Active week' : total >= 2 ? 'Moderate week' : 'Light week'
    return `${label}: ${parts.join(' + ')}`
  }, [weekActivities])

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

  // Sleep intelligence: last 7 days stats
  const sleepStats = useMemo(() => {
    const last7 = sleepBars.slice(-7)
    if (last7.length === 0) return { avg: 0, belowSix: 0, count: 0 }
    const avg = last7.reduce((sum, d) => sum + d.hours, 0) / last7.length
    const belowSix = last7.filter((d) => d.hours > 0 && d.hours < 6).length
    return { avg: Number(avg.toFixed(1)), belowSix, count: last7.length }
  }, [sleepBars])

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
          {prevElevation > 0 && (() => {
            const pct = pctChange(totalElevation, prevElevation)
            return pct != null ? (
              <div className={`text-[10px] font-medium ${pct >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                {pct >= 0 ? '↑' : '↓'} {pct >= 0 ? '+' : ''}{pct}% vs last wk
              </div>
            ) : null
          })()}
        </Card>
        <Card>
          <div className="text-xs text-text-muted">Strength</div>
          <div className="text-xl font-bold text-text-primary">
            {gymSessions}
            <span className="text-xs text-text-muted ml-1">sessions</span>
          </div>
          {prevGymSessions > 0 && gymSessions !== prevGymSessions && (
            <div className={`text-[10px] font-medium ${gymSessions >= prevGymSessions ? 'text-accent-green' : 'text-accent-red'}`}>
              {gymSessions > prevGymSessions ? '↑' : '↓'} {prevGymSessions} last wk
            </div>
          )}
        </Card>
        <Card>
          <div className="text-xs text-text-muted">Body Comp</div>
          {bodyComp ? (
            <>
              <div className="text-xl font-bold text-text-primary">
                {bodyComp.weight?.toFixed(1) ?? '--'}
                <span className="text-xs text-text-muted ml-1">kg</span>
              </div>
              {bodyComp.bodyFat != null && (
                <div className="text-[10px] font-medium text-text-secondary">
                  {bodyComp.bodyFat.toFixed(1)}% bf
                  {bodyComp.muscleMass != null && ` · ${bodyComp.muscleMass.toFixed(1)}kg muscle`}
                </div>
              )}
              {bodyComp.prevWeight != null && bodyComp.weight != null && bodyComp.weight !== bodyComp.prevWeight && (
                <div className={`text-[10px] font-medium ${bodyComp.weight <= bodyComp.prevWeight ? 'text-accent-green' : 'text-accent-yellow'}`}>
                  {bodyComp.weight < bodyComp.prevWeight ? '↓' : '↑'} {Math.abs(bodyComp.weight - bodyComp.prevWeight).toFixed(1)}kg
                </div>
              )}
              <div className="text-[9px] text-text-muted mt-0.5">
                {format(new Date(bodyComp.date), 'MMM d')}
              </div>
            </>
          ) : (
            <div className="text-sm text-text-muted mt-1">No data</div>
          )}
        </Card>
      </div>

      {/* Activity Log */}
      <Card title="Activity Log">
        {weeklySummary && (
          <div className="text-xs font-medium text-text-secondary mb-3 pb-2 border-b border-border">
            {weeklySummary}
          </div>
        )}
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

      {/* Sleep Trend */}
      <Card title="Sleep Trend (14d)" subtitle="Stage breakdown is approximate (±45 min per stage). Total duration is the reliable number.">
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
        {/* Sleep intelligence stats */}
        {sleepStats.count > 0 && (
          <div className="mt-3 space-y-1.5">
            <div className="flex items-center gap-3 text-xs">
              <span className="text-text-muted">Weekly avg:</span>
              <span className={`font-semibold ${
                sleepStats.avg >= 7 ? 'text-accent-green'
                  : sleepStats.avg >= 6 ? 'text-accent-yellow'
                  : 'text-accent-red'
              }`}>
                {sleepStats.avg}h
              </span>
              <span className="text-text-muted">
                (target: 7-8h)
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="text-text-muted">Nights below 6h:</span>
              <span className={`font-semibold ${
                sleepStats.belowSix === 0 ? 'text-accent-green'
                  : sleepStats.belowSix <= 1 ? 'text-accent-yellow'
                  : 'text-accent-red'
              }`}>
                {sleepStats.belowSix} / {sleepStats.count}
              </span>
            </div>
            {sleepStats.avg < 6.5 && (
              <div className="text-xs font-semibold text-accent-red mt-1 py-1 px-2 bg-accent-red/10 rounded">
                Sleep is the bottleneck — below critical threshold
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Flying this week — only shows when flights happened */}
      <WeekFlights activities={weekActivities} />
    </div>
  )
}

function WeekFlights({ activities }: { activities: any[] }) {
  const flights = useMemo(() => {
    const flyActivities = activities.filter((a: any) => a.activity_type === 'hang_gliding')
    if (!flyActivities.length) return []
    return pairHikeAndFly(flyActivities, activities)
  }, [activities])

  if (!flights.length) return null

  const totalAirtime = flights.reduce((s, f) => s + f.airtime, 0)
  const totalDistance = flights.reduce((s, f) => s + f.distance, 0)
  const xcFlights = flights.filter(f => f.flightType === 'xc').length

  const typeLabel = (type: string) => {
    switch (type) {
      case 'xc': return 'XC'
      case 'soaring': return 'Soaring'
      case 'glide_down': return 'Glide'
      case 'hike_and_fly': return 'H&F'
      default: return type
    }
  }

  const typeColor = (type: string) => {
    switch (type) {
      case 'xc': return 'text-accent-orange'
      case 'soaring': return 'text-accent-yellow'
      case 'hike_and_fly': return 'text-accent-green'
      default: return 'text-text-muted'
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2 mb-3">
        <Wind size={14} className="text-accent-orange" />
        <span className="text-xs uppercase tracking-wider text-text-muted font-medium">Flying this week</span>
      </div>
      <div className="flex gap-4 text-sm mb-3">
        <div>
          <span className="text-text-primary font-semibold">{flights.length}</span>
          <span className="text-text-muted text-xs ml-1">flight{flights.length !== 1 ? 's' : ''}</span>
        </div>
        <div>
          <span className="text-text-primary font-semibold">{formatAirtime(totalAirtime)}</span>
          <span className="text-text-muted text-xs ml-1">airtime</span>
        </div>
        {totalDistance > 0 && (
          <div>
            <span className="text-text-primary font-semibold">{formatDistance(totalDistance)}</span>
            <span className="text-text-muted text-xs ml-1">distance</span>
          </div>
        )}
        {xcFlights > 0 && (
          <div>
            <span className="text-accent-orange font-semibold">{xcFlights}</span>
            <span className="text-text-muted text-xs ml-1">XC</span>
          </div>
        )}
      </div>
      <div className="space-y-1.5">
        {flights.map((f, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className={`font-medium ${typeColor(f.flightType)}`}>{typeLabel(f.flightType)}</span>
              <span className="text-text-secondary">{format(new Date(f.date), 'EEE')}</span>
            </div>
            <div className="flex gap-3 text-text-muted">
              <span>{formatAirtime(f.airtime)}</span>
              {f.distance > 100 && <span>{formatDistance(f.distance)}</span>}
              {f.maxAltitude != null && f.maxAltitude > 0 && <span>{Math.round(f.maxAltitude)}m</span>}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
