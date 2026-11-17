import type { RunningCost } from "@/lib/types"

const FUEL: Record<string, string> = {
  eletrico: "elétrico",
  hibrido: "híbrido",
  gasolina: "gasolina",
  diesel: "gasóleo",
  gpl: "GPL",
}

/** Monthly fuel or electricity cost of the recommended car, with the prices it
 *  assumes. Shown only when the consumption figure is real — never estimated. */
export function RunningCostLine({ cost }: { cost?: RunningCost | null }) {
  if (!cost) return null
  const km = cost.km_month.toLocaleString("pt-PT")
  return (
    <div className="mb-4 rounded-md border border-border/70 px-3.5 py-2.5">
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/70">
        Custo de {cost.fuel === "eletrico" ? "carregamento" : "combustível"} · {km} km/mês
      </p>
      <p className="mt-1 text-[14px] text-foreground">
        <span className="font-mono font-bold text-gold">~{cost.eur_month} €/mês</span>
        <span className="ml-2 text-[12px] text-muted-foreground">
          {FUEL[cost.fuel] || cost.fuel}, {cost.consumption.toLocaleString("pt-PT")} {cost.unit}
        </span>
      </p>
      {cost.eur_month_home != null && cost.eur_month_public != null && (
        <p className="mt-0.5 text-[11px] text-muted-foreground/80">
          Só em casa ~{cost.eur_month_home} €/mês · só na rede pública ~{cost.eur_month_public} €/mês
        </p>
      )}
      <p className="mt-0.5 text-[10px] text-muted-foreground/60">{cost.price_note}</p>
    </div>
  )
}
