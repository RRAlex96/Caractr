"use client"

import { cn, formatKm } from "@/lib/utils"
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
 * "Comparado com 9 anúncios de BMW 530 híbrido plug-in · 2017–2023 · entre
 *  119.000 e 221.000 km (este tem 170.000 km)."
 * When no listing has a mileage close to the car's, it says why there is no
 * price verdict instead.
 */
export function MarketBasis({ deal, listing, className }: MarketBasisProps) {
  const km = deal.market_km_comparison
  const captionClass = cn(
    "px-1 text-[11px] font-light leading-relaxed text-muted-foreground/60",
    className
  )

  if (km?.basis === "mismatch") {
    return (
      <p className={captionClass}>
        Não avaliámos o preço face ao mercado: dos{" "}
        <span className="font-mono text-muted-foreground">{km.pool_count}</span>{" "}
        anúncios comparáveis,{" "}
        {km.in_band_count === 0 ? "nenhum tem" : `só ${km.in_band_count} ${km.in_band_count === 1 ? "tem" : "têm"}`}{" "}
        quilometragem próxima da deste carro ({formatKm(km.car_km)}). Os
        restantes rondam os {formatKm(km.pool_median_km)}.
      </p>
    )
  }

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

  let mileage = ""
  if (km?.basis === "band") {
    mileage = ` · entre ${Math.round(km.km_from).toLocaleString("pt-PT")} e ${formatKm(km.km_to)} (este tem ${formatKm(km.car_km)})`
  } else if (km?.basis === "pool") {
    mileage = ` · quilometragem mediana de ${formatKm(km.pool_median_km)}`
  }

  return (
    <p className={captionClass}>
      Comparado com{" "}
      <span className="font-mono text-muted-foreground">{n}</span> anúncios de{" "}
      {model}
      {fuel ? ` ${fuel}` : ""}
      {range}
      {mileage}.
    </p>
  )
}
