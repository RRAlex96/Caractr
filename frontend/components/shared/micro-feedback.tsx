"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"

const FEEDBACK_REASONS = [
  "Preco parece errado",
  "Informacao incompleta",
  "Nao concordo com veredicto",
]

interface MicroFeedbackProps {
  listingUrl: string
  className?: string
}

export function MicroFeedback({ listingUrl, className }: MicroFeedbackProps) {
  const [vote, setVote] = useState<"up" | "down" | null>(null)

  const handleVote = (v: "up" | "down") => {
    setVote(v)
    Analytics.analysisFeedback("", listingUrl, v === "up")
  }

  const handleReason = (reason: string) => {
    Analytics.analysisFeedback("", listingUrl, false, reason)
  }

  if (vote === "up") {
    return (
      <p className={cn("text-[11px] text-muted-foreground/50", className)}>
        Obrigado pelo feedback.
      </p>
    )
  }

  return (
    <div className={className}>
      {vote === null && (
        <div className="flex items-center gap-2.5">
          <p className="text-[11px] text-muted-foreground/55">
            Esta analise foi util?
          </p>
          {(["up", "down"] as const).map((v) => (
            <button
              key={v}
              aria-label={v === "up" ? "Analise util" : "Analise nao util"}
              onClick={() => handleVote(v)}
              className="p-0.5 text-sm opacity-50 transition-opacity hover:opacity-100"
            >
              {v === "up" ? "👍" : "👎"}
            </button>
          ))}
        </div>
      )}
      {vote === "down" && (
        <div>
          <p className="mb-2 text-[11px] text-muted-foreground/55">
            O que correu mal?
          </p>
          <div className="flex flex-wrap gap-1.5">
            {FEEDBACK_REASONS.map((r) => (
              <button
                key={r}
                onClick={() => handleReason(r)}
                className="rounded-full border border-border px-3 py-1 text-[11px] text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
