"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"

const SITE = "https://caractr.pt"

interface ShareButtonProps {
  brand?: string
  model?: string
  year?: number | null
  tier?: string
  priceDeltaPct?: number | null
  /** Positive: below the market (see metrics-grid). */
  priceDelta?: number | null
  /** The analysis permalink is what gets shared; without it, the analyse page. */
  analysisId?: number | null
  listingUrl: string
  className?: string
}

const TIER_LABELS: Record<string, string> = {
  forte: "negócio forte",
  razoavel: "negócio razoável",
  cuidado: "negócio com reservas",
  evitar: "a evitar",
}

/** The message a buyer sends to a partner or a parent: the car, the verdict, and the analysis itself. */
export function shareMessage(p: Omit<ShareButtonProps, "listingUrl" | "className">): { text: string; url: string } {
  const car = [p.brand, p.model, p.year ? String(p.year) : ""].filter(Boolean).join(" ").trim() || "este carro"
  const url = p.analysisId ? `${SITE}/analise/${p.analysisId}` : `${SITE}/analisar`
  let text = `${car}`
  const verdict = p.tier ? TIER_LABELS[p.tier] : ""
  if (verdict) text += `: ${verdict}`
  if (p.priceDeltaPct != null && p.priceDeltaPct !== 0) {
    text += `, ${Math.abs(p.priceDeltaPct)}% ${(p.priceDelta || 0) >= 0 ? "abaixo" : "acima"} do preço de mercado`
  }
  text += p.analysisId ? ". O que achas? Vê a análise:" : ". Analisei-o no Caractr:"
  return { text, url }
}

export function ShareButton({ listingUrl, className, ...p }: ShareButtonProps) {
  const [shared, setShared] = useState(false)

  const handleShare = async () => {
    const { text, url } = shareMessage(p)
    setShared(true)
    setTimeout(() => setShared(false), 2000)

    if (navigator.share) {
      try {
        await navigator.share({ text, url })
        Analytics.analysisShared(p.analysisId, listingUrl, "native")
        return
      } catch (e) {
        if ((e as Error)?.name === "AbortError") return   // the buyer closed the share sheet
        // not allowed here: fall through to WhatsApp
      }
    }
    Analytics.analysisShared(p.analysisId, listingUrl, "whatsapp")
    window.open(`https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`, "_blank")
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
