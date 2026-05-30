import { cn, formatPrice } from "@/lib/utils"

interface MaintenanceEstimateProps {
  estimate: number
  className?: string
}

export function MaintenanceEstimate({ estimate, className }: MaintenanceEstimateProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 rounded-xl border border-border px-5 py-3.5",
        className
      )}
    >
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
        Manutencao estimada / ano
      </p>
      <p className="font-mono text-base font-bold text-foreground">
        ~{formatPrice(Math.round(estimate))}
      </p>
    </div>
  )
}
