"use client"

import { useState, useEffect, useCallback } from "react"
import { fetchPendingModels } from "@/lib/api"
import type { PendingModel } from "@/lib/api"

interface ModelsTabProps {
  token: string
}

function formatDate(iso: string | null): string {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleDateString("pt-PT", {
      day: "2-digit",
      month: "short",
    })
  } catch {
    return "—"
  }
}

export function ModelsTab({ token }: ModelsTabProps) {
  const [models, setModels] = useState<PendingModel[]>([])
  const [count, setCount] = useState(0)
  const [analysedGap, setAnalysedGap] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const data = await fetchPendingModels(token)
      setModels(data.models)
      setCount(data.count)
      setAnalysedGap(data.analysed_gap)
    } catch (err: any) {
      setError(err.message || "Erro ao carregar dados")
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div>
      {/* Header stats */}
      <div className="mb-5 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2">
        <div className="bg-card p-4">
          <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            Sem fiabilidade
          </p>
          <p className="font-display text-[28px] font-bold leading-none text-foreground">
            {count}
          </p>
        </div>
        <div className="bg-card p-4">
          <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
            Já analisados por users
          </p>
          <p className="font-display text-[28px] font-bold leading-none text-gold">
            {analysedGap}
          </p>
        </div>
      </div>

      <p className="mb-4 text-[12px] font-light leading-relaxed text-muted-foreground/70">
        Modelos registados automaticamente que ainda não têm dados de
        fiabilidade. Ordenados pelos mais analisados — preenche estes primeiro.
      </p>

      {loading && (
        <div className="py-12 text-center">
          <p className="font-mono text-[11px] tracking-[1px] text-muted-foreground">
            A CARREGAR...
          </p>
        </div>
      )}

      {error && (
        <div className="py-12 text-center">
          <p className="font-mono text-[11px] tracking-[1px] text-red-500">
            {error.toUpperCase()}
          </p>
        </div>
      )}

      {!loading && !error && models.length === 0 && (
        <div className="py-12 text-center">
          <p className="font-mono text-[11px] tracking-[1px] text-muted-foreground">
            TUDO ENRIQUECIDO — SEM MODELOS PENDENTES
          </p>
        </div>
      )}

      {!loading && !error && models.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border bg-card">
                {["Modelo", "Análises", "Gerações", "Motores", "Adicionado"].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr
                  key={m.id}
                  className="border-b border-border/50 bg-card transition-colors hover:bg-foreground/[0.02]"
                >
                  <td className="px-4 py-3">
                    <span className="text-[14px] font-medium text-foreground">
                      {m.brand_name} {m.model_name}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        m.analyses > 0
                          ? "font-mono text-[13px] font-bold text-gold"
                          : "font-mono text-[13px] text-muted-foreground/50"
                      }
                    >
                      {m.analyses}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-[13px] text-muted-foreground">
                    {m.generations}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {m.has_engines ? "sim" : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground/60">
                    {formatDate(m.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
