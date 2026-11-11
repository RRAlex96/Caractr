"use client"

import { cn } from "@/lib/utils"
import type { Dealbreakers } from "@/lib/types"

/** One-line human summary of what the deal-breakers are (for card context). */
export function dealbreakerSummary(data: Dealbreakers): string {
  const parts: string[] = []
  if (data.recall_count) {
    parts.push(data.recall_count === 1 ? "1 recall oficial" : `${data.recall_count} recalls oficiais`)
  }
  if (data.critical_issue_count) {
    parts.push(
      data.critical_issue_count === 1
        ? "1 falha grave conhecida"
        : `${data.critical_issue_count} falhas graves conhecidas`
    )
  }
  return parts.join(" · ")
}

interface DealbreakerBadgeProps {
  data?: Dealbreakers | null
  className?: string
}

/** Compact red pill for recommendation cards — a model-level "heads up". */
export function DealbreakerBadge({ data, className }: DealbreakerBadgeProps) {
  if (!data || !data.has_dealbreaker) return null
  const total = data.recall_count + data.critical_issue_count
  const label = total === 1 ? "1 alerta sério" : `${total} alertas sérios`

  return (
    <span
      title={dealbreakerSummary(data)}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-danger/45 bg-danger/[0.08] px-3 py-1 font-mono text-[10px] tracking-[1px] text-danger",
        className
      )}
    >
      <span aria-hidden>⚠</span> {label.toUpperCase()}
    </span>
  )
}
