function Skeleton({ className }: { className?: string }) {
  return (
    <div className={`bg-bg-card rounded-2xl animate-pulse ${className ?? ''}`} />
  )
}

export function LoadingState() {
  return (
    <div className="space-y-3">
      {/* Coaching card skeleton */}
      <Skeleton className="h-40 border border-border-subtle" />
      {/* Wellness skeleton */}
      <Skeleton className="h-16 border border-border-subtle" />
      {/* 2-column grid */}
      <div className="grid grid-cols-2 gap-3">
        <Skeleton className="h-28 border border-border-subtle" />
        <Skeleton className="h-28 border border-border-subtle" />
      </div>
      {/* Secondary grid */}
      <div className="grid grid-cols-2 gap-3">
        <Skeleton className="h-20 border border-border-subtle" />
        <Skeleton className="h-20 border border-border-subtle" />
      </div>
      {/* Load card */}
      <Skeleton className="h-20 border border-border-subtle" />
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="text-accent-red text-sm bg-glow-red border border-accent-red/20 rounded-2xl px-5 py-3">
        {message}
      </div>
    </div>
  )
}

export function EmptyState({ icon, title, subtitle }: {
  icon?: string
  title: string
  subtitle?: string
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="text-2xl mb-2">{icon}</div>}
      <div className="text-sm font-semibold text-text-secondary">{title}</div>
      {subtitle && <div className="text-[12px] text-text-muted mt-1 max-w-[250px]">{subtitle}</div>}
    </div>
  )
}
