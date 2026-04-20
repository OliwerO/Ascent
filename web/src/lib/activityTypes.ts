// Canonical list of mountain activity types — import everywhere, don't duplicate
export const MOUNTAIN_ACTIVITY_TYPES = new Set([
  'backcountry_skiing',
  'backcountry_snowboarding',
  'hiking',
  'mountaineering',
  'splitboarding',
  'resort_skiing',
  'resort_snowboarding',
  'ski_touring',
  'hang_gliding',
])

// Cycling activity types
export const CYCLING_ACTIVITY_TYPES = new Set([
  'road_biking',
  'cycling',
  'gravel_cycling',
])

// Self-powered mountain activities (exclude resort/lift-assisted)
export const SELF_POWERED_MOUNTAIN_TYPES = new Set([
  'backcountry_skiing',
  'backcountry_snowboarding',
  'hiking',
  'mountaineering',
  'splitboarding',
  'ski_touring',
])
