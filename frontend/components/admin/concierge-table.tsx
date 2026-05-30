"use client"

import { useState, Fragment } from "react"
import { cn } from "@/lib/utils"
import { updateConcierge } from "@/lib/api"
import type { ConciergeRequestAdmin } from "@/lib/api"

const STATUS_OPTIONS = ["new", "contacted", "searching", "delivered", "closed"] as const

const STATUS_STYLES: Record<string, string> = {
  new: "border-zinc-600 bg-zinc-800/50 text-zinc-300",
  contacted: "border-blue-600/40 bg-blue-900/20 text-blue-400",
  searching: "border-gold/40 bg-gold/[0.08] text-gold",
  delivered: "border-green-600/40 bg-green-900/20 text-green-400",
  closed: "border-zinc-700 bg-zinc-800/30 text-zinc-500",
}

const STATUS_LABELS: Record<string, string> = {
  new: "Novo",
  contacted: "Contactado",
  searching: "A pesquisar",
  delivered: "Entregue",
  closed: "Fechado",
}

interface ConciergeTableProps {
  requests: ConciergeRequestAdmin[]
  token: string
  onUpdate: () => void
}

export function ConciergeTable({ requests, token, onUpdate }: ConciergeTableProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [editingNotes, setEditingNotes] = useState<number | null>(null)
  const [notesValue, setNotesValue] = useState("")
  const [saving, setSaving] = useState<number | null>(null)

  const handleStatusChange = async (id: number, newStatus: string) => {
    setSaving(id)
    try {
      await updateConcierge(token, id, { status: newStatus })
      onUpdate()
    } catch (err) {
      console.error("Status update error:", err)
    } finally {
      setSaving(null)
    }
  }

  const handleNotesSave = async (id: number) => {
    setSaving(id)
    try {
      await updateConcierge(token, id, { admin_notes: notesValue })
      onUpdate()
    } catch (err) {
      console.error("Notes update error:", err)
    } finally {
      setSaving(null)
      setEditingNotes(null)
    }
  }

  const startEditingNotes = (req: ConciergeRequestAdmin) => {
    setEditingNotes(req.id)
    setNotesValue(req.admin_notes || "")
  }

  if (requests.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card px-6 py-12 text-center">
        <p className="font-mono text-[11px] text-muted-foreground">
          Nenhum pedido de concierge
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-border bg-card">
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              #
            </th>
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Nome
            </th>
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Modelo
            </th>
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Orcamento
            </th>
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Status
            </th>
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Notas
            </th>
            <th className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
              Data
            </th>
          </tr>
        </thead>
        <tbody>
          {requests.map((req) => {
            const isExpanded = expandedId === req.id
            return (
              <Fragment key={req.id}>
                <tr
                  className={cn(
                    "cursor-pointer border-b border-border transition-colors hover:bg-card",
                    isExpanded && "bg-card",
                    saving === req.id && "opacity-50"
                  )}
                  onClick={() => setExpandedId(isExpanded ? null : req.id)}
                >
                  <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">
                    {req.id}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-[13px] font-medium text-foreground">
                      {req.name}
                    </div>
                    <div className="font-mono text-[10px] text-muted-foreground">
                      {req.email}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-[13px] text-foreground">
                    {req.model_interest || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-[12px] text-foreground">
                    {req.budget_max
                      ? `${req.budget_max.toLocaleString("pt-PT")} EUR`
                      : "—"}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <select
                      value={req.status}
                      onChange={(e) => handleStatusChange(req.id, e.target.value)}
                      className={cn(
                        "rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[1px] outline-none",
                        STATUS_STYLES[req.status] || STATUS_STYLES.new
                      )}
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s} className="bg-background text-foreground">
                          {STATUS_LABELS[s]}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td
                    className="max-w-[200px] px-4 py-3"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {editingNotes === req.id ? (
                      <input
                        value={notesValue}
                        onChange={(e) => setNotesValue(e.target.value)}
                        onBlur={() => handleNotesSave(req.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleNotesSave(req.id)
                          if (e.key === "Escape") setEditingNotes(null)
                        }}
                        autoFocus
                        className="w-full rounded border border-gold/40 bg-background px-2 py-1 font-mono text-[11px] text-foreground outline-none"
                      />
                    ) : (
                      <button
                        onClick={() => startEditingNotes(req)}
                        className="w-full truncate text-left font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground"
                        title={req.admin_notes || "Adicionar nota"}
                      >
                        {req.admin_notes || (
                          <span className="italic text-muted-foreground/40">
                            + nota
                          </span>
                        )}
                      </button>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-[10px] text-muted-foreground">
                      {req.created_at
                        ? new Date(req.created_at).toLocaleDateString("pt-PT", {
                            day: "2-digit",
                            month: "short",
                          })
                        : "—"}
                    </div>
                    {req.delivered_at && (
                      <div className="font-mono text-[9px] text-green-500/70">
                        entregue{" "}
                        {new Date(req.delivered_at).toLocaleDateString("pt-PT", {
                          day: "2-digit",
                          month: "short",
                        })}
                      </div>
                    )}
                  </td>
                </tr>

                {/* Expanded row detail */}
                {isExpanded && (
                  <tr className="border-b border-border">
                    <td colSpan={7} className="bg-card/50 px-6 py-4">
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                        {/* Tags */}
                        {req.feedback_tags && req.feedback_tags.length > 0 && (
                          <div>
                            <div className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
                              Feedback tags
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {req.feedback_tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="rounded-full border border-border px-2 py-0.5 font-mono text-[10px] text-muted-foreground"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Profile */}
                        {req.profile_summary && (
                          <div>
                            <div className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
                              Perfil
                            </div>
                            <div className="flex flex-col gap-1">
                              {Object.entries(req.profile_summary).map(
                                ([key, val]) => (
                                  <div
                                    key={key}
                                    className="flex items-center gap-2"
                                  >
                                    <span className="w-[80px] font-mono text-[10px] text-muted-foreground">
                                      {key}
                                    </span>
                                    <div className="h-1.5 w-20 overflow-hidden rounded-full bg-border">
                                      <div
                                        className="h-full rounded-full bg-gold/60"
                                        style={{
                                          width: `${((val as number) || 0) * 100}%`,
                                        }}
                                      />
                                    </div>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        )}

                        {/* Models shown */}
                        {req.models_shown && req.models_shown.length > 0 && (
                          <div>
                            <div className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
                              Modelos mostrados
                            </div>
                            <div className="flex flex-col gap-0.5">
                              {req.models_shown.map((m, i) => (
                                <div
                                  key={m.model_id}
                                  className="text-[12px] text-foreground/80"
                                >
                                  <span className="mr-1.5 font-mono text-[10px] text-muted-foreground">
                                    {i + 1}.
                                  </span>
                                  {m.full_name}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Consent + session */}
                        <div>
                          <div className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
                            Info
                          </div>
                          <div className="flex flex-col gap-0.5 font-mono text-[10px] text-muted-foreground">
                            <span>
                              Dealer:{" "}
                              {req.consent_dealer ? (
                                <span className="text-green-500">Sim</span>
                              ) : (
                                <span className="text-zinc-500">Nao</span>
                              )}
                            </span>
                            {req.session_id && (
                              <span
                                className="cursor-pointer truncate text-muted-foreground/40 hover:text-muted-foreground"
                                title={req.session_id}
                              >
                                Session: {req.session_id.slice(0, 8)}...
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

