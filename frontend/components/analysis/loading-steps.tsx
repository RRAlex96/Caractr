"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"

const STEPS = [
  "A recolher dados do anúncio",
  "A consultar referências de mercado",
  "A calcular km/ano e desgaste",
  "A compor a análise",
]

export function LoadingSteps() {
  const [step, setStep] = useState(0)
  const [dots, setDots] = useState("")

  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."))
    }, 400)
    const stepInterval = setInterval(() => {
      setStep((s) => (s < STEPS.length - 1 ? s + 1 : s))
    }, 2200)
    return () => {
      clearInterval(dotsInterval)
      clearInterval(stepInterval)
    }
  }, [])

  return (
    <div className="mt-14 py-10">
      <div className="mb-7 h-0.5 w-8 rounded-full bg-gold" />
      <p className="mb-6 font-mono text-[11px] uppercase tracking-[2px] text-gold">
        {STEPS[step]}{dots}
      </p>
      <div className="flex flex-col gap-2.5">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center gap-3">
            <div
              className={cn(
                "h-1.5 w-1.5 shrink-0 rounded-full transition-all duration-300",
                i <= step ? "bg-gold" : "bg-border",
                i > step && "opacity-30"
              )}
            />
            <p
              className={cn(
                "text-[13px] transition-all duration-300",
                i === step && "text-foreground opacity-100",
                i < step && "text-foreground opacity-50",
                i > step && "text-muted-foreground opacity-25"
              )}
            >
              {s}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
