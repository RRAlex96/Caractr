import { cn } from "@/lib/utils"

interface SourceBadgeProps {
  label: string
  className?: string
}

export function SourceBadge({ label, className }: SourceBadgeProps) {
  if (!label) return null

  return (
    <span
      className={cn(
        "inline-block rounded-full border border-border px-2.5 py-0.5",
        "font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60",
        className
      )}
    >
      {label}
    </span>
  )
}
