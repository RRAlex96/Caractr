"use client"

import { useState } from "react"
import { cn, formatPrice, TIER_CONFIG, FIT_CONFIG } from "@/lib/utils"
import type { DealTier, FitTier } from "@/lib/utils"
import { analyseUrl } from "@/lib/api"
import { Analytics } from "@/lib/analytics"
import { MicroFeedback } from "@/components/shared/micro-feedback"
import { ShareButton } from "@/components/shared/share-button"
import type { AnalysisResult, UserProfile } from "@/lib/types"

interface AdAnalysisPanelProps {
  modelId: number
  sessionId: string
  userProfile: UserProfile
  rank?: number
  className?: string
}

export function AdAnalysisPanel({
  modelId,
  sessionId,
  userProfile,
  rank = 0,
  className,
}: AdAnalysisPanelProps) {
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState("")

  const analyse = async () => {
    if (!url.trim()) return
    setLoading(true)
    setError("")
    setResult(null)
    Analytics.adAnalysisRequested(sessionId, modelId, url.trim())
    try {
      const data = await analyseUrl(url.trim(), {
        modelId,
        userProfile,
      })
      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch {
      setError("Erro ao analisar. Verifica a ligacao e tenta novamente.")
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => {
          setOpen(true)
          Analytics.modelExpanded(sessionId, modelId, rank)
        }}
        className={cn(
          "mt-5 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground transition-colors hover:text-gold",
          className
        )}
      >
        <span className="text-sm">↗</span> Analisar anuncio
      </button>
    )
  }

  const tier = (result?.deal?.tier || result?.analysis?.verdict) as DealTier | undefined
  const tierConfig = tier ? TIER_CONFIG[tier] : null

  return (
    <div className={cn("mt-5 border-t border-border pt-5", className)}>
      <p className="mb-3 font-mono text-[10px] uppercase tracking-[1.5px] text-gold">
        Colar URL do anuncio
        <span className="ml-2.5 tracking-[0.5px] text-muted-foreground/50">
          Standvirtual · OLX · qualquer dealer
        </span>
      </p>

      <div className="flex gap-2">
        <input
          type="url"
          placeholder="https://www.standvirtual.com/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyse()}
          className="flex-1 rounded-lg border border-border bg-card px-3.5 py-2.5 text-xs text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
        />
        <button
          onClick={analyse}
          disabled={loading || !url.trim()}
          className={cn(
            "whitespace-nowrap rounded-lg border px-4.5 py-2.5 text-xs font-semibold transition-all",
            loading
              ? "border-gold bg-transparent text-gold"
              : "border-gold bg-gold text-background hover:bg-gold-dark",
            !url.trim() && "opacity-40"
          )}
        >
          {loading ? "A analisar..." : "Analisar"}
        </button>
      </div>

      {error && (
        <p className="mt-2.5 text-xs text-danger">{error}</p>
      )}

      {result && (
        <div className="mt-5">
          {/* Source + Dual Verdict */}
          <div className="mb-2">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              {result.source_label && (
                <span className="rounded-full border border-border px-2.5 py-0.5 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
                  {result.source_label}
                </span>
              )}
              {tierConfig && (
                <div className="flex flex-col items-start">
                  <span className="mb-0.5 font-mono text-[8px] uppercase tracking-[1px] text-muted-foreground/50">
                    Negocio
                  </span>
                  <span
                    className={cn(
                      "rounded-full px-3.5 py-1 font-mono text-[10px] font-semibold tracking-[1px]",
                      tierConfig.color,
                      tierConfig.bg
                    )}
                  >
                    {tierConfig.label}
                  </span>
                </div>
              )}
              {result.fit && (() => {
                const fitConfig = FIT_CONFIG[result.fit.fit_tier as FitTier]
                if (!fitConfig) return null
                return (
                  <div className="flex flex-col items-start">
                    <span className="mb-0.5 font-mono text-[8px] uppercase tracking-[1px] text-muted-foreground/50">
                      Para ti
                    </span>
                    <span
                      className={cn(
                        "rounded-full px-3.5 py-1 font-mono text-[10px] font-semibold tracking-[1px]",
                        fitConfig.color,
                        fitConfig.bg
                      )}
                    >
                      {result.fit.fit_label}
                    </span>
                  </div>
                )
              })()}
            </div>

            {result.analysis?.verdict_reason && (
              <p className="mb-1.5 text-sm font-medium leading-snug">
                {result.analysis.verdict_reason}
              </p>
            )}
            {tier && TIER_CONFIG[tier]?.emotion && (
              <p className="mb-1 text-xs font-light italic text-muted-foreground/70">
                {TIER_CONFIG[tier].emotion}
              </p>
            )}
            {result.fit?.fit_reason && (
              <p className="text-xs font-light text-muted-foreground/70">
                {result.fit.fit_reason}
              </p>
            )}
          </div>

          {/* Deal metrics */}
          <div className="mb-4 flex flex-wrap gap-5 rounded-lg border border-border bg-card p-3 px-4">
            {result.deal?.price_delta_pct != null && (
              <div>
                <p className="mb-0.5 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
                  Preco vs. mercado
                </p>
                <p
                  className={cn(
                    "font-mono text-[13px] font-semibold",
                    (result.deal.price_delta || 0) >= 0 ? "text-success" : "text-danger"
                  )}
                >
                  {(result.deal.price_delta || 0) >= 0 ? "−" : "+"}
                  {result.deal.price_delta_pct}%
                </p>
              </div>
            )}
            {result.deal?.km_per_year != null && (
              <div>
                <p className="mb-0.5 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
                  Km/ano
                </p>
                <p className="font-mono text-[13px] font-semibold">
                  {Math.round(result.deal.km_per_year).toLocaleString("pt-PT")}
                </p>
              </div>
            )}
            {result.deal?.market_avg_price != null && (
              <div>
                <p className="mb-0.5 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
                  Referencia mercado
                  <span className="ml-1.5 text-[8px] normal-case opacity-40">
                    {result.deal.market_data_source === "live" ? "tempo real" : "historico"}
                  </span>
                </p>
                <p className="font-mono text-[13px] font-semibold">
                  {Math.round(result.deal.market_avg_price).toLocaleString("pt-PT")} EUR
                </p>
              </div>
            )}
            {result.analysis?.spec_tier && (
              <div>
                <p className="mb-0.5 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
                  Versao
                </p>
                <p className="font-mono text-[13px] font-semibold">
                  {result.analysis.trim_level || result.analysis.spec_tier.toUpperCase()}
                </p>
              </div>
            )}
          </div>

          {/* Flags */}
          <div className="mb-3.5 flex flex-wrap gap-3">
            {(result.analysis?.green_flags || []).map((f, i) => (
              <div key={`g${i}`} className="flex items-center gap-1.5">
                <span className="text-xs text-success">✓</span>
                <span className="text-xs text-muted-foreground">{f}</span>
              </div>
            ))}
            {(result.analysis?.red_flags || []).map((f, i) => (
              <div key={`r${i}`} className="flex items-center gap-1.5">
                <span className="text-xs text-danger">⚠</span>
                <span className="text-xs text-muted-foreground">{f}</span>
              </div>
            ))}
          </div>

          {/* Key extras */}
          {result.analysis?.key_extras && result.analysis.key_extras.length > 0 && (
            <div className="mb-3.5">
              <p className="mb-2 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground">
                Extras detetados
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.analysis.key_extras.map((e, i) => (
                  <span
                    key={i}
                    className="rounded-full border border-border px-2.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                  >
                    {e}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Profile fit */}
          {result.analysis?.profile_fit && (
            <p className="mb-3 text-xs leading-relaxed text-muted-foreground">
              <span className="mr-2 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/50">
                Para ti
              </span>
              {result.analysis.profile_fit}
            </p>
          )}

          {/* Verdict narrative */}
          {result.analysis?.verdict_narrative && (
            <div className="mb-3 rounded-lg border border-border bg-card p-3 px-4">
              <p className="mb-1.5 font-mono text-[8px] uppercase tracking-[1.5px] text-gold">
                Veredicto
              </p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {result.analysis.verdict_narrative}
              </p>
            </div>
          )}

          {/* Negotiation numbers — the weapon */}
          {result.negotiation && (
            <div className="mb-3">
              <p className="mb-2 font-mono text-[8px] uppercase tracking-[1.5px] text-gold">
                A tua estratégia
              </p>
              <div className="grid grid-cols-3 gap-px overflow-hidden rounded-md border border-border bg-border">
                {[
                  { l: "Abre em", v: result.negotiation.opening_offer, c: "text-gold" },
                  { l: "Valor justo", v: result.negotiation.fair_value, c: "text-foreground" },
                  { l: "Máximo", v: result.negotiation.walk_away, c: "text-muted-foreground" },
                ].map((f) => (
                  <div key={f.l} className="bg-card px-2 py-2.5 text-center">
                    <p className="mb-1 font-mono text-[7px] uppercase tracking-[1px] text-muted-foreground">
                      {f.l}
                    </p>
                    <p className={cn("font-mono text-[13px] font-bold leading-none", f.c)}>
                      {formatPrice(f.v)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Negotiation */}
          {(result.analysis?.negotiation_script || (!result.negotiation && result.negotiation_tips?.length > 0)) && (
            <div className="mb-3">
              <p className="mb-2 font-mono text-[8px] uppercase tracking-[1.5px] text-muted-foreground">
                Como negociar
              </p>
              {result.analysis?.negotiation_script ? (
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {result.analysis.negotiation_script}
                </p>
              ) : (
                <div className="flex flex-col gap-1.5">
                  {result.negotiation_tips.map((tip, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="mt-0.5 shrink-0 text-[11px] text-gold">→</span>
                      <span className="text-xs leading-snug text-muted-foreground">{tip}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Inspection checklist */}
          {result.inspection_checklist?.length > 0 && (
            <div className="mb-3">
              <p className="mb-2 font-mono text-[8px] uppercase tracking-[1.5px] text-muted-foreground">
                O que verificar
              </p>
              <div className="flex flex-col gap-1.5">
                {result.inspection_checklist.map((item, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="mt-0.5 shrink-0 font-mono text-[9px] text-gold">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="text-xs leading-snug text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Caveat */}
          {result.caveat && (
            <p className="border-t border-border pt-2.5 text-[10px] leading-snug text-muted-foreground/40">
              {result.caveat}
            </p>
          )}

          {/* Micro-feedback + Share */}
          <div className="mt-1 flex flex-wrap items-center justify-between gap-2.5">
            <MicroFeedback listingUrl={url} />
            <ShareButton
              brand={result.listing?.brand_name}
              model={result.listing?.model_name}
              year={result.listing?.year}
              tier={tier}
              priceDeltaPct={result.deal?.price_delta_pct}
              priceDelta={result.deal?.price_delta}
              listingUrl={url}
            />
          </div>

          {/* Reset */}
          <button
            onClick={() => {
              setResult(null)
              setUrl("")
            }}
            className="mt-3 font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground transition-colors hover:text-gold"
          >
            Analisar outro anuncio ↩
          </button>
        </div>
      )}
    </div>
  )
}
