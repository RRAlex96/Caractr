"use client"

import { cn } from "@/lib/utils"

interface Option {
  value: string
  label: string
  desc?: string
}

interface QuestionCardProps {
  stepLabel: string
  question: string
  options: Option[]
  selected?: string
  onSelect: (value: string) => void
  className?: string
}

export function QuestionCard({
  stepLabel,
  question,
  options,
  selected,
  onSelect,
  className,
}: QuestionCardProps) {
  return (
    <div className={className}>
      <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
      <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        {stepLabel}
      </p>
      <h2 className="mb-10 font-display text-[clamp(28px,4vw,44px)] font-extrabold leading-[0.95] tracking-tight">
        {question}
      </h2>

      <div className="border-t border-border">
        {options.map((opt, idx) => {
          const isSelected = selected === opt.value
          const letter = String.fromCharCode(65 + idx)

          return (
            <button
              key={opt.value}
              aria-label={opt.label}
              onClick={() => onSelect(opt.value)}
              className="group flex w-full items-start gap-5 border-b border-border py-[clamp(18px,3vw,28px)] text-left"
            >
              <span
                className={cn(
                  "mt-0.5 w-5 shrink-0 font-mono text-[11px] tracking-[0.05em] transition-colors",
                  isSelected ? "text-gold" : "text-muted-foreground"
                )}
              >
                {letter}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-3">
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
                    {opt.label}
                  </span>
                </div>
                {opt.desc && (
                  <p
                    className={cn(
                      "mt-1 text-[13px] font-light text-muted-foreground transition-[margin-left] duration-300",
                      isSelected ? "ml-9" : "ml-0"
                    )}
                  >
                    {opt.desc}
                  </p>
                )}
              </div>
              <div
                className={cn(
                  "mt-2 h-2 w-2 shrink-0 rounded-full transition-all",
                  isSelected
                    ? "bg-gold"
                    : "border border-border bg-transparent"
                )}
              />
            </button>
          )
        })}
      </div>
    </div>
  )
}
