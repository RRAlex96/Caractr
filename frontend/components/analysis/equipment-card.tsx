"use client"

import { cn } from "@/lib/utils"
import type { AnalysisDetails } from "@/lib/types"

interface EquipmentCardProps {
  analysis: AnalysisDetails
  className?: string
}

const TIER_LABEL: Record<string, string> = {
  base: "Equipamento base",
  medio: "Bem equipado",
  alto: "Muito completo",
}

export function EquipmentCard({ analysis, className }: EquipmentCardProps) {
  const trim = analysis.trim_level
  const includes = analysis.trim_includes || []
  const extras = analysis.optional_extras || []
  const note = analysis.equipment_note
  // Fall back to the flat extras list if the split fields aren't present.
  const fallbackExtras = !includes.length && !extras.length ? analysis.key_extras || [] : []

  const hasContent = trim || includes.length || extras.length || fallbackExtras.length || note
  if (!hasContent) return null

  return (
    <div className={cn("rounded-xl border border-border bg-card p-5", className)}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
          Equipamento
        </p>
        {analysis.spec_tier && (
          <span className="font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
            {TIER_LABEL[analysis.spec_tier] || analysis.spec_tier}
          </span>
        )}
      </div>

      {/* Trim badge + plain-language note */}
      {trim && (
        <div className="mb-3 inline-flex items-center rounded-full border border-gold/30 bg-gold/5 px-3 py-1">
          <span className="font-mono text-[10px] uppercase tracking-[1px] text-gold">
            Versão {trim}
          </span>
        </div>
      )}
      {note && (
        <p className="mb-4 text-[15px] font-light leading-relaxed text-foreground">
          {note}
        </p>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        {includes.length > 0 && (
          <div>
            <p className="mb-2.5 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/50">
              De série (versão)
            </p>
            <div className="flex flex-col gap-2">
              {includes.map((item, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="mt-[5px] h-1 w-1 shrink-0 rounded-full bg-muted-foreground/40" />
                  <span className="text-[13px] leading-snug text-muted-foreground">{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {(extras.length > 0 || fallbackExtras.length > 0) && (
          <div>
            <p className="mb-2.5 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/50">
              {includes.length > 0 ? "Extras opcionais" : "Extras detetados"}
            </p>
            <div className="flex flex-col gap-2">
              {(extras.length ? extras : fallbackExtras).map((item, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="mt-0.5 shrink-0 text-xs text-gold">+</span>
                  <span className="text-[13px] leading-snug text-foreground">{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
