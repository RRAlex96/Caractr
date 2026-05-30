"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { submitConcierge } from "@/lib/api"
import type { ProfileNarrative } from "@/lib/types"

const FEEDBACK_TAGS = [
  { id: "wrong_brand", label: "Nao me identifico com a marca" },
  { id: "want_sportier", label: "Quero algo mais desportivo" },
  { id: "want_comfort", label: "Quero mais conforto" },
  { id: "want_practical", label: "Quero algo mais pratico" },
  { id: "budget_off", label: "Orcamento nao esta certo" },
  { id: "want_premium", label: "Quero algo mais premium" },
  { id: "want_discreet", label: "Quero algo mais discreto" },
  { id: "want_bigger", label: "Preciso de mais espaco" },
]

function ConciergeContent() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get("session") || ""
  const modelFromUrl = searchParams.get("model") || ""
  const modelsFromUrl = searchParams.get("models") || ""
  const modelIdsParam = searchParams.get("model_ids") || ""
  const listingUrl = searchParams.get("listing_url") || ""
  const listingVerdict = searchParams.get("listing_verdict") || ""

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [modelInterest, setModelInterest] = useState("")
  const [budgetMax, setBudgetMax] = useState("")
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [consentCaractr, setConsentCaractr] = useState(false)
  const [consentDealer, setConsentDealer] = useState(false)
  const [sending, setSending] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState("")
  const [profileNarrative, setProfileNarrative] = useState<ProfileNarrative | null>(null)
  const [listingModel, setListingModel] = useState("")
  const [interestedModels, setInterestedModels] = useState<string[]>([])

  useEffect(() => {
    if (modelsFromUrl) {
      const models = decodeURIComponent(modelsFromUrl)
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
      setInterestedModels(models)
      setModelInterest(models.join(", "))
    } else if (modelFromUrl) {
      setModelInterest(decodeURIComponent(modelFromUrl))
      setInterestedModels([decodeURIComponent(modelFromUrl)])
    }

    const stored = localStorage.getItem("caractr_results")
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (!modelFromUrl && !modelsFromUrl && parsed.recommendations?.[0]) {
          setModelInterest(parsed.recommendations[0].full_name)
        }
        if (parsed.answers?.p8_budget_max) {
          setBudgetMax(String(parsed.answers.p8_budget_max))
        }
        if (parsed.profile_narrative) {
          setProfileNarrative(parsed.profile_narrative)
        }
      } catch {}
    }
    if (listingUrl) {
      const slug = listingUrl.split("/").filter(Boolean).pop() || ""
      setListingModel(slug.replace(/-/g, " ").slice(0, 60))
    }
  }, [modelFromUrl, modelsFromUrl, listingUrl])

  const toggleTag = (id: string) => {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    )
  }

  const submit = async () => {
    if (!name.trim() || !email.trim()) {
      setError("Nome e email sao obrigatorios.")
      return
    }
    if (!consentCaractr) {
      setError("E necessario aceitar o contacto pela Caractr para continuar.")
      return
    }
    setSending(true)
    setError("")
    try {
      const result = await submitConcierge({
        session_id: sessionId || null,
        name: name.trim(),
        email: email.trim(),
        model_interest: modelInterest.trim() || null,
        model_ids: modelIdsParam
          ? modelIdsParam.split(",").map(Number).filter(Boolean)
          : [],
        budget_max: budgetMax ? parseInt(budgetMax) : null,
        feedback_tags: selectedTags,
        consent_caractr: consentCaractr,
        consent_dealer: consentDealer,
        listing_url: listingUrl || null,
        listing_verdict: listingVerdict || null,
      })
      if (result.status === "ok") {
        setSubmitted(true)
      } else {
        setError(result.error || "Erro ao enviar. Tenta novamente.")
      }
    } catch {
      setError("Erro de ligacao. Verifica a internet e tenta novamente.")
    } finally {
      setSending(false)
    }
  }

  // ── Success screen ─────────────────────────────────────────────────────────

  if (submitted) {
    const firstName = name.split(" ")[0] || name
    return (
      <main className="flex min-h-screen flex-col items-center justify-center px-[clamp(24px,5vw,64px)] pt-16 text-center">
        <div className="w-full max-w-[480px]">
          <div className="mb-6 h-0.5 w-12 rounded-full bg-gold" />
          <h1 className="mb-5 font-display text-[clamp(36px,7vw,64px)] font-extrabold leading-[0.9] tracking-tight">
            RECEBIDO,
            <br />
            {firstName.toUpperCase()}.
          </h1>

          {/* What happens next */}
          <div className="mb-8 rounded-2xl border border-border bg-card p-6 text-left md:px-7">
            <p className="mb-4.5 font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
              O que acontece agora
            </p>
            {[
              "Vemos o teu perfil e os modelos que te interessam.",
              "Pesquisamos anuncios reais que se encaixam nas tuas prioridades.",
              "Entramos em contacto via email com uma shortlist curada.",
            ].map((step, i) => (
              <div
                key={i}
                className={cn("flex items-start gap-4", i < 2 && "mb-3.5")}
              >
                <span className="mt-0.5 shrink-0 font-mono text-[11px] text-gold">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <p className="text-sm font-light leading-relaxed text-muted-foreground">
                  {step}
                </p>
              </div>
            ))}
          </div>

          <p className="mb-8 text-[13px] leading-relaxed text-muted-foreground/55">
            Enviamos uma confirmacao para{" "}
            <strong className="font-normal text-foreground">{email}</strong>.
          </p>

          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/resultados"
              className="rounded-full border border-border px-5 py-2 text-[13px] text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
            >
              ← shortlist
            </Link>
            <Link
              href="/analisar"
              className="rounded-full border border-border px-5 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
            >
              analisar anuncio
            </Link>
          </div>
        </div>
      </main>
    )
  }

  // ── Form ────────────────────────────────────────────────────────────────────

  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-[560px] px-[clamp(24px,5vw,32px)] pb-[clamp(48px,6vw,64px)] pt-24 md:pt-32">
        {/* Title */}
        <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
        <h1 className="mb-3.5 font-display text-[clamp(32px,5vw,48px)] font-extrabold leading-[0.95] tracking-tight">
          QUERO AJUDA
        </h1>
        <p
          className={cn(
            "text-[15px] font-light leading-relaxed text-muted-foreground",
            interestedModels.length > 0 ? "mb-6" : "mb-12"
          )}
        >
          Pesquisamos anuncios reais que se adequam ao teu perfil e enviamos-te
          uma shortlist curada. Gratuito durante o lancamento.
        </p>

        {/* Interested models chips */}
        {interestedModels.length > 1 && (
          <div className="mb-8">
            <p className="mb-2.5 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/60">
              Modelos com interesse
            </p>
            <div className="flex flex-wrap gap-2">
              {interestedModels.map((m, i) => (
                <span
                  key={i}
                  className="rounded-full border border-gold px-3.5 py-1 font-mono text-[11px] text-gold/80"
                >
                  {m}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Profile card */}
        {profileNarrative && (
          <div className="mb-8 rounded-xl border border-border bg-card p-4 px-5">
            <p className="mb-2.5 font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
              Conhecemos o teu perfil
            </p>
            {profileNarrative.priorities && (
              <p className="mb-1 text-[13px] leading-relaxed">
                {profileNarrative.priorities}
              </p>
            )}
            {profileNarrative.aversion && (
              <p className="text-xs leading-snug text-muted-foreground">
                {profileNarrative.aversion}
              </p>
            )}
          </div>
        )}

        {/* Listing context banner */}
        {listingUrl && (
          <div className="mb-8 flex items-center gap-3 rounded-[10px] border border-border bg-card p-3 px-4">
            <span className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Anuncio analisado
            </span>
            {listingVerdict && (
              <span
                className={cn(
                  "font-mono text-[10px] font-bold uppercase tracking-[1px]",
                  listingVerdict === "forte"
                    ? "text-success"
                    : listingVerdict === "evitar"
                      ? "text-danger"
                      : "text-gold"
                )}
              >
                {listingVerdict.toUpperCase()}
              </span>
            )}
            {listingModel && (
              <span className="flex-1 truncate text-xs text-muted-foreground">
                {listingModel}
              </span>
            )}
          </div>
        )}

        {/* ── Contact ── */}
        <div className="mb-10">
          <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            Os teus dados
          </p>
          <div className="mb-2.5 grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-2.5">
            <div>
              <label className="mb-2 block font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
                Nome *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="O teu nome"
                className="w-full rounded-[10px] border border-border bg-card px-4.5 py-3.5 text-sm font-light text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
              />
            </div>
            <div>
              <label className="mb-2 block font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
                Email *
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="o-teu@email.pt"
                className="w-full rounded-[10px] border border-border bg-card px-4.5 py-3.5 text-sm font-light text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
              />
            </div>
          </div>
        </div>

        {/* ── Model & budget ── */}
        <div className="mb-10">
          <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            O que procuras
          </p>
          <div className="mb-2.5">
            <label className="mb-2 block font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
              Modelo de interesse
            </label>
            <input
              type="text"
              value={modelInterest}
              onChange={(e) => setModelInterest(e.target.value)}
              placeholder="ex: BMW Serie 3, Mazda CX-5..."
              className="w-full rounded-[10px] border border-border bg-card px-4.5 py-3.5 text-sm font-light text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
            />
          </div>
          <div>
            <label className="mb-2 block font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/60">
              Orcamento maximo (EUR)
            </label>
            <input
              type="number"
              value={budgetMax}
              onChange={(e) => setBudgetMax(e.target.value)}
              placeholder="ex: 25000"
              className="w-full rounded-[10px] border border-border bg-card px-4.5 py-3.5 text-sm font-light text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
            />
          </div>
        </div>

        {/* ── Feedback chips ── */}
        <div className="mb-10">
          <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            A recomendacao nao esta certa? (opcional)
          </p>
          <p className="mb-4 text-[13px] text-muted-foreground/70">
            Seleciona o que nao se adequa — ajuda-nos a afinar.
          </p>
          <div className="flex flex-wrap gap-2">
            {FEEDBACK_TAGS.map((tag) => {
              const active = selectedTags.includes(tag.id)
              return (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  className={cn(
                    "rounded-full border px-4 py-2 text-xs transition-colors",
                    active
                      ? "border-gold bg-gold/[0.08] text-gold"
                      : "border-border text-muted-foreground hover:border-gold/40 hover:text-foreground"
                  )}
                >
                  {tag.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Consent ── */}
        <div className="mb-10 flex flex-col gap-4">
          <p className="mb-1 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            Consentimento (RGPD)
          </p>

          {[
            {
              key: "caractr",
              checked: consentCaractr,
              onChange: setConsentCaractr,
              required: true,
              label:
                "Aceito ser contactado pela equipa Caractr relativamente ao meu pedido.",
              showPrivacy: true,
            },
            {
              key: "dealer",
              checked: consentDealer,
              onChange: setConsentDealer,
              required: false,
              label:
                "Aceito receber propostas de dealers parceiros da Caractr com base no meu perfil de comprador.",
              showPrivacy: false,
            },
          ].map((c) => (
            <label
              key={c.key}
              className="flex cursor-pointer items-start gap-3"
              onClick={() => c.onChange(!c.checked)}
            >
              <div
                className={cn(
                  "mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded transition-colors",
                  c.checked
                    ? "border border-gold bg-gold"
                    : "border border-border bg-transparent"
                )}
              >
                {c.checked && (
                  <svg
                    width="10"
                    height="8"
                    viewBox="0 0 10 8"
                    fill="none"
                  >
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
              <span className="text-[13px] leading-relaxed text-muted-foreground">
                {c.label}
                {c.required && (
                  <span className="ml-1 text-gold">*</span>
                )}
                {c.showPrivacy && (
                  <>
                    {" "}
                    (
                    <a
                      href="/privacidade"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-gold-dark underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Politica de Privacidade
                    </a>
                    )
                  </>
                )}
              </span>
            </label>
          ))}
        </div>

        {error && (
          <p className="mb-4 text-[13px] text-danger">{error}</p>
        )}

        <button
          onClick={submit}
          disabled={sending || !consentCaractr}
          className={cn(
            "rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark",
            (sending || !consentCaractr) && "cursor-not-allowed opacity-40"
          )}
        >
          {sending ? "A enviar..." : "Enviar pedido"}
        </button>

        <p className="mt-3 text-xs font-light text-muted-foreground/50">
          Estas entre os primeiros a experimentar o Caractr — este servico e nosso presente de lancamento.
        </p>

        <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground/40">
          Os teus dados sao usados exclusivamente para os fins indicados acima.
          Nunca sao partilhados sem consentimento explicito.
        </p>
      </div>
    </main>
  )
}

export default function ConciergePage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center">
          <p className="font-mono text-[11px] uppercase tracking-[1px] text-muted-foreground">
            A CARREGAR...
          </p>
        </main>
      }
    >
      <ConciergeContent />
    </Suspense>
  )
}
