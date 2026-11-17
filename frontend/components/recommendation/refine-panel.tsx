"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

// "None of these convinces me": two quick questions, then a new shortlist of 5
// that leaves out every model already shown.

const WANTS = [
  { value: "mais_barato", label: "Mais barato" },
  { value: "mais_espaco", label: "Mais espaço" },
  { value: "mais_economico", label: "Gastar menos a andar" },
  { value: "mais_fiavel", label: "Mais fiável" },
  { value: "mais_conforto", label: "Mais confortável" },
  { value: "mais_desportivo", label: "Mais desportivo" },
  { value: "mais_premium", label: "Mais premium" },
  { value: "mais_discreto", label: "Mais discreto" },
]

export const POWERTRAINS = [
  { value: "indiferente", label: "Tanto faz" },
  { value: "eletrico", label: "Elétrico" },
  { value: "hibrido", label: "Híbrido" },
  { value: "combustao", label: "Gasolina ou gasóleo" },
]

export const CONDITIONS = [
  { value: "usado", label: "Usado" },
  { value: "novo", label: "Novo" },
  { value: "indiferente", label: "Tanto faz" },
]

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-4 py-2 text-[13px] transition-colors",
        active ? "border-gold bg-gold/10 text-gold" : "border-border text-muted-foreground hover:border-gold/40",
      )}
    >
      {children}
    </button>
  )
}

interface RefinePanelProps {
  initialPowertrain?: string
  initialCondition?: string
  loading: boolean
  error: boolean
  canGoBack: boolean
  onSubmit: (wants: string[], powertrain: string, condition: string) => void
  onBack: () => void
}

export function RefinePanel({
  initialPowertrain, initialCondition, loading, error, canGoBack, onSubmit, onBack,
}: RefinePanelProps) {
  const [open, setOpen] = useState(false)
  const [wants, setWants] = useState<string[]>([])
  const [powertrain, setPowertrain] = useState(initialPowertrain || "indiferente")
  const [condition, setCondition] = useState(initialCondition || "indiferente")

  const toggleWant = (v: string) =>
    setWants((prev) => (prev.includes(v) ? prev.filter((w) => w !== v) : prev.length < 2 ? [...prev, v] : [prev[1], v]))

  return (
    <section className="px-[clamp(24px,5vw,80px)] pb-[clamp(48px,6vw,64px)]">
      <div className="rounded-xl border border-border bg-card p-[clamp(24px,4vw,36px)]">
        {!open ? (
          <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-display text-[20px] font-bold tracking-tight">Nenhum destes te convence?</p>
              <p className="mt-1 text-[14px] font-light text-muted-foreground">
                Responde a duas perguntas e fazemos uma lista nova, sem repetir estes modelos.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {canGoBack && (
                <button type="button" onClick={onBack}
                  className="rounded-full border border-border px-5 py-2.5 text-[13px] text-muted-foreground hover:border-gold/40">
                  voltar à lista anterior
                </button>
              )}
              <button type="button" onClick={() => setOpen(true)}
                className="rounded-full bg-gold px-6 py-2.5 text-[13px] font-semibold text-background hover:bg-gold-dark">
                afinar a lista
              </button>
            </div>
          </div>
        ) : (
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[2px] text-gold">1 de 2</p>
            <p className="mb-4 mt-2 font-display text-[20px] font-bold tracking-tight">
              O que faltou? <span className="text-[14px] font-normal text-muted-foreground">(até duas)</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {WANTS.map((w) => (
                <Chip key={w.value} active={wants.includes(w.value)} onClick={() => toggleWant(w.value)}>
                  {w.label}
                </Chip>
              ))}
            </div>

            <p className="mt-8 font-mono text-[10px] uppercase tracking-[2px] text-gold">2 de 2</p>
            <p className="mb-4 mt-2 font-display text-[20px] font-bold tracking-tight">Que carro procuras?</p>
            <div className="flex flex-wrap gap-2">
              {POWERTRAINS.map((p) => (
                <Chip key={p.value} active={powertrain === p.value} onClick={() => setPowertrain(p.value)}>
                  {p.label}
                </Chip>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {CONDITIONS.map((c) => (
                <Chip key={c.value} active={condition === c.value} onClick={() => setCondition(c.value)}>
                  {c.label}
                </Chip>
              ))}
            </div>
            {powertrain === "eletrico" && (
              <p className="mt-3 text-[12px] text-muted-foreground">
                Mostramos o custo de carregamento por mês: em casa sai bem mais barato do que só na rede pública.
              </p>
            )}

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <button type="button" disabled={loading}
                onClick={() => onSubmit(wants, powertrain, condition)}
                className="rounded-full bg-gold px-7 py-3 text-[13px] font-semibold text-background hover:bg-gold-dark disabled:opacity-60">
                {loading ? "a procurar..." : "ver nova lista"}
              </button>
              <button type="button" onClick={() => setOpen(false)} className="text-[13px] text-muted-foreground hover:text-gold">
                cancelar
              </button>
              {error && (
                <p className="text-[13px] text-danger">
                  Não encontrámos outros modelos com estas escolhas. Experimenta outra combinação.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
