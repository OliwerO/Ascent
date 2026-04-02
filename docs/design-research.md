# Ascent — Dark-Mode Health Dashboard Design Research

> Created: 2026-04-02
> Purpose: Reference document for implementing design improvements to the Ascent React + Tailwind mobile-first dashboard

---

## 1. Dark-Mode Dashboard Best Practices

### Background Color Hierarchy

The most effective health/fitness dashboards (Whoop, Oura, Garmin Connect, Apple Health) use a layered dark background system rather than pure black. Pure black (`#000000`) causes excessive contrast against white text and makes cards feel like they're floating in a void.

**Recommended background layers:**

| Layer | Purpose | Hex | Tailwind |
|-------|---------|-----|----------|
| Base / screen | App background | `#0A0A0F` or `#0C0D12` | `bg-[#0C0D12]` |
| Surface / card | Card backgrounds | `#141419` or `#16171D` | `bg-[#16171D]` |
| Elevated surface | Modals, popovers, active states | `#1C1D24` or `#1E1F27` | `bg-[#1E1F27]` |
| Subtle surface | Hover states, input fields | `#22232B` | `bg-[#22232B]` |

**Why not pure black?** Whoop and Oura both use very dark blue-gray rather than pure black. This gives depth, avoids OLED "smearing" artifacts during scrolling, and makes the layered card system perceptible. Pure black also creates an uncomfortable high-contrast ratio against white text (21:1) that causes eye strain.

### Contrast Ratios

- **Primary text** (key numbers, headings): `#F0F0F5` or `#EAEAF0` on `#0C0D12` = ~16:1 ratio. Well above WCAG AAA (7:1).
- **Secondary text** (labels, descriptions): `#9394A1` or `#8E8FA0` on `#0C0D12` = ~5.5:1. Meets WCAG AA (4.5:1).
- **Tertiary text** (timestamps, disabled): `#5C5D6E` on `#0C0D12` = ~3.2:1. Meets WCAG AA for large text only (3:1). Use at 14px+ only.
- **Never** go below 3:1 contrast for any text, even decorative labels.

### Borders vs Shadows

On dark backgrounds, shadows are nearly invisible. Every major dark-mode health app uses **borders** rather than shadows to define card edges.

- **Card borders:** 1px solid with very subtle opacity. `border border-white/[0.06]` or `border border-[#2A2B35]`.
- **Dividers within cards:** `border-b border-white/[0.04]` — even subtler than card borders.
- **Active/selected states:** Slightly brighter border `border-white/[0.12]` or a colored accent border.
- **Drop shadows:** Only useful for elevated overlays (modals, bottom sheets). Use `shadow-xl shadow-black/40` sparingly.

### Patterns from Specific Apps

**Whoop:** Near-black background (`~#0A0A0A`), single accent color (strain green), cards with rounded corners, heavy use of circular gauges. Minimal chrome — data speaks.

**Oura:** Dark navy-black (`~#0D0E14`), muted accent colors that shift by data type (sleep=blue, readiness=green, activity=orange). Generous whitespace. Cards feel spacious.

**Garmin Connect:** Darker than most (`~#0B0C0F`), aggressive use of color-coded metrics. More dense than Oura/Whoop — packs more data per screen. Uses horizontal scrolling carousels for metric cards.

**Strava:** Slightly lighter dark (`~#1A1A2E`), orange accent throughout. Feed-based layout, not card-grid. Good model for activity stream but not for dashboard-style metrics.

**Apple Health:** Uses system dark mode (`#000000` on OLED), but each health category has a distinct color. Cards are generous with padding. Sparklines inside cards are a standout pattern.

---

## 2. Typography for Data-Dense UIs

### Font Stack

For a health dashboard, use a system font stack with a good tabular-figures variant:

```css
/* Primary (UI text) */
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', system-ui, sans-serif;

/* Numeric data */
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Rounded', 'SF Mono', 'Segoe UI', system-ui, sans-serif;
```

Alternatively, use **Inter** — it has excellent tabular figures and is free. Tailwind default sans works well if configured to Inter.

### Tabular Figures

This is critical for a data dashboard. Without tabular (monospaced-width) figures, numbers jump around as values change, making them harder to scan.

```css
/* Enable tabular figures */
font-variant-numeric: tabular-nums;

/* Tailwind */
className="tabular-nums"
```

Apply `tabular-nums` to all numeric displays: HRV values, sleep scores, weight, step counts, heart rate, percentages.

### Font Size Scale (Mobile-First)

