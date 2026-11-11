"use client"

import { useId, useState } from "react"

import { cn } from "@/lib/utils"
import type { Dealbreakers } from "@/lib/types"
import { CriticalIssueList } from "@/components/analysis/dealbreaker-warning"

interface DealbreakerCardAlertProps {
  data?: Dealbreakers | null
  className?: string
}

/**
 * Recommendation-card alert — only for critical known failures of a specific
 * engine or gearbox (recalls are a listing-level checklist, not a model
 * verdict). Expands on tap to name the engine, so the buyer can choose a
 * different version instead of dropping the car.
 */
export function DealbreakerCardAlert({ data, className }: DealbreakerCardAlertProps) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  const issues = data?.critical_issues ?? []
  if (!issues.length) return null

  const label = issues.length === 1 ? "Uma versão a evitar" : `${issues.length} versões a evitar`

  return (
    <div className={cn("mb-3", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1.5 rounded-full border border-danger/45 bg-danger/[0.08] px-3 py-1 font-mono text-[10px] tracking-[1px] text-danger transition-colors hover:bg-danger/[0.15] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger/50"
      >
        <span aria-hidden>⚠</span>
        {label.toUpperCase()}
        <span className="tracking-normal text-danger/70">· {open ? "esconder" : "ver qual"}</span>
      </button>
      {open && (
        <div id={panelId} className="mt-3 rounded-xl border border-danger/30 bg-danger/[0.05] p-4">
          <p className="mb-3 text-[12px] font-light leading-relaxed text-muted-foreground">
            Falha crónica e cara de uma motorização específica — vê se o modelo tem outra que te sirva.
          </p>
          <CriticalIssueList issues={issues} />
        </div>
      )}
    </div>
  )
}
