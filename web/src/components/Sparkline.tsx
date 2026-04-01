import { ResponsiveContainer, AreaChart, Area, ReferenceLine } from 'recharts'

interface Props {
  data: { value: number }[]
  color?: string
  height?: number
  baseline?: { low: number; high: number }
}

export function Sparkline({ data, color = '#3b82f6', height = 40, baseline }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
        <defs>
          <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        {baseline && (
          <>
            <ReferenceLine y={baseline.low} stroke="#555570" strokeDasharray="2 2" />
            <ReferenceLine y={baseline.high} stroke="#555570" strokeDasharray="2 2" />
          </>
        )}
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#grad-${color})`}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