| Element | Size | Weight | Line Height | Tailwind |
|---------|------|--------|-------------|----------|
| Hero metric (e.g., HRV number) | 36–40px | 700 (bold) | 1.1 | `text-4xl font-bold leading-tight` |
| Card title number (e.g., sleep score) | 28–32px | 600 (semibold) | 1.2 | `text-3xl font-semibold` |
| Secondary metric | 20–24px | 600 | 1.2 | `text-xl font-semibold` |
| Card heading label | 13–14px | 500 (medium) | 1.4 | `text-sm font-medium` |
| Body text / descriptions | 14–15px | 400 (normal) | 1.5 | `text-sm` or `text-[15px]` |
| Tertiary label / timestamp | 12px | 400 | 1.4 | `text-xs` |
| Chart axis labels | 10–11px | 400 | 1.3 | `text-[11px]` |

**Mobile minimums:**
- Never go below 11px for any text, including chart labels.
- Body text minimum: 14px. This is Apple's HIG recommendation.
- Touch-target labels: 14px minimum.

### Monospace vs Proportional

- **Proportional** (Inter, SF Pro): Use for all UI text, labels, headings.
- **Tabular-nums proportional**: Use for all standalone numeric displays (scores, metrics, stats). This gives even digit widths without the "code" aesthetic.
- **Monospace** (SF Mono, JetBrains Mono): Only for debugging, raw data views, or code. Not appropriate for the main dashboard.

### Making Numbers Scannable

1. **Size hierarchy is everything.** The most important number on a card should be 2-3x the size of its label. Whoop does this: the strain score is 36px, the label "STRAIN" is 11px.
2. **Color coding** the number itself (not just a dot or badge) reinforces meaning. A green "82" for sleep score is faster to parse than a white "82" next to a green dot.
3. **Unit suffixes** should be smaller and lighter. "72 bpm" — the "bpm" should be ~60% the size of "72" and a lighter color.
4. **Alignment:** Right-align columns of numbers. Left-align labels.

---

## 3. Color System for Health Data

### Semantic Status Colors

Health apps universally use a green-yellow-red system for status indication. On dark backgrounds, these need to be desaturated slightly to avoid being garish.

| Status | Meaning | Hex | Tailwind | Opacity on dark bg |
|--------|---------|-----|----------|--------------------|
| Excellent / optimal | Top-tier recovery, great sleep | `#34D399` | `text-emerald-400` | 100% for text, 12-15% for bg tint |
| Good | Normal / healthy range | `#4ADE80` | `text-green-400` | 100% for text, 12-15% for bg tint |
| Moderate / caution | Slightly off, pay attention | `#FBBF24` | `text-amber-400` | 100% for text, 10-12% for bg tint |
| Poor / warning | Below target, needs action | `#F87171` | `text-red-400` | 100% for text, 10-12% for bg tint |
| Critical | Significantly off baseline | `#EF4444` | `text-red-500` | 100% for text, 12% for bg tint |

**Important:** Use the 400-weight variants on dark backgrounds, not 500 or 600. The lighter variants have better contrast against dark surfaces without being overwhelming.

### Category Accent Colors

Each health data category should have a consistent color identity across the entire app:

| Category | Primary Color | Hex | Tailwind | Rationale |
|----------|--------------|-----|----------|-----------|
| Sleep | Indigo / Purple | `#818CF8` | `text-indigo-400` | Universal sleep association (night, calm) |
| HRV / Recovery | Blue | `#60A5FA` | `text-blue-400` | Clinical/health feel, calm |
| Heart Rate | Rose / Red | `#FB7185` | `text-rose-400` | Heart = red, universal |
| Strength / Training | Orange | `#FB923C` | `text-orange-400` | Energy, power, effort |
| Activity / Steps | Cyan / Teal | `#2DD4BF` | `text-teal-400` | Movement, fresh |
| Body Composition | Violet | `#A78BFA` | `text-violet-400` | Distinct from sleep indigo |
| Stress | Amber | `#FCD34D` | `text-amber-300` | Caution association |
| Nutrition | Lime / Green | `#A3E635` | `text-lime-400` | Food, health, fresh |
| Body Battery | Emerald | `#34D399` | `text-emerald-400` | Energy = green |

### Opacity Levels for Dark Backgrounds

When using accent colors as background tints (e.g., a subtle colored card background to indicate category):

| Use Case | Opacity | Example |
|----------|---------|---------|
| Background tint on card | 8–12% | `bg-indigo-500/10` |
| Background tint on badge/pill | 15–20% | `bg-emerald-500/15` |
| Border accent | 20–30% | `border-blue-400/25` |
| Chart fill area | 10–20% | `fill-opacity: 0.15` |
| Chart line / bar | 80–100% | Full color |
| Icon tint | 60–80% | Slightly muted |
| Hover state overlay | 5–8% | `hover:bg-white/5` |

