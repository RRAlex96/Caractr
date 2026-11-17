"use client"

import { useState } from "react"
import type { AnalysisResult } from "@/lib/types"
import { VerdictCard } from "@/components/analysis/verdict-card"
import { MetricsGrid } from "@/components/analysis/metrics-grid"
import { MarketBasis } from "@/components/analysis/market-basis"
import { AnomalyBadge } from "@/components/analysis/anomaly-badge"
import { EngineWatchList, KnownFailureAlert, RecallChecklist } from "@/components/analysis/dealbreaker-warning"
import { PriceHistory } from "@/components/analysis/price-history"
import { FlagsList } from "@/components/analysis/flags-list"
import { EngineCard } from "@/components/analysis/engine-card"
import { SellerRead } from "@/components/analysis/seller-read"
import { TextPanel } from "@/components/analysis/text-panel"
import { InspectionChecklist } from "@/components/analysis/inspection-checklist"
import { NegotiationPlan } from "@/components/analysis/negotiation-plan"
import { NegotiationNumbers } from "@/components/analysis/negotiation-numbers"
import { CostOfOwnership } from "@/components/analysis/cost-of-ownership"
import { EquipmentCard } from "@/components/analysis/equipment-card"
import { MaintenanceEstimate } from "@/components/analysis/maintenance-estimate"
import { DepreciationChart } from "@/components/analysis/depreciation-chart"
import { TrustPanel } from "@/components/shared/trust-panel"

/**
 * The analysis in the order a buyer uses it: the verdict, what to check, how
 * to negotiate. Everything else — market details, equipment, ownership costs,
 * depreciation, reliability data — is one tap away under "Ver análise completa",
 * instead of twenty blocks in a row.
 */
export function AnalysisBody({ result }: { result: AnalysisResult }) {
  const [more, setMore] = useState(false)
  const a = result.analysis
  const modelName = `${result.listing?.brand_name || ""} ${result.listing?.model_name || ""}`.trim() || undefined

  return (
    <div className="space-y-5">
      <KnownFailureAlert data={result.dealbreakers} />
      <AnomalyBadge anomaly={result.anomaly} />

      <VerdictCard listing={result.listing} deal={result.deal} analysis={a} fit={result.fit} sourceLabel={result.source_label} />
      <MetricsGrid deal={result.deal} analysis={a} />

      {a.verdict_narrative && (
        <TextPanel label="Em resumo" accent filled>
          {a.verdict_narrative}
        </TextPanel>
      )}

      <FlagsList greenFlags={(a.green_flags || []).slice(0, 3)} redFlags={(a.red_flags || []).slice(0, 3)} />

      {/* What to check before buying */}
      <EngineWatchList data={result.dealbreakers} />
      <RecallChecklist data={result.dealbreakers} year={result.listing?.year} />
      <InspectionChecklist items={(result.inspection_checklist || []).slice(0, 5)} />

      {/* How to negotiate (older stored analyses without a plan keep the numbers box) */}
      {result.negotiation_plan ? (
        <NegotiationPlan plan={result.negotiation_plan} analysisId={result.analysis_id} />
      ) : (
        <NegotiationNumbers data={result.negotiation} />
      )}

      <button
        type="button"
        onClick={() => setMore((v) => !v)}
        className="w-full rounded-xl border border-border px-5 py-3.5 text-[14px] text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground"
      >
        {more ? "Esconder detalhes" : "Ver análise completa — mercado, equipamento, custos e fiabilidade"}
      </button>

      {more && (
        <div className="space-y-5">
          <MarketBasis deal={result.deal} listing={result.listing} />
          <PriceHistory data={result.price_history} />
          <EquipmentCard analysis={a} />
          {a.extras_analysis && <TextPanel label="Equipamento & valor">{a.extras_analysis}</TextPanel>}
          {a.engine_analysis && <EngineCard engineCode={a.engine_code} engineAnalysis={a.engine_analysis} />}
          <SellerRead sellerAnalysis={a.seller_analysis} sellerRead={a.seller_read} />
          <CostOfOwnership data={result.cost_of_ownership} />
          {result.maintenance_estimate && <MaintenanceEstimate estimate={result.maintenance_estimate} />}
          {result.depreciation && <DepreciationChart depreciation={result.depreciation} currentPrice={result.listing.price} />}
          <TrustPanel reliability={result.reliability} reliabilityLimited={!result.reliability} modelName={modelName} />
        </div>
      )}
    </div>
  )
}
