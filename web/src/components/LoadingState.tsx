export function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="flex gap-1.5">
        <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
        <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse [animation-delay:150ms]" />
        <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse [animation-delay:300ms]" />
      </div>
      <div className="text-xs text-text-muted">Loading data</div>
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
