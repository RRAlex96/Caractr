import { cn } from "@/lib/utils"

interface SellerReadProps {
  sellerAnalysis?: string | null
  sellerRead?: string | null
  className?: string
}

export function SellerRead({ sellerAnalysis, sellerRead, className }: SellerReadProps) {
  if (!sellerAnalysis && !sellerRead) return null

  return (
    <div className={cn("flex flex-col gap-5", className)}>
      {/* Seller analysis */}
      {sellerAnalysis && (
        <div className="rounded-xl border border-border p-4 md:p-5">
          <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            Análise do vendedor
          </p>
          <p className="text-[13px] leading-relaxed text-muted-foreground">
            {sellerAnalysis}
          </p>
        </div>
      )}

      {/* Seller read — psychology/motivation */}
      {sellerRead && (
        <div className="rounded-xl border border-border p-4 md:p-5">
          <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            Leitura do vendedor
          </p>
          <p className="text-[13px] leading-relaxed text-muted-foreground">
            {sellerRead}
          </p>
        </div>
      )}
    </div>
  )
}
