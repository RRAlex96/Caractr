import { cn } from "@/lib/utils"

interface FlagsListProps {
  greenFlags: string[]
  redFlags: string[]
  className?: string
}

export function FlagsList({ greenFlags, redFlags, className }: FlagsListProps) {
  if (greenFlags.length === 0 && redFlags.length === 0) return null

  return (
    <div
      className={cn(
        "flex flex-col gap-2.5 rounded-xl border border-border bg-card p-5",
        className
      )}
    >
      <p className="mb-1 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
        Pontos de análise
      </p>
      {greenFlags.map((f, i) => (
        <div key={`g${i}`} className="flex items-start gap-3">
          <span className="mt-0.5 shrink-0 text-xs font-bold text-success">✓</span>
          <span className="text-[13px] leading-relaxed text-muted-foreground">{f}</span>
        </div>
      ))}
      {redFlags.map((f, i) => (
        <div key={`r${i}`} className="flex items-start gap-3">
          <span className="mt-0.5 shrink-0 text-xs font-bold text-danger">⚠</span>
          <span className="text-[13px] leading-relaxed text-muted-foreground">{f}</span>
        </div>
      ))}
    </div>
  )
}
