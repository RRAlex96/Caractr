"use client"

import { cn, formatPrice } from "@/lib/utils"
import type { PriceHistory as PriceHistoryData } from "@/lib/types"

interface PriceHistoryProps {
  data?: PriceHistoryData | null
  className?: string
}

export function PriceHistory({ data, className }: PriceHistoryProps) {
  if (!data) return null

  const { drop_total, last_change, relisted_before, rollback_suspected, first_price, current_price } = data
  const dropped = drop_total > 0

  // Nothing meaningful to show
  if (!dropped && !relisted_before) return null

  return (
    <div className={cn("rounded-xl border border-border bg-card p-5", className)}>
      <div className="mb-3 flex items-center justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
          Histórico do anúncio
        </p>
        <p className="font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/50">
          só o Caractr vê isto
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {dropped && (
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 shrink-0 text-xs text-success">↓</span>
            <p className="text-[14px] leading-relaxed text-foreground">
              O preço já <span className="font-semibold text-success">baixou {formatPrice(drop_total)}</span>
              {" — de "}
              <span className="font-mono">{formatPrice(first_price)}</span> para{" "}
              <span className="font-mono">{formatPrice(current_price)}</span>
              {last_change?.days_ago != null && last_change.days_ago <= 60
                ? `. A última descida foi há ${last_change.days_ago} ${last_change.days_ago === 1 ? "dia" : "dias"}.`
                : "."}
              {" "}O vendedor pode estar mais aberto a negociar.
            </p>
          </div>
        )}

        {relisted_before && !rollback_suspected && (
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 shrink-0 text-xs text-gold">↺</span>
            <p className="text-[14px] leading-relaxed text-muted-foreground">
              Este carro já tinha estado à venda antes. Não vendeu à primeira —
              pode ser margem para negociar, ou um sinal para perceber porquê.
            </p>
          </div>
        )}

        {rollback_suspected && (
          <div className="flex items-start gap-2.5 rounded-lg border border-danger/40 bg-danger/[0.06] p-3">
            <span className="mt-0.5 shrink-0 text-sm text-danger">⚠</span>
            <p className="text-[14px] leading-relaxed text-foreground">
              <span className="font-semibold text-danger">Atenção:</span> quando
              vimos este carro antes, tinha mais quilómetros. Uma quilometragem
              que <span className="font-semibold">desce</span> é sinal clássico de
              manipulação do conta-quilómetros. Confirma com cuidado.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
