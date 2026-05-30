"use client"

import { useEffect } from "react"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error("[Caractr] Unhandled error:", error)
  }, [error])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 pt-16 text-center">
      <p className="mb-5 font-mono text-[11px] uppercase tracking-[2px] text-gold">
        ALGO CORREU MAL
      </p>
      <h1 className="mb-4 font-display text-[clamp(28px,5vw,48px)] font-extrabold leading-none tracking-tight text-foreground">
        ERRO INESPERADO
      </h1>
      <p className="mb-9 max-w-[400px] text-[15px] font-light leading-relaxed text-muted-foreground">
        Ocorreu um erro que nao conseguimos prever. Tenta novamente — se o
        problema persistir, contacta-nos.
      </p>
      <button
        onClick={reset}
        className="rounded-full bg-gold px-8 py-3.5 text-sm font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
      >
        Tentar novamente
      </button>
    </div>
  )
}
