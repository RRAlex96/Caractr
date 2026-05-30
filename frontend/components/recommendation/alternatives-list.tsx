"use client"

import { cn } from "@/lib/utils"
import { ModelCard } from "./model-card"
import { InterestActions } from "./interest-actions"
import { AdAnalysisPanel } from "./ad-analysis-panel"
import { TrustPanel } from "@/components/shared/trust-panel"
import type { Recommendation, UserProfile } from "@/lib/types"

interface AlternativesListProps {
  alternatives: Recommendation[]
  sessionId: string
  userProfile: UserProfile
  dismissedCount: number
  interests: number[]
  dismissed: Record<number, string>
  onInterest: (modelId: number) => void
  onDismiss: (modelId: number, reason: string) => void
  onUndo: (modelId: number) => void
  onFetchAlternatives: () => void
  alternativesLoading: boolean
  alternativesFetched: boolean
  alternativesError: boolean
  className?: string
}

export function AlternativesList({
  alternatives,
  sessionId,
  userProfile,
  dismissedCount,
  interests,
  dismissed,
  onInterest,
  onDismiss,
  onUndo,
  onFetchAlternatives,
  alternativesLoading,
  alternativesFetched,
  alternativesError,
  className,
}: AlternativesListProps) {
  if (dismissedCount === 0) return null

  return (
    <section className={cn("px-[clamp(24px,5vw,80px)] pb-[clamp(40px,5vw,56px)]", className)}>
      {/* CTA to fetch alternatives */}
      {!alternativesFetched && !alternativesLoading && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-dashed border-border p-5 px-6">
          <p className="text-[13px] leading-snug text-muted-foreground">
            <span className="mr-2.5 font-mono text-[9px] uppercase tracking-[1px] text-gold">
              {dismissedCount === 1 ? "1 descartado" : `${dismissedCount} descartados`}
            </span>
            Usamos o teu feedback para ajustar o perfil. Queres ver alternativas?
          </p>
          <button
            onClick={onFetchAlternatives}
            className="whitespace-nowrap rounded-full border border-gold px-5.5 py-2 font-mono text-[10px] uppercase tracking-[1px] text-gold transition-colors hover:bg-gold/[0.08]"
          >
            Ver alternativas →
          </button>
        </div>
      )}

      {/* Loading */}
      {alternativesLoading && (
        <div className="py-10 text-center">
          <p className="font-mono text-[10px] uppercase tracking-[2px] text-muted-foreground/60">
            A ajustar o perfil e procurar alternativas...
          </p>
        </div>
      )}

      {/* Error */}
      {alternativesFetched && alternativesError && (
        <p className="py-6 text-center text-[13px] text-muted-foreground/50">
          Nao encontramos alternativas suficientemente diferentes. Tenta refinar o perfil.
        </p>
      )}

      {/* Alternative cards */}
      {alternatives.length > 0 && (
        <>
          <div className="mb-5 flex items-center gap-4">
            <div className="h-px w-8 bg-gold/40" />
            <p className="font-mono text-[9px] uppercase tracking-[2px] text-gold/70">
              Alternativas — baseadas no teu feedback
            </p>
          </div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,320px),1fr))] gap-3">
            {alternatives.map((rec, i) => (
              <ModelCard
                key={`alt-${rec.model_id || i}`}
                rec={rec}
                rank={0}
                isDismissed={!!dismissed[rec.model_id]}
                tag="Alternativa"
              >
                <InterestActions
                  modelId={rec.model_id}
                  isInterested={interests.includes(rec.model_id)}
                  dismissReason={dismissed[rec.model_id]}
                  onInterest={onInterest}
                  onDismiss={onDismiss}
                  onUndo={onUndo}
                  className="mt-5"
                />
                <AdAnalysisPanel
                  modelId={rec.model_id}
                  sessionId={sessionId}
                  userProfile={userProfile}
                  rank={10 + i}
                />
                <TrustPanel
                  reliability={rec.reliability}
                  market={rec.market}
                  modelName={rec.full_name}
                />
              </ModelCard>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
