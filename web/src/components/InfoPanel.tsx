import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface Props {
  title: string
  children: React.ReactNode
}

export function InfoPanel({ title, children }: Props) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-1 text-[12px] text-text-dim hover:text-text-muted transition-colors">
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {title}
      </button>
      {open && (
        <div className="mt-2 text-[12px] text-text-muted leading-relaxed glass-card px-3 py-2.5 space-y-2">
          {children}
        </div>
      )}
    </div>
  )
}
