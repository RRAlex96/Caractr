"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { ProgressBar } from "@/components/wizard/progress-bar"
import { QuestionCard } from "@/components/wizard/question-card"
import { DreamBrandPicker } from "@/components/wizard/dream-brand-picker"
import { BudgetPicker } from "@/components/wizard/budget-picker"
import { recommend, fetchDreamCars, warmBackend } from "@/lib/api"
import { Analytics } from "@/lib/analytics"

// ── Question definitions ──────────────────────────────────────────────────

const QUESTIONS = [
  {
    id: "p1_context",
    label: "01 — Dia a dia",
    question: "Onde passas mais tempo ao volante?",
    options: [
      { value: "cidade",  label: "Cidade",   desc: "Transito, estacionamento, trajetos curtos" },
      { value: "misto",   label: "Misto",    desc: "Um pouco de tudo — cidade e estrada" },
      { value: "estrada", label: "Estrada",  desc: "Autoestrada, viagens longas, muitos km" },
      { value: "familia", label: "Família",  desc: "Escola, compras, logística familiar" },
    ],
  },
  {
    id: "p2_relationship",
    label: "02 — Relacao com o carro",
    question: "Como ves o teu carro?",
    options: [
      { value: "apenas_transporte", label: "Apenas transporte",  desc: "Leva-me do A ao B, sem drama" },
      { value: "gosto_conduzir",    label: "Gosto de conduzir",  desc: "Aprecio uma boa viagem, mas não é obsessão" },
      { value: "adoro_conduzir",    label: "Adoro conduzir",     desc: "O carro e uma extensao de mim" },
    ],
  },
  {
    id: "p3_driving_style",
    label: "03 — Ao volante",
    question: "O que preferes sentir ao volante?",
    options: [
      { value: "suave_previsivel",     label: "Suave e previsível",    desc: "Conforto acima de tudo, zero surpresas" },
      { value: "confortavel_com_alma", label: "Confortável com alma",  desc: "Suavidade no dia a dia, capaz quando preciso" },
      { value: "dinamico_envolvente",  label: "Dinâmico e envolvente", desc: "Quero sentir a estrada — chassis, resposta, emoção" },
    ],
  },
  {
    id: "p5_presence",
    label: "04 — Presença",
    question: "O que queres que o carro comunique?",
    options: [
      { value: "discreto",     label: "Discreto",          desc: "Não preciso de atenção — só de um bom carro" },
      { value: "bom_aspeto",   label: "Bom aspeto",        desc: "Elegante, sem ser ostentacao" },
      { value: "vire_cabecas", label: "Que vire cabeças",  desc: "Presença forte — gosto de ser notado" },
    ],
  },
  {
    id: "p6_aversion",
    label: "05 — Limites",
    question: "O que seria inaceitável no teu próximo carro?",
    options: [
      { value: "fiabilidade", label: "Problemas mecânicos", desc: "Avarias, custos inesperados, falta de confiança" },
      { value: "conforto",    label: "Desconforto",         desc: "Barulho, suspensao dura, viagens longas a sofrer" },
      { value: "espaco",      label: "Falta de espaço",     desc: "Pouco espaço para passageiros ou bagagem" },
      { value: "potencia",    label: "Falta de resposta",   desc: "Motor fraco, aceleracao lenta, sem dinamismo" },
    ],
  },
]

const DREAM_BRANDS_FALLBACK = [
  { id: "porsche",    name: "Porsche",     identity: "Performance sem compromisso" },
  { id: "bmw",        name: "BMW",         identity: "O prazer de conduzir" },
  { id: "mercedes",   name: "Mercedes",    identity: "Elegancia e refinamento" },
  { id: "toyota",     name: "Toyota",      identity: "Fiavel como nada" },
  { id: "volvo",      name: "Volvo",       identity: "Seguranca e conforto escandinavo" },
  { id: "volkswagen", name: "Volkswagen",  identity: "Solido, maduro, sem teatros" },
]

const DIM_LABELS: Record<string, string> = {
  economy: "economia", comfort: "conforto", driving: "condução",
  practical: "praticidade", status: "imagem", reliability: "fiabilidade",
}

function cap(s: string) { return s.charAt(0).toUpperCase() + s.slice(1) }

