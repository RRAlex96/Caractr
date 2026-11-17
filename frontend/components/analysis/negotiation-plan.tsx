"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"
import type { NegotiationPlan as Plan } from "@/lib/types"

const eur = (n: number) => `${n.toLocaleString("pt-PT")} €`

// "de" + article, contracted: da correia, do turbo, dos injetores.
function deDe(topic?: string | null): string {
  const t = topic || "da reparação"
  for (const [art, c] of [["a ", "da "], ["o ", "do "], ["as ", "das "], ["os ", "dos "]] as const) {
    if (t.startsWith(art)) return c + t.slice(art.length)
  }
  return t.startsWith("da ") ? t : `de ${t}`
}

function MessageBox({ label, text, analysisId, kind }: { label: string; text: string; analysisId?: number | null; kind: string }) {
  const [value, setValue] = useState(text)
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard blocked: the text stays selectable */
    }
    Analytics.sellerMessageCopied(analysisId, `${kind}:copy`)
  }
  const whatsapp = () => {
    Analytics.sellerMessageCopied(analysisId, `${kind}:whatsapp`)
    window.open(`https://wa.me/?text=${encodeURIComponent(value)}`, "_blank")
  }
  return (
    <div>
      <p className="mb-2 text-[13px] text-muted-foreground">{label}</p>
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={Math.min(10, value.split("\n").length + 1)}
        className="w-full resize-y rounded-[10px] border border-border bg-background px-4 py-3 text-[14px] leading-relaxed text-foreground outline-none focus:border-gold"
      />
      <div className="mt-2 flex flex-wrap gap-2">
        <button onClick={copy} className="rounded-full bg-gold px-4 py-1.5 text-[12px] font-medium text-background hover:opacity-90">
          {copied ? "Copiada" : "Copiar"}
        </button>
        <button onClick={whatsapp} className="rounded-full border border-border px-4 py-1.5 text-[12px] text-muted-foreground hover:border-gold/40 hover:text-foreground">
          Enviar por WhatsApp
        </button>
      </div>
    </div>
  )
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-border pt-5 first:border-t-0 first:pt-0">
      <p className="mb-3 flex items-baseline gap-2.5">
        <span className="font-mono text-[11px] text-gold">{n}</span>
        <span className="font-display text-[17px] font-bold text-foreground">{title}</span>
      </p>
      {children}
    </div>
  )
}

/** One plan, three steps: what to ask first, the numbers, and the offer with replies. */
export function NegotiationPlan({ plan, analysisId, className }: { plan?: Plan | null; analysisId?: number | null; className?: string }) {
  const [openCounter, setOpenCounter] = useState<number | null>(null)
  if (!plan) return null
  const n = plan.numbers

  return (
    <section className={cn("rounded-xl border border-gold/30 bg-card p-5 md:p-6", className)}>
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">Negociar</p>
      <p className="mb-5 mt-1 font-display text-[21px] font-bold text-foreground">Como fazer o melhor negócio</p>

      <div className="space-y-6">
        <Step n={1} title="Antes de ir ver o carro">
          <MessageBox label="Envia isto ao vendedor. Sem falar de preço ainda." text={plan.messages.first_contact} analysisId={analysisId} kind="first" />
        </Step>

        <Step n={2} title="Os teus números">
          {n ? (
            <>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { k: "Começa em", v: n.opening, hint: "a tua primeira oferta" },
                  { k: "Objetivo", v: n.target, hint: "onde queres fechar" },
                  { k: "Máximo", v: n.ceiling, hint: "acima disto, sai" },
                ].map((x) => (
                  <div key={x.k} className="rounded-lg border border-border px-3 py-3">
                    <p className="text-[11px] text-muted-foreground">{x.k}</p>
                    <p className="mt-0.5 font-mono text-[17px] font-bold text-foreground">{eur(x.v)}</p>
                    <p className="text-[10px] text-muted-foreground/70">{x.hint}</p>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-[12px] text-muted-foreground">
                Pedem {eur(n.asking)}.{plan.walk_away?.ceiling_unproven != null && (
                  <> Sem a fatura indicada abaixo, o teu máximo desce para <span className="text-foreground">{eur(plan.walk_away.ceiling_unproven)}</span>.</>
                )}
              </p>
            </>
          ) : (
            <p className="text-[14px] leading-relaxed text-muted-foreground">{plan.note}</p>
          )}
          {plan.arguments.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-[13px] text-muted-foreground">Os teus argumentos:</p>
              <ul className="space-y-2">
                {plan.arguments.map((a, i) => (
                  <li key={i} className="flex gap-2.5 text-[14px] leading-relaxed text-foreground/90">
                    <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-gold" />
                    <span>{a.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Step>

        <Step n={3} title="Fazer a proposta">
          <MessageBox
            label={plan.messages.offer_no_invoice
              ? `Depois da visita, se houver fatura ${deDe(plan.messages.no_invoice_topic)} e o carro estiver como esperado:`
              : "Depois da visita, se o carro estiver como esperado:"}
            text={plan.messages.offer}
            analysisId={analysisId}
            kind="offer"
          />
          {plan.messages.offer_no_invoice && (
            <div className="mt-4">
              <MessageBox
                label={`Se não houver fatura ${deDe(plan.messages.no_invoice_topic)}:`}
                text={plan.messages.offer_no_invoice}
                analysisId={analysisId}
                kind="offer_no_invoice"
              />
            </div>
          )}
          {plan.messages.counters.length > 0 && (
            <div className="mt-5">
              <p className="mb-2 text-[13px] text-muted-foreground">Se o vendedor responder…</p>
              <div className="divide-y divide-border rounded-lg border border-border">
                {plan.messages.counters.map((c, i) => (
                  <div key={i}>
                    <button
                      type="button"
                      onClick={() => setOpenCounter(openCounter === i ? null : i)}
                      className="flex w-full items-center justify-between px-4 py-3 text-left text-[14px] text-foreground"
                    >
                      {c.if}
                      <span className="ml-3 text-muted-foreground">{openCounter === i ? "−" : "+"}</span>
                    </button>
                    {openCounter === i && (
                      <p className="px-4 pb-4 text-[14px] leading-relaxed text-muted-foreground">{c.reply}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Step>
      </div>
    </section>
  )
}
