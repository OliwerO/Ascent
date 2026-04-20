# Ascent Design System

Inspired by **Linear** (precision, dark-native hierarchy) and **Bevel** (liquid glass,
radial gauges, vibrant glows on deep black). This file is the single reference for all
UI work — coding agents read it before writing any component.

---

## 1. Visual Theme & Atmosphere

Dark-native athlete dashboard. Near-black canvas where data emerges through luminance
layers and colored glows. Cards use **liquid glass** — translucent surfaces with subtle
backdrop blur, faint borders, and soft inner light. Status information uses **radial
gauges and colored arcs** (Bevel-style) rather than flat progress bars. Accent colors
are vibrant but controlled — they glow rather than shout.

**Key characteristics:**
- Deep black base (`#08090e`) with cool blue undertone
- Liquid glass cards: `backdrop-filter: blur(16px)` + translucent white bg + gradient borders
- Colored glow halos behind status indicators (8-15% opacity)
- Radial progress rings for key metrics (strain, recovery, sleep quality)
- Inter Variable with OpenType `"cv01", "ss03"` — geometric, engineered feel
- Signature weight 510 for UI text, 590 for emphasis
- Domain colors glow, not just fill — `box-shadow` halos, not solid backgrounds
- Tabular figures (`font-variant-numeric: tabular-nums`) on all data

---

## 2. Color Palette

### Backgrounds (luminance ladder)
| Token | Hex | Use |
|-------|-----|-----|
| `bg-primary` | `#08090e` | Page canvas — deepest black |
| `bg-secondary` | `#0f1016` | Panel/sidebar backgrounds |
| `bg-card` | `rgba(255,255,255,0.03)` | Glass card surfaces — translucent, never solid |
| `bg-card-hover` | `rgba(255,255,255,0.06)` | Card hover / pressed state |
| `bg-elevated` | `rgba(255,255,255,0.08)` | Modals, dropdowns, popovers |
| `bg-inset` | `rgba(0,0,0,0.3)` | Recessed wells inside cards (gauge backgrounds) |

### Text (WCAG AAA on bg-card)
| Token | Hex | Use |
|-------|-----|-----|
| `text-primary` | `#f0f0f5` | Headlines, key data — near-white, not pure white |
| `text-secondary` | `#a8a8c0` | Body text, descriptions |
| `text-muted` | `#6a6a82` | Labels, metadata, timestamps |
| `text-dim` | `#4a4a5e` | Disabled, placeholders |

### Status (vibrant, glow-capable)
| Token | Hex | Glow (12% opacity) | Use |
|-------|-----|-----|-----|
| `accent-green` | `#34d399` | `rgba(52,211,153,0.12)` | Recovery good, completed, on-track |
| `accent-yellow` | `#fbbf24` | `rgba(251,191,36,0.12)` | Caution, adjusted, cycling |
| `accent-red` | `#f87171` | `rgba(248,113,113,0.12)` | Alert, missed, low recovery |
| `accent-blue` | `#60a5fa` | `rgba(96,165,250,0.12)` | Info, HRV, active |
| `accent-purple` | `#a78bfa` | `rgba(167,139,250,0.12)` | Gym, training load |
| `accent-orange` | `#fb923c` | `rgba(251,146,60,0.12)` | Body battery bar |

### Domain colors
| Token | Hex | Use |
|-------|-----|-----|
| `mountain` | `#38bdf8` | Mountain/outdoor activities — cyan |
| `gym` | `#a78bfa` | Gym sessions — purple |
| `cycling` | `#f59e0b` | Cycling activities — amber |
| `sleep` | `#818cf8` | Sleep metrics — indigo |
| `heart` | `#fb7185` | Heart rate — pink |
| `rest` | `#6a6a82` | Rest days — muted |

### Borders & dividers
| Token | Value | Use |
|-------|-------|-----|
| `border-glass` | `rgba(255,255,255,0.08)` | Default glass card border |
| `border-subtle` | `rgba(255,255,255,0.04)` | Dividers within cards |
| `border-glow` | Gradient border via pseudo-element | Featured/active cards — see Liquid Glass section |

---

## 3. Typography

