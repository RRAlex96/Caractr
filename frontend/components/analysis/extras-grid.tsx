import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

interface ExtrasGridProps {
  extras: string[]
  className?: string
}

export function ExtrasGrid({ extras, className }: ExtrasGridProps) {
  if (!extras || extras.length === 0) return null

  return (
    <div className={className}>
      <p className="mb-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
        Extras detectados
      </p>
      <div className="flex flex-wrap gap-1.5">
        {extras.map((e, i) => (
          <Badge
            key={i}
            variant="outline"
            className="rounded-full border-border px-3.5 py-1 font-mono text-[10px] tracking-[0.5px] text-muted-foreground"
          >
            {e}
          </Badge>
        ))}
      </div>
    </div>
  )
}
