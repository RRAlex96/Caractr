"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"
import { refreshRecommendations } from "@/lib/api"
import type { RecommendationResult, Recommendation } from "@/lib/types"

import { ProfileHeader } from "@/components/recommendation/profile-header"
import { FeaturedModel } from "@/components/recommendation/featured-model"
import { ModelCard } from "@/components/recommendation/model-card"
import { InterestActions } from "@/components/recommendation/interest-actions"
import { AdAnalysisPanel } from "@/components/recommendation/ad-analysis-panel"
import { AlternativesList } from "@/components/recommendation/alternatives-list"
import { ConciergeCTA } from "@/components/recommendation/concierge-cta"
import { TrustPanel } from "@/components/shared/trust-panel"

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ResultadosPage() {
  const router = useRouter()
  const [data, setData] = useState<RecommendationResult | null>(null)
  const [interests, setInterests] = useState<number[]>([])
  const [dismissed, setDismissed] = useState<Record<number, string>>({})
  const [alternatives, setAlternatives] = useState<Recommendation[]>([])
  const [alternativesLoading, setAlternativesLoading] = useState(false)
  const [alternativesFetched, setAlternativesFetched] = useState(false)
  const [alternativesError, setAlternativesError] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem("caractr_results")
    if (stored) {
      const parsed = JSON.parse(stored) as RecommendationResult
      setData(parsed)
      const recs = parsed.recommendations || []
      Analytics.resultsViewed(
        parsed.session_id || "",
        recs.length,
        recs.some((r) => r.is_wildcard),
        recs.some((r) => r.is_stretch)
      )
    } else {
      router.push("/escolher")
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!data) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="font-mono text-[11px] uppercase tracking-[1px] text-muted-foreground">
          A carregar...
        </p>
      </main>
    )
  }

  const recs = data.recommendations || []
  const first = recs[0]
  const rest = recs.slice(1)
  const allModels = [...recs, ...alternatives]
  const interestedRecs = allModels.filter((r) => interests.includes(r.model_id))
  const allDismissed = recs.length > 0 && recs.every((r) => dismissed[r.model_id])
  const sessionId = data.session_id || ""
  const userProfile = data.profile || { economy: 0, comfort: 0, driving: 0, practical: 0, status: 0, reliability: 0 }

  const handleInterest = (modelId: number) => {
    setInterests((prev) =>
      prev.includes(modelId) ? prev.filter((id) => id !== modelId) : [...prev, modelId]
    )
    setDismissed((prev) => {
      const next = { ...prev }
      delete next[modelId]
      return next
    })
  }

  const handleDismiss = (modelId: number, reason: string) => {
    setDismissed((prev) => ({ ...prev, [modelId]: reason }))
    setInterests((prev) => prev.filter((id) => id !== modelId))
    Analytics.feedbackSubmitted(sessionId, "dismissed", modelId)
  }

  const handleUndo = (modelId: number) => {
    setDismissed((prev) => {
      const next = { ...prev }
      delete next[modelId]
      return next
    })
    setInterests((prev) => prev.filter((id) => id !== modelId))
  }

  const fetchAlternatives = async () => {
    const dismissedIds = Object.keys(dismissed).map(Number)
    const dismissReasons = Object.values(dismissed)
    setAlternativesLoading(true)
    setAlternativesError(false)
    try {
      const json = await refreshRecommendations(
        sessionId,
        dismissedIds,
        dismissReasons,
        3
      )
      if (json.recommendations?.length > 0) {
        setAlternatives(json.recommendations)
      } else {
        setAlternativesError(true)
      }
    } catch {
      setAlternativesError(true)
    } finally {
      setAlternativesLoading(false)
      setAlternativesFetched(true)
    }
  }

  return (
    <main className="min-h-screen">
      {/* ── Profile Hero Header ── */}
      <ProfileHeader
        profile={userProfile}
        narrative={data.profile_narrative}
        profileSummary={data.profile_summary}
      />

      {/* ── Featured Recommendation #1 ── */}
      {first && (
        <section
          className="cursor-default px-[clamp(24px,5vw,80px)] py-[clamp(48px,6vw,80px)]"
          onClick={() =>
            Analytics.modelClicked(sessionId, first.model_id, 1, !!first.is_wildcard)
          }
        >
          <FeaturedModel rec={first} isDismissed={!!dismissed[first.model_id]}>
            <InterestActions
              modelId={first.model_id}
              isInterested={interests.includes(first.model_id)}
              dismissReason={dismissed[first.model_id]}
              onInterest={handleInterest}
              onDismiss={handleDismiss}
              onUndo={handleUndo}
              className="mt-5"
            />
            <AdAnalysisPanel
              modelId={first.model_id}
              sessionId={sessionId}
              userProfile={userProfile}
              rank={1}
            />
            <TrustPanel
              reliability={first.reliability}
              market={first.market}
              modelName={first.full_name}
            />
          </FeaturedModel>
        </section>
      )}

      {/* ── Remaining #2-#5 Grid ── */}
      <section className="px-[clamp(24px,5vw,80px)] pb-[clamp(48px,6vw,64px)]">
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,320px),1fr))] gap-3">
          {rest.map((rec, i) => (
            <ModelCard
              key={rec.model_id || i}
              rec={rec}
              rank={i + 2}
              isDismissed={!!dismissed[rec.model_id]}
              className="cursor-default"
            >
              <InterestActions
                modelId={rec.model_id}
                isInterested={interests.includes(rec.model_id)}
                dismissReason={dismissed[rec.model_id]}
                onInterest={handleInterest}
                onDismiss={handleDismiss}
                onUndo={handleUndo}
                className="mt-5"
              />
              <AdAnalysisPanel
                modelId={rec.model_id}
                sessionId={sessionId}
                userProfile={userProfile}
                rank={i + 2}
              />
              <TrustPanel
                reliability={rec.reliability}
                market={rec.market}
                modelName={rec.full_name}
              />
            </ModelCard>
          ))}
        </div>
      </section>

      {/* ── Alternatives (after dismissals) ── */}
      <AlternativesList
        alternatives={alternatives}
        sessionId={sessionId}
        userProfile={userProfile}
        dismissedCount={Object.keys(dismissed).length}
        interests={interests}
        dismissed={dismissed}
        onInterest={handleInterest}
        onDismiss={handleDismiss}
        onUndo={handleUndo}
        onFetchAlternatives={fetchAlternatives}
        alternativesLoading={alternativesLoading}
        alternativesFetched={alternativesFetched}
        alternativesError={alternativesError}
      />

      {/* ── Suggestions ── */}
      {data.suggestions && (
        <section className="mx-[clamp(24px,5vw,80px)] rounded-xl bg-card p-[clamp(24px,4vw,32px)]">
          <p className="text-sm font-light leading-relaxed text-muted-foreground">
            Encontramos {data.suggestions.models_available} opcoes no teu orcamento. Se alargares ate{" "}
            <span className="text-gold">
              {data.suggestions.stretch_budget?.toLocaleString("pt-PT")} EUR
            </span>
            , tens mais opcoes.
          </p>
        </section>
      )}

      {/* ── Concierge CTA ── */}
      <ConciergeCTA
        sessionId={sessionId}
        interestedRecs={interestedRecs}
        allDismissed={allDismissed}
      />

      {/* ── Feedback CTA ── */}
      <section className="bg-background px-[clamp(24px,5vw,80px)] py-[clamp(48px,8vw,96px)] text-center">
        <h2 className="mb-3 font-display text-[clamp(28px,4vw,48px)] font-extrabold tracking-tight">
          Gostaste?
        </h2>
        <p className="mb-8 text-[15px] font-light text-foreground/40">
          Ajuda-nos a melhorar em 30 segundos.
        </p>
        <Link
          href={`/feedback?session=${sessionId}`}
          className="rounded-full border border-border px-6 py-3 text-[13px] font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
        >
          dar feedback
        </Link>
      </section>
    </main>
  )
}