### WCAG AA Contrast Requirements

- **Normal text (< 18px / < 14px bold):** 4.5:1 minimum contrast ratio.
- **Large text (>= 18px / >= 14px bold):** 3:1 minimum contrast ratio.
- **UI components and graphical objects:** 3:1 minimum.

Verified contrast ratios on `#0C0D12` background:

| Color | Hex | Ratio vs `#0C0D12` | Passes AA? |
|-------|-----|---------------------|------------|
| Emerald 400 | `#34D399` | 9.8:1 | Yes |
| Blue 400 | `#60A5FA` | 7.2:1 | Yes |
| Indigo 400 | `#818CF8` | 6.1:1 | Yes (large text AA at min) |
| Orange 400 | `#FB923C` | 8.3:1 | Yes |
| Rose 400 | `#FB7185` | 7.0:1 | Yes |
| Red 400 | `#F87171` | 6.5:1 | Yes |
| Amber 400 | `#FBBF24` | 10.2:1 | Yes |
| Violet 400 | `#A78BFA` | 6.8:1 | Yes |

All Tailwind 400-weight colors pass WCAG AA against our recommended dark background. Some 500-weight colors (like indigo-500 at `#6366F1`) drop to ~4.8:1 — still passing but tight. Stick with 400 for body text.

---

## 4. Card-Based Layouts

### Card Dimensions and Spacing

| Property | Value | Tailwind | Notes |
|----------|-------|----------|-------|
| Card border radius | 12–16px | `rounded-xl` (12px) or `rounded-2xl` (16px) | Oura uses ~16px, Whoop ~12px |
| Card inner padding | 16–20px | `p-4` (16px) or `p-5` (20px) | 16px on mobile, 20px on larger screens |
| Gap between cards | 12–16px | `gap-3` (12px) or `gap-4` (16px) | Consistent vertical rhythm |
| Card border | 1px | `border border-white/[0.06]` | Subtle, not distracting |
| Card background | Elevated surface | `bg-[#16171D]` | One step lighter than base |

### Inner Spacing Ratios

Within a card, maintain consistent internal hierarchy:

```
+--[ Card ]-------------------------------------------+
|  (16-20px padding all sides)                        |
|                                                     |
|  LABEL            (13px, medium, secondary color)   |
|  (4px gap)                                          |
|  72 bpm           (28-32px, semibold, primary)      |
|  (2px gap)                                          |
|  +3 from yesterday (12px, regular, tertiary/green)  |
|                                                     |
|  (12px gap before chart area if present)            |
|  ~~~~~~~~~~~~~ sparkline ~~~~~~~~~~~~~~~~           |
|  (chart height: 40-60px for inline sparklines)      |
|                                                     |
+-----------------------------------------------------+
```

**Key ratios:**
- Label-to-value gap: 4px (`gap-1`)
- Value-to-subtext gap: 2px (`gap-0.5`)
- Section-to-section gap within card: 12–16px (`gap-3` or `gap-4`)
- Chart area top margin: 12px

### Information Density Per Card

**Rule of thumb: One primary metric per card, up to 2-3 supporting details.**

Good card examples:
- **Sleep card:** Sleep score (hero), total duration, sleep stages bar, bed/wake times
- **HRV card:** Last night average (hero), 7-day trend sparkline, baseline range indicator, status label
- **Body weight card:** Current weight (hero), delta from last week, 30-day sparkline
- **Training readiness card:** Readiness score (hero), contributing factors (sleep, recovery, training load) as small sub-metrics

Bad card examples:
- Cramming HRV + sleep + resting HR + Body Battery into one card (too many competing hero metrics)
- A card with only a label and number but no trend or context (too sparse, wastes space)

### Expandable / Disclosure Sections

