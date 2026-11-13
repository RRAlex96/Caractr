"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { formatPrice } from "@/lib/utils"
import type { ReliabilityData, MarketData } from "@/lib/types"

// ── Helpers ─────────────────────────────────────────────────────────────────

const DATA_QUALITY_LABELS: Record<string, { label: string; colorClass: string; hint: string }> = {
  strong_data: { label: "Dados fortes",    colorClass: "text-success border-success/40", hint: "Dados extensos de múltiplas fontes" },
  robust:      { label: "Dados robustos",  colorClass: "text-success border-success/40", hint: "Múltiplas fontes independentes" },
  limited:     { label: "Dados limitados", colorClass: "text-warning border-warning/40", hint: "Poucas fontes disponíveis" },
  prior_only:  { label: "Estimativa",      colorClass: "text-muted-foreground border-border", hint: "Baseado em padrões do segmento" },
}

function toBarPct(v: number): number {
  return Math.round(((v - 1) / 9) * 100)
}

function freshnessLabel(asOf: string | null | undefined): string {
  if (!asOf) return ""
  try {
    const d = new Date(asOf)
    const now = new Date()
    const days = Math.round((now.getTime() - d.getTime()) / 86400000)
    if (days <= 35) return `dados de ${days < 7 ? "esta semana" : "este mês"}`
    const months = Math.round(days / 30)
    return `dados de há ${months} ${months === 1 ? "mês" : "meses"}`
  } catch {
    return ""
  }
}

// ── Sub-components ──────────────────────────────────────────────────────────

function ReliabilityBlock({ reliability }: { reliability: ReliabilityData }) {
  const qMeta = DATA_QUALITY_LABELS[reliability.data_quality] ?? DATA_QUALITY_LABELS.prior_only
  const scorePct = toBarPct(reliability.score)
  const lowPct = toBarPct(reliability.ci_low)
  const highPct = toBarPct(reliability.ci_high)
  const ciWidthPct = highPct - lowPct

  return (
    <div>
      <div className="mb-2.5 flex items-baseline gap-2">
        <span className="font-mono text-[28px] font-bold tracking-tight text-foreground">
          {reliability.score.toFixed(1)}
        </span>
        <span className="font-mono text-xs text-muted-foreground/60">/ 10</span>
        <span
          className={cn(
            "ml-auto rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide",
            qMeta.colorClass
          )}
        >
          {qMeta.label}
        </span>
      </div>

      {/* CI bar */}
      <div className="relative mb-1.5 h-1.5 rounded-full bg-border">
        <div
          className="absolute h-full rounded-full bg-gold/30"
          style={{ left: `${lowPct}%`, width: `${ciWidthPct}%` }}
        />
        <div
          className="absolute -top-[3px] h-3 w-1 rounded-sm bg-gold"
          style={{ left: `${scorePct}%`, transform: "translateX(-50%)" }}
        />
      </div>

      <div className="flex justify-between font-mono text-[10px] text-muted-foreground/55">
        <span>IC 90%: {reliability.ci_low.toFixed(1)} — {reliability.ci_high.toFixed(1)}</span>
        <span>{qMeta.hint}</span>
      </div>
    </div>
  )
}

function MarketBlock({ market }: { market: MarketData }) {
  const freshness = freshnessLabel(market.as_of)
  const p10 = market.band?.p10
  const p90 = market.band?.p90
  const sampleCount = market.band?.sample_count

  return (
    <div>
      <div className="mb-2.5 flex items-baseline gap-2">
        <span className="font-mono text-[22px] font-bold text-foreground">
          {formatPrice(market.p50)}
        </span>
        <span className="font-mono text-[10px] text-muted-foreground/60">mediana</span>
        {sampleCount && (
          <span className="ml-auto font-mono text-[10px] text-gold">
            {sampleCount} anúncios
          </span>
        )}
      </div>

      {p10 != null && p90 != null && (
        <div className="mb-1.5 flex items-center gap-1.5">
          <span className="font-mono text-[11px] text-muted-foreground/70">{formatPrice(p10)}</span>
          <div className="relative h-1 flex-1 rounded-full bg-border">
            <div className="absolute inset-x-[10%] h-full rounded-full bg-gold/40" />
          </div>
          <span className="font-mono text-[11px] text-muted-foreground/70">{formatPrice(p90)}</span>
        </div>
      )}

      {freshness && (
        <span className="font-mono text-[10px] text-muted-foreground/50">{freshness}</span>
      )}
    </div>
  )
}

function VerificationBlock() {
  const items = [
    { id: "recalls", label: "Verificar recalls ativos (VIN check)" },
    { id: "inspection", label: "Inspeção independente por mecânico" },
    { id: "history", label: "Histórico de manutenção documentado" },
    { id: "vin", label: "Verificação de VIN (roubo / acidente)" },
  ]

  const [checked, setChecked] = useState<Set<string>>(new Set())

  const toggle = (id: string) => {
    setChecked((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item) => (
        <label
          key={item.id}
          className="flex cursor-pointer items-center gap-2.5"
          onClick={() => toggle(item.id)}
        >
          <div
            className={cn(
              "flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] border transition-colors",
              checked.has(item.id)
                ? "border-gold bg-gold"
                : "border-border bg-transparent"
            )}
          >
            {checked.has(item.id) && (
              <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                <path
                  d="M1 4L3.5 6.5L9 1"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-background"
                />
              </svg>
            )}
          </div>
          <span
            className={cn(
              "text-[13px] font-light transition-all",
              checked.has(item.id)
                ? "text-muted-foreground line-through"
                : "text-foreground"
            )}
          >
            {item.label}
          </span>
        </label>
      ))}
    </div>
  )
}

// ── Main component ──────────────────────────────────────────────────────────

interface TrustPanelProps {
  reliability?: ReliabilityData | null
  market?: MarketData | null
  modelName?: string
  reliabilityLimited?: boolean
  className?: string
}

export function TrustPanel({ reliability, market, modelName, reliabilityLimited, className }: TrustPanelProps) {
  if (!reliability && !market && !reliabilityLimited) return null

  return (
    <div className={cn("mt-5 border-t border-border pt-5", className)}>
      <span className="mb-4 block font-mono text-[10px] uppercase tracking-[0.15em] text-gold/80">
        Dados de confiança
      </span>

      {reliability && (
        <div className="mt-4 border-t border-border pt-4">
          <span className="mb-3 block font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground/55">
            Fiabilidade
          </span>
          <ReliabilityBlock reliability={reliability} />
        </div>
      )}

      {!reliability && reliabilityLimited && (
        <div className="mt-4 border-t border-border pt-4">
          <span className="mb-2 block font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground/55">
            Fiabilidade
          </span>
          <p className="text-[13px] font-light leading-relaxed text-muted-foreground">
            Ainda estamos a reunir dados de fiabilidade para este modelo. A
            análise acima baseia-se no preço, mercado e no que o anúncio revela.
          </p>
        </div>
      )}

      {market && (
        <div className="mt-4 border-t border-border pt-4">
          <span className="mb-3 block font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground/55">
            Preço de mercado
          </span>
          <MarketBlock market={market} />
        </div>
      )}

      <div className="mt-4 border-t border-border pt-4">
        <span className="mb-3 block font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground/55">
          Verificação antes de comprar
        </span>
        <VerificationBlock />
      </div>
    </div>
  )
}
