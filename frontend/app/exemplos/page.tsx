"use client"

import { useState } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { EXAMPLES } from "@/lib/examples"
import { AnalysisView } from "@/components/analysis/analysis-view"

const TIER_DOT: Record<string, string> = {
  forte: "bg-success",
  razoavel: "bg-gold",
  cuidado: "bg-warning",
  evitar: "bg-danger",
}

export default function ExemplosPage() {
  const [sel, setSel] = useState(0)
  const ex = EXAMPLES[sel]

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-[680px] px-[clamp(20px,5vw,32px)] pt-24 md:pt-28">
        <Link
          href="/analisar"
          className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground transition-colors hover:text-gold"
        >
          ← Analisar o meu anúncio
        </Link>

        <div className="mb-2 mt-3 h-0.5 w-10 rounded-full bg-gold" />
        <p className="mb-1 font-mono text-[10px] uppercase tracking-[2px] text-gold">
          Exemplos
        </p>
        <h1 className="mb-3 font-display text-[clamp(26px,5vw,40px)] font-extrabold leading-[0.95] tracking-tight text-foreground">
          Análises reais, instantâneas
        </h1>
        <p className="mb-6 max-w-[520px] text-[15px] font-light leading-relaxed text-muted-foreground">
          Estas são análises verdadeiras de anúncios reais — carregadas na hora,
          sem espera. Escolhe um carro para ver o que o Caractr diz sobre ele.
        </p>

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((e, i) => {
            const l = e.data.listing
            return (
              <button
                key={e.slug}
                onClick={() => setSel(i)}
                className={cn(
                  "flex items-center gap-2 rounded-full border px-3.5 py-2 text-[13px] transition-colors",
                  i === sel
                    ? "border-gold bg-gold/[0.08] text-foreground"
                    : "border-border text-muted-foreground hover:border-foreground/20 hover:text-foreground"
                )}
              >
                <span className={cn("h-1.5 w-1.5 rounded-full", TIER_DOT[e.data.deal?.tier] || "bg-muted-foreground")} />
                {l.brand_name} {l.model_name}
                <span className="font-mono text-[11px] text-muted-foreground/60">{l.year}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Full, real analysis — rendered instantly from bundled data, no backend */}
      <AnalysisView key={ex.slug} data={ex.data} analysisId={sel + 1} />
    </div>
  )
}
