import { useState } from 'react'
import { Card } from '../../components/Card'
import type { Activity, PlannedWorkout, PlannedExercise } from '../../lib/types'
import { format } from 'date-fns'
import { ChevronDown, ChevronUp, ArrowRightLeft, Check } from 'lucide-react'
import { formatDuration, formatActivityType } from '../../lib/format'
import { MountainActivityCard } from '../../components/MountainActivityCard'
import { MOUNTAIN_ACTIVITY_TYPES, SELF_POWERED_MOUNTAIN_TYPES, CYCLING_ACTIVITY_TYPES } from '../../lib/constants'

type DayStatus = 'completed' | 'adjusted' | 'rescheduled' | 'skipped' | 'planned' | 'missed' | 'today' | 'rest' | 'mountain' | 'cycling'

export interface DayCell {
  date: Date
  dateStr: string
  label: string
  isToday: boolean
  planned: PlannedWorkout | null
  templateSession: string | null
  templateDayType: 'gym' | 'rest' | 'mobility' | 'mountain' | 'cardio' | 'intervals' | null
  activities: Activity[]
  status: DayStatus
  displayLabel: string | null
}

const STATUS_BADGES: Record<DayStatus, { icon: string; label: string; color: string }> = {
  completed: { icon: 'OK', label: 'Done', color: 'text-accent-green' },
  adjusted: { icon: '~', label: 'Adjusted', color: 'text-accent-blue' },
  rescheduled: { icon: '↔', label: 'Moved', color: 'text-accent-purple' },
  skipped: { icon: 'X', label: 'Skipped', color: 'text-text-muted' },
  planned: { icon: '...', label: 'Planned', color: 'text-text-secondary' },
  missed: { icon: '!', label: 'Missed', color: 'text-accent-red' },
  today: { icon: '>', label: 'Today', color: 'text-accent-green' },
  rest: { icon: '-', label: 'Rest', color: 'text-text-dim' },
  mountain: { icon: '^', label: 'Mountain', color: 'text-mountain' },
  cycling: { icon: '🚲', label: 'Cycling', color: 'text-accent-blue' },
}

const RPE_LABELS: Record<number, string> = {
  0: 'Rest', 1: 'Very light', 2: 'Light', 3: 'Moderate', 4: 'Somewhat hard',
  5: 'Hard', 6: '', 7: 'Very hard', 8: '', 9: '', 10: 'Maximal',
}

interface Props {
  dayCells: DayCell[]
  hasPlannedWorkouts: boolean
  canReschedule: (cell: DayCell) => boolean
  onReschedule: (cell: DayCell) => void
  canMarkDone: (cell: DayCell) => boolean
  onMarkDone: (cell: DayCell, srpe: number) => void
  markDoneLoading: number | null
}

