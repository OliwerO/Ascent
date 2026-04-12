import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

interface Props {
  title: string
  defaultOpen?: boolean
  children: React.ReactNode
}

export function CollapsibleSection({ title, defaultOpen = false, children }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between py-2 text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold"
      >
        {title}
        <ChevronDown size={14} className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="space-y-3">{children}</div>}
    </div>
  )
}
