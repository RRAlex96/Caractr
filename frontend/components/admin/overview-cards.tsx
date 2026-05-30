interface OverviewCardsProps {
  data: {
    unique_users: number
    sessions_started: number
    sessions_completed: number
    analyses_requested: number
    concierge_submissions: number
    total_events: number
  }
}

export function OverviewCards({ data }: OverviewCardsProps) {
  const cards = [
    { value: data.unique_users, label: "Utilizadores" },
    { value: data.sessions_started, label: "Wizards iniciados" },
    { value: data.sessions_completed, label: "Wizards completos" },
    { value: data.analyses_requested, label: "Analises pedidas" },
    { value: data.concierge_submissions, label: "Concierge" },
  ]

  return (
    <div className="mb-8 grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-3">
      {cards.map((c, i) => (
        <div key={i} className="rounded-xl border border-border bg-card px-5 py-4">
          <div className="font-display text-[28px] font-bold leading-none text-foreground">
            {(c.value ?? 0).toLocaleString()}
          </div>
          <div className="mt-1.5 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            {c.label}
          </div>
        </div>
      ))}
    </div>
  )
}
