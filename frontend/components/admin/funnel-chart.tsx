interface FunnelStep {
  event: string
  label: string
  count: number
  pct_of_start: number
  pct_of_prev: number
}

interface FunnelChartProps {
  steps: FunnelStep[]
}

export function FunnelChart({ steps }: FunnelChartProps) {
  const maxCount = steps[0]?.count || 1

  return (
    <div className="mb-8 rounded-xl border border-border bg-card px-6 py-5">
      <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        Funil de conversao
      </div>
      <div className="flex flex-col gap-2.5">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-[140px] shrink-0 text-right font-mono text-[10px] text-muted-foreground">
              {step.label}
            </div>
            <div className="relative h-6 flex-1 overflow-hidden rounded bg-border/50">
              <div
                className="h-full rounded bg-gold transition-[width] duration-500"
                style={{
                  width: `${Math.max(2, (step.count / maxCount) * 100)}%`,
                  opacity: 1 - i * 0.08,
                }}
              />
            </div>
            <div className="w-[50px] shrink-0 text-right font-mono text-[11px] text-foreground">
              {step.count}
            </div>
            <div className="w-[50px] shrink-0 font-mono text-[10px] text-muted-foreground">
              {step.pct_of_start}%
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
