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

const pct = (value: number) =>
  Math.abs(value).toLocaleString("pt-PT", { maximumFractionDigits: 1 })

/**
 * Transparency caption: what the market number is actually compared to.
 * "Comparado com 16 anúncios de BMW 530 híbrido plug-in · 2017–2023, com o
 *  preço de cada um ajustado ao ano e aos quilómetros deste carro (2018,
 *  170 000 km). Neste modelo, cada ano de diferença pesa cerca de 8,2% no
 *  preço e cada 10 000 km cerca de 1,3%. Margem da referência: ±3,5%."
 * When the listings are not comparable with the car in mileage or model year,
 * it says why there is no price verdict instead.
 */
export function MarketBasis({ deal, listing, className }: MarketBasisProps) {
  const km = deal.market_km_comparison
  const yr = deal.market_year_comparison
  const captionClass = cn(
    "px-1 text-[11px] font-light leading-relaxed text-muted-foreground/60",
    className
  )
  const num = "font-mono text-muted-foreground"

  if (km?.basis === "mismatch") {
    return (
      <p className={captionClass}>
        Não avaliámos o preço face ao mercado: dos{" "}
        <span className={num}>{km.pool_count}</span>{" "}
        anúncios comparáveis,{" "}
        {km.in_band_count === 0 ? "nenhum tem" : `só ${km.in_band_count} ${km.in_band_count === 1 ? "tem" : "têm"}`}{" "}
        quilometragem próxima da deste carro ({formatKm(km.car_km)}). Os
        restantes rondam os {formatKm(km.pool_median_km)}.
      </p>
    )
  }

  if (yr?.basis === "mismatch") {
    return (
      <p className={captionClass}>
        Não avaliámos o preço face ao mercado: os{" "}
        <span className={num}>{yr.count}</span> anúncios comparáveis são
        sobretudo de {Math.round(yr.median_year)} (entre {yr.year_from} e{" "}
        {yr.year_to}) e este carro é de {yr.car_year}. São poucos para
        ajustar o preço ao ano com confiança.
      </p>
    )
  }

  const n = deal.market_sample_count
  if (!n || n < 1) return null

  const model = `${listing.brand_name || ""} ${listing.model_name || ""}`.trim()
  const fuelRaw = (deal.market_fuel_type || "").toLowerCase()
  const fuel = FUEL_LABEL[fuelRaw] || (fuelRaw || "")

  let range = ""
  if (yr?.basis === "adjusted" || yr?.basis === "near") {
    // The years of the listings actually compared.
    range = yr.year_from === yr.year_to ? ` · ${yr.year_from}` : ` · ${yr.year_from}–${yr.year_to}`
  } else if (deal.generation_year_start) {
    range = ` · ${deal.generation_year_start}–${deal.generation_year_end || "hoje"}`
  } else if (listing.year) {
    range = ` · anos próximos de ${listing.year}`
  }

  if (yr?.basis === "adjusted") {
    const excluded = yr.excluded_count || 0
    return (
      <p className={captionClass}>
        Comparado com <span className={num}>{n}</span> anúncios de {model}
        {fuel ? ` ${fuel}` : ""}
        {range}, com o preço de cada um ajustado ao ano e aos quilómetros
        deste carro ({yr.car_year}
        {yr.car_km ? `, ${formatKm(yr.car_km)}` : ""}).
        {yr.per_year_pct != null && yr.per_10k_km_pct != null && (
          <>
            {" "}Neste modelo, cada ano de diferença pesa cerca de{" "}
            {pct(yr.per_year_pct)}% no preço e cada {formatKm(10000)} cerca de{" "}
            {pct(yr.per_10k_km_pct)}%.
          </>
        )}
        {yr.margin_pct != null && <> Margem da referência: ±{pct(yr.margin_pct)}%.</>}
        {excluded > 0 && (
          <>
            {" "}
            {excluded === 1
              ? "1 anúncio com preço muito fora do padrão ficou de fora."
              : `${excluded} anúncios com preço muito fora do padrão ficaram de fora.`}
          </>
        )}
      </p>
    )
  }

  let mileage = ""
  if (km?.basis === "band") {
    mileage = ` · entre ${Math.round(km.km_from).toLocaleString("pt-PT")} e ${formatKm(km.km_to)} (este tem ${formatKm(km.car_km)})`
  } else if (km?.basis === "pool") {
    mileage = ` · quilometragem mediana de ${formatKm(km.pool_median_km)}`
  }

  return (
    <p className={captionClass}>
      Comparado com <span className={num}>{n}</span> anúncios de {model}
      {fuel ? ` ${fuel}` : ""}
      {range}
      {yr?.basis === "near" ? ` (o ano deste carro, ${yr.car_year}, e os vizinhos)` : ""}
      {mileage}.
    </p>
  )
}
