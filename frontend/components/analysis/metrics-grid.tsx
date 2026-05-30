import { cn } from "@/lib/utils"
import { formatPrice, formatKmYear } from "@/lib/utils"
import type { AnalysisDeal, AnalysisDetails } from "@/lib/types"

interface MetricsGridProps {
  deal: AnalysisDeal
  analysis: AnalysisDetails
  className?: string
}

interface MetricItem {
  label: string
  value: string
  colorClass?: string
}

export function MetricsGrid({ deal, analysis, className }: MetricsGridProps) {
  const items: MetricItem[] = []

  if (deal.price_delta_pct != null) {
    const positive = (deal.price_delta || 0) >= 0
    items.push({
      label: "vs. Mercado",
      value: `${positive ? "-" : "+"}${Math.abs(deal.price_delta_pct)}%`,
      colorClass: positive ? "text-success" : "text-danger",
    })
  }

  if (deal.market_avg_price != null) {
    const sampleNote = deal.market_sample_count
      ? ` (${deal.market_sample_count})`
      : ""
    items.push({
      label: `Media mercado${sampleNote}`,
      value: formatPrice(Math.round(deal.market_avg_price)),
    })
  }

  if (deal.km_per_year != null) {
    items.push({
      label: "Km / ano",
      value: formatKmYear(Math.round(deal.km_per_year)),
    })
  }

  if (analysis.spec_tier) {
    items.push({
      label: "Versao",
      value: (analysis.trim_level || analysis.spec_tier).toUpperCase(),
    })
  }

  if (items.length === 0) return null

  return (
    <div
      className={cn(
        "grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-px overflow-hidden rounded-xl border border-border bg-border",
        className
      )}
    >
      {items.map((item) => (
        <div key={item.label} className="bg-card p-4">
          <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            {item.label}
          </p>
          <p
            className={cn(
              "font-mono text-xl font-bold leading-none",
              item.colorClass || "text-foreground"
            )}
          >
            {item.value}
          </p>
        </div>
      ))}
    </div>
  )
}
