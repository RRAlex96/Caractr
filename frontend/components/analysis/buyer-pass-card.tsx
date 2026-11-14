"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"

interface BuyerPassCardProps {
  analysisId?: number | null
  className?: string
}

const INCLUDES = [
  "Análises completas ilimitadas durante 30 dias",
  "Números e guião de negociação em todos os anúncios",
  "Comparação lado a lado dos carros que estás a ver",
  "Aviso por email quando o preço de um anúncio baixa",
]

/**
 * The Buyer Pass is not on sale yet. This card measures whether people would
 * buy it at its price, before payments are built (plan, phase 1): a click is
 * recorded as `pass_interest`, and the buyer is told plainly that it is not
 * available yet and that analyses stay free meanwhile.
 */
export function BuyerPassCard({ analysisId, className }: BuyerPassCardProps) {
  const [clicked, setClicked] = useState(false)

  return (
    <div className={cn("rounded-xl border border-border bg-card p-5 md:p-6", className)}>
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">Vais ver vários carros?</p>
      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-display text-[20px] font-bold text-foreground">Buyer Pass</p>
        <p className="font-mono text-[15px] text-foreground">
          9,90 € <span className="text-[12px] text-muted-foreground">· 30 dias · pagamento único</span>
        </p>
      </div>
      <ul className="mt-3 space-y-1.5 text-[13px] font-light leading-relaxed text-muted-foreground">
        {INCLUDES.map((i) => (
          <li key={i} className="flex gap-2">
            <span className="text-gold">✓</span>
            {i}
          </li>
        ))}
      </ul>
      {clicked ? (
        <p className="mt-4 rounded-lg border border-gold/30 bg-gold/[0.06] px-4 py-3 text-[13px] leading-relaxed text-foreground">
          Obrigado. O Buyer Pass ainda está a ser preparado e registámos o teu interesse. Até lá, as análises
          continuam grátis.
        </p>
      ) : (
        <button
          onClick={() => {
            setClicked(true)
            Analytics.passInterest(analysisId, "analysis")
          }}
          className="mt-4 rounded-full bg-gold px-5 py-2.5 text-[13px] font-medium text-background transition-opacity hover:opacity-90"
        >
          Quero o Buyer Pass
        </button>
      )}
    </div>
  )
}
