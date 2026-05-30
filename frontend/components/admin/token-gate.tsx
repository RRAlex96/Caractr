"use client"

import { useState } from "react"

interface TokenGateProps {
  onAuthenticate: (token: string) => void
}

export function TokenGate({ onAuthenticate }: TokenGateProps) {
  const [input, setInput] = useState("")

  const handleSubmit = () => {
    if (input.trim()) {
      localStorage.setItem("caractr_admin_token", input.trim())
      onAuthenticate(input.trim())
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-[360px] rounded-xl border border-border bg-card p-6 text-center">
        <div className="mb-6 font-display text-sm font-bold tracking-[0.12em] text-foreground">
          CARACTR ADMIN
        </div>
        <input
          type="password"
          placeholder="Admin token"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          className="mb-3 w-full rounded-lg border border-border bg-background px-4 py-3 font-mono text-[13px] text-foreground outline-none transition-colors placeholder:text-muted-foreground/40 focus:border-gold/60"
        />
        <button
          onClick={handleSubmit}
          className="w-full rounded-lg bg-foreground px-4 py-3 font-mono text-[11px] uppercase tracking-[1.5px] text-background transition-opacity hover:opacity-90"
        >
          Entrar
        </button>
      </div>
    </div>
  )
}
