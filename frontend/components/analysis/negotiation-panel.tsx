"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

interface NegotiationPanelProps {
  script?: string | null
  tips?: string[]
  className?: string
}

export function NegotiationPanel({ script, tips, className }: NegotiationPanelProps) {
  const [copied, setCopied] = useState(false)

  const hasContent = script || (tips && tips.length > 0)
  if (!hasContent) return null

  const handleCopy = async () => {
    if (!script) return
    try {
      await navigator.clipboard.writeText(script)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {}
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-border p-5",
        className
      )}
    >
      <div className="mb-3.5 flex items-center justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
          Como negociar
        </p>
        {script && (
          <button
            onClick={handleCopy}
            className={cn(
              "rounded-full border border-border px-2.5 py-1 font-mono text-[9px] uppercase tracking-[1px] transition-colors",
              copied
                ? "border-gold/40 text-gold"
                : "text-muted-foreground/50 hover:border-gold/30 hover:text-gold"
            )}
          >
            {copied ? "Copiado" : "Copiar"}
          </button>
        )}
      </div>

      {script && (
        <p
          className={cn(
            "text-[13px] leading-relaxed text-foreground",
            tips && tips.length > 0 && "mb-3.5"
          )}
        >
          {script}
        </p>
      )}

      {tips && tips.length > 0 && !script && (
        <div className="flex flex-col gap-2.5">
          {tips.map((tip, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="mt-0.5 shrink-0 text-xs text-gold">→</span>
              <span className="text-[13px] leading-relaxed text-muted-foreground">
                {tip}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
