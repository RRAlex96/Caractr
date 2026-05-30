interface TopModelsProps {
  recommended: { model_id?: number; name: string; count: number }[]
  analysed: { name: string; count: number }[]
}

export function TopModels({ recommended, analysed }: TopModelsProps) {
  return (
    <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="rounded-xl border border-border bg-card px-6 py-5">
        <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
          Top recomendados
        </div>
        {(recommended || []).slice(0, 8).map((m, i) => (
          <div
            key={i}
            className="flex justify-between border-b border-border py-1.5 last:border-0"
          >
            <span className="text-[13px] text-foreground">
              <span className="mr-2 font-mono text-[10px] text-muted-foreground">
                {i + 1}.
              </span>
              {m.name}
            </span>
            <span className="font-mono text-[11px] text-muted-foreground">
              {m.count}x
            </span>
          </div>
        ))}
        {(!recommended || recommended.length === 0) && (
          <div className="font-mono text-[11px] text-muted-foreground">
            Sem dados
          </div>
        )}
      </div>

      <div className="rounded-xl border border-border bg-card px-6 py-5">
        <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
          Top analisados
        </div>
        {(analysed || []).slice(0, 8).map((m, i) => (
          <div
            key={i}
            className="flex justify-between border-b border-border py-1.5 last:border-0"
          >
            <span className="text-[13px] text-foreground">
              <span className="mr-2 font-mono text-[10px] text-muted-foreground">
                {i + 1}.
              </span>
              {m.name}
            </span>
            <span className="font-mono text-[11px] text-muted-foreground">
              {m.count}x
            </span>
          </div>
        ))}
        {(!analysed || analysed.length === 0) && (
          <div className="font-mono text-[11px] text-muted-foreground">
            Sem dados
          </div>
        )}
      </div>
    </div>
  )
}
