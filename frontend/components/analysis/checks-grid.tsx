import { cn } from "@/lib/utils"

const CHECKS = [
  { label: "PREÇO VS. MERCADO", desc: "Comparamos com anúncios reais da mesma marca e modelo." },
  { label: "KM / ANO",         desc: "Calculamos se o desgaste é compatível com o ano de matrícula." },
  { label: "VENDEDOR",         desc: "Particular ou dealer — cada um tem padrões diferentes." },
  { label: "EXTRAS",           desc: "Identificamos equipamentos relevantes que afetam o valor." },
]

interface ChecksGridProps {
  className?: string
}

export function ChecksGrid({ className }: ChecksGridProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-px overflow-hidden rounded-xl border border-border bg-border",
        className
      )}
    >
      {CHECKS.map((c) => (
        <div key={c.label} className="bg-card p-4">
          <p className="mb-1.5 font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
            {c.label}
          </p>
          <p className="text-xs leading-relaxed text-muted-foreground">
            {c.desc}
          </p>
        </div>
      ))}
    </div>
  )
}
