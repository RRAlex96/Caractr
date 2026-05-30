import { cn } from "@/lib/utils"

interface InspectionChecklistProps {
  items: string[]
  className?: string
}

export function InspectionChecklist({ items, className }: InspectionChecklistProps) {
  if (!items || items.length === 0) return null

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-5",
        className
      )}
    >
      <p className="mb-3.5 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
        O que verificar
      </p>
      <div className="flex flex-col gap-2.5">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className="mt-0.5 shrink-0 font-mono text-[10px] text-gold">
              {String(i + 1).padStart(2, "0")}
            </span>
            <span className="text-[13px] leading-relaxed text-muted-foreground">
              {item}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
