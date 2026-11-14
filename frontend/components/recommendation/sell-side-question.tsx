"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"

const ANSWERS = [
  { value: "sell_privately", label: "Sim, vou vendê-lo" },
  { value: "trade_in", label: "Sim, para retoma" },
  { value: "no", label: "Não" },
] as const

/**
 * One tap, to size demand for a sell-side feature (plan: a candidate bet for
 * phase 3 if a quarter or more of buyers have a car to sell). Recorded as
 * `sell_side_answer`; nothing else is asked or stored.
 */
export function SellSideQuestion({ className }: { className?: string }) {
  const [answer, setAnswer] = useState<string | null>(null)

  return (
    <section className={cn("mx-[clamp(24px,5vw,80px)] rounded-xl border border-border bg-card p-[clamp(20px,4vw,28px)]", className)}>
      {answer ? (
        <p className="text-sm font-light text-muted-foreground">Obrigado, ajuda-nos a perceber o que construir a seguir.</p>
      ) : (
        <>
          <p className="text-[15px] text-foreground">Tens um carro para vender ou dar para retoma?</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {ANSWERS.map((a) => (
              <button
                key={a.value}
                onClick={() => {
                  setAnswer(a.value)
                  Analytics.sellSideAnswer(a.value)
                }}
                className="rounded-full border border-border px-4 py-2 text-[13px] text-muted-foreground transition-colors hover:border-gold hover:text-foreground"
              >
                {a.label}
              </button>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
