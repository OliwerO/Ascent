import type { ReactNode } from 'react'

interface Props {
  title?: string
  children: ReactNode
  className?: string
}

export function Card({ title, children, className = '' }: Props) {
  return (
    <div className={`bg-bg-card border border-border rounded-xl p-4 ${className}`}>
      {title && <h3 className="text-sm text-text-secondary font-medium mb-3">{title}</h3>}
      {children}
    </div>
  )
}
