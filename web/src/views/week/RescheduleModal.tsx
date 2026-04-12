import type { DayCell } from './ScheduleGrid'
import { format, isBefore, parseISO } from 'date-fns'

interface Props {
  source: DayCell
  dayCells: DayCell[]
  today: Date
  target: string | null
  loading: boolean
  onTargetChange: (dateStr: string | null) => void
  onConfirm: () => void
  onClose: () => void
}

export function RescheduleModal({ source, dayCells, today, target, loading, onTargetChange, onConfirm, onClose }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60"
      onClick={() => { if (!loading) onClose() }}
    >
      <div
        className="w-full max-w-lg glass-card rounded-t-[20px] rounded-b-none p-5 pb-8 animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-[590] text-text-primary">Move session</h3>
          <button onClick={() => { if (!loading) onClose() }} className="text-text-muted text-sm px-2 py-1">Cancel</button>
        </div>
        <div className="text-[13px] text-text-secondary mb-4">
          <span className="font-semibold text-text-primary">
            {source.planned?.workout_definition?.session_name
              ?? source.planned?.session_name
              ?? source.templateSession}
          </span>
          {' '}from {format(source.date, 'EEEE, MMM d')}
        </div>
        <div className="grid grid-cols-7 gap-1.5">
          {dayCells.map((cell) => {
            const isSource = cell.dateStr === source.dateStr
            const isPast = isBefore(cell.date, today) && !cell.isToday
            const isCompleted = cell.status === 'completed'
            const disabled = isSource || isPast || isCompleted || loading
            const hasSwappableWorkout = cell.planned != null
              && cell.planned.status !== 'skipped' && cell.planned.status !== 'completed'
              && cell.status !== 'mountain'
            const isSelected = target === cell.dateStr
            return (
              <button
                key={cell.dateStr}
                disabled={disabled}
                onClick={() => !disabled && onTargetChange(isSelected ? null : cell.dateStr)}
                className={`flex flex-col items-center py-2.5 rounded-xl border transition-colors ${
                  isSource
                    ? 'border-accent-blue/40 bg-accent-blue/10 opacity-50'
                    : isSelected
                      ? 'border-accent-green bg-accent-green/15'
                    : disabled
                      ? 'border-border bg-bg-card opacity-30 cursor-not-allowed'
                      : hasSwappableWorkout
                        ? 'border-accent-yellow/40 bg-accent-yellow/5 active:bg-accent-yellow/15'
                        : 'border-border bg-bg-card active:bg-accent-green/10 active:border-accent-green/40'
                }`}
              >
                <div className={`text-[10px] uppercase tracking-wider font-semibold ${cell.isToday ? 'text-accent-green' : 'text-text-muted'}`}>
                  {cell.label}
                </div>
                <div className={`text-base font-bold font-data ${isSource ? 'text-accent-blue' : isSelected ? 'text-accent-green' : 'text-text-primary'}`}>
                  {format(cell.date, 'd')}
                </div>
                {!isSource && hasSwappableWorkout && !disabled && !isSelected && (
                  <div className="text-[9px] text-accent-yellow font-semibold mt-0.5">swap</div>
                )}
                {isSelected && <div className="text-[9px] text-accent-green font-semibold mt-0.5">to</div>}
                {isSource && <div className="text-[9px] text-accent-blue font-semibold mt-0.5">from</div>}
              </button>
            )
          })}
        </div>
        {target && (
          <button
            onClick={onConfirm}
            disabled={loading}
            className="w-full mt-4 py-2.5 rounded-xl bg-accent-green text-bg-primary font-semibold text-[14px] disabled:opacity-50 transition-colors active:bg-accent-green/80"
          >
            {loading ? 'Moving...' : `Move to ${format(parseISO(target), 'EEEE')}`}
          </button>
        )}
        <div className="text-[11px] text-text-dim text-center mt-2">
          Garmin push will happen at next daily coaching run
        </div>
      </div>
    </div>
  )
}
