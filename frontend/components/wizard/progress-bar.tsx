import { cn } from "@/lib/utils"

interface ProgressBarProps {
  current: number
  total: number
  className?: string
}

export function ProgressBar({ current, total, className }: ProgressBarProps) {
  const pct = ((current + 1) / total) * 100

  return (
    <div className={className}>
      <div className="mx-auto flex max-w-[640px] items-center justify-between">
        <span className="font-display text-sm font-bold tracking-[0.12em]">CARACTR</span>
        <span className="font-mono text-[11px] text-muted-foreground">
          {current + 1}/{total}
        </span>
      </div>
      <div className="mx-auto mt-6 h-0.5 max-w-[640px] rounded-full bg-border">
        <div
          className="h-full rounded-full bg-gold transition-[width] duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mx-auto mt-6 h-px max-w-[640px] bg-border" />
    </div>
  )
}
