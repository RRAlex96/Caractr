"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { enrichModelDraft, enrichModelSave } from "@/lib/api"
import type { ModelEnrichment, KnownIssue } from "@/lib/api"

interface ModelEnrichPanelProps {
  token: string
  modelId: number
  label: string
  onSaved: () => void
}

const SEVERITIES = ["alto", "medio", "baixo"]

export function ModelEnrichPanel({ token, modelId, label, onSaved }: ModelEnrichPanelProps) {
  const [draft, setDraft] = useState<ModelEnrichment | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState("")

  const generate = async () => {
    setLoading(true)
    setError("")
    try {
      const d = await enrichModelDraft(token, modelId)
      setDraft({ ...d, known_issues: d.known_issues || [] })
    } catch (e: any) {
      setError(e.message || "Erro ao gerar")
    } finally {
      setLoading(false)
    }
  }

  const save = async () => {
    if (!draft) return
    setSaving(true)
    setError("")
    try {
      await enrichModelSave(token, modelId, draft)
      setSaved(true)
      setTimeout(onSaved, 800)
    } catch (e: any) {
      setError(e.message || "Erro ao guardar")
    } finally {
      setSaving(false)
    }
  }

  const set = (patch: Partial<ModelEnrichment>) =>
    setDraft((d) => (d ? { ...d, ...patch } : d))

  const setIssue = (i: number, patch: Partial<KnownIssue>) =>
    setDraft((d) => {
      if (!d) return d
      const issues = [...d.known_issues]
      issues[i] = { ...issues[i], ...patch }
      return { ...d, known_issues: issues }
    })

  const removeIssue = (i: number) =>
    setDraft((d) => (d ? { ...d, known_issues: d.known_issues.filter((_, j) => j !== i) } : d))

  const inputCls =
    "w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-[13px] text-foreground outline-none focus:border-gold/40"
  const labelCls = "mb-1 block font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground"

  if (saved) {
    return (
      <div className="px-4 py-3">
        <p className="font-mono text-[11px] tracking-[1px] text-success">GUARDADO ✓</p>
      </div>
    )
  }

  if (!draft) {
    return (
      <div className="flex items-center gap-3 px-4 py-3">
        <button
          onClick={generate}
          disabled={loading}
          className="rounded-full bg-gold px-4 py-1.5 font-mono text-[10px] uppercase tracking-[1px] text-background transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "A gerar…" : "Gerar com IA"}
        </button>
        {error && <span className="font-mono text-[10px] text-red-500">{error}</span>}
      </div>
    )
  }

  return (
    <div className="space-y-4 px-4 py-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <label className={labelCls}>Fiabilidade (0-10)</label>
          <input
            type="number" step="0.1" min="0" max="10"
            className={inputCls}
            value={draft.reliability_score ?? ""}
            onChange={(e) => set({ reliability_score: e.target.value === "" ? null : parseFloat(e.target.value) })}
          />
        </div>
        <div>
          <label className={labelCls}>Manutenção €/ano</label>
          <input
            type="number" className={inputCls}
            value={draft.maintenance_cost_year ?? ""}
            onChange={(e) => set({ maintenance_cost_year: e.target.value === "" ? null : parseInt(e.target.value) })}
          />
        </div>
        <div>
          <label className={labelCls}>Motor (código)</label>
          <input
            className={inputCls}
            value={draft.engine_code ?? ""}
            onChange={(e) => set({ engine_code: e.target.value })}
          />
        </div>
        <div>
          <label className={labelCls}>Anos</label>
          <div className="flex gap-1">
            <input
              type="number" placeholder="início" className={inputCls}
              value={draft.year_start ?? ""}
              onChange={(e) => set({ year_start: e.target.value === "" ? null : parseInt(e.target.value) })}
            />
            <input
              type="number" placeholder="fim" className={inputCls}
              value={draft.year_end ?? ""}
              onChange={(e) => set({ year_end: e.target.value === "" ? null : parseInt(e.target.value) })}
            />
          </div>
        </div>
      </div>

      <div>
        <label className={labelCls}>Resumo de fiabilidade</label>
        <textarea
          className={cn(inputCls, "min-h-[56px] resize-y")}
          value={draft.reliability_summary ?? ""}
          onChange={(e) => set({ reliability_summary: e.target.value })}
        />
      </div>

      <div>
        <label className={labelCls}>Problemas conhecidos</label>
        <div className="space-y-2">
          {draft.known_issues.map((iss, i) => (
            <div key={i} className="flex flex-wrap items-start gap-2 rounded-md border border-border/60 p-2">
              <select
                className={cn(inputCls, "w-auto")}
                value={iss.severity}
                onChange={(e) => setIssue(i, { severity: e.target.value })}
              >
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <input
                className={cn(inputCls, "flex-1 min-w-[180px]")}
                placeholder="descrição"
                value={iss.description}
                onChange={(e) => setIssue(i, { description: e.target.value })}
              />
              <input
                className={cn(inputCls, "w-24")}
                placeholder="anos"
                value={iss.affected_years ?? ""}
                onChange={(e) => setIssue(i, { affected_years: e.target.value })}
              />
              <input
                className={cn(inputCls, "w-28")}
                placeholder="custo"
                value={iss.fix_cost_estimate ?? ""}
                onChange={(e) => setIssue(i, { fix_cost_estimate: e.target.value })}
              />
              <button
                onClick={() => removeIssue(i)}
                className="px-2 py-1 font-mono text-[11px] text-muted-foreground hover:text-red-500"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={save}
          disabled={saving}
          className="rounded-full bg-gold px-5 py-1.5 font-mono text-[10px] uppercase tracking-[1px] text-background transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {saving ? "A guardar…" : `Guardar — ${label}`}
        </button>
        <span className="font-mono text-[9px] uppercase tracking-[1px] text-muted-foreground/50">
          Marca como dados estimados por IA
        </span>
        {error && <span className="font-mono text-[10px] text-red-500">{error}</span>}
      </div>
    </div>
  )
}
