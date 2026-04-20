// Centralized coaching state decision tree.
// Used by TodayView (top coaching card) and RecoveryView (recommendation card).
// Aligned with coaching-context.md decision matrix and KB rule #13 (multi-signal override).

export type CardState = 'green' | 'amber' | 'red'

export interface CoachingInputs {
  hrvStatus: string | null | undefined // 'BALANCED' | 'UNBALANCED' | 'LOW'
  hrvVal: number | null
  hrvWeeklyAvg: number | null
  sleepHoursLastNight: number | null
  sleep7dAvg: number | null
  wellnessComposite: number | null
  bodyBattery: number | null
  trainingReadiness: number | null
  rhrElevated: boolean
  // Recovery tip inputs (all optional for backwards compat)
  deepSleepPct: number | null
  remSleepPct: number | null
  poorSleepNights7d: number
  mountainDays3d: number
  isDeload: boolean
  lastSrpe: number | null
  soreness: number | null // wellness_soreness (1-5, lower = more sore)
}

export interface CoachingDecision {
  state: CardState
  label: string
  recommendation: string
  reasons: string[]
  recoveryTip: string | null
}

export function computeCoachingState(inputs: CoachingInputs): CoachingDecision {
  const {
    hrvStatus, hrvVal, hrvWeeklyAvg, sleepHoursLastNight, sleep7dAvg,
    wellnessComposite, bodyBattery, trainingReadiness, rhrElevated,
    deepSleepPct, remSleepPct, poorSleepNights7d, mountainDays3d,
    isDeload, lastSrpe,
  } = inputs

  const hrvStatusLow = hrvStatus?.toUpperCase() === 'LOW'
  const hrvUnbalanced = hrvStatus?.toUpperCase() === 'UNBALANCED'
  const hrvBelowBaseline = hrvVal != null && hrvWeeklyAvg != null && hrvVal < hrvWeeklyAvg * 0.85
  const sleepShort = sleepHoursLastNight != null && sleepHoursLastNight < 6
  const wellnessLow = wellnessComposite != null && wellnessComposite < 2.5
  const bbLow = bodyBattery != null && bodyBattery < 30
  const readinessLow = trainingReadiness != null && trainingReadiness < 40

  const reasons: string[] = []
  let state: CardState = 'green'

  // Multi-signal override (KB rule #13)
  if (wellnessLow) { state = 'red'; reasons.push(`Wellness score ${wellnessComposite!.toFixed(1)}/5`) }
  if (bbLow) { state = 'red'; reasons.push(`Body Battery ${bodyBattery}`) }
  if (readinessLow) { state = 'red'; reasons.push(`Training Readiness ${trainingReadiness}`) }

  if (state !== 'red') {
    if (hrvStatusLow) {
      state = 'red'
      reasons.push('HRV status: Low')
    } else if (hrvUnbalanced && sleepShort) {
      state = 'red'
      reasons.push('HRV unbalanced + sleep <6h')
    } else if (hrvUnbalanced) {
      state = 'amber'
      reasons.push('HRV status: Unbalanced')
    } else if (hrvBelowBaseline) {
      state = 'amber'
      reasons.push(`HRV ${hrvVal} vs baseline ${hrvWeeklyAvg}`)
    } else if (sleepShort) {
      state = 'amber'
      reasons.push(`Sleep ${sleepHoursLastNight!.toFixed(1)}h last night`)
    } else if (sleep7dAvg != null && sleep7dAvg < 7) {
      state = 'amber'
      reasons.push(`7d sleep avg ${sleep7dAvg.toFixed(1)}h`)
    } else if (rhrElevated) {
      state = 'amber'
      reasons.push('Resting HR elevated')
    }
  }

  const label =
    state === 'green' ? 'Good to train'
    : state === 'amber' ? 'Train with caution'
    : 'Consider rest or light session'

  // Autonomy-supportive framing per CLAUDE.md
  const recommendation =
    state === 'red'
      ? "I'd suggest rest or mobility today. Multiple recovery signals are degraded — pushing through usually backfires."
    : state === 'amber'
      ? "I'd train if the warmup feels good. Cap RPE around 6, cut accessory volume ~30%, and bail to mobility if it doesn't click."
      : "Full session as planned. Aim for the prescribed RPE and focus on quality."

  // Recovery tip — pick highest priority that applies (max 1)
  let recoveryTip: string | null = null
  if (deepSleepPct != null && deepSleepPct < 15) {
    recoveryTip = 'Deep sleep was low — cooler room, earlier screen cutoff, and consistent bedtime tend to help'
  } else if (remSleepPct != null && remSleepPct < 18) {
    recoveryTip = 'REM sleep trending low — alcohol, late caffeine, and irregular sleep times are common culprits'
  } else if (sleepHoursLastNight != null && sleepHoursLastNight < 6) {
    recoveryTip = 'Short sleep last night — a 20-min nap before training can partially compensate'
  } else if (mountainDays3d > 0) {
    recoveryTip = 'Hydration and protein intake support recovery after mountain days — 1.6-2.2g/kg/day protein target'
  } else if (isDeload) {
    recoveryTip = 'Deload week — extra sleep and light mobility maximize adaptation from the training block'
  } else if (lastSrpe != null && lastSrpe >= 8) {
    recoveryTip = 'Yesterday was a grinder — extra carbs and protein in the next 24h support recovery'
  } else if (poorSleepNights7d >= 3) {
    recoveryTip = 'Sleep has been short this week — even 30min earlier to bed compounds'
  }

  return { state, label, recommendation, reasons, recoveryTip }
}
