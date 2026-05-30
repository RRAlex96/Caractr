"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"

interface ShareButtonProps {
  brand?: string
  model?: string
  year?: number | null
  tier?: string
  priceDeltaPct?: number | null
  priceDelta?: number | null
  listingUrl: string
  className?: string
}

const TIER_LABELS: Record<string, string> = {
  forte: "NEGOCIO FORTE",
  razoavel: "RAZOAVEL",
  cuidado: "ATENCAO",
  evitar: "EVITAR",
}

export function ShareButton({
  brand,
  model,
  year,
  tier,
  priceDeltaPct,
  priceDelta,
  listingUrl,
  className,
}: ShareButtonProps) {
  const [shared, setShared] = useState(false)

  const handleShare = async () => {
    const yearStr = year ? ` ${year}` : ""
    const verdictLabel = tier ? TIER_LABELS[tier] || tier.toUpperCase() : ""
    const dir = (priceDelta || 0) >= 0 ? "abaixo" : "acima"

    let text = `Analisei um ${[brand, model, yearStr].filter(Boolean).join(" ").trim() || "carro"} no Caractr`
    if (verdictLabel) text += ` — ${verdictLabel}`
    if (priceDeltaPct != null) text += `, ${Math.abs(priceDeltaPct)}% ${dir} do mercado`
    text += `. Experimenta: caractr.pt/analisar`

    Analytics.analysisShared("", listingUrl, "whatsapp")
    setShared(true)
    setTimeout(() => setShared(false), 2000)

    if (navigator.share) {
      try {
        await navigator.share({ text })
        return
      } catch {}
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank")
  }

  return (
    <button
      onClick={handleShare}
      className={cn(
        "flex shrink-0 items-center gap-1.5 rounded-full border border-border px-3.5 py-1.5",
        "font-mono text-[9px] uppercase tracking-[1px] transition-colors",
        shared
          ? "border-gold/40 text-gold"
          : "text-muted-foreground hover:border-gold/30 hover:text-gold",
        className
      )}
    >
      {shared ? "Partilhado" : "Partilhar"}
    </button>
  )
}
