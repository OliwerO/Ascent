import { createPortal } from 'react-dom'
import type { ReactNode } from 'react'

interface Props {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}

export function MetricDetailSheet({ title, open, onClose, children }: Props) {
  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/60" onClick={onClose}>
      <div
        className="w-full max-w-[480px] bg-bg-secondary border-t border-border rounded-t-[20px] p-5 pb-8 max-h-[75vh] overflow-auto animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[15px] font-[590] text-text-primary">{title}</h3>
          <button onClick={onClose} className="text-text-muted text-[13px] px-2 py-1">Done</button>
        </div>
        {children}
      </div>
    </div>,
    document.body
  )
}
