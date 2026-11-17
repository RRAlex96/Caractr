"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"
import type { NegotiationPlan as Plan, NegotiationStage } from "@/lib/types"

const eur = (n: number) => `${n.toLocaleString("pt-PT")} €`

// "de" + article, contracted: da correia, do turbo, dos injetores.
function deDe(topic?: string | null): string {
  const t = topic || "a reparação"
  for (const [art, c] of [["a ", "da "], ["o ", "do "], ["as ", "das "], ["os ", "dos "]] as const) {
    if (t.startsWith(art)) return c + t.slice(art.length)
  }
  return `de ${t}`
}

function MessageBox({ label, text, analysisId, kind }: { label?: string; text: string; analysisId?: number | null; kind: string }) {
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
      {label && <p className="mb-2 text-[13px] text-muted-foreground">{label}</p>}
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={Math.min(10, Math.ceil(value.length / 48) + value.split("\n").length)}
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

function StageBody({ s, analysisId }: { s: NegotiationStage; analysisId?: number | null }) {
  const [openCounter, setOpenCounter] = useState<number | null>(null)
  return (
    <div className="space-y-4">
      {s.tips && s.tips.length > 0 && (
        <ul className="space-y-2">
          {s.tips.map((t, i) => (
            <li key={i} className="flex gap-2.5 text-[14px] leading-relaxed text-foreground/90">
              <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-gold" />
              <span>{t}</span>
            </li>
          ))}
        </ul>
      )}
      {s.message && (
        <MessageBox
          label={s.message_no_invoice ? `Se houver fatura ${deDe(s.no_invoice_topic)}:` : s.key === "fecho" ? "Se não chegarem a acordo:" : undefined}
          text={s.message}
          analysisId={analysisId}
          kind={s.key}
        />
      )}
      {s.message_no_invoice && (
        <MessageBox label={`Se não houver fatura ${deDe(s.no_invoice_topic)}:`} text={s.message_no_invoice} analysisId={analysisId} kind={`${s.key}_sem_fatura`} />
      )}
      {s.ladder && s.ladder.length > 0 && (
        <div>
          <p className="mb-2 text-[13px] text-muted-foreground">Sobe assim, um degrau de cada vez:</p>
          <ol className="space-y-2">
            {s.ladder.map((l, i) => (
              <li key={i} className="flex items-baseline gap-3 rounded-lg border border-border px-3.5 py-2.5">
                <span className="font-mono text-[14px] font-bold text-foreground">{eur(l.price)}</span>
                <span className="text-[13px] text-muted-foreground">«{l.say}»</span>
              </li>
            ))}
          </ol>
        </div>
      )}
      {s.counters && s.counters.length > 0 && (
        <div className="divide-y divide-border rounded-lg border border-border">
          {s.counters.map((c, i) => (
            <div key={i}>
              <button type="button" onClick={() => setOpenCounter(openCounter === i ? null : i)}
                className="flex w-full items-center justify-between px-4 py-3 text-left text-[14px] text-foreground">
                {c.if}
                <span className="ml-3 text-muted-foreground">{openCounter === i ? "−" : "+"}</span>
              </button>
              {openCounter === i && <p className="px-4 pb-4 text-[14px] leading-relaxed text-muted-foreground">{c.reply}</p>}
            </div>
          ))}
        </div>
      )}
      <p className="border-l-2 border-gold/40 pl-3 text-[12px] leading-relaxed text-muted-foreground">
        <span className="text-foreground/80">Porque resulta: </span>{s.why}
      </p>
    </div>
  )
}

/** The negotiation guide: your numbers, then five moments with ready messages. */
export function NegotiationPlan({ plan, analysisId, className }: { plan?: Plan | null; analysisId?: number | null; className?: string }) {
  const [open, setOpen] = useState(0)
  if (!plan) return null
  const n = plan.numbers
  const stages = plan.stages ?? []

  return (
    <section className={cn("rounded-xl border border-gold/30 bg-card p-5 md:p-6", className)}>
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">Negociar</p>
      <p className="mb-5 mt-1 font-display text-[21px] font-bold text-foreground">Como fazer o melhor negócio</p>

      {n ? (
        <>
          <div className="grid grid-cols-3 gap-2">
            {[
              { k: "Começa em", v: n.opening },
              { k: "Objetivo", v: n.target },
              { k: "Máximo", v: n.ceiling },
            ].map((x) => (
              <div key={x.k} className="rounded-lg border border-border px-3 py-3">
                <p className="text-[11px] text-muted-foreground">{x.k}</p>
                <p className="mt-0.5 font-mono text-[17px] font-bold text-foreground">{eur(x.v)}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[12px] text-muted-foreground">
            Pedem {eur(n.asking)}.
            {plan.walk_away?.ceiling_unproven != null && (
              <> Sem fatura {deDe(stages.find((s) => s.no_invoice_topic)?.no_invoice_topic)}, o teu máximo desce para{" "}
                <span className="text-foreground">{eur(plan.walk_away.ceiling_unproven)}</span>.</>
            )}
          </p>
        </>
      ) : (
        <p className="text-[14px] leading-relaxed text-muted-foreground">{plan.note}</p>
      )}

      {plan.arguments.length > 0 && (
        <ul className="mt-4 space-y-2">
          {plan.arguments.map((a, i) => (
            <li key={i} className="flex gap-2.5 text-[14px] leading-relaxed text-foreground/90">
              <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-gold" />
              <span>{a.text}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-6 divide-y divide-border border-t border-border">
        {stages.map((s, i) => (
          <div key={s.key} className="py-4">
            <button type="button" onClick={() => setOpen(open === i ? -1 : i)} className="flex w-full items-baseline gap-3 text-left">
              <span className="font-mono text-[11px] text-gold">{i + 1}</span>
              <span className="flex-1 font-display text-[16px] font-bold text-foreground">{s.title}</span>
              <span className="text-muted-foreground">{open === i ? "−" : "+"}</span>
            </button>
            {open === i && (
              <div className="mt-4">
                <StageBody s={s} analysisId={analysisId} />
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
