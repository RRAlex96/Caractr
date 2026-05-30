"use client"

import { type RefObject } from "react"
import { cn } from "@/lib/utils"

interface AnalysisInputProps {
  url: string
  onUrlChange: (url: string) => void
  onSubmit: () => void
  loading: boolean
  inputRef?: RefObject<HTMLInputElement | null>
  className?: string
}

export function AnalysisInput({
  url,
  onUrlChange,
  onSubmit,
  loading,
  inputRef,
  className,
}: AnalysisInputProps) {
  return (
    <div className={className}>
      <div className="flex flex-wrap gap-2.5">
        <input
          ref={inputRef}
          type="url"
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSubmit()}
          placeholder="https://www.standvirtual.com/...  ·  olx.pt/..."
          disabled={loading}
          className={cn(
            "h-12 min-w-0 flex-1 rounded-[10px] border border-border bg-card px-5",
            "text-sm font-light text-foreground outline-none placeholder:text-muted-foreground/40",
            "transition-colors focus:border-gold focus:ring-1 focus:ring-gold/20",
            "disabled:pointer-events-none disabled:opacity-50"
          )}
        />
        <button
          onClick={onSubmit}
          disabled={loading || !url.trim()}
          className={cn(
            "h-12 shrink-0 rounded-[10px] px-7 text-[13px] font-semibold transition-all",
            "disabled:cursor-not-allowed",
            loading
              ? "border border-gold bg-transparent text-gold"
              : "bg-gold text-background hover:bg-gold-dark",
            !url.trim() && !loading && "opacity-35"
          )}
        >
          {loading ? "A analisar..." : "Analisar"}
        </button>
      </div>
      <p className="mt-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/35">
        Standvirtual · OLX · CustoJusto · Autosapo · Autoscout24 · Qualquer dealer
      </p>
    </div>
  )
}
