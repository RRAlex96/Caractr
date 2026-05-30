import { cn } from "@/lib/utils"
import { TIER_CONFIG, FIT_CONFIG, formatPrice, formatKm } from "@/lib/utils"
import { SourceBadge } from "@/components/shared/source-badge"
import type { AnalysisListing, AnalysisDeal, AnalysisDetails, FitData } from "@/lib/types"

const VERDICT_EMOTION: Record<string, string> = {
  forte:    "Este tipo de negocio nao dura muito.",
  razoavel: "Um negocio justo — avanca com confianca.",
  cuidado:  "Ha melhores opcoes no mercado neste momento.",
  evitar:   "Nao vale o risco. Continua a procurar.",
}

interface VerdictCardProps {
  listing: AnalysisListing
  deal: AnalysisDeal
  analysis: AnalysisDetails
  fit?: FitData | null
  sourceLabel?: string
  className?: string
}

export function VerdictCard({
  listing,
  deal,
  analysis,
  fit,
  sourceLabel,
  className,
}: VerdictCardProps) {
  const tier = deal.tier
  const tierConfig = TIER_CONFIG[tier]
  const fitConfig = fit?.fit_tier ? FIT_CONFIG[fit.fit_tier] : null

  return (
    <div
      className={cn(
        "rounded-2xl border p-7",
        `tier-${tier}`,
        className
      )}
    >
      {/* Source label */}
      {sourceLabel && (
        <div className="mb-3">
          <SourceBadge label={sourceLabel} />
        </div>
      )}

      {/* Dual verdict pills */}
      <div className="mb-2.5 flex flex-wrap items-start gap-3">
        <div className="flex flex-col gap-1">
          {fit && (
            <p className="font-mono text-[8px] uppercase tracking-[1.5px] text-muted-foreground">
              Negocio
            </p>
          )}
          <span
            className={cn(
              "font-mono text-[11px] font-bold uppercase tracking-[1.5px]",
              tierConfig?.color
            )}
          >
            {tierConfig?.label}
          </span>
        </div>

        {fit && fitConfig && (
          <div className="flex flex-col gap-1">
            <p className="font-mono text-[8px] uppercase tracking-[1.5px] text-muted-foreground">
              Para ti
            </p>
            <span
              className={cn(
                "font-mono text-[11px] font-bold uppercase tracking-[1.5px]",
                fitConfig?.color
              )}
            >
              {fit.fit_label || fit.fit_tier.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Emotional anchoring line */}
      {VERDICT_EMOTION[tier] && (
        <p className="mb-3.5 text-xs font-light leading-relaxed text-muted-foreground/70">
          {VERDICT_EMOTION[tier]}
          {fit?.fit_reason && (tier as string) !== (fit.fit_tier as string) && (
            <span className="ml-2 opacity-80">· {fit.fit_reason}</span>
          )}
        </p>
      )}

      {/* Model name */}
      {(listing.brand_name || listing.model_name) && (
        <p className="mb-2.5 font-display text-[clamp(22px,4vw,32px)] font-extrabold leading-none tracking-tight">
          {[listing.brand_name, listing.model_name].filter(Boolean).join(" ").toUpperCase()}
        </p>
      )}

      {/* Specs line */}
      <p className="mb-4 font-mono text-[11px] tracking-[0.5px] text-muted-foreground">
        {[
          listing.year,
          listing.km ? formatKm(listing.km) : null,
          listing.price ? formatPrice(listing.price) : null,
          listing.seller_type && listing.seller_type !== "desconhecido"
            ? listing.seller_type
            : null,
          listing.listing_age_days != null
            ? listing.listing_age_days <= 7
              ? "publicado esta semana"
              : `ha ${listing.listing_age_days} dias`
            : null,
        ]
          .filter(Boolean)
          .join("  ·  ")}
      </p>

      {/* Verdict reason */}
      {analysis.verdict_reason && (
        <p className="text-sm leading-relaxed text-foreground">
          {analysis.verdict_reason}
        </p>
      )}
    </div>
  )
}
