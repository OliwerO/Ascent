import { Card } from '../../components/Card'
import { CollapsibleSection } from '../../components/CollapsibleSection'
import { metricColor, hrvStatusInfo } from '../../lib/colors'
import { formatDuration, formatActivityType } from '../../lib/format'
import { Heart, Clock, Flame, ArrowUpRight, TrendingUp, Activity as ActivityIcon } from 'lucide-react'
import type { Activity, DailyMetrics } from '../../lib/types'

interface RecoverySignalsProps {
  hrvVal: number | null
  hrvWeeklyAvg: number | null
  hrvStatus: string | null | undefined
  sleepHours: number | null
  sleepBelowCount: number
  bbHigh: number | null
  bbLowest: number | null
  readiness: number | null
}

interface WeeklyLoadProps {
  thisWeekLoad: { gym: number; mountain: number; cycling: number }
  lastWeekLoad: { gym: number; mountain: number; cycling: number }
  thisWeekElev: number
  lastWeekElev: number
  loadChangePct: number | null
  prevTrainingLoad: number
}

interface Props {
  recovery: RecoverySignalsProps
  weeklyLoad: WeeklyLoadProps
  todayMetrics: DailyMetrics | null
  rhrTrend: string | null
  rhr7dAvg: number | null
  rhrElevated: boolean
  lastActivity: Activity | null
  programEnded: boolean
  block: number
  week: number
}

