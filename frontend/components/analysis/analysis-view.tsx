"use client"

import { useEffect } from "react"
import Link from "next/link"
import type { AnalysisResult } from "@/lib/types"
import { Analytics } from "@/lib/analytics"

import { AnalysisBody } from "@/components/analysis/analysis-body"
import { ShareButton } from "@/components/shared/share-button"
import { WizardBridge } from "@/components/shared/wizard-bridge"

interface AnalysisViewProps {
  data: AnalysisResult
  analysisId: number
  /** True on a real permalink (/analise/[id]) — the examples page reuses this view. */
  shared?: boolean
}

export function AnalysisView({ data, analysisId, shared = false }: AnalysisViewProps) {
  const tier = data.deal?.tier || "razoavel"
  const brand = data.listing?.brand_name || ""
  const model = data.listing?.model_name || ""
  const year = data.listing?.year

  // A visit to a shared analysis: the share loop's second half.
  useEffect(() => {
    if (shared) Analytics.sharedAnalysisViewed(analysisId)
  }, [shared, analysisId])

  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-[680px] px-[clamp(20px,5vw,32px)] pb-[clamp(32px,6vw,56px)] pt-24 md:pt-28">
        {/* Header */}
        <div className="mb-3">
          <Link
            href="/analisar"
            onClick={() => shared && Analytics.sharedCtaClicked(analysisId)}
            className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground transition-colors hover:text-gold"
          >
            ← Analisar outro
          </Link>
        </div>

        <div className="mb-2 h-0.5 w-10 rounded-full bg-gold" />
        <p className="mb-1 font-mono text-[10px] uppercase tracking-[2px] text-gold">
          Análise #{analysisId}
        </p>
        <h1 className="mb-8 font-display text-[clamp(28px,5vw,44px)] font-extrabold leading-[0.95] tracking-tight text-foreground">
          {brand} {model} {year}
        </h1>

        {/* Analysis components — same as /analisar */}
        <div className="space-y-5">
          <AnalysisBody result={data} />

          {/* Share */}
          <div className="flex items-center justify-end pt-2">
            <ShareButton
              brand={brand}
              model={model}
              year={year}
              tier={tier}
              priceDeltaPct={data.deal.price_delta_pct}
              priceDelta={data.deal.price_delta}
              analysisId={analysisId}
              listingUrl={data.source_url || `/analise/${analysisId}`}
            />
          </div>

          {/* Someone sent you this: the same, for your own car */}
          {shared && (
            <div className="rounded-xl border border-gold/30 bg-gold/[0.05] p-5 md:p-6">
              <p className="font-display text-[19px] font-bold text-foreground">Também andas à procura de carro?</p>
              <p className="mt-1 text-[14px] font-light leading-relaxed text-muted-foreground">
                Cola o link de qualquer anúncio e recebes esta mesma análise: se o preço é justo para aquele
                ano e motor, o que verificar e quanto oferecer. Grátis.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link
                  href="/analisar"
                  onClick={() => Analytics.sharedCtaClicked(analysisId)}
                  className="rounded-full bg-gold px-5 py-2.5 text-[13px] font-medium text-background transition-opacity hover:opacity-90"
                >
                  Analisar um anúncio
                </Link>
                <Link
                  href="/escolher"
                  onClick={() => Analytics.sharedCtaClicked(analysisId)}
                  className="rounded-full border border-border px-5 py-2.5 text-[13px] text-foreground transition-colors hover:border-gold"
                >
                  Descobrir que carro me serve
                </Link>
              </div>
            </div>
          )}

          {/* Caveat */}
          {data.caveat && (
            <p className="border-t border-border pt-4 text-[11px] leading-relaxed text-muted-foreground/35">
              {data.caveat}
            </p>
          )}

          {/* Wizard bridge */}
          <WizardBridge listingUrl={data.source_url} tier={tier} />
        </div>
      </div>
    </main>
  )
}
