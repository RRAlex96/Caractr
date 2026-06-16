"use client"

import Link from "next/link"
import type { AnalysisResult } from "@/lib/types"

import { VerdictCard } from "@/components/analysis/verdict-card"
import { MetricsGrid } from "@/components/analysis/metrics-grid"
import { MarketBasis } from "@/components/analysis/market-basis"
import { AnomalyBadge } from "@/components/analysis/anomaly-badge"
import { FlagsList } from "@/components/analysis/flags-list"
import { EngineCard } from "@/components/analysis/engine-card"
import { SellerRead } from "@/components/analysis/seller-read"
import { TextPanel } from "@/components/analysis/text-panel"
import { InspectionChecklist } from "@/components/analysis/inspection-checklist"
import { NegotiationPanel } from "@/components/analysis/negotiation-panel"
import { NegotiationNumbers } from "@/components/analysis/negotiation-numbers"
import { CostOfOwnership } from "@/components/analysis/cost-of-ownership"
import { EquipmentCard } from "@/components/analysis/equipment-card"
import { MaintenanceEstimate } from "@/components/analysis/maintenance-estimate"
import { DepreciationChart } from "@/components/analysis/depreciation-chart"
import { TrustPanel } from "@/components/shared/trust-panel"
import { ShareButton } from "@/components/shared/share-button"
import { WizardBridge } from "@/components/shared/wizard-bridge"

interface AnalysisViewProps {
  data: AnalysisResult
  analysisId: number
}

export function AnalysisView({ data, analysisId }: AnalysisViewProps) {
  const tier = data.deal?.tier || "razoavel"
  const brand = data.listing?.brand_name || ""
  const model = data.listing?.model_name || ""
  const year = data.listing?.year

  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-[680px] px-[clamp(20px,5vw,32px)] pb-[clamp(32px,6vw,56px)] pt-24 md:pt-28">
        {/* Header */}
        <div className="mb-3">
          <Link
            href="/analisar"
            className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground transition-colors hover:text-gold"
          >
            ← Analisar outro
          </Link>
        </div>

        <div className="mb-2 h-0.5 w-10 rounded-full bg-gold" />
        <p className="mb-1 font-mono text-[10px] uppercase tracking-[2px] text-gold">
          Analise #{analysisId}
        </p>
        <h1 className="mb-8 font-display text-[clamp(28px,5vw,44px)] font-extrabold leading-[0.95] tracking-tight text-foreground">
          {brand} {model} {year}
        </h1>

        {/* Analysis components — same as /analisar */}
        <div className="space-y-5">
          <AnomalyBadge anomaly={data.anomaly} />

          <VerdictCard
            listing={data.listing}
            deal={data.deal}
            analysis={data.analysis}
            fit={data.fit}
            sourceLabel={data.source_label}
          />

          <MetricsGrid deal={data.deal} analysis={data.analysis} />

          <MarketBasis deal={data.deal} listing={data.listing} />

          <EquipmentCard analysis={data.analysis} />

          <FlagsList
            greenFlags={data.analysis.green_flags || []}
            redFlags={data.analysis.red_flags || []}
          />

          {data.analysis.engine_analysis && (
            <EngineCard
              engineCode={data.analysis.engine_code}
              engineAnalysis={data.analysis.engine_analysis}
            />
          )}

          <SellerRead
            sellerAnalysis={data.analysis.seller_analysis}
            sellerRead={data.analysis.seller_read}
          />

          {data.analysis.verdict_narrative && (
            <TextPanel label="Veredicto" accent filled>
              {data.analysis.verdict_narrative}
            </TextPanel>
          )}

          {data.analysis.extras_analysis && (
            <TextPanel label="Equipamento & valor">
              {data.analysis.extras_analysis}
            </TextPanel>
          )}

          <InspectionChecklist items={data.inspection_checklist || []} />

          <NegotiationNumbers data={data.negotiation} />

          <NegotiationPanel
            script={data.analysis.negotiation_script}
            tips={data.negotiation ? [] : data.negotiation_tips || []}
          />

          <CostOfOwnership data={data.cost_of_ownership} />

          {data.maintenance_estimate && (
            <MaintenanceEstimate estimate={data.maintenance_estimate} />
          )}

          {data.depreciation && (
            <DepreciationChart
              depreciation={data.depreciation}
              currentPrice={data.listing.price}
            />
          )}

          <TrustPanel
            reliability={data.reliability}
            reliabilityLimited={!data.reliability}
            modelName={`${brand} ${model}`.trim() || undefined}
          />

          {/* Share */}
          <div className="flex items-center justify-end pt-2">
            <ShareButton
              brand={brand}
              model={model}
              year={year}
              tier={tier}
              priceDeltaPct={data.deal.price_delta_pct}
              priceDelta={data.deal.price_delta}
              listingUrl={data.source_url || `/analise/${analysisId}`}
            />
          </div>

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
