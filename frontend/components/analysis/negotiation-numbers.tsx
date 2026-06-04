"use client"

import { cn, formatPrice } from "@/lib/utils"
import type { NegotiationNumbers as NegotiationNumbersData } from "@/lib/types"

interface NegotiationNumbersProps {
  data?: NegotiationNumbersData | null
  className?: string
}

const CONFIDENCE_LABEL: Record<string, string> = {
  alta: "confiança alta",
  media: "confiança média",
  baixa: "poucos comparáveis",
}

export function NegotiationNumbers({ data, className }: NegotiationNumbersProps) {
  if (!data) return null

  const { opening_offer, fair_value, walk_away, potential_saving, leverage, confidence, sample_count } = data
  const showSaving = potential_saving >= 150

  const figures = [
    { label: "Abre em", value: opening_offer, valueClass: "text-gold", hint: "a tua primeira oferta" },
    { label: "Valor justo", value: fair_value, valueClass: "text-foreground", hint: "o que vale no mercado" },
    { label: "Não passes de", value: walk_away, valueClass: "text-muted-foreground", hint: "acima disto, recusa" },
  ]

  return (
    <div className={cn("rounded-xl border border-gold/25 bg-card p-5", className)}>
      <div className="mb-4 flex items-center justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
          A tua estratégia
        </p>
        <p className="font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
          {CONFIDENCE_LABEL[confidence] || confidence}
          {sample_count > 0 ? ` · ${sample_count} anúncios` : ""}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-px overflow-hidden rounded-lg border border-border bg-border">
        {figures.map((f) => (
          <div key={f.label} className="bg-card px-3 py-4 text-center">
            <p className="mb-2 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
              {f.label}
            </p>
            <p className={cn("font-mono text-[clamp(15px,4.5vw,22px)] font-bold leading-none", f.valueClass)}>
              {formatPrice(f.value)}
            </p>
            <p className="mt-2 hidden text-[10px] font-light leading-tight text-muted-foreground/50 sm:block">
              {f.hint}
            </p>
          </div>
        ))}
      </div>

      {showSaving && (
        <p className="mt-4 text-center text-[13px] font-light text-muted-foreground">
          Poupança potencial:{" "}
          <span className="font-mono font-semibold text-success">
            até {formatPrice(potential_saving)}
          </span>
        </p>
      )}

      {leverage && leverage.length > 0 && (
        <div className="mt-4 flex flex-col gap-2 border-t border-border pt-4">
          <p className="mb-0.5 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/50">
            Os teus argumentos
          </p>
          {leverage.map((point, i) => (
            <div key={i} className="flex items-start gap-2.5">
              <span className="mt-0.5 shrink-0 text-xs text-gold">→</span>
              <span className="text-[13px] leading-relaxed text-muted-foreground">
                {point}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
