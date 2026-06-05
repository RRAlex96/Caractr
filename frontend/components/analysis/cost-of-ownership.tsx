"use client"

import { cn, formatPrice } from "@/lib/utils"
import type { CostOfOwnership as CostData } from "@/lib/types"

interface CostOfOwnershipProps {
  data?: CostData | null
  className?: string
}

export function CostOfOwnership({ data, className }: CostOfOwnershipProps) {
  if (!data) return null

  const {
    monthly_running,
    monthly_true,
    annual_fuel,
    annual_iuc,
    annual_maintenance,
    depreciation_monthly,
    assumptions,
  } = data

  const rows: { label: string; value: number | null }[] = [
    { label: "Combustível / energia", value: annual_fuel },
    { label: "IUC (imposto anual)", value: annual_iuc },
    { label: "Manutenção", value: annual_maintenance },
  ].filter((r) => r.value != null)

  const fuelUnit = assumptions.consumption_unit === "kwh" ? "kWh/100km" : "l/100km"

  return (
    <div className={cn("rounded-xl border border-border p-5", className)}>
      <div className="mb-4 flex items-center justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
          Custo de utilização
        </p>
        <p className="font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/50">
          estimativa
        </p>
      </div>

      {/* Hero monthly figure */}
      <div className="mb-4 flex items-end gap-5">
        <div>
          <p className="font-mono text-[clamp(26px,7vw,38px)] font-bold leading-none text-gold">
            {formatPrice(monthly_running)}
            <span className="ml-1 text-base font-normal text-muted-foreground">/mês</span>
          </p>
          <p className="mt-2 text-[11px] font-light text-muted-foreground/60">
            combustível + impostos + manutenção
          </p>
        </div>
        {monthly_true != null && (
          <div className="border-l border-border pl-5">
            <p className="font-mono text-xl font-bold leading-none text-foreground">
              {formatPrice(monthly_true)}
              <span className="ml-1 text-xs font-normal text-muted-foreground">/mês</span>
            </p>
            <p className="mt-2 text-[11px] font-light text-muted-foreground/60">
              custo real (com depreciação)
            </p>
          </div>
        )}
      </div>

      {/* Annual breakdown */}
      <div className="flex flex-col gap-2 border-t border-border pt-4">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between">
            <span className="text-[13px] font-light text-muted-foreground">{r.label}</span>
            <span className="font-mono text-[13px] text-foreground">
              {formatPrice(r.value as number)}
              <span className="text-[11px] text-muted-foreground/50">/ano</span>
            </span>
          </div>
        ))}
        {depreciation_monthly != null && (
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-light text-muted-foreground">
              Depreciação estimada
            </span>
            <span className="font-mono text-[13px] text-foreground">
              {formatPrice(depreciation_monthly * 12)}
              <span className="text-[11px] text-muted-foreground/50">/ano</span>
            </span>
          </div>
        )}
      </div>

      <p className="mt-4 text-[11px] font-light leading-relaxed text-muted-foreground/50">
        Pressupõe {assumptions.km_year.toLocaleString("pt-PT")} km/ano e ~
        {assumptions.consumption.toLocaleString("pt-PT")} {fuelUnit}. Seguro não
        incluído (varia com o condutor). IUC é uma estimativa — o valor exato
        depende das emissões registadas.
      </p>
    </div>
  )
}
