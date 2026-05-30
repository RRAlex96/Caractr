import Link from "next/link"
import { cn } from "@/lib/utils"

interface WizardBridgeProps {
  /** URL of the current listing (for concierge deep-link) */
  listingUrl?: string
  /** Deal tier for concierge context */
  tier?: string
  className?: string
}

export function WizardBridge({ listingUrl, tier, className }: WizardBridgeProps) {
  const conciergeHref = listingUrl
    ? `/concierge?listing_url=${encodeURIComponent(listingUrl)}${tier ? `&listing_verdict=${tier}` : ""}`
    : "/concierge"

  return (
    <div
      className={cn(
        "rounded-2xl bg-foreground p-8 md:p-9",
        className
      )}
    >
      <div className="mb-5 h-0.5 w-8 rounded-full bg-gold" />
      <h2 className="font-display text-[clamp(22px,3.5vw,32px)] font-extrabold leading-none tracking-tight text-background">
        QUERES A SHORTLIST CERTA?
      </h2>
      <p className="mt-3 max-w-[400px] text-sm font-light leading-relaxed text-background/60">
        Responde a algumas perguntas sobre o teu estilo de vida. Encontramos os
        modelos que se adequam a ti — com analise detalhada de cada opcao.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          href="/escolher"
          className="rounded-full bg-background px-6 py-3 text-[13px] font-medium text-foreground transition-colors hover:bg-background/90"
        >
          descobrir o meu carro
        </Link>
        <Link
          href={conciergeHref}
          className="rounded-full border border-white/20 px-6 py-3 text-[13px] font-medium text-white/70 transition-colors hover:border-white/40 hover:text-white"
        >
          quero ajuda pessoal
        </Link>
      </div>
    </div>
  )
}
