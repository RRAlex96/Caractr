interface DailyTrendProps {
  data: { day: string; events: number; users: number }[]
}

export function DailyTrend({ data }: DailyTrendProps) {
  if (!data || data.length < 2) return null

  const W = 500
  const H = 140
  const PAD = 30
  const maxEvents = Math.max(...data.map((d) => d.events), 1)
  const maxUsers = Math.max(...data.map((d) => d.users), 1)

  const eventsPoints = data
    .map((d, i) => {
      const x = PAD + (i / (data.length - 1)) * (W - PAD * 2)
      const y = H - PAD - (d.events / maxEvents) * (H - PAD * 2)
      return `${x},${y}`
    })
    .join(" ")

  const usersPoints = data
    .map((d, i) => {
      const x = PAD + (i / (data.length - 1)) * (W - PAD * 2)
      const y = H - PAD - (d.users / maxUsers) * (H - PAD * 2)
      return `${x},${y}`
    })
    .join(" ")

  return (
    <div className="mb-8 rounded-xl border border-border bg-card px-6 py-5">
      <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        Tendência diária
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[600px]">
        <polyline
          points={eventsPoints}
          fill="none"
          className="stroke-gold"
          strokeWidth="2"
          opacity="0.8"
        />
        <polyline
          points={usersPoints}
          fill="none"
          stroke="#4aa35a"
          strokeWidth="2"
          opacity="0.6"
        />
        <text
          x={PAD}
          y={H - 5}
          className="fill-muted-foreground font-mono text-[9px]"
        >
          {data[0]?.day?.slice(5)}
        </text>
        <text
          x={W - PAD}
          y={H - 5}
          className="fill-muted-foreground font-mono text-[9px]"
          textAnchor="end"
        >
          {data[data.length - 1]?.day?.slice(5)}
        </text>
        <line
          x1={PAD}
          y1="12"
          x2={PAD + 20}
          y2="12"
          className="stroke-gold"
          strokeWidth="2"
        />
        <text
          x={PAD + 25}
          y="15"
          className="fill-muted-foreground font-mono text-[9px]"
        >
          eventos
        </text>
        <line
          x1={PAD + 85}
          y1="12"
          x2={PAD + 105}
          y2="12"
          stroke="#4aa35a"
          strokeWidth="2"
        />
        <text
          x={PAD + 110}
          y="15"
          className="fill-muted-foreground font-mono text-[9px]"
        >
          utilizadores
        </text>
      </svg>
    </div>
  )
}
