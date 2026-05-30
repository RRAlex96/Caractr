import type { ConciergeStats } from "@/lib/api"
import { cn } from "@/lib/utils"

interface ConciergeStatsProps {
  stats: ConciergeStats | null
}

export function ConciergeStatsCards({ stats }: ConciergeStatsProps) {
  if (!stats) return null

  const cards = [
    { value: stats.total, label: "Total" },
    { value: stats.by_status.new || 0, label: "Novos", accent: true },
    { value: stats.by_status.contacted || 0, label: "Contactados" },
    { value: stats.by_status.searching || 0, label: "A pesquisar" },
    { value: stats.by_status.delivered || 0, label: "Entregues" },
    { value: stats.by_status.closed || 0, label: "Fechados" },
  ]

  return (
    <div className="mb-6">
      <div className="mb-4 grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-2">
        {cards.map((c, i) => (
          <div
            key={i}
            className={cn(
              "rounded-lg border px-4 py-3",
              c.accent
                ? "border-gold/30 bg-gold/[0.05]"
                : "border-border bg-card"
            )}
          >
            <div
              className={cn(
                "font-display text-xl font-bold leading-none",
                c.accent ? "text-gold" : "text-foreground"
              )}
            >
              {c.value}
            </div>
            <div className="mt-1 font-mono text-[8px] uppercase tracking-[1.5px] text-muted-foreground">
              {c.label}
            </div>
          </div>
        ))}
      </div>

      {/* Free slots remaining */}
      <div className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-2.5">
        <span className="font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground">
          Oferta de lancamento
        </span>
        <span className="font-mono text-[11px] text-gold">
          {stats.free_remaining} de {stats.free_limit} restantes
        </span>
        {stats.avg_hours_to_delivery !== null && (
          <span className="font-mono text-[10px] text-muted-foreground">
            Tempo medio: {stats.avg_hours_to_delivery}h
          </span>
        )}
      </div>
    </div>
  )
}
