"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { fetchAdminDashboard } from "@/lib/api"
import { TokenGate } from "@/components/admin/token-gate"
import { AnalyticsTab } from "@/components/admin/analytics-tab"
import { ConciergeTab } from "@/components/admin/concierge-tab"
import { ModelsTab } from "@/components/admin/models-tab"

type Tab = "analytics" | "concierge" | "models"

export default function AdminPage() {
  const [token, setToken] = useState("")
  const [tab, setTab] = useState<Tab>("analytics")
  const [period, setPeriod] = useState("30d")
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  // Restore token from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("caractr_admin_token")
    if (saved) setToken(saved)
  }, [])

  // Fetch analytics data
  useEffect(() => {
    if (!token || tab !== "analytics") return
    setLoading(true)
    setError("")
    fetchAdminDashboard(token, period)
      .then((d) => {
        setData(d)
        setLoading(false)
      })
      .catch((e) => {
        setError(e.message)
        setLoading(false)
      })
  }, [token, period, tab])

  const handleLogout = () => {
    localStorage.removeItem("caractr_admin_token")
    setToken("")
    setData(null)
  }

  if (!token) {
    return <TokenGate onAuthenticate={setToken} />
  }

  return (
    <div className="min-h-screen bg-background px-6 pb-8 pt-24">
      <div className="mx-auto max-w-[960px]">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-display text-sm font-bold tracking-[0.12em] text-foreground">
              CARACTR
            </span>
            <span className="font-mono text-[10px] tracking-[1px] text-muted-foreground">
              ADMIN
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Tab switcher */}
            <div className="flex gap-1">
              {([
                { key: "analytics", label: "Analytics" },
                { key: "concierge", label: "Concierge" },
                { key: "models", label: "Modelos" },
              ] as const).map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={cn(
                    "rounded-full border px-4 py-1.5 font-mono text-[10px] uppercase tracking-[1px] transition-colors",
                    tab === t.key
                      ? "border-gold bg-gold/[0.08] text-gold"
                      : "border-border text-muted-foreground hover:border-foreground/20 hover:text-foreground"
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Period selector — only for analytics tab */}
            {tab === "analytics" && (
              <div className="ml-2 flex gap-1">
                {["7d", "30d", "90d"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={cn(
                      "rounded-full border px-3.5 py-1.5 font-mono text-[10px] tracking-[1px] transition-colors",
                      period === p
                        ? "border-foreground/20 bg-foreground/[0.05] text-foreground"
                        : "border-border text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="ml-2 rounded-full border border-border px-3 py-1.5 font-mono text-[10px] tracking-[1px] text-muted-foreground transition-colors hover:text-foreground"
            >
              SAIR
            </button>
          </div>
        </div>

        {/* Analytics Tab */}
        {tab === "analytics" && (
          <>
            {loading && (
              <div className="py-16 text-center">
                <p className="font-mono text-[11px] tracking-[1px] text-muted-foreground">
                  A CARREGAR...
                </p>
              </div>
            )}
            {error && (
              <div className="py-16 text-center">
                <p className="font-mono text-[11px] tracking-[1px] text-red-500">
                  {error.toUpperCase()}
                </p>
              </div>
            )}
            {data && !loading && <AnalyticsTab data={data} />}
          </>
        )}

        {/* Concierge Tab */}
        {tab === "concierge" && <ConciergeTab token={token} />}

        {/* Models Tab */}
        {tab === "models" && <ModelsTab token={token} />}
      </div>
    </div>
  )
}
