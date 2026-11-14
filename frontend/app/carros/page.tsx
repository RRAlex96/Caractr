import type { Metadata } from "next"
import Link from "next/link"
import { SNAPSHOT, eur, modelsByBrand, monthYear, num } from "@/lib/models"

export const metadata: Metadata = {
  title: "Carros usados: preço real por ano, motores e fiabilidade",
  description:
    "Quanto custa cada modelo usado em Portugal, ano a ano, a partir de dezenas de milhares de anúncios. Motores, consumos, gerações e fiabilidade, com fontes.",
  alternates: { canonical: "/carros" },
}

export default function CarrosIndex() {
  const brands = modelsByBrand()
  const total = brands.reduce((n, [, ms]) => n + ms.length, 0)
  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-[900px] px-[clamp(20px,5vw,32px)] pb-24 pt-24 md:pt-28">
        <div className="mb-2 h-0.5 w-10 rounded-full bg-gold" />
        <p className="mb-1 font-mono text-[10px] uppercase tracking-[2px] text-gold">Guia de usados</p>
        <h1 className="font-display text-[clamp(30px,6vw,48px)] font-extrabold leading-[0.95] tracking-tight text-foreground">
          Carros usados em Portugal
        </h1>
        <p className="mt-3 max-w-[620px] text-[15px] font-light leading-relaxed text-muted-foreground">
          {total} modelos, com o preço típico por ano de matrícula
          {SNAPSHOT ? ` medido em ${num(SNAPSHOT.listings)} anúncios (${monthYear(SNAPSHOT.collected_on)})` : ""},
          os motores à venda e a fiabilidade da marca.
        </p>

        <div className="mt-12 space-y-10">
          {brands.map(([brand, models]) => (
            <section key={brand}>
              <h2 className="mb-3 font-display text-[18px] font-bold text-foreground">{brand}</h2>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
                {models.map((m) => (
                  <Link
                    key={m.slug}
                    href={`/carros/${m.slug}`}
                    className="flex items-baseline justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:border-gold/50"
                  >
                    <span className="text-[14px] text-foreground">{m.model}</span>
                    {m.prices.length > 0 && (
                      <span className="font-mono text-[11px] text-muted-foreground">
                        desde {eur(Math.min(...m.prices.map((p) => p.p50)))}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>
    </div>
  )
}
