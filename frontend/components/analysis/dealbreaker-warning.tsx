"use client"

import { cn } from "@/lib/utils"
import type { Dealbreakers } from "@/lib/types"

interface DealbreakerWarningProps {
  data?: Dealbreakers | null
  className?: string
}

/**
 * The loud "would this put a buyer off?" banner. Shows official recalls and
 * known critical failures with their sources. It never hides the car — it
 * warns, and lets the buyer decide.
 */
export function DealbreakerWarning({ data, className }: DealbreakerWarningProps) {
  if (!data || !data.has_dealbreaker) return null

  const total = data.recall_count + data.critical_issue_count

  return (
    <div
      className={cn(
        "rounded-xl border border-danger/45 bg-danger/[0.07] p-5",
        className
      )}
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
            Recalls oficiais
          </p>
          {data.recalls.map((r, i) => (
            <div key={i} className="border-l-2 border-danger/40 pl-3.5">
              <p className="text-[13px] font-medium leading-snug text-foreground">
                {r.title}
              </p>
              {r.description && (
                <p className="mt-1 text-xs font-light leading-relaxed text-muted-foreground">
                  {r.description}
                </p>
              )}
              <p className="mt-1.5 font-mono text-[10px] text-muted-foreground/60">
                {r.source}
                {r.date ? ` · ${r.date}` : ""}
                {r.source_url && (
                  <>
                    {" · "}
                    <a
                      href={r.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-danger/70 underline underline-offset-2 hover:text-danger"
                    >
                      fonte
                    </a>
                  </>
                )}
              </p>
            </div>
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
    </div>
  )
}
