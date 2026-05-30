import { cn } from "@/lib/utils"
import type { Recommendation } from "@/lib/types"

interface ModelCardProps {
  rec: Recommendation
  rank: number
  isDismissed?: boolean
  /** Tag label for alternatives */
  tag?: string
  children?: React.ReactNode
  className?: string
}

export function ModelCard({
  rec,
  rank,
  isDismissed,
  tag,
  children,
  className,
}: ModelCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card p-7 transition-[border-color,opacity] duration-200",
        "hover:border-gold/40",
        isDismissed && "opacity-[0.42]",
        className
      )}
    >
      {/* Tag (stretch / wildcard / alternativa) */}
      {(rec.is_stretch || rec.is_wildcard || tag) && (
        <p className="mb-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/80">
          {tag
            ? tag
            : rec.is_stretch
              ? "Acima do orcamento — mas vale considerar"
              : "Fora do esperado — mas ouve-nos"}
        </p>
      )}

      {/* Rank + Name + Price */}
      <div className="mb-5 flex items-baseline gap-3">
        <span className="font-display text-[clamp(28px,4vw,48px)] font-extrabold leading-[0.75] text-border/40">
          {String(rank).padStart(2, "0")}
        </span>
        <div>
          <h3 className="font-display text-[17px] font-bold tracking-tight">
            {rec.full_name}
          </h3>
          {rec.price_range && (
            <span className="font-mono text-[11px] text-gold">
              {rec.price_range.min?.toLocaleString("pt-PT")} — {rec.price_range.max?.toLocaleString("pt-PT")} EUR
            </span>
          )}
        </div>
      </div>

      {/* Headline */}
      <p className="mb-3.5 font-display text-base font-normal leading-tight tracking-tight">
        {rec.headline}
      </p>

      {/* Reasons (top 2 for grid cards) */}
      <div
        className={cn(
          "flex flex-col gap-2",
          rec.tradeoff ? "mb-3" : "mb-5"
        )}
      >
        {rec.reasons?.slice(0, 2).map((r, j) => (
          <div key={j} className="flex items-start gap-2">
            <div className="mt-[7px] h-[3px] w-[3px] shrink-0 rounded-full bg-gold" />
            <p className="text-[13px] font-light leading-relaxed text-muted-foreground">{r}</p>
          </div>
        ))}
      </div>

      {/* Tradeoff */}
      {rec.tradeoff && (
        <div className="mb-5 border-l-2 border-border pl-3.5">
          <p className="text-xs font-light leading-relaxed text-muted-foreground/70">
            <span className="mr-1.5 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/50">
              Tradeoff
            </span>
            {rec.tradeoff}
          </p>
        </div>
      )}

      {/* Badges */}
      <div className="mb-1 flex flex-wrap gap-2">
        {rec.is_wildcard && (
          <span className="rounded-full bg-gold/10 px-3.5 py-1 font-mono text-[10px] tracking-[1px] text-gold">
            WILDCARD
          </span>
        )}
        {rec.is_stretch && (
          <span className="rounded-full bg-gold/10 px-3.5 py-1 font-mono text-[10px] tracking-[1px] text-gold">
            STRETCH
          </span>
        )}
        {rec.body_type && !rec.is_wildcard && !rec.is_stretch && (
          <span className="rounded-full border border-border px-3 py-0.5 font-mono text-[10px] text-muted-foreground">
            {rec.body_type.toUpperCase()}
          </span>
        )}
      </div>

      {/* Slot for InterestActions, TrustPanel, AdAnalysis etc */}
      {children}
    </div>
  )
}
