"use client"

import { cn } from "@/lib/utils"
import type { AnalysisDeal, AnalysisListing } from "@/lib/types"

interface MarketBasisProps {
  deal: AnalysisDeal
  listing: AnalysisListing
  className?: string
}

const FUEL_LABEL: Record<string, string> = {
  diesel: "diesel",
  gasolina: "gasolina",
  "híbrido": "híbrido",
  "híbrido (plug-in)": "híbrido plug-in",
  "elétrico": "elétrico",
  gpl: "GPL",
}

/**
 * One-line transparency caption: what the market number is actually compared to.
 * "Comparado com 22 anúncios de BMW Serie 1 diesel · 2015–2019"
 */
export function MarketBasis({ deal, listing, className }: MarketBasisProps) {
  const n = deal.market_sample_count
  if (!n || n < 1) return null

  const model = `${listing.brand_name || ""} ${listing.model_name || ""}`.trim()
  const fuelRaw = (deal.market_fuel_type || "").toLowerCase()
  const fuel = FUEL_LABEL[fuelRaw] || (fuelRaw || "")

  let range = ""
  if (deal.generation_year_start) {
    range = ` · ${deal.generation_year_start}–${deal.generation_year_end || "hoje"}`
  } else if (listing.year) {
    range = ` · anos próximos de ${listing.year}`
  }

  return (
    <p
      className={cn(
        "px-1 text-[11px] font-light leading-relaxed text-muted-foreground/60",
        className
      )}
    >
      Comparado com{" "}
      <span className="font-mono text-muted-foreground">{n}</span> anúncios de{" "}
      {model}
      {fuel ? ` ${fuel}` : ""}
      {range}.
    </p>
  )
}
