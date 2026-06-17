"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { fetchExtractionHealth } from "@/lib/api"
import type { ExtractionHealth as HealthData } from "@/lib/api"

const STATUS_META: Record<string, { label: string; cls: string }> = {
  ok: { label: "Saudável", cls: "text-success border-success/40" },
  degraded: { label: "Degradado", cls: "text-warning border-warning/40" },
  critical: { label: "Crítico", cls: "text-danger border-danger/40" },
  no_data: { label: "Sem dados", cls: "text-muted-foreground border-border" },
}

function barColor(pct: number | null): string {
  if (pct == null) return "bg-border"
  if (pct >= 80) return "bg-success/60"
  if (pct >= 55) return "bg-warning/60"
  return "bg-danger/60"
}

export function ExtractionHealth({ token }: { token: string }) {
  const [data, setData] = useState<HealthData | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    fetchExtractionHealth(token).then(setData).catch((e) => setError(e.message))
  }, [token])

  if (error || !data) return null

  const meta = STATUS_META[data.status] || STATUS_META.no_data

  return (
    <div className="mt-8 border-t border-border pt-6">
      <div className="mb-4 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-gold/80">
          Saúde de extração
        </span>
        <span className={cn("rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide", meta.cls)}>
          {meta.label}
          {data.recent_price_pct != null ? ` · ${data.recent_price_pct}% c/ preço` : ""}
        </span>
      </div>

      {/* Daily completeness bars (price extracted) */}
      <div className="mb-4">
        <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/55">
          % com preço extraído — últimos 21 dias
        </p>
        <div className="flex items-end gap-1" style={{ height: 56 }}>
          {data.daily.map((d, i) => (
            <div
              key={i}
              className="group relative flex-1"
              title={`${d.day}: ${d.price_pct ?? "—"}% de ${d.total}`}
            >
              <div
                className={cn("w-full rounded-sm", barColor(d.price_pct))}
                style={{ height: `${Math.max(3, ((d.price_pct ?? 0) / 100) * 56)}px` }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Per-source (last 7 days) */}
      <div className="flex flex-wrap gap-4">
        {data.by_source.map((s) => (
          <div key={s.source} className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-[1px] text-muted-foreground">
              {s.source}
            </span>
            <span
              className={cn(
                "font-mono text-[12px] font-bold",
                (s.price_pct ?? 0) >= 80 ? "text-success"
                  : (s.price_pct ?? 0) >= 55 ? "text-warning" : "text-danger"
              )}
            >
              {s.price_pct ?? "—"}%
            </span>
            <span className="font-mono text-[10px] text-muted-foreground/50">({s.total})</span>
          </div>
        ))}
      </div>
    </div>
  )
}
