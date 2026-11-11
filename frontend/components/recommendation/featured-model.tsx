import { cn } from "@/lib/utils"
import type { Recommendation } from "@/lib/types"
import { DealbreakerBadge } from "@/components/shared/dealbreaker-badge"

interface FeaturedModelProps {
  rec: Recommendation
  isDismissed?: boolean
  children?: React.ReactNode
  className?: string
}

export function FeaturedModel({
  rec,
  isDismissed,
  children,
  className,
}: FeaturedModelProps) {
  return (
    <div
      className={cn(
        "max-w-[800px] transition-opacity duration-300",
        isDismissed && "opacity-[0.42]",
        className
      )}
    >
      <p className="mb-4 font-mono text-[10px] uppercase tracking-[1.5px] text-gold/80">
        A tua melhor correspondencia
      </p>

      {/* Rank + Name + Price */}
      <div className="mb-6 flex items-baseline gap-5">
        <span className="font-display text-[clamp(48px,8vw,96px)] font-extrabold leading-[0.75] text-border/30">
          01
        </span>
        <div>
          <h2 className="font-display text-[clamp(22px,3vw,32px)] font-bold leading-tight tracking-tight">
            {rec.full_name}
          </h2>
          {rec.price_range && (
            <span className="font-mono text-xs text-gold">
              {rec.price_range.min?.toLocaleString("pt-PT")} — {rec.price_range.max?.toLocaleString("pt-PT")} EUR
            </span>
          )}
        </div>
      </div>

      {/* Headline */}
      <p className="mb-7 max-w-[560px] font-display text-[clamp(20px,2.5vw,28px)] font-normal leading-[1.2] tracking-tight">
        {rec.headline}
      </p>

      {/* Full reasons list */}
      <div className="mb-8 flex flex-col gap-3">
        {rec.reasons?.map((r, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="mt-2 h-1 w-1 shrink-0 rounded-full bg-gold" />
            <p className="text-sm font-light leading-relaxed text-muted-foreground">
              {r}
            </p>
          </div>
        ))}
      </div>

      {/* Tradeoff */}
      {rec.tradeoff && (
        <div className="mb-5 border-l-2 border-border pl-5">
          <p className="text-[13px] font-light leading-relaxed text-muted-foreground">
            <span className="mr-2 font-mono text-[10px] uppercase tracking-[1px] text-muted-foreground/50">
              Tradeoff
            </span>
            {rec.tradeoff}
          </p>
        </div>
      )}

      {/* Badges */}
      <div className="mb-1 flex flex-wrap gap-2">
        <DealbreakerBadge data={rec.dealbreakers} />
        {rec.is_stretch && (
          <span className="rounded-full bg-gold/10 px-3.5 py-1 font-mono text-[10px] tracking-[1px] text-gold">
            STRETCH
          </span>
        )}
        {rec.is_wildcard && (
          <span className="rounded-full bg-gold/10 px-3.5 py-1 font-mono text-[10px] tracking-[1px] text-gold">
            WILDCARD
          </span>
        )}
      </div>

      {/* Slot for InterestActions, AdAnalysisPanel, TrustPanel */}
      {children}
    </div>
  )
}
