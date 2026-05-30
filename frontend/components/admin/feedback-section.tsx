interface FeedbackSectionProps {
  data: {
    satisfaction: Record<string, number>
    analysis_helpful: number
    analysis_not_helpful: number
    analysis_feedback_total: number
  }
}

export function FeedbackSection({ data }: FeedbackSectionProps) {
  const sat = data?.satisfaction || {}
  const totalSat = Object.values(sat).reduce((a, b) => a + (b || 0), 0)
  const helpful = data?.analysis_helpful ?? 0
  const notHelpful = data?.analysis_not_helpful ?? 0
  const totalHelp = helpful + notHelpful

  return (
    <div className="rounded-xl border border-border bg-card px-6 py-5">
      <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        Feedback
      </div>

      {totalSat > 0 && (
        <div className="mb-4">
          <div className="mb-2 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
            Satisfacao ({totalSat})
          </div>
          {Object.entries(sat).map(([key, count]) => (
            <div key={key} className="mb-1 flex items-center gap-2">
              <div className="w-[80px] font-mono text-[10px] text-muted-foreground">
                {key}
              </div>
              <div className="relative h-3 flex-1 overflow-hidden rounded bg-border/50">
                <div
                  className="h-full rounded bg-gold opacity-50"
                  style={{ width: `${(count / totalSat) * 100}%` }}
                />
              </div>
              <div className="w-[25px] text-right font-mono text-[10px] text-muted-foreground">
                {count}
              </div>
            </div>
          ))}
        </div>
      )}

      {totalHelp > 0 && (
        <div>
          <div className="mb-2 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
            Analise util? ({totalHelp})
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <div className="font-display text-[20px] text-green-500">
                {helpful}
              </div>
              <div className="font-mono text-[9px] text-muted-foreground">
                SIM
              </div>
            </div>
            <div className="text-center">
              <div className="font-display text-[20px] text-red-500">
                {notHelpful}
              </div>
              <div className="font-mono text-[9px] text-muted-foreground">
                NAO
              </div>
            </div>
            <div className="text-center">
              <div className="font-display text-[20px] text-gold">
                {totalHelp > 0 ? Math.round((helpful / totalHelp) * 100) : 0}%
              </div>
              <div className="font-mono text-[9px] text-muted-foreground">
                TAXA
              </div>
            </div>
          </div>
        </div>
      )}

      {totalSat === 0 && totalHelp === 0 && (
        <div className="font-mono text-[11px] text-muted-foreground">
          Sem feedback no periodo
        </div>
      )}
    </div>
  )
}
