"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"

const QUICK_DIMS = [
  { value: "reliability", label: "Fiabilidade" },
  { value: "comfort",     label: "Conforto" },
  { value: "driving",     label: "Conducao" },
  { value: "economy",     label: "Economia" },
]

const QUICK_AVERSIONS = [
  { value: "fiabilidade", label: "Pouca fiabilidade" },
  { value: "conforto",    label: "Pouco conforto" },
  { value: "espaco",      label: "Pouco espaco" },
  { value: "potencia",    label: "Pouca potencia" },
]

const QUICK_BUDGETS = [
  { value: "10000", label: "10k" },
  { value: "15000", label: "15k" },
  { value: "20000", label: "20k" },
  { value: "30000", label: "30k" },
  { value: "40000", label: "40k+" },
]

interface QuickProfileProps {
  onComplete: (profile: Record<string, number>) => void
  className?: string
}

export function QuickProfile({ onComplete, className }: QuickProfileProps) {
  const [topDim,   setTopDim]   = useState("")
  const [aversion, setAversion] = useState("")
  const [budget,   setBudget]   = useState("")

  const canComplete = topDim && aversion && budget

  const buildQuickProfile = () => {
    const profile: Record<string, number> = {
      economy: 0.09, comfort: 0.09, driving: 0.09,
      practical: 0.09, status: 0.09, reliability: 0.09,
    }
    profile[topDim] = 0.35
    const secondDimMap: Record<string, string> = {
      reliability: "economy", economy: "reliability",
      comfort: "practical", practical: "comfort",
      driving: "comfort", status: "driving",
    }
    const second = secondDimMap[topDim] || "comfort"
    profile[second] = 0.20
    const total = Object.values(profile).reduce((a, b) => a + b, 0)
    Object.keys(profile).forEach((k) => {
      profile[k] = Math.round((profile[k] / total) * 10000) / 10000
    })
    localStorage.setItem("caractr_quick_profile", JSON.stringify({ profile, topDim, aversion, budget }))
    Analytics.quickProfileCompleted("", topDim, aversion, budget)
    onComplete(profile)
  }

  return (
    <div className={cn("rounded-2xl border border-border bg-card p-7", className)}>
      <div className="mb-4 h-0.5 w-8 rounded-full bg-gold" />
      <p className="mb-2 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        Para ti
      </p>
      <p className="mb-5 font-display text-[15px] font-bold leading-tight">
        Este carro e bom negocio.<br />Mas e bom <em>para ti</em>?
      </p>

      {/* Top dimension */}
      <div className="mb-5">
        <p className="mb-2.5 text-xs text-muted-foreground">O que mais importa?</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_DIMS.map((d) => (
            <button
              key={d.value}
              onClick={() => setTopDim(d.value)}
              className={cn(
                "rounded-full border px-4 py-2 text-[13px] transition-colors",
                topDim === d.value
                  ? "border-gold/60 bg-gold/10 text-gold"
                  : "border-border text-muted-foreground hover:border-gold/30 hover:text-gold"
              )}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* Aversion */}
      <div className="mb-5">
        <p className="mb-2.5 text-xs text-muted-foreground">O que e inaceitavel?</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_AVERSIONS.map((a) => (
            <button
              key={a.value}
              onClick={() => setAversion(a.value)}
              className={cn(
                "rounded-full border px-4 py-2 text-[13px] transition-colors",
                aversion === a.value
                  ? "border-gold/60 bg-gold/10 text-gold"
                  : "border-border text-muted-foreground hover:border-gold/30 hover:text-gold"
              )}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>

      {/* Budget */}
      <div className="mb-6">
        <p className="mb-2.5 text-xs text-muted-foreground">Orcamento maximo?</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_BUDGETS.map((b) => (
            <button
              key={b.value}
              onClick={() => setBudget(b.value)}
              className={cn(
                "rounded-full border px-4 py-2 text-[13px] transition-colors",
                budget === b.value
                  ? "border-gold/60 bg-gold/10 text-gold"
                  : "border-border text-muted-foreground hover:border-gold/30 hover:text-gold"
              )}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={buildQuickProfile}
        disabled={!canComplete}
        className={cn(
          "rounded-full border border-gold px-6 py-2.5 text-[13px] font-semibold transition-all",
          canComplete
            ? "bg-gold text-background hover:bg-gold-dark"
            : "cursor-not-allowed bg-transparent text-gold opacity-40"
        )}
      >
        Ver o meu veredicto pessoal
      </button>
    </div>
  )
}
