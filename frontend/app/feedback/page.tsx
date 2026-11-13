"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { submitFeedback } from "@/lib/api"
import { Analytics } from "@/lib/analytics"

function FeedbackContent() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get("session") || ""
  const [data, setData] = useState<any>(null)
  const [satisfaction, setSatisfaction] = useState<string | null>(null)
  const [preferredModel, setPreferredModel] = useState<number | null>(null)
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)
  const [sending, setSending] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem("caractr_results")
    if (stored) setData(JSON.parse(stored))
  }, [])

  const submit = async () => {
    setSending(true)
    try {
      // Map satisfaction to numeric values for the API
      const satisfactionMap: Record<string, number> = {
        sim: 5,
        mais_ou_menos: 3,
        nao: 1,
      }
      await submitFeedback({
        session_id: sessionId,
        overall: satisfactionMap[satisfaction || ""] || 3,
        accuracy: satisfactionMap[satisfaction || ""] || 3,
        usefulness: satisfactionMap[satisfaction || ""] || 3,
        would_recommend: satisfaction === "sim",
        comments: preferredModel
          ? `Preferred model ID: ${preferredModel}`
          : undefined,
      })
      Analytics.feedbackSubmitted(
        sessionId,
        satisfaction || "",
        preferredModel ?? undefined,
        !!email
      )
      setSubmitted(true)
    } catch (err) {
      console.error("Feedback error:", err)
    } finally {
      setSending(false)
    }
  }

  const recs = data?.recommendations || []

  // ── Success screen ─────────────────────────────────────────────────────────

  if (submitted) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center px-[clamp(24px,5vw,64px)] pt-16">
        <div className="mb-6 h-0.5 w-12 rounded-full bg-gold" />
        <h1 className="mb-6 text-center font-display text-[clamp(36px,7vw,72px)] font-extrabold leading-[0.88] tracking-tight">
          OBRIGADO
        </h1>
        <p className="max-w-[400px] text-center text-[15px] font-light leading-relaxed text-muted-foreground">
          O teu feedback ajuda-nos a melhorar o Caractr para ti e para todos.
          {email && " Avisamos-te quando estivermos prontos."}
        </p>
        <div className="mt-12">
          <Link
            href="/"
            className="rounded-full border border-border px-5 py-2 text-[13px] text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
          >
            voltar ao início
          </Link>
        </div>
      </main>
    )
  }

  // ── Form ────────────────────────────────────────────────────────────────────

  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-[540px] px-[clamp(24px,5vw,32px)] pb-[clamp(48px,6vw,64px)] pt-24 md:pt-32">
        {/* Title */}
        <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
        <h1 className="mb-3.5 font-display text-[clamp(32px,5vw,56px)] font-extrabold leading-[0.95] tracking-tight">
          O QUE ACHASTE?
        </h1>
        <p className="mb-13 text-[15px] font-light leading-relaxed text-muted-foreground">
          Tudo opcional. Demora 30 segundos. Ajuda-nos a melhorar.
        </p>

        {/* ── Satisfaction ── */}
        <div className="mb-14">
          <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            Isto fez sentido para ti?
          </p>
          <div className="flex gap-2.5">
            {[
              { value: "sim", label: "Sim" },
              { value: "mais_ou_menos", label: "Mais ou menos" },
              { value: "nao", label: "Não" },
            ].map((opt) => {
              const selected = satisfaction === opt.value
              return (
                <button
                  key={opt.value}
                  onClick={() => setSatisfaction(opt.value)}
                  className={cn(
                    "flex-1 rounded-full border py-3.5 text-center text-sm font-medium transition-colors",
                    selected
                      ? "border-gold bg-gold/[0.08] text-gold"
                      : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                  )}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Preferred model ── */}
        <div className="mb-14">
          <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            Qual te interessou mais?
          </p>
          <div className="border-t border-border">
            {[
              ...recs,
              {
                model_id: -1,
                rank: "—",
                full_name: "Nenhum me interessou",
              },
            ].map((rec: any, idx: number) => {
              const selected = preferredModel === rec.model_id
              return (
                <button
                  key={rec.model_id}
                  onClick={() => setPreferredModel(rec.model_id)}
                  className="group flex w-full items-center gap-4 border-b border-border py-4 text-left"
                >
                  <span
                    className={cn(
                      "w-4 shrink-0 font-mono text-[10px] transition-colors",
                      selected ? "text-gold" : "text-muted-foreground"
                    )}
                  >
                    {rec.model_id === -1
                      ? "—"
                      : `#${rec.rank || idx + 1}`}
                  </span>
                  <div className="flex flex-1 items-center gap-2.5">
                    <div
                      className={cn(
                        "h-0.5 shrink-0 rounded-full bg-gold transition-[width] duration-300",
                        selected ? "w-5" : "w-0 group-hover:w-5"
                      )}
                    />
                    <span
                      className={cn(
                        "text-[15px] transition-transform duration-300",
                        rec.model_id === -1
                          ? "font-light text-muted-foreground"
                          : "font-medium text-foreground",
                        !selected && "group-hover:translate-x-1.5"
                      )}
                    >
                      {rec.full_name}
                    </span>
                  </div>
                  <div
                    className={cn(
                      "h-2 w-2 shrink-0 rounded-full transition-all",
                      selected
                        ? "bg-gold"
                        : "border border-border bg-transparent"
                    )}
                  />
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Email ── */}
        <div className="mb-14">
          <p className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            Queres que te avisemos?
          </p>
          <input
            type="email"
            placeholder="o-teu@email.pt"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-[10px] border border-border bg-card px-5 py-4 text-sm font-light text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
          />
          <p className="mt-2 text-xs font-light text-muted-foreground/50">
            Sem spam. Só um aviso quando lançarmos.
          </p>
        </div>

        {/* Submit */}
        <button
          onClick={submit}
          disabled={sending}
          className={cn(
            "rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark",
            sending && "cursor-wait opacity-50"
          )}
        >
          {sending ? "a enviar..." : "enviar feedback"}
        </button>
      </div>
    </main>
  )
}

export default function FeedbackPage() {
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
      <FeedbackContent />
    </Suspense>
  )
}
