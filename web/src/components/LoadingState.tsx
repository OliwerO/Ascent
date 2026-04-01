export function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-pulse text-text-muted">Loading...</div>
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-accent-red">{message}</div>
    </div>
  )
}
