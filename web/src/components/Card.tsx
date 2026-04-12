import type { ReactNode } from 'react'

interface Props {
  title?: string
  subtitle?: string
  children: ReactNode
  className?: string
  glow?: 'green' | 'yellow' | 'red' | 'blue' | 'purple'
  accentStrip?: 'green' | 'yellow' | 'red'
  variant?: 'default' | 'featured' | 'inset'
}

const glowStyles = {
  green: 'shadow-[0_0_24px_rgba(52,211,153,0.12),inset_0_1px_0_rgba(52,211,153,0.06)] border-accent-green/20',
  yellow: 'shadow-[0_0_24px_rgba(251,191,36,0.12),inset_0_1px_0_rgba(251,191,36,0.06)] border-accent-yellow/20',
  red: 'shadow-[0_0_24px_rgba(248,113,113,0.12),inset_0_1px_0_rgba(248,113,113,0.06)] border-accent-red/20',
  blue: 'shadow-[0_0_24px_rgba(96,165,250,0.12),inset_0_1px_0_rgba(96,165,250,0.06)] border-accent-blue/20',
  purple: 'shadow-[0_0_24px_rgba(167,139,250,0.12),inset_0_1px_0_rgba(167,139,250,0.06)] border-accent-purple/20',
}

const accentColors = {
  green: 'bg-accent-green',
  yellow: 'bg-accent-yellow',
  red: 'bg-accent-red',
}

export function Card({ title, subtitle, children, className = '', glow, accentStrip, variant = 'default' }: Props) {
  const glowClass = glow ? glowStyles[glow] : 'border-border'
  const isInset = variant === 'inset'

  const baseClass = isInset
    ? 'bg-bg-inset rounded-xl p-3'
    : 'glass-card'

  return (
    <div className={`${baseClass} ${glowClass} ${className}`}>
      {accentStrip && (
        <div
          className={`absolute left-0 top-[30%] w-[3px] h-[40%] rounded-r-full ${accentColors[accentStrip]}`}
        />
      )}
      {title && (
        <h3 className="text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold mb-1">
          {title}
        </h3>
      )}
      {subtitle && (
        <p className="text-[11px] leading-relaxed text-text-dim mb-3">{subtitle}</p>
      )}
      {!subtitle && title && <div className="mb-3" />}
      {children}
    </div>
  )
}
