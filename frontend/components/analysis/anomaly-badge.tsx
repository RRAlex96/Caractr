"use client"

import { cn } from "@/lib/utils"
import type { Anomaly } from "@/lib/types"

interface AnomalyBadgeProps {
  anomaly?: Anomaly | null
  className?: string
}

export function AnomalyBadge({ anomaly, className }: AnomalyBadgeProps) {
  if (!anomaly) return null

  const danger = anomaly.level === "danger"

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border p-4",
        danger
          ? "border-danger/40 bg-danger/[0.06]"
          : "border-warning/40 bg-warning/[0.06]",
        className
      )}
      role="alert"
    >
      <span
        className={cn(
          "mt-0.5 shrink-0 text-base leading-none",
          danger ? "text-danger" : "text-warning"
        )}
        aria-hidden
      >
        {danger ? "⚠" : "!"}
      </span>
      <div>
        <p
          className={cn(
            "mb-1 font-mono text-[10px] uppercase tracking-[1.5px]",
            danger ? "text-danger" : "text-warning"
          )}
        >
          {anomaly.title}
        </p>
        <p className="text-[13px] font-light leading-relaxed text-foreground">
          {anomaly.message}
        </p>
      </div>
    </div>
  )
}
