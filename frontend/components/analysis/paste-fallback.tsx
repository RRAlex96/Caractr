"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

interface PasteFallbackProps {
  /** "fetch_failed": we could not read the page; "paste_incomplete": the pasted text had no price. */
  reason: "fetch_failed" | "paste_incomplete"
  message: string
  loading: boolean
  onSubmit: (text: string) => void
  className?: string
}

/**
 * When the listing page cannot be read (the site blocks us, the ad is behind
 * a login), the buyer copies the page and pastes it here. The analysis then
 * runs on that text, so it never depends on our server being let in.
 */
export function PasteFallback({ reason, message, loading, onSubmit, className }: PasteFallbackProps) {
  const [text, setText] = useState("")
  const ready = text.trim().length >= 40

  return (
    <div className={cn("rounded-xl border border-gold/30 bg-gold/[0.05] p-5 md:p-6", className)}>
      <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-gold">
        {reason === "fetch_failed" ? "Não conseguimos abrir o anúncio" : "Falta o preço"}
      </p>
      <p className="text-[14px] leading-relaxed text-foreground">
        {reason === "fetch_failed"
          ? "O site não nos deixou ler esta página. Não faz mal: copia-a tu e analisamos na mesma."
          : message}
      </p>
      <ol className="mt-3 list-decimal space-y-1 pl-5 text-[13px] font-light leading-relaxed text-muted-foreground">
        <li>Abre o anúncio no browser.</li>
        <li>
          Seleciona tudo e copia: <span className="font-mono text-[12px]">Ctrl+A</span> e{" "}
          <span className="font-mono text-[12px]">Ctrl+C</span> (no telemóvel: toca sem largar, &quot;Selecionar
          tudo&quot;, &quot;Copiar&quot;).
        </li>
        <li>Cola aqui em baixo.</li>
      </ol>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
        rows={6}
        maxLength={20000}
        placeholder="Cola aqui o texto do anúncio: título, preço, ano, quilómetros, combustível..."
        className={cn(
          "mt-4 w-full resize-y rounded-[10px] border border-border bg-card px-4 py-3",
          "text-[13px] font-light text-foreground outline-none placeholder:text-muted-foreground/40",
          "transition-colors focus:border-gold focus:ring-1 focus:ring-gold/20 disabled:opacity-50"
        )}
      />
      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-[11px] text-muted-foreground/60">Só usamos o texto para analisar este anúncio.</p>
        <button
          onClick={() => onSubmit(text)}
          disabled={loading || !ready}
          className={cn(
            "h-10 shrink-0 rounded-full px-6 text-[13px] font-semibold transition-all disabled:cursor-not-allowed",
            loading ? "border border-gold text-gold" : "bg-gold text-background hover:bg-gold-dark",
            !ready && !loading && "opacity-35"
          )}
        >
          {loading ? "A analisar..." : "Analisar o texto"}
        </button>
      </div>
    </div>
  )
}
