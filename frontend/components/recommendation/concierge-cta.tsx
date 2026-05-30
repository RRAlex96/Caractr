import Link from "next/link"
import type { Recommendation } from "@/lib/types"

interface ConciergeCTAProps {
  sessionId: string
  interestedRecs: Recommendation[]
  allDismissed: boolean
}

export function ConciergeCTA({
  sessionId,
  interestedRecs,
  allDismissed,
}: ConciergeCTAProps) {
  return (
    <section className="mt-[clamp(32px,4vw,56px)] flex flex-col items-center border-t border-border px-[clamp(24px,5vw,80px)] py-[clamp(48px,6vw,72px)] text-center">
      <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />

      {interestedRecs.length > 0 ? (
        <>
          <h2 className="mb-3 font-display text-[clamp(24px,3.5vw,40px)] font-extrabold tracking-tight">
            Otimo.{" "}
            <span className="text-gold-dark">
              {interestedRecs.length === 1
                ? `Quer que encontremos um ${interestedRecs[0].full_name} para ti?`
                : "Quer ajuda a encontrar uma destas opcoes?"}
            </span>
          </h2>
          <p className="mb-2 max-w-[480px] text-[15px] font-light leading-relaxed text-muted-foreground">
            Durante o lancamento, a pesquisa e gratuita para um numero limitado de utilizadores.
            Deixa o teu contacto e tratamos do resto.
          </p>
          {interestedRecs.length > 1 && (
            <div className="mb-4 flex flex-wrap justify-center gap-2">
              {interestedRecs.map((r) => (
                <span
                  key={r.model_id}
                  className="rounded-full border border-gold px-3 py-1 font-mono text-[10px] text-gold/80"
                >
                  {r.full_name}
                </span>
              ))}
            </div>
          )}
          <Link
            href={`/concierge?session=${sessionId}&models=${encodeURIComponent(interestedRecs.map((r) => r.full_name).join(","))}&model_ids=${interestedRecs.map((r) => r.model_id).join(",")}&model=${encodeURIComponent(interestedRecs[0]?.full_name || "")}&model_id=${interestedRecs[0]?.model_id || ""}`}
            className="mt-3 rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
          >
            Sim, quero ajuda
          </Link>
        </>
      ) : allDismissed ? (
        <>
          <h2 className="mb-3 font-display text-[clamp(24px,3.5vw,40px)] font-extrabold tracking-tight">
            Nenhuma sugestao acertou.
          </h2>
          <p className="mb-7 max-w-[480px] text-[15px] font-light leading-relaxed text-muted-foreground">
            O teu feedback ja foi registado — vamos usar para melhorar.
            Podes refinar o teu perfil e tentar de novo, ou pedir-nos que facamos a pesquisa por ti.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/escolher"
              className="rounded-full border border-border px-6 py-3 text-[13px] font-medium text-muted-foreground transition-colors hover:border-gold/40 hover:text-gold"
            >
              Refinar o meu perfil
            </Link>
            <Link
              href={`/concierge?session=${sessionId}`}
              className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              Peco que facam por mim
            </Link>
          </div>
        </>
      ) : (
        <>
          <h2 className="mb-3 font-display text-[clamp(24px,3.5vw,40px)] font-extrabold tracking-tight">
            Queres uma shortlist de anuncios reais?
          </h2>
          <p className="mb-7 max-w-[480px] text-[15px] font-light leading-relaxed text-muted-foreground">
            Pesquisamos o mercado com base no teu perfil e enviamos-te os melhores anuncios encontrados.
            Gratuito durante o lancamento.
          </p>
          <Link
            href={`/concierge?session=${sessionId}`}
            className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
          >
            reservar o meu lugar
          </Link>
        </>
      )}
    </section>
  )
}
