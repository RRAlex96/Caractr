import { cn } from "@/lib/utils"

interface AnalysisErrorProps {
  error: string
  className?: string
}

function categorizeError(error: string): string {
  const lower = error.toLowerCase()
  if (lower.includes("aceder") || lower.includes("anuncio")) return "Anuncio inacessivel"
  if (lower.includes("modelo")) return "Modelo nao registado"
  if (lower.includes("dados")) return "Dados de mercado limitados"
  return "Erro na analise"
}

export function AnalysisError({ error, className }: AnalysisErrorProps) {
  const category = categorizeError(error)
  const isAccess = category === "Anuncio inacessivel"

  return (
    <div
      className={cn(
        "rounded-xl border border-danger/25 bg-danger/5 p-5 md:p-6",
        className
      )}
    >
      <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-danger">
        {category}
      </p>
      <p className="text-[13px] leading-relaxed text-muted-foreground">
        {error}
      </p>
      {isAccess && (
        <p className="mt-2 text-xs text-muted-foreground/60">
          Tenta outro URL ou verifica se o anuncio ainda esta publicado.
        </p>
      )}
    </div>
  )
}