export function SecondaryInfo({
  recovery, weeklyLoad, todayMetrics, rhrTrend, rhr7dAvg, rhrElevated,
  lastActivity, programEnded, block, week,
}: Props) {
  const hrvInfo = hrvStatusInfo(recovery.hrvStatus)

  return (
    <CollapsibleSection title="Details" defaultOpen={false}>
      {/* Recovery Signals */}
      <div className="grid grid-cols-2 gap-2">
        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">HRV</span>
            <span className={`text-[11px] font-semibold ${hrvInfo.color}`}>{hrvInfo.label}</span>
          </div>
          <div className={`data-value-md font-data ${hrvInfo.color}`}>
            {recovery.hrvVal ?? '—'}<span className="text-[13px] font-normal text-text-muted ml-1">ms</span>
          </div>
          {recovery.hrvWeeklyAvg != null && recovery.hrvVal != null && (
            <div className="text-[12px] text-text-muted mt-1.5">
              {recovery.hrvVal >= recovery.hrvWeeklyAvg ? '↑ above' : '↓ below'} {recovery.hrvWeeklyAvg}ms avg
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Sleep</span>
            {recovery.sleepBelowCount > 0 && (
              <span className="text-[11px] text-accent-red font-semibold">{recovery.sleepBelowCount}×&lt;6h</span>
            )}
          </div>
          <div className={`data-value-md font-data ${metricColor(recovery.sleepHours, 7, 6)}`}>
            {recovery.sleepHours ?? '—'}<span className="text-[13px] font-normal text-text-muted ml-1">h</span>
          </div>
          <div className="text-[12px] text-text-muted mt-1.5">Target 7-8h</div>
        </Card>
      </div>

      {/* Garmin estimates */}
      <div className="grid grid-cols-2 gap-2">
        <Card className="opacity-60">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-[0.06em] font-semibold">Body Battery</span>
            <span className="text-[9px] text-text-dim">(est.)</span>
          </div>
          <div className={`text-lg font-bold font-data ${metricColor(recovery.bbHigh, 60, 30)}`}>
            {recovery.bbHigh ?? '—'}
          </div>
          <div className="text-[11px] text-text-dim">
            {recovery.bbLowest != null
              ? `Low ${recovery.bbLowest} · Range ${(recovery.bbHigh ?? 0) - recovery.bbLowest}`
              : ''}
          </div>
        </Card>

        <Card className="opacity-60">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px] text-text-muted uppercase tracking-[0.06em] font-semibold">Readiness</span>
            <span className="text-[9px] text-text-dim">(est.)</span>
          </div>
          <div className={`text-lg font-bold font-data ${metricColor(recovery.readiness, 60, 40)}`}>
            {recovery.readiness ?? '—'}
          </div>
          <div className="text-[11px] text-text-dim">
            {recovery.readiness != null && recovery.readiness >= 60 ? 'Ready' : recovery.readiness != null && recovery.readiness >= 40 ? 'Borderline' : recovery.readiness != null ? 'Low' : ''}
          </div>
        </Card>
      </div>

      {/* Weekly Load */}
      <Card>
        <div className="flex items-center gap-2 mb-3">
          <ActivityIcon size={15} className="text-accent-purple" />
          <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Weekly Load</span>
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-[14px]">
          <div>
            <span className="text-text-primary font-semibold">{formatDuration(weeklyLoad.thisWeekLoad.gym)}</span>
            <span className="text-text-muted text-[12px] ml-1">gym</span>
          </div>
          <div>
            <span className="text-text-primary font-semibold">{formatDuration(weeklyLoad.thisWeekLoad.mountain)}</span>
            <span className="text-text-muted text-[12px] ml-1">mountain</span>
          </div>
          {weeklyLoad.thisWeekLoad.cycling > 0 && (
            <div>
              <span className="text-text-primary font-semibold">{formatDuration(weeklyLoad.thisWeekLoad.cycling)}</span>
              <span className="text-text-muted text-[12px] ml-1">cycling</span>
            </div>
          )}
          <div>
            <span className="text-text-primary font-semibold">{Math.round(weeklyLoad.thisWeekElev).toLocaleString()}m</span>
            <span className="text-text-muted text-[12px] ml-1">elev</span>
          </div>
          {weeklyLoad.loadChangePct != null && (
            <span className={`text-[12px] font-semibold ${
              Math.abs(weeklyLoad.loadChangePct) < 15 ? 'text-accent-green' : Math.abs(weeklyLoad.loadChangePct) < 25 ? 'text-accent-yellow' : 'text-accent-red'
            }`}>
              {weeklyLoad.loadChangePct >= 0 ? '+' : ''}{weeklyLoad.loadChangePct}% vs last wk
            </span>
          )}
        </div>
        {weeklyLoad.prevTrainingLoad > 0 && (
          <div className="text-[12px] text-text-muted mt-1.5">
            Last week: {formatDuration(weeklyLoad.lastWeekLoad.gym)} gym · {formatDuration(weeklyLoad.lastWeekLoad.mountain)} mountain
            {weeklyLoad.lastWeekLoad.cycling > 0 ? ` · ${formatDuration(weeklyLoad.lastWeekLoad.cycling)} cycling` : ''} · {Math.round(weeklyLoad.lastWeekElev).toLocaleString()}m
          </div>
        )}
      </Card>

      {/* Resting HR */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Heart size={15} className="text-heart" />
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Resting HR</span>
            <span className="text-[15px] font-bold font-data text-text-primary">
              {todayMetrics?.resting_hr ?? '--'} bpm
            </span>
            {rhrTrend && (
              <span className={`text-[11px] font-medium ${rhrElevated ? 'text-accent-yellow' : 'text-text-muted'}`}>
                {rhrTrend}
              </span>
            )}
          </div>
          {rhr7dAvg != null && (
            <span className="text-[11px] text-text-muted">
              7d avg: {Math.round(rhr7dAvg)}bpm
            </span>
          )}
        </div>
      </Card>

      {/* Latest Activity */}
      {lastActivity && (
        <Card>
          <div className="flex items-center gap-2 mb-2">
            {(lastActivity.elevation_gain ?? 0) > 0
              ? <TrendingUp size={15} className="text-mountain" />
              : <ActivityIcon size={15} className="text-gym" />
            }
            <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">Latest Activity</span>
          </div>
          <div className="text-[16px] font-[590] text-text-primary leading-tight">
            {lastActivity.activity_name || formatActivityType(lastActivity.activity_type)}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[13px] text-text-secondary">
            {lastActivity.duration_seconds && (
              <span className="flex items-center gap-1.5"><Clock size={12} className="text-text-muted" />{formatDuration(lastActivity.duration_seconds)}</span>
            )}
            {(lastActivity.elevation_gain ?? 0) > 0 && (
              <span className="flex items-center gap-1.5"><ArrowUpRight size={12} className="text-mountain" />{Math.round(lastActivity.elevation_gain!)}m</span>
            )}
            {lastActivity.calories != null && (
              <span className="flex items-center gap-1.5"><Flame size={12} className="text-accent-orange" />{lastActivity.calories} kcal</span>
            )}
            {lastActivity.avg_hr != null && (
              <span className="flex items-center gap-1.5"><Heart size={12} className="text-heart" />{lastActivity.avg_hr} bpm</span>
            )}
          </div>
        </Card>
      )}

      {/* Program Progress */}
      <Card>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] text-text-muted uppercase tracking-[0.06em] font-semibold">
            {programEnded ? 'Program Complete' : `${block === 1 ? 'Base Rebuild' : 'Progression'} · Block ${block}`}
          </span>
          <span className="text-[15px] font-bold font-data text-accent-green">
            {programEnded ? '8/8' : <>{week}<span className="text-text-muted font-normal">/8</span></>}
          </span>
        </div>
        <div className="w-full bg-bg-elevated rounded-full h-1.5">
          <div
            className="bg-accent-green rounded-full h-1.5 transition-all duration-500"
            style={{ width: `${programEnded ? 100 : (week / 8) * 100}%` }}
          />
        </div>
      </Card>
    </CollapsibleSection>
  )
}
