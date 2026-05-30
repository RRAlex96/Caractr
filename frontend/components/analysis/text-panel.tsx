import { cn } from "@/lib/utils"

interface TextPanelProps {
  label: string
  children: string
  /** Highlight the label in gold (e.g., for verdict narrative) */
  accent?: boolean
  /** Use card background */
  filled?: boolean
  className?: string
}

export function TextPanel({
  label,
  children,
  accent = false,
  filled = false,
  className,
}: TextPanelProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border p-4 md:p-5",
        filled && "bg-card",
        className
      )}
    >
      <p
        className={cn(
          "mb-2 font-mono text-[9px] uppercase tracking-[1.5px]",
          accent ? "text-gold" : "text-muted-foreground"
        )}
      >
        {label}
      </p>
      <p
        className={cn(
          "text-[13px] leading-relaxed",
          accent ? "text-foreground font-light" : "text-muted-foreground"
        )}
      >
        {children}
      </p>
    </div>
  )
}
