import { useMemo } from 'react'
import { Card } from '../../components/Card'
import type { Activity } from '../../lib/types'
import { pairHikeAndFly, formatAirtime, formatDistance } from '../../lib/flying'
import { Wind } from 'lucide-react'
import { format } from 'date-fns'

interface Props {
  activities: Activity[]
}

export function FlyingSection({ activities }: Props) {
  const flights = useMemo(() => {
    const flyActivities = activities.filter((a: Activity) => a.activity_type === 'hang_gliding')
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
        <Wind size={15} className="text-accent-orange" />
        <span className="text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold">Flying this week</span>
      </div>
      <div className="flex gap-4 text-[14px] mb-3">
        <div>
          <span className="text-text-primary font-bold">{flights.length}</span>
          <span className="text-text-muted text-[12px] ml-1">flight{flights.length !== 1 ? 's' : ''}</span>
        </div>
        <div>
          <span className="text-text-primary font-bold">{formatAirtime(totalAirtime)}</span>
          <span className="text-text-muted text-[12px] ml-1">airtime</span>
        </div>
        {totalDistance > 0 && (
          <div>
            <span className="text-text-primary font-bold">{formatDistance(totalDistance)}</span>
            <span className="text-text-muted text-[12px] ml-1">distance</span>
          </div>
        )}
        {xcFlights > 0 && (
          <div>
            <span className="text-accent-orange font-bold">{xcFlights}</span>
            <span className="text-text-muted text-[12px] ml-1">XC</span>
          </div>
        )}
      </div>
      <div className="space-y-2">
        {flights.map((f, i) => (
          <div key={i} className="flex items-center justify-between text-[13px]">
            <div className="flex items-center gap-2">
              <span className={`font-semibold ${typeColor(f.flightType)}`}>{typeLabel(f.flightType)}</span>
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
