import { cn } from "@/lib/utils"

interface EngineCardProps {
  engineCode?: string | null
  engineAnalysis: string
  className?: string
}

export function EngineCard({ engineCode, engineAnalysis, className }: EngineCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-4 md:p-5",
        className
      )}
    >
      <div className="mb-2 flex items-center gap-2.5">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
          Motor
        </p>
        {engineCode && (
          <span className="rounded-full border border-gold/80 px-2.5 py-0.5 font-mono text-[10px] tracking-[0.5px] text-gold/80">
            {engineCode}
          </span>
        )}
      </div>
      <p className="text-[13px] leading-relaxed text-foreground">
        {engineAnalysis}
      </p>
    </div>
  )
}