export function ScheduleGrid({ dayCells, hasPlannedWorkouts, canReschedule, onReschedule, canMarkDone, onMarkDone, markDoneLoading }: Props) {
  const [expandedDay, setExpandedDay] = useState<string | null>(null)
  const [rpePickerFor, setRpePickerFor] = useState<string | null>(null)
  const [selectedRPE, setSelectedRPE] = useState<number | null>(null)

  return (
    <Card title="Schedule">
      {!hasPlannedWorkouts && (
        <div className="text-[11px] text-text-dim mb-3 italic">
          Showing template — sessions not yet generated for this week
        </div>
      )}
      <div className="space-y-1.5">
        {dayCells.map((cell) => {
          const badge = STATUS_BADGES[cell.status]
          const hasMountainActivity = cell.status === 'mountain' && cell.activities.length > 0
          const hasCyclingActivity = cell.status === 'cycling' && cell.activities.length > 0
          const isExpandable = cell.planned?.workout_definition?.exercises?.length || hasMountainActivity || hasCyclingActivity
          const isExpanded = expandedDay === cell.dateStr
          const sessionName = cell.displayLabel
            ?? cell.planned?.workout_definition?.session_name
            ?? cell.templateSession
            ?? (cell.templateDayType === 'mobility' ? 'Mobility'
              : cell.templateDayType === 'mountain' ? 'Mountain day'
              : cell.templateDayType === 'cardio' ? 'Cardio'
              : cell.templateDayType === 'intervals' ? 'Intervals'
              : 'Rest')

          const completedActivity = cell.activities.find((a) =>
            cell.planned?.actual_garmin_activity_id
              ? a.garmin_activity_id === cell.planned.actual_garmin_activity_id
              : false
          ) ?? cell.activities[0]

          const showRpePicker = rpePickerFor === cell.dateStr

          return (
            <div
              key={cell.dateStr}
              className={`rounded-xl border px-3 py-2 ${
                cell.isToday
                  ? 'border-accent-green/40 bg-accent-green/5'
                  : 'border-border bg-bg-card'
              }`}
            >
              <button
                onClick={() => isExpandable && setExpandedDay(isExpanded ? null : cell.dateStr)}
                className={`w-full flex items-center gap-3 text-left ${isExpandable ? 'cursor-pointer' : 'cursor-default'}`}
              >
                <div className="w-10 shrink-0">
                  <div className={`text-[10px] uppercase tracking-wider font-semibold ${cell.isToday ? 'text-accent-green' : 'text-text-muted'}`}>
                    {cell.label}
                  </div>
                  <div className={`text-base font-bold font-data ${cell.isToday ? 'text-text-primary' : 'text-text-secondary'}`}>
                    {format(cell.date, 'd')}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold text-text-primary truncate">
                    {cell.status === 'cycling' && '🚲 '}{sessionName}
                  </div>
                  {completedActivity && (
                    <div className="text-[11px] text-text-muted truncate">
                      {formatDuration(completedActivity.duration_seconds)}
                      {CYCLING_ACTIVITY_TYPES.has(completedActivity.activity_type) ? (
                        <>
                          {completedActivity.distance_meters != null && completedActivity.distance_meters > 0 && (
                            <span className="ml-2">{(completedActivity.distance_meters / 1000).toFixed(1)} km</span>
                          )}
                          {completedActivity.avg_speed != null && completedActivity.avg_speed > 0 && (
                            <span className="ml-2">{(completedActivity.avg_speed * 3.6).toFixed(1)} km/h</span>
                          )}
                          {completedActivity.elevation_gain != null && completedActivity.elevation_gain > 0 && (
                            <span className="text-mountain ml-2">{Math.round(completedActivity.elevation_gain)}m</span>
                          )}
                        </>
                      ) : (
                        completedActivity.elevation_gain != null && completedActivity.elevation_gain > 0 && (
                          <span className="text-mountain ml-2">{Math.round(completedActivity.elevation_gain)}m</span>
                        )
                      )}
                    </div>
                  )}
                </div>
                <div className="shrink-0 flex items-center gap-2">
                  <span className={`text-[11px] font-semibold ${badge.color}`}>
                    {badge.label}
                  </span>
                  {isExpandable ? (
                    isExpanded ? <ChevronUp size={14} className="text-text-muted" /> : <ChevronDown size={14} className="text-text-muted" />
                  ) : null}
                </div>
              </button>

              {isExpanded && cell.planned?.workout_definition && !hasMountainActivity && (
                <div className="mt-3 pt-3 border-t border-border-subtle space-y-1.5">
                  {cell.planned.workout_definition.warmup?.length > 0 && (
                    <div className="text-[11px] text-text-muted mb-2">
                      Warmup: {cell.planned.workout_definition.warmup.map((w) => w.name).join(', ')}
                    </div>
                  )}
                  {(cell.planned.workout_definition.exercises ?? []).map((ex: PlannedExercise, i: number) => (
                    <div key={i} className="flex items-baseline justify-between text-[12px]">
                      <span className="text-text-primary truncate pr-2">{ex.name}</span>
                      <span className="text-text-muted shrink-0 font-data">
                        {ex.sets}×{ex.reps}
                        {ex.weight_kg != null && ` @ ${ex.weight_kg}kg`}
                      </span>
                    </div>
                  ))}
                  {cell.planned.workout_definition.rpe_range && (
                    <div className="text-[11px] text-text-dim mt-2">
                      Target RPE: {cell.planned.workout_definition.rpe_range[0]}–{cell.planned.workout_definition.rpe_range[1]}
                    </div>
                  )}
                  {cell.planned.adjustment_reason && (
                    <div className="text-[11px] text-accent-blue mt-2 italic">
                      Adjusted: {cell.planned.adjustment_reason}
                    </div>
                  )}

                  {/* RPE picker (shown after tapping Mark as done) */}
                  {showRpePicker && (
                    <div className="mt-3 pt-2 border-t border-border-subtle">
                      <div className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold mb-2">Session RPE</div>
                      <div className="text-[12px] text-text-secondary mb-2">How hard was this session?</div>
                      <div className="flex gap-1">
                        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => (
                          <button
                            key={v}
                            onClick={(e) => { e.stopPropagation(); setSelectedRPE(v) }}
                            className={`flex-1 h-8 rounded-lg text-[10px] font-semibold transition-all ${
                              selectedRPE === v
                                ? v >= 8 ? 'bg-accent-red/20 text-accent-red border border-accent-red/40'
                                  : v >= 5 ? 'bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/40'
                                  : 'bg-accent-green/20 text-accent-green border border-accent-green/40'
                                : 'bg-bg-primary/50 text-text-muted border border-transparent'
                            }`}
                          >
                            {v}
                          </button>
                        ))}
                      </div>
                      {selectedRPE != null && RPE_LABELS[selectedRPE] && (
                        <div className="text-[10px] text-text-dim mt-1 text-center">{RPE_LABELS[selectedRPE]}</div>
                      )}
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            if (selectedRPE != null) {
                              onMarkDone(cell, selectedRPE)
                              setRpePickerFor(null)
                              setSelectedRPE(null)
                            }
                          }}
                          disabled={selectedRPE == null || markDoneLoading === cell.planned?.id}
                          className="flex-1 py-2 rounded-xl bg-accent-green/15 text-accent-green text-[12px] font-semibold
                                     disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                        >
                          {markDoneLoading === cell.planned?.id ? 'Saving...' : 'Done'}
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); setRpePickerFor(null); setSelectedRPE(null) }}
                          className="px-3 py-2 rounded-xl text-text-muted text-[12px] font-medium"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Action buttons (hidden when RPE picker is shown) */}
                  {!showRpePicker && (canReschedule(cell) || canMarkDone(cell)) && (
                    <div className="mt-3 pt-2 border-t border-border-subtle flex items-center gap-4">
                      {canMarkDone(cell) && (
                        <button
                          onClick={(e) => { e.stopPropagation(); setRpePickerFor(cell.dateStr); setSelectedRPE(null) }}
                          className="flex items-center gap-1.5 text-[12px] text-accent-green font-medium"
                        >
                          <Check size={13} />
                          Mark as done
                        </button>
                      )}
                      {canReschedule(cell) && (
                        <button
                          onClick={(e) => { e.stopPropagation(); onReschedule(cell) }}
                          className="flex items-center gap-1.5 text-[12px] text-accent-blue font-medium"
                        >
                          <ArrowRightLeft size={13} />
                          Move to another day
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}

              {isExpanded && hasMountainActivity && (
                <div className="mt-3 pt-3 border-t border-border-subtle">
                  {cell.activities
                    .filter((a) => SELF_POWERED_MOUNTAIN_TYPES.has(a.activity_type) || MOUNTAIN_ACTIVITY_TYPES.has(a.activity_type))
                    .map((a, i) => (
                      <MountainActivityCard key={a.garmin_activity_id ?? i} activity={a} showDate={false} />
                    ))}
                </div>
              )}

              {isExpanded && hasCyclingActivity && (
                <div className="mt-3 pt-3 border-t border-border-subtle space-y-2">
                  {cell.activities
                    .filter((a) => CYCLING_ACTIVITY_TYPES.has(a.activity_type))
                    .map((a, i) => (
                      <div key={a.garmin_activity_id ?? i} className="text-[12px]">
                        <div className="font-semibold text-text-primary">
                          {a.activity_name || formatActivityType(a.activity_type)}
                        </div>
                        <div className="flex flex-wrap gap-3 text-text-secondary mt-1">
                          <span>{formatDuration(a.duration_seconds)}</span>
                          {a.distance_meters != null && a.distance_meters > 0 && (
                            <span>{(a.distance_meters / 1000).toFixed(1)} km</span>
                          )}
                          {a.avg_speed != null && a.avg_speed > 0 && (
                            <span>{(a.avg_speed * 3.6).toFixed(1)} km/h avg</span>
                          )}
                          {a.elevation_gain != null && a.elevation_gain > 0 && (
                            <span className="text-mountain">{Math.round(a.elevation_gain)}m ↑</span>
                          )}
                          {a.avg_hr != null && <span>{a.avg_hr} bpm avg</span>}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
