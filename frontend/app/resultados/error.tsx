"use client"

import { useEffect } from "react"
import Link from "next/link"

export default function ResultadosError({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  useEffect(() => {
    console.error("[Caractr/resultados]", error)
  }, [error])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 pt-16 text-center">
      <p className="mb-5 font-mono text-[11px] uppercase tracking-[2px] text-gold">
        ALGO CORREU MAL
      </p>
      <h2 className="mb-4 font-display text-[clamp(24px,4vw,40px)] font-extrabold tracking-tight text-foreground">
        ERRO NOS RESULTADOS
      </h2>
      <p className="mb-9 max-w-[360px] text-[15px] font-light leading-relaxed text-muted-foreground">
        Nao conseguimos carregar as tuas recomendacoes. O teu perfil esta
        guardado — tenta novamente.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <button
          onClick={reset}
          className="rounded-full bg-gold px-7 py-3.5 text-sm font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
        >
          Tentar novamente
        </button>
        <Link
          href="/escolher"
          className="rounded-full border border-border px-7 py-3.5 text-sm font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
        >
          Refazer perfil
        </Link>
      </div>
    </div>
  )
}
