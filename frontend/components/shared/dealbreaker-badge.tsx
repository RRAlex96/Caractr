"use client"

import { useId, useState } from "react"

import { cn } from "@/lib/utils"
import type { Dealbreakers } from "@/lib/types"
import { DealbreakerWarning } from "@/components/analysis/dealbreaker-warning"

interface DealbreakerCardAlertProps {
  data?: Dealbreakers | null
  className?: string
}

/**
 * Deal-breaker alert for recommendation cards. A loud red pill that expands,
 * on tap, into the full warning (what the recall is, production period,
 * source link). A hover tooltip alone didn't work on phones — a warning the
 * buyer can't read scares without informing.
 */
export function DealbreakerCardAlert({ data, className }: DealbreakerCardAlertProps) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  if (!data || !data.has_dealbreaker) return null

  const total = data.recall_count + data.critical_issue_count
  const label = total === 1 ? "1 alerta sério" : `${total} alertas sérios`

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
        <span className="tracking-normal text-danger/70">· {open ? "esconder" : "ver porquê"}</span>
      </button>
      {open && (
        <div id={panelId} className="mt-3">
          <DealbreakerWarning data={data} />
        </div>
      )}
    </div>
  )
}
