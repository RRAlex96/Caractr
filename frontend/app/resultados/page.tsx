"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"
import { refineRecommendations } from "@/lib/api"
import type { RecommendationResult } from "@/lib/types"

import { ProfileHeader } from "@/components/recommendation/profile-header"
import { FeaturedModel } from "@/components/recommendation/featured-model"
import { ModelCard } from "@/components/recommendation/model-card"
import { InterestActions } from "@/components/recommendation/interest-actions"
import { AdAnalysisPanel } from "@/components/recommendation/ad-analysis-panel"
import { RefinePanel } from "@/components/recommendation/refine-panel"
import { ConciergeCTA } from "@/components/recommendation/concierge-cta"
import { SellSideQuestion } from "@/components/recommendation/sell-side-question"
import { TrustPanel } from "@/components/shared/trust-panel"

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ResultadosPage() {
  const router = useRouter()
  const [data, setData] = useState<RecommendationResult | null>(null)
  const [interests, setInterests] = useState<number[]>([])
  const [dismissed, setDismissed] = useState<Record<number, string>>({})
  // Earlier shortlists (newest last) — "voltar à lista anterior" and the
  // models to leave out of the next one.
  const [history, setHistory] = useState<RecommendationResult[]>([])
  const [refineLoading, setRefineLoading] = useState(false)
  const [refineError, setRefineError] = useState(false)

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
  const allModels = recs
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

  const resetCardState = () => {
    setDismissed({})
    setInterests([])
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const refine = async (wants: string[], powertrain: string, condition: string) => {
    const shown = [...history.flatMap((h) => h.recommendations || []), ...recs].map((r) => r.model_id)
    setRefineLoading(true)
    setRefineError(false)
    try {
      const next = await refineRecommendations({
        session_id: sessionId,
        answers: data.answers,
        shown_model_ids: Array.from(new Set(shown)),
        wants,
        powertrain,
        condition,
      })
      if (!next.recommendations?.length) {
        setRefineError(true)
        return
      }
      setHistory((h) => [...h, data])
      setData(next)
      localStorage.setItem("caractr_results", JSON.stringify(next))
      Analytics.resultsViewed(next.session_id || "", next.recommendations.length,
        next.recommendations.some((r) => r.is_wildcard), next.recommendations.some((r) => r.is_stretch))
      resetCardState()
    } catch {
      setRefineError(true)
    } finally {
      setRefineLoading(false)
    }
  }

  const goBack = () => {
    const prev = history[history.length - 1]
    if (!prev) return
    setHistory((h) => h.slice(0, -1))
    setData(prev)
    localStorage.setItem("caractr_results", JSON.stringify(prev))
    resetCardState()
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

      {/* ── None of these? Two questions, a new shortlist ── */}
      <RefinePanel
        key={sessionId}
        initialPowertrain={(data.answers?.powertrain as string) || undefined}
        initialCondition={(data.answers?.condition as string) || undefined}
        loading={refineLoading}
        error={refineError}
        canGoBack={history.length > 0}
        onSubmit={refine}
        onBack={goBack}
      />

      {/* ── Suggestions ── */}
      {data.suggestions && (
        <section className="mx-[clamp(24px,5vw,80px)] rounded-xl bg-card p-[clamp(24px,4vw,32px)]">
          <p className="text-sm font-light leading-relaxed text-muted-foreground">
            Encontrámos {data.suggestions.models_available} opções no teu orçamento. Se alargares até{" "}
            <span className="text-gold">
              {data.suggestions.stretch_budget?.toLocaleString("pt-PT")} EUR
            </span>
            , tens mais opções.
          </p>
        </section>
      )}

      <SellSideQuestion />

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
