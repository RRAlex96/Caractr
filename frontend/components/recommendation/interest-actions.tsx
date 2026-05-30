"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

const DISMISS_REASONS = [
  "Nao gosto da marca",
  "Quero algo mais desportivo",
  "Quero algo mais luxuoso",
  "Quero algo mais pratico",
  "Acima do meu orcamento",
  "Nao e o estilo certo",
]

interface InterestActionsProps {
  modelId: number
  isInterested: boolean
  dismissReason?: string
  onInterest: (modelId: number) => void
  onDismiss: (modelId: number, reason: string) => void
  onUndo: (modelId: number) => void
  className?: string
}

export function InterestActions({
  modelId,
  isInterested,
  dismissReason,
  onInterest,
  onDismiss,
  onUndo,
  className,
}: InterestActionsProps) {
  const [showReasons, setShowReasons] = useState(false)

  if (isInterested) {
    return (
      <div className={cn("flex items-center gap-3 border-t border-border pt-4", className)}>
        <span className="flex items-center gap-1.5 font-mono text-[10px] tracking-[1px] text-success">
          <span>✓</span> Com interesse
        </span>
        <button
          onClick={() => onUndo(modelId)}
          className="font-mono text-[9px] tracking-[0.5px] text-muted-foreground/50 hover:text-muted-foreground"
        >
          desfazer
        </button>
      </div>
    )
  }

  if (dismissReason) {
    return (
      <div className={cn("flex items-center gap-2.5 border-t border-border pt-4", className)}>
        <span className="text-[11px] text-muted-foreground/50">{dismissReason}</span>
        <button
          onClick={() => onUndo(modelId)}
          className="font-mono text-[9px] tracking-[0.5px] text-muted-foreground/50 hover:text-muted-foreground"
        >
          desfazer
        </button>
      </div>
    )
  }

  return (
    <div className={cn("border-t border-border pt-4", className)}>
      <div className="flex items-center gap-4">
        <button
          onClick={() => onInterest(modelId)}
          className="rounded-full border border-success px-3.5 py-1 font-mono text-[10px] tracking-[0.5px] text-success transition-colors hover:bg-success/[0.08]"
        >
          Tenho interesse
        </button>
        <button
          onClick={() => setShowReasons(!showReasons)}
          className="text-xs text-muted-foreground/50 transition-opacity hover:text-muted-foreground"
        >
          Nao e para mim
        </button>
      </div>
      {showReasons && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {DISMISS_REASONS.map((reason) => (
            <button
              key={reason}
              onClick={() => {
                onDismiss(modelId, reason)
                setShowReasons(false)
              }}
              className="rounded-full border border-border px-3 py-1 text-[11px] text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground"
            >
              {reason}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