### Font stack
- **Primary:** `'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Mono:** `'Berkeley Mono', ui-monospace, 'SF Mono', Menlo, monospace`
- **OpenType features:** `font-feature-settings: "cv01", "ss03"` on all text
- **Rendering:** `-webkit-font-smoothing: antialiased`

### Scale
| Role | Size | Weight | Line Height | Letter Spacing | Use |
|------|------|--------|-------------|----------------|-----|
| Display | 28px | 510 | 1.1 | -0.02em | Page titles ("Today", "Week") |
| Data XL | 32px | 700 | 1.0 | -0.02em | Hero metrics (inside radial gauges) |
| Data LG | 20px | 600 | 1.2 | -0.01em | Card headline numbers |
| Data MD | 15px | 600 | 1.3 | 0 | Inline stat values |
| Heading | 15px | 590 | 1.3 | -0.01em | Card titles, section headers |
| Body | 14px | 400 | 1.5 | 0 | Descriptions, coaching text |
| Caption | 12px | 510 | 1.4 | 0 | Labels, metadata, timestamps |
| Section label | 11px | 600 | 1.4 | 0.06em | Uppercase section dividers |
| Micro | 10px | 510 | 1.4 | 0 | Gauge labels, tiny annotations |

**All data values:** `font-variant-numeric: tabular-nums` for column alignment.

---

## 4. Liquid Glass Cards

The signature component. Translucent surfaces with depth, blur, and colored edge light.

```css
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px;
  position: relative;
}

/* Subtle inner glow at top edge — simulates light hitting glass */
.glass-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.15),
    transparent
  );
  border-radius: 16px 16px 0 0;
}
```

### Glass card variants
| Variant | Extra treatment | Use |
|---------|----------------|-----|
| **Default** | As above | Standard cards |
| **Status glow** | `box-shadow: 0 0 20px <glow-color>` | Recovery/readiness cards — glow matches status |
| **Active/selected** | Border becomes gradient (purple→blue) | Today's session, selected items |
| **Inset well** | `background: rgba(0,0,0,0.3); border-radius: 12px` inside card | Gauge backgrounds, chart containers |
| **Coaching card** | Top-left colored accent strip (3px wide, 40% height) | Coach decision cards |

### Border radius scale
| Size | Radius | Use |
|------|--------|-----|
| Micro | 4px | Inline badges, small tags |
| Standard | 8px | Buttons, inputs, inner containers |
| Card | 16px | All glass cards |
| Large | 20px | Modals, bottom sheets |
| Pill | 9999px | Status pills, filter chips |
| Circle | 50% | Radial gauges, avatars |

---

## 5. Radial Gauges (Bevel-style)

Key metrics (recovery, strain, sleep) use radial progress rings instead of flat bars.

```
Structure:
┌─────────────────────┐
│  ╭──────────────╮   │  ← Glass card
│  │   ┌──────┐   │   │
│  │   │ 92%  │   │   │  ← Data XL centered in ring
│  │   └──────┘   │   │
│  │   ○○○○○○○○   │   │  ← SVG circle, stroke-dasharray for progress
│  ╰──────────────╯   │
│    Recovery          │  ← Caption below
└─────────────────────┘
```

- Ring stroke: 4-6px, rounded caps (`stroke-linecap: round`)
- Track (background): `rgba(255,255,255,0.06)`
- Progress: domain color with glow filter (`filter: drop-shadow(0 0 4px <color>)`)
- Ring size: 80-100px diameter for hero, 48-60px for compact
- Value text centered inside, Data XL or Data LG weight
- Label below ring, Caption style

### Three-gauge hero row (Bevel-inspired)
For TodayView top section — three radial gauges side by side:
- **Recovery** (green arc) — HRV-based readiness score
- **Strain** (orange arc) — training load this week
- **Sleep** (blue/indigo arc) — sleep quality score

Each in its own glass card, arranged in a 3-column grid with 8px gap.

---

## 6. Glow & Light Effects

### Status glow halos
Cards with status meaning get a colored glow:
```css
/* Green glow — recovery good */
box-shadow: 0 0 24px rgba(52, 211, 153, 0.12),
            inset 0 1px 0 rgba(52, 211, 153, 0.06);

/* Red glow — alert state */
box-shadow: 0 0 24px rgba(248, 113, 113, 0.12),
            inset 0 1px 0 rgba(248, 113, 113, 0.06);
