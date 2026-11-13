interface BudgetDistProps {
  data: { bucket: string; count: number }[]
}

export function BudgetDist({ data }: BudgetDistProps) {
  const max = Math.max(...(data || []).map((d) => d.count), 1)

  return (
    <div className="rounded-xl border border-border bg-card px-6 py-5">
      <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        Orçamento
      </div>
      <div className="flex flex-col gap-2">
        {(data || []).map((b, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-[50px] text-right font-mono text-[10px] text-muted-foreground">
              {b.bucket}
            </div>
            <div className="relative h-4 flex-1 overflow-hidden rounded bg-border/50">
              <div
                className="h-full rounded bg-gold opacity-60"
                style={{ width: `${(b.count / max) * 100}%` }}
              />
            </div>
            <div className="w-[30px] text-right font-mono text-[10px] text-muted-foreground">
              {b.count}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
