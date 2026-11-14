"use client"

import { useMemo, useState } from "react"
import { cn } from "@/lib/utils"
import { Analytics } from "@/lib/analytics"
import { sellerMessage } from "@/lib/seller-message"
import type { AnalysisResult } from "@/lib/types"

interface SellerMessageProps {
  result: AnalysisResult
  className?: string
}

/** The questions to ask the seller before going to see the car, ready to copy or send. */
export function SellerMessage({ result, className }: SellerMessageProps) {
  const initial = useMemo(() => sellerMessage(result), [result])
  const [text, setText] = useState(initial)
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard blocked: the text is still selectable */
    }
    Analytics.sellerMessageCopied(result.analysis_id, "copy")
  }

  const whatsapp = () => {
    Analytics.sellerMessageCopied(result.analysis_id, "whatsapp")
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank")
  }

  return (
    <div className={cn("rounded-xl border border-border bg-card p-5 md:p-6", className)}>
      <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-gold">Antes de ir ver o carro</p>
      <p className="mt-2 font-display text-[18px] font-bold text-foreground">Mensagem para o vendedor</p>
      <p className="mt-1 text-[13px] font-light leading-relaxed text-muted-foreground">
        As perguntas a fazer antes de marcar a visita, a partir desta análise. Podes editar antes de enviar.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={Math.min(16, text.split("\n").length + 1)}
        className={cn(
          "mt-4 w-full resize-y rounded-[10px] border border-border bg-background px-4 py-3",
          "text-[13px] font-light leading-relaxed text-foreground outline-none",
          "transition-colors focus:border-gold focus:ring-1 focus:ring-gold/20"
        )}
      />
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          onClick={copy}
          className="rounded-full bg-gold px-5 py-2 text-[13px] font-medium text-background transition-opacity hover:opacity-90"
        >
          {copied ? "Copiada" : "Copiar mensagem"}
        </button>
        <button
          onClick={whatsapp}
          className="rounded-full border border-border px-5 py-2 text-[13px] text-foreground transition-colors hover:border-gold"
        >
          Enviar por WhatsApp
        </button>
      </div>
    </div>
  )
}