Use expandable sections when:
- A card has a clear "summary" and "detail" mode (e.g., sleep: show score at top, expand to see full stage breakdown and timeline)
- Data is useful but not always needed (e.g., heart rate zones from yesterday's workout)
- The detail view would make the card > 200px tall in collapsed state

Implementation pattern:
```jsx
// Collapsed: show hero metric + label
// Expanded: show full breakdown
<Card>
  <CardHeader onClick={toggle}>
    <Label>Sleep</Label>
    <HeroMetric>82</HeroMetric>
    <ChevronIcon rotated={expanded} />
  </CardHeader>
  {expanded && (
    <CardDetail>
      {/* Stage breakdown, timeline, detailed stats */}
    </CardDetail>
  )}
</Card>
```

Use a subtle animation: `transition-all duration-200 ease-out`. Height animation with `overflow-hidden` and `max-height` or use Headless UI `Disclosure` component.

### Card Grid Layout

For mobile (primary use case):
- **Single column**, full width minus safe area padding
- Cards stack vertically with 12px gap
- Horizontal scroll only for related small metric pills (e.g., a row of "Steps | Floors | Calories" mini-cards)

For tablet/desktop:
- 2-column grid for secondary metrics
- Hero/summary card spans full width at top
- `grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4`

---

## 5. Mobile-First Responsive Patterns

### Touch Targets

Apple Human Interface Guidelines and WCAG 2.1 require:

| Element | Minimum Size | Recommended | Notes |
|---------|-------------|-------------|-------|
| Tappable button | 44x44px | 48x48px | Apple HIG minimum |
| Icon button (no label) | 44x44px | 48x48px | Includes padding around icon |
| List row | 44px height | 48-56px | Include vertical padding |
| Tab bar item | 44x44px | 49pt x 49pt | iOS standard |
| Inline link / text button | 44px tap area | — | Use padding to extend hit area beyond text |

In Tailwind:
```jsx
// Minimum touch target
className="min-h-[44px] min-w-[44px]"

// Recommended
className="min-h-[48px] min-w-[48px] flex items-center justify-center"

// Extending tap area beyond visual bounds
className="relative after:absolute after:inset-[-8px] after:content-['']"
```

### Safe Area Handling

iPhone has notch/Dynamic Island at top and home indicator at bottom. The app must respect these.

```css
/* Apply safe area insets */
padding-top: env(safe-area-inset-top);
padding-bottom: env(safe-area-inset-bottom);
padding-left: env(safe-area-inset-left);
padding-right: env(safe-area-inset-right);

/* Tailwind (with plugin or custom values) */
/* For the outer page container: */
className="pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]"
```

Also add to `index.html`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

The `viewport-fit=cover` is essential — without it, iOS adds its own padding and you can't control the safe area yourself.

### Bottom Navigation

Whoop, Oura, and Garmin Connect all use a bottom tab bar. This is the correct pattern for a mobile health dashboard.

**Recommended structure:**

```
+--[ Screen Content ]--+
|                      |
|  (scrollable area)   |
|                      |
|                      |
+----------------------+
| [Home] [Trends] [+] |  <- Bottom nav, 56-64px height
+--[ safe area pad ]---+
```

- **Height:** 56px content + safe area bottom padding (~34px on modern iPhone) = ~90px total
- **Background:** Match card surface color or slightly lighter. `bg-[#16171D]/95 backdrop-blur-xl` for a frosted effect.
- **Icons:** 24px, with 12px label below. Active state = accent color, inactive = `text-[#5C5D6E]`.
- **Border top:** `border-t border-white/[0.06]` — subtle separator.
- **Position:** `fixed bottom-0 left-0 right-0` with `pb-[env(safe-area-inset-bottom)]`.

### Scrolling Behavior

- **Main content:** Standard vertical scroll. No custom scroll physics — iOS native momentum scrolling is excellent and users expect it.
- **Header:** Can be sticky or scroll away. For a dashboard, a **collapsing header** works well — show a greeting/date header that collapses to just the date as you scroll down.
- **Pull-to-refresh:** Expected behavior for a data dashboard. Implement with a subtle loading indicator at top.
- **Scroll padding at bottom:** Add `pb-24` (96px) or more to the scroll container to ensure the last card isn't hidden behind the bottom nav.

```jsx
<main className="pb-28 pt-[env(safe-area-inset-top)]">
  {/* Dashboard content */}
</main>
<BottomNav className="fixed bottom-0 inset-x-0 pb-[env(safe-area-inset-bottom)]" />
```

### How Whoop and Oura Handle Mobile Layouts

**Whoop:**
- Single metric hero at top (strain gauge, circular)
- Horizontal scroll row of secondary metric cards (recovery, sleep, HRV)
- Vertical feed of recent activities below
- Bottom nav: Overview, Coaching, Health, Community, More
- Very generous vertical spacing — not afraid of whitespace
- Black/dark background with green as primary accent
- Uses full-screen modal-style drill-downs (not inline expansion)

**Oura:**
- Three "ring" scores at top (Readiness, Sleep, Activity) as horizontal scroll
- Tap a ring to drill into detailed view
- Below rings: vertical card stack with daily insights
- Cards use category-colored left accent borders
- Bottom nav: Home, Explore, +, Tags, Profile
- Generous padding (20px+), rounded cards (16px radius)
- Muted, calm color palette — never loud

**Garmin Connect:**
- "My Day" dashboard at top with key stats in a compact grid
- Horizontal scroll carousels for different categories
- More information-dense than Whoop/Oura — targets data-oriented users
- Uses colored pill/badge indicators for status
- Heavier use of iconography
- Bottom nav: My Day, Calendar, Activities, Challenges, More

### Recommended Layout for Ascent

Given that Ascent is a personal dashboard with dense health data:

```
+--[ Status Bar ]------+
|                      |
|  Good morning, Oli   |  <- Greeting + date, collapses on scroll
|  Wednesday, Apr 2    |
|                      |
|  +--[Recovery]-----+ |  <- Hero card: Recovery triad
|  | HRV  Sleep  BB  | |     (HRV, sleep score, Body Battery)
|  | 62   84    72   | |     Color-coded status per metric
|  +-----------------+ |
|                      |
|  +--[Readiness]----+ |  <- Training readiness card
|  | 78  Ready       | |     With contributing factors
|  +-----------------+ |
|                      |
|  +--[Sleep]--------+ |  <- Expandable sleep detail
|  | 7h 42m  Score:84| |
|  | ~~sparkline~~   | |
|  +-----------------+ |
|                      |
|  +--[HRV Trend]---+ |  <- 7-day trend
|  | 62ms  ▲ +4     | |
|  | ~~sparkline~~   | |
|  +-----------------+ |
|                      |
|  +--[Body]--------+  |  <- Weight + composition
|  | 82.4 kg  -0.3  | |
|  +-----------------+ |
|                      |
|  +--[Training]----+  |  <- Today's plan or last session
|  | Upper Body A   | |
|  | 19:00 scheduled| |
|  +-----------------+ |
|                      |
|  (pb-28 spacer)      |
+----------------------+
| [Home][Trends][Plan] |  <- Bottom nav
+--[safe-area]--------+
```

### Page Width and Horizontal Padding

- **Container max-width:** None on mobile. On tablet/desktop: `max-w-lg` (512px) centered.
- **Horizontal padding:** 16px on each side (`px-4`). This is the iOS standard margin.
- **Content width:** `100vw - 32px` on mobile = 343px on iPhone 14 (390px screen).

### Performance Considerations

- **Lazy load** cards below the fold. The recovery triad and readiness card load immediately; sleep detail, trends, and body composition can load as the user scrolls.
- **Skeleton screens** during data loading — not spinners. Show card outlines with animated placeholder bars.
- **Chart rendering:** Use a lightweight library (e.g., recharts with minimal config, or custom SVG sparklines). Avoid heavy charting libraries for simple sparklines.
- **Image optimization:** If showing any images, use `next/image` or equivalent with WebP format.

---

## Summary: Quick Reference for Implementation

### Tailwind Theme Extension

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        surface: {
          base: '#0C0D12',
          card: '#16171D',
          elevated: '#1E1F27',
          subtle: '#22232B',
        },
        text: {
          primary: '#F0F0F5',
          secondary: '#9394A1',
          tertiary: '#5C5D6E',
        },
        // Category accents use Tailwind defaults:
        // indigo-400, blue-400, rose-400, orange-400, etc.
      },
      borderColor: {
        DEFAULT: 'rgba(255, 255, 255, 0.06)',
      },
    },
  },
}
```

### Design Tokens Summary

| Token | Value |
|-------|-------|
| Base background | `#0C0D12` |
| Card background | `#16171D` |
| Primary text | `#F0F0F5` |
| Secondary text | `#9394A1` |
| Tertiary text | `#5C5D6E` |
| Card border | `rgba(255,255,255,0.06)` |
| Card radius | 12–16px |
| Card padding | 16px mobile, 20px tablet+ |
| Card gap | 12px |
| Page horizontal padding | 16px |
| Bottom nav height | 56px + safe area |
| Min touch target | 44x44px |
| Hero metric size | 36–40px bold |
| Card metric size | 28–32px semibold |
| Body text minimum | 14px |
| Chart label minimum | 11px |
| Numeric display | `tabular-nums` always |
| Sleep accent | indigo-400 `#818CF8` |
| HRV accent | blue-400 `#60A5FA` |
| Heart rate accent | rose-400 `#FB7185` |
| Training accent | orange-400 `#FB923C` |
| Activity accent | teal-400 `#2DD4BF` |
| Body comp accent | violet-400 `#A78BFA` |
| Good status | emerald-400 `#34D399` |
| Caution status | amber-400 `#FBBF24` |
| Warning status | red-400 `#F87171` |