```

### Gradient borders (featured cards)
```css
.glass-card-featured {
  border: 1px solid transparent;
  background-clip: padding-box;
  position: relative;
}
.glass-card-featured::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 17px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(167, 139, 250, 0.3),
    rgba(96, 165, 250, 0.1),
    transparent
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
```

### Body battery bar (Bevel-style)
Segmented horizontal bar with green→yellow→red gradient fill:
- Container: `h-2 rounded-full bg-[rgba(255,255,255,0.06)]`
- Fill: `linear-gradient(90deg, #34d399, #fbbf24, #fb923c)` clipped to percentage
- Value label right-aligned, bold, accent-green if >50%, accent-yellow if 30-50%, accent-red if <30%

---

## 7. Coaching Card

The AI coaching summary uses a distinctive glass card with accent strip:

```
┌──┬──────────────────────────┐
│▋ │  Coach: Full send today   │  ← Accent strip (3px, colored by decision)
│▋ │                           │
│▋ │  HRV balanced, 7.2h       │  ← Body text with key signals
│▋ │  sleep, no mountain load  │
│  │                           │
│  │  ▸ Why?                   │  ← Expandable rationale
└──┴──────────────────────────┘
```

- Strip color: green (train), yellow (adjusted), red (rest)
- "Why?" section: collapsible, shows decision rule + inputs
- Text style: Body, not all caps, autonomy-supportive language

---

## 8. Spacing & Layout

### Spacing scale (8px base)
`4px · 8px · 12px · 16px · 20px · 24px · 32px · 48px`

### Page layout
- Max width: 480px (mobile-first, single column)
- Page padding: 16px horizontal
- Card gap: 12px vertical
- Section gap: 24px vertical
- Inner card padding: 16px

### Navigation
- Bottom tab bar: glass card style, 5 tabs
- Active tab: accent-blue icon + label
- Inactive: `text-muted` icon only
- Tab bar height: 56px + safe area inset

---

## 9. Interaction & Motion

### Transitions
- Default: `150ms ease-out` (opacity, transform, background)
- Card expand: `250ms ease-out` (height, with `will-change: height`)
- Bottom sheet: `250ms ease-out` slide-up
- Gauge fill: `800ms ease-out` on mount (animated stroke-dasharray)

### Touch feedback
- Cards: scale to `0.98` on press (`active:scale-[0.98]`)
- Buttons: opacity `0.85` on press
- Min touch target: 44x44px

### Scroll behavior
- `scroll-behavior: smooth` on html
- Custom scrollbar: 4px wide, `border-subtle` thumb, transparent track
- Pull-to-refresh: disabled (explicit refresh button)

---

## 10. Charts

All charts use Recharts. Consistent treatment:

- Chart background: transparent (sits inside glass card inset well)
- Grid lines: `rgba(255,255,255,0.04)` — barely visible
- Axis text: Caption style, `text-muted` color
- Line stroke: 2px, domain color
- Area fill: domain color at 10% opacity
- Dots: only on hover, 4px radius, solid domain color
- Tooltip: glass card style, `backdrop-filter: blur(16px)`
- Active dot glow: `filter: drop-shadow(0 0 4px <domain-color>)`

---

## 11. Do's and Don'ts

### Do
- Use `backdrop-filter: blur(16px)` on all card surfaces
- Use `rgba(255,255,255,0.03)` backgrounds — never solid dark colors for cards
- Apply colored `box-shadow` glows for status meaning
- Use radial gauges for key metrics, not flat progress bars
- Keep Inter Variable with `"cv01","ss03"` on all text
- Use weight 510 for UI labels, 590 for emphasis, 700 only for hero data
- Apply `tabular-nums` on any number that might change or align
- Use the luminance ladder: deeper = less white opacity, elevated = more

### Don't
- Don't use solid card backgrounds (`#16161e`) — use translucent `rgba` values
- Don't use pure `#ffffff` for text — `#f0f0f5` prevents glare
- Don't use flat colored bars where a radial gauge would be clearer
- Don't add warm tones to the chrome — palette is cool blue-gray + vibrant accents
- Don't use `font-weight: 700` on UI elements — max is 590, with 510 as default emphasis
- Don't skip the glass `::before` top-edge highlight — it sells the depth illusion
- Don't use opaque borders — always semi-transparent white
- Don't let glow opacity exceed 15% — it should suggest light, not compete with content
