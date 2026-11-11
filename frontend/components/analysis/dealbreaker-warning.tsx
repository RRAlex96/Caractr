"use client"

import { cn } from "@/lib/utils"
import type { DealbreakerRecall, Dealbreakers } from "@/lib/types"

interface DealbreakerWarningProps {
  data?: Dealbreakers | null
  className?: string
}

function RecallItem({ r, tone }: { r: DealbreakerRecall; tone: "danger" | "muted" }) {
  const border = tone === "danger" ? "border-danger/40" : "border-border"
  const link = tone === "danger" ? "text-danger/70 hover:text-danger" : "text-muted-foreground hover:text-foreground"
  return (
    <div className={cn("border-l-2 pl-3.5", border)}>
      <p className="text-[13px] font-medium leading-snug text-foreground">{r.title}</p>
      {r.description && (
        <p className="mt-1 text-xs font-light leading-relaxed text-muted-foreground">{r.description}</p>
      )}
      <p className="mt-1.5 font-mono text-[10px] text-muted-foreground/60">
        {r.affected_years ? `Produção ${r.affected_years} · ` : ""}
        {r.source}
        {r.date ? ` · ${r.date}` : ""}
        {r.source_url && (
          <>
            {" · "}
            <a
              href={r.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className={cn("underline underline-offset-2", link)}
            >
              fonte
            </a>
          </>
        )}
      </p>
    </div>
  )
}

/** US recalls: real, but for US-spec cars — shown with that caveat, never loud. */
function UsRecalls({ recalls, standalone }: { recalls: DealbreakerRecall[]; standalone?: boolean }) {
  if (!recalls.length) return null
  return (
    <div className={cn("space-y-3", !standalone && "mt-4 border-t border-border/60 pt-4")}>
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground/80">
        Recalls nos EUA (NHTSA)
      </p>
      <p className="text-[11px] font-light leading-relaxed text-muted-foreground">
        Dizem respeito à versão americana — motores e componentes podem ser diferentes na europeia.
        Confirma com um concessionário se se aplicam a este carro.
      </p>
      {recalls.map((r, i) => (
        <RecallItem key={i} r={r} tone="muted" />
      ))}
    </div>
  )
}

/**
 * The loud "would this put a buyer off?" banner: EU-official recalls and
 * known critical failures, with their sources. It never hides the car — it
 * warns, and lets the buyer decide. US recalls appear separately and quietly.
 */
export function DealbreakerWarning({ data, className }: DealbreakerWarningProps) {
  if (!data) return null
  const usRecalls = data.us_recalls ?? []

  // Only US recalls on record: an informative, neutral panel — not a red alarm.
  if (!data.has_dealbreaker) {
    if (!usRecalls.length) return null
    return (
      <div className={cn("rounded-xl border border-border bg-card p-5", className)}>
        <UsRecalls recalls={usRecalls} standalone />
      </div>
    )
  }

  const total = data.recall_count + data.critical_issue_count

  return (
    <div
      className={cn("rounded-xl border border-danger/45 bg-danger/[0.07] p-5", className)}
      role="alert"
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="text-base leading-none text-danger" aria-hidden>
          ⚠
        </span>
        <p className="font-mono text-[10px] uppercase tracking-[1.5px] text-danger">
          {total === 1 ? "Alerta sério" : `${total} alertas sérios`}
        </p>
      </div>

      <p className="mb-4 text-[13px] font-light leading-relaxed text-foreground">
        Encontrámos recalls oficiais ou falhas graves conhecidas neste modelo.
        Não é motivo para desistir à partida — mas confirma cada ponto antes de avançar.
      </p>

      {data.recalls.length > 0 && (
        <div className="mb-4 space-y-3">
          <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-danger/80">
            Recalls oficiais (UE)
          </p>
          {data.recalls.map((r, i) => (
            <RecallItem key={i} r={r} tone="danger" />
          ))}
        </div>
      )}

      {data.critical_issues.length > 0 && (
        <div className="space-y-3">
          <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-danger/80">
            Falhas graves conhecidas
          </p>
          {data.critical_issues.map((c, i) => (
            <div key={i} className="border-l-2 border-danger/40 pl-3.5">
              <p className="text-[13px] font-light leading-relaxed text-foreground">
                {c.description}
              </p>
              {(c.affected_years || c.fix_cost_estimate || c.source) && (
                <p className="mt-1.5 font-mono text-[10px] text-muted-foreground/60">
                  {[
                    c.affected_years,
                    c.fix_cost_estimate ? `reparação ~${c.fix_cost_estimate}` : null,
                    c.source,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <UsRecalls recalls={usRecalls} />
    </div>
  )
}
