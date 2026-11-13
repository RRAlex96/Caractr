import { cn } from "@/lib/utils"

const TIER_COLORS: Record<string, string> = {
  forte: "bg-green-500",
  razoavel: "bg-gold",
  cuidado: "bg-amber-500",
  evitar: "bg-red-500",
}

const TIER_TEXT: Record<string, string> = {
  forte: "text-green-500",
  razoavel: "text-gold",
  cuidado: "text-amber-500",
  evitar: "text-red-500",
}

interface AnalysisStatsProps {
  stats: {
    total: number
    avg_deal_score: number
    tiers: Record<string, number>
  }
}

export function AnalysisStats({ stats }: AnalysisStatsProps) {
  const tiers = stats?.tiers || {}
  const total = Object.values(tiers).reduce((a, b) => a + (b || 0), 0)

  return (
    <div className="rounded-xl border border-border bg-card px-6 py-5">
      <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        Análises
      </div>
      <div className="mb-4 flex gap-6">
        <div>
          <div className="font-display text-[22px] font-bold text-foreground">
            {stats?.total ?? 0}
          </div>
          <div className="mt-1 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            Total
          </div>
        </div>
        <div>
          <div className="font-display text-[22px] font-bold text-foreground">
            {stats?.avg_deal_score ?? 0}
          </div>
          <div className="mt-1 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            Score medio
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        {(["forte", "razoavel", "cuidado", "evitar"] as const).map((tier) => (
          <div key={tier} className="flex items-center gap-2">
            <div
              className={cn(
                "w-[70px] font-mono text-[10px]",
                TIER_TEXT[tier]
              )}
            >
              {tier.toUpperCase()}
            </div>
            <div className="relative h-3.5 flex-1 overflow-hidden rounded bg-border/50">
              <div
                className={cn(
                  "h-full rounded opacity-70",
                  TIER_COLORS[tier]
                )}
                style={{
                  width: `${total > 0 ? ((tiers[tier] || 0) / total) * 100 : 0}%`,
                }}
              />
            </div>
            <div className="w-[30px] text-right font-mono text-[10px] text-muted-foreground">
              {tiers[tier] || 0}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
