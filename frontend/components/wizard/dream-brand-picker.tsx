"use client"

import { cn } from "@/lib/utils"

interface DreamBrand {
  id: string
  name: string
  identity?: string
}

interface DreamBrandPickerProps {
  brands: DreamBrand[]
  selected?: string
  onSelect: (id: string) => void
  onContinue: () => void
  loading?: boolean
  className?: string
}

export function DreamBrandPicker({
  brands,
  selected,
  onSelect,
  onContinue,
  loading,
  className,
}: DreamBrandPickerProps) {
  return (
    <div className={className}>
      <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
      <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
        06 — Opcional
      </p>
      <h2 className="mb-3 font-display text-[clamp(28px,4vw,44px)] font-extrabold leading-[0.95] tracking-tight">
        Se dinheiro não fosse problema?
      </h2>
      <p className="mb-9 text-sm font-light leading-relaxed text-muted-foreground">
        A marca de sonho diz muito sobre ti. Escolhe uma — ou salta este passo.
      </p>

      {loading ? (
        <div className="py-12 font-mono text-[11px] tracking-[1px] text-muted-foreground">
          A personalizar opcoes...
        </div>
      ) : (
        <div className="border-t border-border">
          {brands.slice(0, 6).map((brand, idx) => {
            const isSelected = selected === brand.id

            return (
              <button
                key={brand.id}
                aria-label={`Selecionar ${brand.name}`}
                onClick={() => onSelect(brand.id)}
                className="group flex w-full items-center gap-5 border-b border-border py-[clamp(14px,2vw,20px)] text-left"
              >
                <span
                  className={cn(
                    "w-5 shrink-0 font-mono text-[10px] tracking-[0.05em] transition-colors",
                    isSelected ? "text-gold" : "text-muted-foreground"
                  )}
                >
                  {String(idx + 1).padStart(2, "0")}
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
                        "font-display text-[clamp(16px,2vw,20px)] font-bold tracking-tight transition-transform duration-300",
                        !isSelected && "group-hover:translate-x-2"
                      )}
                    >
                      {brand.name}
                    </span>
                  </div>
                  {brand.identity && (
                    <p
                      className={cn(
                        "mt-0.5 text-xs font-light text-muted-foreground transition-[margin-left] duration-300",
                        isSelected ? "ml-9" : "ml-0"
                      )}
                    >
                      {brand.identity}
                    </p>
                  )}
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
      )}

      <div className="mt-10">
        <button
          onClick={onContinue}
          className="rounded-full border border-border px-6 py-3 text-[13px] font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
        >
          {selected ? "continuar" : "saltar"}
        </button>
      </div>
    </div>
  )
}
