interface Props {
  value: number
  max: number
  color: string
}

export function ProgressBar({ value, max, color }: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="w-full bg-bg-inset rounded-full h-2 mt-2">
      <div
        className="rounded-full h-2 transition-all duration-500"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  )
}
