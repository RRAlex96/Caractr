"use client"

import { useState, useEffect, useRef, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { PageContainer } from "@/components/layout/page-container"
import { AnalysisInput } from "@/components/analysis/analysis-input"
import { LoadingSteps } from "@/components/analysis/loading-steps"
import { AnalysisError } from "@/components/analysis/analysis-error"
import { PasteFallback } from "@/components/analysis/paste-fallback"
import { BuyerPassCard } from "@/components/analysis/buyer-pass-card"
import { AnalysisBody } from "@/components/analysis/analysis-body"
import { ChecksGrid } from "@/components/analysis/checks-grid"
import { QuickProfile } from "@/components/analysis/quick-profile"
import { ShareButton } from "@/components/shared/share-button"
import { MicroFeedback } from "@/components/shared/micro-feedback"
import { WizardBridge } from "@/components/shared/wizard-bridge"
import { analyseUrl, warmBackend } from "@/lib/api"
import { Analytics } from "@/lib/analytics"
import type { AnalysisResult } from "@/lib/types"

/* ─────────────────────────────────────────────────────────── */

function AnalisarContent() {
  const searchParams = useSearchParams()
  const [url, setUrl] = useState(searchParams.get("url") || "")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState("")
  const [errorCode, setErrorCode] = useState("")
  const [userProfile, setUserProfile] = useState<Record<string, number> | null>(null)
  const [showQuick, setShowQuick] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Wake the free-tier backend while the user reads the page / types a URL.
  useEffect(() => {
    warmBackend()
  }, [])

  // Load profile from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("caractr_results")
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed.profile) setUserProfile(parsed.profile)
      }
    } catch {}
    try {
      const quick = localStorage.getItem("caractr_quick_profile")
      if (quick) {
        const parsed = JSON.parse(quick)
        if (parsed.profile) setUserProfile((prev) => prev ?? parsed.profile)
      }
    } catch {}
  }, [])

  // Auto-analyse from query param
  useEffect(() => {
    const preUrl = searchParams.get("url")
    if (preUrl && preUrl.startsWith("http")) {
      setUrl(preUrl)
      triggerAnalysis(preUrl)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const triggerAnalysis = async (targetUrl: string, profileOverride?: Record<string, number>, pastedText?: string) => {
    if (!targetUrl.trim()) return
    setLoading(true)
    setError("")
    setErrorCode("")
    setResult(null)
    const profile = profileOverride || userProfile
    Analytics.analysisStarted(targetUrl, !!profile)
    try {
      const data = await analyseUrl(targetUrl, {
        userProfile: profile as any,
        pastedText,
      })
      if (data.error) {
        setError(data.error)
        setErrorCode(data.error_code || "")
        Analytics.analysisFailed(targetUrl, data.error, data.error_code, !!pastedText)
      } else {
        setResult(data)
        Analytics.analysisCompleted(targetUrl, data.deal?.tier, !!data.from_cache, data.analysis_id)
      }
    } catch {
      setError("Erro ao analisar. Verifica a ligação e tenta novamente.")
      Analytics.analysisFailed(targetUrl, "network")
    } finally {
      setLoading(false)
    }
  }

  const handleQuickProfileComplete = (profile: Record<string, number>) => {
    setUserProfile(profile)
    setShowQuick(false)
    if (url.trim() && result) triggerAnalysis(url, profile)
  }

  const handleReset = () => {
    setResult(null)
    setUrl("")
    setError("")
    setShowQuick(false)
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  const tier = result?.deal?.tier

  return (
    <PageContainer size="sm" className="pb-24 pt-24 md:pt-32">
      {/* ── Intro ── */}
      <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
      <h1 className="mb-5 font-display text-[clamp(36px,6vw,64px)] font-extrabold leading-[0.92] tracking-tight">
        ANALISAR<br />ANÚNCIO
      </h1>
      <p className="mb-10 max-w-[460px] text-[15px] font-light leading-relaxed text-muted-foreground">
        Cola o link de qualquer anúncio — Standvirtual, OLX ou qualquer stand.
        Dizemos-te se o preço é justo, o que preocupa e o que valoriza.
      </p>

      {/* ── Checks grid (pre-analysis) ── */}
      {!result && !loading && <ChecksGrid className="mb-9" />}

      {/* ── URL input ── */}
      <AnalysisInput
        url={url}
        onUrlChange={setUrl}
        onSubmit={() => triggerAnalysis(url)}
        loading={loading}
        inputRef={inputRef}
      />

      {/* First visit lands fast: see a real analysis instantly, no waiting */}
      {!result && !loading && (
        <p className="mt-3 text-center text-[13px] font-light text-muted-foreground">
          Sem anúncio à mão?{" "}
          <Link href="/exemplos" className="text-gold underline-offset-2 hover:underline">
            Vê análises de exemplo
          </Link>
          .
        </p>
      )}

      {/* ── Error ── */}
      {error && !loading && (errorCode === "fetch_failed" || errorCode === "paste_incomplete") ? (
        <PasteFallback
          reason={errorCode as "fetch_failed" | "paste_incomplete"}
          message={error}
          loading={loading}
          onSubmit={(text) => triggerAnalysis(url, undefined, text)}
          className="mt-5"
        />
      ) : (
        error && !loading && <AnalysisError error={error} className="mt-5" />
      )}

      {/* ── Loading ── */}
      {loading && <LoadingSteps />}

      {/* ── Result ── */}
      {result && !loading && (
        <div className="mt-12 space-y-5">
          <AnalysisBody result={result} />

          <BuyerPassCard analysisId={result.analysis_id} />

          {/* Share + Feedback + Permalink */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <MicroFeedback listingUrl={url} />
            <div className="flex items-center gap-2">
              {result.analysis_id && (
                <CopyPermalink analysisId={result.analysis_id} />
              )}
              <ShareButton
                brand={result.listing.brand_name}
                model={result.listing.model_name}
                year={result.listing.year}
                tier={tier}
                priceDeltaPct={result.deal.price_delta_pct}
                priceDelta={result.deal.price_delta}
                analysisId={result.analysis_id}
                listingUrl={url}
              />
            </div>
          </div>

          {/* Caveat */}
          {result.caveat && (
            <p className="border-t border-border pt-4 text-[11px] leading-relaxed text-muted-foreground/35">
              {result.caveat}
            </p>
          )}

          {/* Wizard bridge */}
          <WizardBridge listingUrl={url} tier={tier} />

          {/* Analyse another */}
          <button
            onClick={handleReset}
            className="font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground/45 transition-colors hover:text-muted-foreground"
          >
            Analisar outro anúncio
          </button>

          {/* Quick Profile — shown when no wizard profile */}
          {!userProfile && (
            showQuick ? (
              <QuickProfile
                onComplete={handleQuickProfileComplete}
                className="mt-3"
              />
            ) : (
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border p-4 md:p-5">
                <p className="text-[13px] font-light text-muted-foreground">
                  Queres saber se este carro e mesmo para ti?
                </p>
                <div className="flex flex-wrap gap-2.5">
                  <button
                    onClick={() => setShowQuick(true)}
                    className="rounded-full border border-gold px-4 py-1.5 text-xs font-medium text-gold transition-colors hover:bg-gold/10"
                  >
                    Resposta rápida
                  </button>
                  <Link
                    href="/escolher"
                    className="rounded-full border border-border px-4 py-1.5 text-xs text-muted-foreground transition-colors hover:border-gold/30 hover:text-gold"
                  >
                    Perfil completo
                  </Link>
                </div>
              </div>
            )
          )}
        </div>
      )}

      {/* ── Pre-analysis wizard bridge ── */}
      {!result && !loading && (
        <div className="mt-18 border-t border-border pt-10">
          <p className="mb-4 font-mono text-[9px] uppercase tracking-[2px] text-muted-foreground/50">
            Ainda não tens um anúncio?
          </p>
          <p className="mb-5 max-w-[400px] text-sm font-light leading-relaxed text-muted-foreground">
            Responde a algumas perguntas sobre o teu estilo de vida e encontramos
            os modelos que melhor se adequam a ti.
          </p>
          <Link
            href="/escolher"
            className="rounded-full border border-border px-6 py-3 text-[13px] font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
          >
            descobrir o meu carro
          </Link>
        </div>
      )}
    </PageContainer>
  )
}

/* ── Copy Permalink ────────────────────────────────────────── */

function CopyPermalink({ analysisId }: { analysisId: number }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const origin = typeof window !== "undefined" ? window.location.origin : "https://caractr.pt"
    const url = `${origin}/analise/${analysisId}`
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const input = document.createElement("input")
      input.value = url
      document.body.appendChild(input)
      input.select()
      document.execCommand("copy")
      document.body.removeChild(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="rounded-full border border-border px-3.5 py-1.5 font-mono text-[10px] uppercase tracking-[1px] text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
    >
      {copied ? "Copiado!" : "Copiar link"}
    </button>
  )
}

/* ─────────────────────────────────────────────────────────── */

export default function AnalisarPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="font-mono text-[11px] tracking-[1px] text-muted-foreground">
            A CARREGAR...
          </p>
        </div>
      }
    >
      <AnalisarContent />
    </Suspense>
  )
}
