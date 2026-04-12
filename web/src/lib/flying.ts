import type { Activity } from './types'

export type FlightType = 'xc' | 'soaring' | 'glide_down' | 'hike_and_fly'

export interface FlightData {
  date: string
  activityName: string | null
  flightType: FlightType
  airtime: number // seconds
  distance: number // meters
  thermalGain: number // meters climbed in thermals
  elevationLoss: number
  maxAltitude: number | null
  minAltitude: number | null
  maxClimbRate: number | null // m/s
  maxSpeed: number | null // m/s
  avgSpeed: number | null
  avgHR: number | null
  maxHR: number | null
  // Hike & fly pairing
  hikeActivity: {
    elevationGain: number
    duration: number
    distance: number
  } | null
}

export function classifyFlight(elevationGain: number, distance: number): FlightType {
  if (elevationGain < 100) return 'glide_down'
  if (distance > 20000) return 'xc'
  return 'soaring'
}

export function parseFlightFromActivity(activity: Activity): FlightData {
  const raw = activity.raw_json ?? {}
  const gain = activity.elevation_gain ?? 0
  const dist = activity.distance_meters ?? 0

  const num = (v: unknown): number | null =>
    typeof v === 'number' ? v : null

  return {
    date: activity.date,
    activityName: activity.activity_name,
    flightType: classifyFlight(gain, dist),
    airtime: num(raw.movingDuration) ?? activity.duration_seconds ?? 0,
    distance: dist,
    thermalGain: gain,
    elevationLoss: activity.elevation_loss ?? 0,
    maxAltitude: num(raw.maxElevation),
    minAltitude: num(raw.minElevation),
    maxClimbRate: num(raw.maxVerticalSpeed),
    maxSpeed: num(raw.maxSpeed) ?? activity.max_speed ?? null,
    avgSpeed: num(raw.averageSpeed) ?? activity.avg_speed ?? null,
    avgHR: activity.avg_hr,
    maxHR: activity.max_hr,
    hikeActivity: null, // filled by pairing logic
  }
}

export function pairHikeAndFly(
  flights: Activity[],
  allActivities: Activity[]
): FlightData[] {
  return flights.map((flight) => {
    const fd = parseFlightFromActivity(flight)

    // Find hiking activity on the same day that ended before the flight started
    const hike = allActivities.find(
      (a) =>
        a.date === flight.date &&
        (a.activity_type === 'hiking' || a.activity_type === 'mountaineering') &&
        a.start_time &&
        flight.start_time &&
        new Date(a.start_time) < new Date(flight.start_time)
    )

    if (hike) {
      fd.flightType = 'hike_and_fly'
      fd.hikeActivity = {
        elevationGain: hike.elevation_gain ?? 0,
        duration: hike.duration_seconds ?? 0,
        distance: hike.distance_meters ?? 0,
      }
    }

    return fd
  })
}

export function formatAirtime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export function formatClimbRate(ms: number): string {
  return `${ms.toFixed(1)} m/s`
}

export function formatSpeed(ms: number): string {
  return `${Math.round(ms * 3.6)} km/h`
}

export function formatDistance(meters: number): string {
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`
  return `${Math.round(meters)} m`
}
