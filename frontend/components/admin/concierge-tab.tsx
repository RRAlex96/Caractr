"use client"

import { useState, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { fetchConciergeList, fetchConciergeStats } from "@/lib/api"
import type { ConciergeRequestAdmin, ConciergeStats } from "@/lib/api"
import { ConciergeStatsCards } from "./concierge-stats"
import { ConciergeTable } from "./concierge-table"

interface ConciergeTabProps {
  token: string
}

const STATUS_FILTERS = [
  { value: "", label: "Todos" },
  { value: "new", label: "Novos" },
  { value: "contacted", label: "Contactados" },
  { value: "searching", label: "A pesquisar" },
  { value: "delivered", label: "Entregues" },
  { value: "closed", label: "Fechados" },
] as const

export function ConciergeTab({ token }: ConciergeTabProps) {
  const [stats, setStats] = useState<ConciergeStats | null>(null)
  const [requests, setRequests] = useState<ConciergeRequestAdmin[]>([])
  const [statusFilter, setStatusFilter] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [statsData, listData] = await Promise.all([
        fetchConciergeStats(token),
        fetchConciergeList(token, {
          status: statusFilter || undefined,
        }),
      ])
      setStats(statsData)
      setRequests(listData.requests)
    } catch (err: any) {
      setError(err.message || "Erro ao carregar dados")
    } finally {
      setLoading(false)
    }
  }, [token, statusFilter])

  useEffect(() => {
    loadData()
  }, [loadData])

  return (
    <div>
      {/* Stats */}
      <ConciergeStatsCards stats={stats} />

      {/* Status filter */}
      <div className="mb-4 flex gap-1.5">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={cn(
              "rounded-full border px-3 py-1.5 font-mono text-[10px] uppercase tracking-[1px] transition-colors",
              statusFilter === f.value
                ? "border-gold bg-gold/[0.08] text-gold"
                : "border-border text-muted-foreground hover:border-foreground/20 hover:text-foreground"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Loading / Error */}
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

      {/* Table */}
      {!loading && !error && (
        <ConciergeTable
          requests={requests}
          token={token}
          onUpdate={loadData}
        />
      )}
    </div>
  )
}
