"use client"

import { cn } from "@/lib/utils"
import type { DealbreakerIssue, DealbreakerRecall, Dealbreakers } from "@/lib/types"

function SourceLine({ parts, url }: { parts: (string | null | undefined)[]; url?: string | null }) {
  const text = parts.filter(Boolean).join(" · ")
  if (!text && !url) return null
  return (
    <p className="mt-1.5 font-mono text-[10px] text-muted-foreground/60">
      {text}
      {url && (
        <>
          {text ? " · " : ""}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-foreground"
          >
            fonte
          </a>
        </>
      )}
    </p>
  )
}

/**
 * Critical known failures: a chronic, expensive weakness of one engine or
 * gearbox. The only thing that shows in red — and it names the engine, so
 * the buyer can pick a different version rather than drop the model.
 */
export function CriticalIssueList({ issues }: { issues: DealbreakerIssue[] }) {
  if (!issues.length) return null
  return (
    <div className="space-y-3">
      {issues.map((c, i) => (
        <div key={i} className="border-l-2 border-danger/50 pl-3.5">
          {c.engine && (
            <p className="text-[13px] font-medium leading-snug text-foreground">{c.engine}</p>
          )}
          <p className="mt-0.5 text-[13px] font-light leading-relaxed text-foreground/90">
            {c.description}
          </p>
          <SourceLine
            parts={[
              c.affected_years ? `Afeta ${c.affected_years}` : null,
              c.fix_cost_estimate ? `reparação ~${c.fix_cost_estimate}` : null,
              c.source,
            ]}
          />
        </div>
      ))}
    </div>
  )
}

function RecallItem({ r }: { r: DealbreakerRecall }) {
  // Lead with what's wrong; "<Model>: Risco de ferimentos" is just a tag.
  const body = r.description || r.title
  return (
    <li className="flex gap-3">
      <span
        aria-hidden
        className={cn(
          "mt-[3px] h-3.5 w-3.5 shrink-0 rounded-[4px] border",
          r.priority ? "border-warning/70" : "border-border"
        )}
      />
      <div className="min-w-0">
        {r.priority && (
          <p className="mb-1 font-mono text-[9px] uppercase tracking-[1.5px] text-warning">
            Prioritário · airbag
          </p>
        )}
        <p className="text-[13px] font-light leading-relaxed text-foreground/90">{body}</p>
        <SourceLine
          parts={[r.affected_years ? `Produção ${r.affected_years}` : null, r.risk, r.source, r.date]}
          url={r.source_url}
        />
      </div>
    </li>
  )
}

interface PanelProps {
  data?: Dealbreakers | null
  className?: string
}

/**
 * Critical known failure for this model/year — rare and engine-specific, the
 * only red panel in the analysis. Sits near the top: it changes the decision.
 */
export function KnownFailureAlert({ data, className }: PanelProps) {
  const critical = data?.critical_issues ?? []
  if (!critical.length) return null
  return (
    <div
      className={cn("rounded-xl border border-danger/40 bg-danger/[0.06] p-5", className)}
      role="alert"
    >
      <p className="mb-1 font-mono text-[10px] uppercase tracking-[1.5px] text-danger">
        ⚠ {critical.length === 1 ? "Falha grave conhecida" : `${critical.length} falhas graves conhecidas`}
      </p>
      <p className="mb-4 text-[12px] font-light leading-relaxed text-muted-foreground">
        Um problema crónico e caro de um motor ou caixa específicos. Confirma a versão exata do
        anúncio — e, se coincidir, pede prova de que já foi reparado.
      </p>
      <CriticalIssueList issues={critical} />
    </div>
  )
}

/**
 * Recall checklist — calm on purpose. EU recalls are free fixes the
 * manufacturer already owns, often for a single production batch: the
 * buyer's job is to confirm they were done, not to walk away.
 */
export function RecallChecklist({ data, year, className }: PanelProps & { year?: number | null }) {
  const recalls = data?.recalls ?? []
  if (!recalls.length) return null
  const hasPriority = recalls.some((r) => r.priority)
  const forYear = year ? ` para carros de ${year}` : ""

  return (
    <section className={cn("rounded-xl border border-border bg-card p-5", className)}>
      <p className="mb-3 font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground">
        Recalls a confirmar
      </p>
      <p className="text-[13px] font-medium leading-snug text-foreground">
        {recalls.length === 1
          ? `1 campanha de recall${forYear}`
          : `${recalls.length} campanhas de recall${forYear}`}
      </p>
      <p className="mb-4 mt-1 text-[12px] font-light leading-relaxed text-muted-foreground">
        São reparações gratuitas no concessionário da marca e muitas abrangem só um lote de
        produção. Liga para um concessionário com o número do quadro (VIN) — dizem-te se este carro
        estava incluído e se a reparação já foi feita.
        {hasPriority &&
          " Dá prioridade às de airbag: num carro mais antigo que falhou a campanha, o insuflador degradado pode ferir ao disparar."}
      </p>
      <ul className="space-y-4">
        {recalls.map((r, i) => (
          <RecallItem key={i} r={r} />
        ))}
      </ul>
    </section>
  )
}
