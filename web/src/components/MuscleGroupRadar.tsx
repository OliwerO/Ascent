import { useState, useMemo } from 'react'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from 'recharts'
import { ChevronUp, ChevronDown, Dumbbell, Weight, RefreshCw } from 'lucide-react'
import { Card } from './Card'
import { computeRadarData, type RadarMode } from '../lib/muscleGroups'
import type { TrainingSet, TrainingSession } from '../lib/types'

const MODES: { key: RadarMode; label: string; icon: typeof Dumbbell }[] = [
  { key: 'load', label: 'Muscular Load', icon: Dumbbell },
  { key: 'volume', label: 'Total Volume', icon: Weight },
  { key: 'frequency', label: 'Workout Frequency', icon: RefreshCw },
]

interface Props {
  sets: TrainingSet[]
  sessions: TrainingSession[]
}

export function MuscleGroupRadar({ sets, sessions }: Props) {
  const [modeIdx, setModeIdx] = useState(0)
  const mode = MODES[modeIdx]

  const data = useMemo(
    () => computeRadarData(sets, sessions, mode.key),
    [sets, sessions, mode.key],
  )

  const hasData = data.some((d) => d.value > 0)

  const cycleMode = () => setModeIdx((i) => (i + 1) % MODES.length)

  const Icon = mode.icon

  return (
    <Card>
      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon size={16} className="text-gym" />
            <span className="text-[14px] font-bold text-text-primary">{mode.label}</span>
          </div>
          <button
            onClick={cycleMode}
            className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Switch mode"
          >
            <div className="flex flex-col items-center">
              <ChevronUp size={10} className="text-text-dim -mb-0.5" />
              <ChevronDown size={10} className="text-text-dim -mt-0.5" />
            </div>
          </button>
        </div>

        {/* Radar chart */}
        <div className="relative h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="65%" data={data}>
              <PolarGrid
                stroke="rgba(255,255,255,0.08)"
                strokeWidth={1}
              />
              <PolarAngleAxis
                dataKey="group"
                tick={(props: Record<string, unknown>) => {
                  const payload = props.payload as { value: string }
                  const x = props.x as number
                  const y = props.y as number
                  const textAnchor = props.textAnchor as 'start' | 'middle' | 'end' | undefined
                  const item = data.find((d) => d.group === payload.value)
                  return (
                    <g>
                      <text
                        x={x}
                        y={y - 10}
                        textAnchor={textAnchor}
                        fill="#8a8aa0"
                        fontSize={13}
                        fontStyle="italic"
                      >
                        {item?.label ?? ''}
                      </text>
                      <text
                        x={x}
                        y={y + 6}
                        textAnchor={textAnchor}
                        fill="#f0f0f5"
                        fontSize={13}
                        fontWeight={600}
                      >
                        {payload.value}
                      </text>
                    </g>
                  )
                }}
              />
              <Radar
                dataKey="value"
                stroke="#a78bfa"
                fill="#a78bfa"
                fillOpacity={hasData ? 0.25 : 0.05}
                strokeWidth={hasData ? 2 : 1}
                dot={hasData ? { r: 3, fill: '#a78bfa', stroke: '#16161e', strokeWidth: 2 } : false}
              />
            </RadarChart>
          </ResponsiveContainer>

          {!hasData && (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-[13px] text-text-dim">No training data yet</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
