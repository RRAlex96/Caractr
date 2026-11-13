import Link from "next/link"

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 pt-16 text-center">
      <div className="mb-6 h-0.5 w-12 rounded-full bg-gold" />
      <h1 className="mb-3 font-display text-[clamp(48px,10vw,96px)] font-extrabold leading-[0.85] tracking-tight text-foreground">
        404
      </h1>
      <p className="mb-8 max-w-[360px] text-[15px] font-light leading-relaxed text-muted-foreground">
        Esta página não existe ou foi movida. Volta ao início e tenta novamente.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link
          href="/"
          className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
        >
          Voltar ao início
        </Link>
        <Link
          href="/analisar"
          className="rounded-full border border-border px-6 py-3.5 text-[13px] font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
        >
          Analisar anúncio
        </Link>
      </div>
    </div>
  )
}
