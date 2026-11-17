"use client"

import { cn } from "@/lib/utils"

interface BudgetPreset {
  value: string
  label: string
  min: number
  max: number
}

const BUDGET_PRESETS: BudgetPreset[] = [
  { value: "8_15",    label: "€8.000 — €15.000",  min: 8000,  max: 15000 },
  { value: "15_25",   label: "€15.000 — €25.000", min: 15000, max: 25000 },
  { value: "25_40",   label: "€25.000 — €40.000", min: 25000, max: 40000 },
  { value: "40_plus", label: "€40.000+",           min: 40000, max: 80000 },
]

const CONDITIONS = [
  { value: "usado", label: "Usado" },
  { value: "novo", label: "Novo" },
  { value: "indiferente", label: "Tanto faz" },
]

interface BudgetPickerProps {
  selected?: string
  condition?: string
  onCondition?: (value: string) => void
  onSelect: (value: string, min: number, max: number) => void
  onSubmit: () => void
  submitting?: boolean
  error?: string
  className?: string
}

export function BudgetPicker({
  selected,
  condition = "indiferente",
  onCondition,
  onSelect,
  onSubmit,
  submitting,
  error,
  className,
}: BudgetPickerProps) {
  return (
    <div className={className}>
      <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
      <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        08 — Orçamento
      </p>
      <h2 className="mb-3 font-display text-[clamp(28px,4vw,44px)] font-extrabold leading-[0.95] tracking-tight">
        Quanto queres investir?
      </h2>
      <p className="mb-10 text-sm font-light leading-relaxed text-muted-foreground">
        O orçamento é o último filtro — não o ponto de partida.
      </p>

      {onCondition && (
        <div className="mb-8">
          <p className="mb-3 text-[13px] text-muted-foreground">Novo ou usado?</p>
          <div className="flex flex-wrap gap-2">
            {CONDITIONS.map((c) => (
              <button
                key={c.value}
                type="button"
                aria-pressed={condition === c.value}
                onClick={() => onCondition(c.value)}
                className={cn(
                  "rounded-full border px-4 py-2 text-[13px] transition-colors",
                  condition === c.value
                    ? "border-gold bg-gold/10 text-gold"
                    : "border-border text-muted-foreground hover:border-gold/40"
                )}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mb-10 border-t border-border">
        {BUDGET_PRESETS.map((preset) => {
          const isSelected = selected === preset.value

          return (
            <button
              key={preset.value}
              aria-label={`Orçamento ${preset.label}`}
              onClick={() => onSelect(preset.value, preset.min, preset.max)}
              className="group flex w-full items-center gap-5 border-b border-border py-[clamp(18px,3vw,28px)] text-left"
            >
              <div className="flex flex-1 items-center gap-3">
                <div
                  className={cn(
                    "h-0.5 shrink-0 rounded-full bg-gold transition-[width] duration-300",
                    isSelected ? "w-6" : "w-0 group-hover:w-6"
                  )}
                />
                <span
                  className={cn(
                    "font-display text-[clamp(18px,2.5vw,24px)] font-bold tracking-tight transition-transform duration-300",
                    !isSelected && "group-hover:translate-x-2"
                  )}
                >
                  {preset.label}
                </span>
              </div>
              <div
                className={cn(
                  "h-2 w-2 shrink-0 rounded-full transition-all",
                  isSelected
                    ? "bg-gold"
                    : "border border-border bg-transparent"
                )}
              />
            </button>
          )
        })}
      </div>

      <button
        aria-label="Ver as minhas recomendações"
        onClick={onSubmit}
        disabled={submitting || !selected}
        className={cn(
          "rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-all hover:bg-gold-dark",
          (submitting || !selected) && "cursor-not-allowed opacity-50"
        )}
      >
        {submitting ? "a analisar..." : "ver resultados"}
      </button>

      {error && (
        <p className="mt-4 text-[13px] leading-relaxed text-danger">
          {error}
        </p>
      )}
    </div>
  )
}
