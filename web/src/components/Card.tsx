import type { ReactNode } from 'react'

interface Props {
  title?: string
  children: ReactNode
  className?: string
  glow?: 'green' | 'yellow' | 'red' | 'blue'
}

const glowStyles = {
  green: 'shadow-[0_0_20px_rgba(52,211,153,0.06)] border-accent-green/20',
  yellow: 'shadow-[0_0_20px_rgba(245,158,11,0.06)] border-accent-yellow/20',
  red: 'shadow-[0_0_20px_rgba(248,113,113,0.06)] border-accent-red/20',
  blue: 'shadow-[0_0_20px_rgba(96,165,250,0.06)] border-accent-blue/20',
}

export function Card({ title, children, className = '', glow }: Props) {
  const glowClass = glow ? glowStyles[glow] : 'border-border-subtle'
  return (
    <div className={`bg-bg-card border rounded-2xl p-5 transition-colors ${glowClass} ${className}`}>
      {title && (
        <h3 className="text-xs uppercase tracking-wider text-text-muted font-medium mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  )
}