function buildFallbackNarrative(data: any): { summary: string; lines: string[] } {
  const profile = data.profile || {}
  const sorted = Object.entries(profile).sort((a: any, b: any) => b[1] - a[1])
  const top2 = sorted.slice(0, 2).map(([k]) => DIM_LABELS[k] || k)
  const summary = top2.length >= 2
    ? `${cap(top2[0])} e ${top2[1]} como prioridades.`
    : top2.length === 1
      ? `${cap(top2[0])} como prioridade principal.`
      : "Perfil equilibrado."
  const lines: string[] = []
  if (top2.length >= 2)
    lines.push(`${cap(top2[0])} e ${top2[1]} estao no topo das tuas prioridades.`)
  if (data.answers?.p6_aversion && data.answers.p6_aversion !== "nenhuma") {
    const map: Record<string, string> = {
      fiabilidade: "Ficou claro: problemas mecânicos são inaceitáveis para ti.",
      conforto: "Ficou claro: desconforto é inaceitável para ti.",
      espaco: "Ficou claro: falta de espaço é inaceitável para ti.",
      potencia: "Ficou claro: falta de resposta do motor é inaceitável para ti.",
    }
    if (map[data.answers.p6_aversion]) lines.push(map[data.answers.p6_aversion])
  }
  return { summary, lines }
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function EscolherPage() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, any>>({
    p8_budget_min: 8000,
    p8_budget_max: 25000,
  })
  const [dreamCars, setDreamCars] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState("")
  const [transitioning, setTransitioning] = useState(false)
  const [existingProfileAge, setExistingProfileAge] = useState<number | null>(null)
  const [profileStage, setProfileStage] = useState<"wizard" | "interpreting" | "narrative">("wizard")
  const [narrativeData, setNarrativeData] = useState<any>(null)
  const [narrativeVisible, setNarrativeVisible] = useState(false)
  const startTimeRef = useRef<number>(Date.now())

  const totalSteps = QUESTIONS.length + 2
  const isDreamStep = step === QUESTIONS.length
  const isBudgetStep = step === QUESTIONS.length + 1
  const current = step < QUESTIONS.length ? QUESTIONS[step] : null

  // Check for existing profile on mount
  useEffect(() => {
    warmBackend()  // wake the backend while the user answers the 5 questions
    Analytics.selectorStarted()
    startTimeRef.current = Date.now()
    const timestamp = localStorage.getItem("caractr_profile_timestamp")
    if (timestamp) {
      const ageDays = Math.floor((Date.now() - new Date(timestamp).getTime()) / (1000 * 60 * 60 * 24))
      setExistingProfileAge(ageDays)
      const stored = localStorage.getItem("caractr_results")
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          Analytics.returnVisit(parsed.session_id || "", ageDays)
        } catch {}
      }
    }
  }, [])

  // Fetch dream brands when reaching that step
  useEffect(() => {
    if (isDreamStep) loadDreamCars()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step])

  const loadDreamCars = async () => {
    setLoading(true)
    try {
      const cars = await fetchDreamCars(answers)
      setDreamCars(cars.length > 0 ? cars : DREAM_BRANDS_FALLBACK)
    } catch {
      setDreamCars(DREAM_BRANDS_FALLBACK)
    } finally {
      setLoading(false)
    }
  }

  const goToStep = (next: number) => {
    setTransitioning(true)
    setTimeout(() => {
      setStep(next)
      setTransitioning(false)
    }, 250)
  }

  const selectChoice = (field: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [field]: value }))
    Analytics.stepCompleted(step + 1, field, value)
    setTimeout(() => goToStep(Math.min(step + 1, totalSteps - 1)), 300)
  }

  const submit = async () => {
    setSubmitting(true)
    Analytics.selectorCompleted(Date.now() - startTimeRef.current, answers.p8_budget_max || 25000)
    try {
      const data = await recommend({
        p1_context: answers.p1_context || "misto",
        p2_relationship: answers.p2_relationship || "gosto_conduzir",
        p3_driving_style: answers.p3_driving_style || "confortavel_com_alma",
        p5_presence: answers.p5_presence || "bom_aspeto",
        p6_aversion: answers.p6_aversion || "nenhuma",
        p7_dream_brand: answers.p7_dream_brand || null,
        p8_budget_range: answers.p8_budget_range || null,
        p8_budget_min: answers.p8_budget_min || 8000,
        p8_budget_max: answers.p8_budget_max || 25000,
      })
      localStorage.setItem("caractr_results", JSON.stringify(data))
      localStorage.setItem("caractr_profile_timestamp", new Date().toISOString())
      setNarrativeData(data)
      setProfileStage("interpreting")
      Analytics.profileShown(data.session_id || "")
      setTimeout(() => {
        setProfileStage("narrative")
        setTimeout(() => setNarrativeVisible(true), 80)
      }, 1500)
    } catch (err) {
      console.error("Submit error:", err)
      setSubmitError("Erro ao calcular o perfil. Verifica a ligacao e tenta novamente.")
      setSubmitting(false)
    }
  }

  // ── Profile interpretation screen ──────────────────────────────────────

  if (profileStage === "interpreting") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6">
        <div className="text-center">
          <div className="mx-auto mb-7 h-0.5 w-8 animate-pulse-gold rounded-full bg-gold" />
          <p className="font-mono text-[11px] uppercase tracking-[2px] text-gold">
            A analisar o teu perfil...
          </p>
        </div>
      </div>
    )
  }

  if (profileStage === "narrative" && narrativeData) {
    const narrative = narrativeData.profile_narrative
    const fallback = buildFallbackNarrative(narrativeData)
    const lines: string[] = narrative
      ? [narrative.priorities, narrative.tension, narrative.aversion, narrative.identity, narrative.context].filter(Boolean)
      : fallback.lines
    const summary = narrative?.summary || fallback.summary

    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6">
        <div
          className={cn(
            "w-full max-w-[580px] transition-all duration-500",
            narrativeVisible ? "translate-y-0 opacity-100" : "translate-y-5 opacity-0"
          )}
        >
          <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
          <p className="mb-5 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            O TEU PERFIL CARACTR
          </p>
          <h2 className="mb-8 font-display text-[clamp(28px,4vw,44px)] font-extrabold leading-[0.95] tracking-tight">
            {summary.toUpperCase().replace(".", "")}
          </h2>

          {/* Narrative card */}
          <div className="mb-9 flex flex-col gap-3.5 rounded-2xl border border-border bg-card p-7 md:p-8">
            {lines.length > 0 ? (
              lines.map((line, i) => (
                <div key={i} className="flex items-start gap-4">
                  <div className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-gold" />
                  <p className="text-[15px] font-light leading-relaxed">
                    {line}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-[15px] font-light leading-relaxed text-muted-foreground">
                Perfil calculado com base nas tuas respostas.
              </p>
            )}
          </div>

          <button
            onClick={() => router.push("/resultados")}
            className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
          >
            Ver as tuas recomendações
          </button>
        </div>
      </div>
    )
  }

  // ── Wizard ──────────────────────────────────────────────────────────────

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <ProgressBar current={step} total={totalSteps} className="px-6 pt-24 md:px-16" />

      {/* Return visit banner */}
      {existingProfileAge !== null && step === 0 && (
        <div className="mx-auto w-full max-w-[640px] px-6 pt-4 md:px-16">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-[10px] border border-border bg-card p-4">
            <p className="text-[13px] leading-relaxed text-muted-foreground">
              {existingProfileAge < 7
                ? "Tens um perfil guardado. Continuar para os teus resultados?"
                : existingProfileAge <= 30
                  ? `O teu perfil tem ${existingProfileAge} dias. Continuar ou refazer?`
                  : `O teu perfil tem ${existingProfileAge} dias — recomendamos refazer.`}
            </p>
            <Link
              href="/resultados"
              className="whitespace-nowrap font-mono text-[10px] uppercase tracking-[1px] text-gold"
            >
              Ver resultados
            </Link>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex flex-1 items-center justify-center px-6 pb-20 md:px-16">
        <div
          className={cn(
            "w-full max-w-[640px] transition-all duration-250",
            transitioning ? "translate-y-3 opacity-0" : "translate-y-0 opacity-100"
          )}
        >
          {/* Back button */}
          {step > 0 && (
            <button
              aria-label="Voltar"
              onClick={() => goToStep(step - 1)}
              className="mb-10 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              ← voltar
            </button>
          )}

          {/* Questions P1-P6 */}
          {current && !isDreamStep && !isBudgetStep && (
            <QuestionCard
              stepLabel={current.label}
              question={current.question}
              options={current.options}
              selected={answers[current.id]}
              onSelect={(value) => selectChoice(current.id, value)}
            />
          )}

          {/* Dream Brand */}
          {isDreamStep && (
            <DreamBrandPicker
              brands={dreamCars}
              selected={answers.p7_dream_brand}
              onSelect={(id) => setAnswers((p) => ({ ...p, p7_dream_brand: id }))}
              onContinue={() => goToStep(step + 1)}
              loading={loading}
            />
          )}

          {/* Budget */}
          {isBudgetStep && (
            <BudgetPicker
              selected={answers.p8_budget_range}
              onSelect={(value, min, max) =>
                setAnswers((p) => ({ ...p, p8_budget_range: value, p8_budget_min: min, p8_budget_max: max }))
              }
              onSubmit={submit}
              submitting={submitting}
              error={submitError}
            />
          )}
        </div>
      </div>
    </div>
  )
}
