import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ENGINE_PAGES, getEnginePage, type EnginePage } from "@/lib/models"

const SITE_URL = "https://caractr.pt"

interface PageProps {
  params: Promise<{ slug: string }>
}

export const dynamicParams = false

export function generateStaticParams() {
  // Next needs at least one path for a static dynamic route; with no approved
  // entry yet the placeholder 404s.
  return ENGINE_PAGES.length ? ENGINE_PAGES.map((e) => ({ slug: e.page })) : [{ slug: "_" }]
}

function heading(e: EnginePage) {
  return `${e.engine}: ${e.problem.charAt(0).toLowerCase()}${e.problem.slice(1)}`
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params
  const e = getEnginePage(slug)
  if (!e) return { title: "Página não encontrada", robots: { index: false, follow: true } }
  const title = `${e.engine}: problemas, anos afetados e o que verificar`
  const description = `${e.problem}. Afeta ${e.affected_years}. O que verificar antes de comprar, quanto custa e as fontes.`
  return {
    title,
    description,
    alternates: { canonical: `/motores/${e.page}` },
    openGraph: { title, description, url: `${SITE_URL}/motores/${e.page}`, type: "article" },
  }
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-12">
      <h2 className="mb-3 font-display text-[21px] font-bold tracking-tight text-foreground">{title}</h2>
      {children}
    </section>
  )
}

export default async function EnginePageView({ params }: PageProps) {
  const { slug } = await params
  const e = getEnginePage(slug)
  if (!e) notFound()
  const critical = e.severity === "critico"

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Carros usados", item: `${SITE_URL}/carros` },
          { "@type": "ListItem", position: 2, name: e.engine, item: `${SITE_URL}/motores/${e.page}` },
        ],
      },
      {
        "@type": "FAQPage",
        mainEntity: [
          { q: `Que anos do ${e.engine} são afetados?`, a: `${e.affected_years}. ${e.problem}.` },
          { q: "O que verificar antes de comprar?", a: e.check },
          ...(e.fix_cost_estimate ? [{ q: "Quanto custa?", a: e.fix_cost_estimate }] : []),
        ].map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
      },
    ],
  }

  return (
    <div className="min-h-screen">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <main className="mx-auto max-w-[720px] px-[clamp(20px,5vw,32px)] pb-24 pt-24 md:pt-28">
        <nav className="font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground">
          <Link href="/carros" className="transition-colors hover:text-gold">Carros usados</Link>
          <span className="mx-2 text-muted-foreground/40">/</span>
          <span>{e.component === "caixa" ? "Caixas de velocidades" : "Motores"}</span>
        </nav>

        <div className="mb-2 mt-4 h-0.5 w-10 rounded-full bg-gold" />
        <p className={`font-mono text-[10px] uppercase tracking-[2px] ${critical ? "text-danger" : "text-warning"}`}>
          {critical ? "Problema grave conhecido" : "Ponto a verificar"} · {e.affected_years}
        </p>
        <h1 className="mt-2 font-display text-[clamp(28px,5.5vw,44px)] font-extrabold leading-[1.0] tracking-tight text-foreground">
          {heading(e)}
        </h1>
        {e.codes.length > 0 && (
          <p className="mt-3 font-mono text-[12px] text-muted-foreground">Códigos: {e.codes.join(", ")}</p>
        )}

        <p className="mt-8 text-[16px] leading-relaxed text-foreground/90">{e.description}</p>

        <Section title="O que verificar antes de comprar">
          <p className="text-[15px] leading-relaxed text-muted-foreground">{e.check}</p>
        </Section>

        {e.fix_cost_estimate && (
          <Section title="Quanto custa">
            <p className="font-mono text-[15px] text-foreground">{e.fix_cost_estimate}</p>
            <p className="mt-2 text-[12px] font-light text-muted-foreground/70">
              Estimativa para Portugal, em oficina independente, peças e mão de obra. Um orçamento concreto pode variar.
            </p>
          </Section>
        )}

        {e.mitigation && (
          <Section title="Garantias e peças revistas">
            <p className="text-[15px] leading-relaxed text-muted-foreground">{e.mitigation}</p>
          </Section>
        )}

        {(e.affected_models.length > 0 || e.models_text.length > 0) && (
          <Section title="Modelos com este motor">
            {e.affected_models.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {e.affected_models.map((m) => (
                  <Link
                    key={m.slug}
                    href={`/carros/${m.slug}`}
                    className="rounded-full border border-border px-3.5 py-2 text-[13px] text-muted-foreground transition-colors hover:border-gold hover:text-foreground"
                  >
                    {m.brand} {m.model}
                  </Link>
                ))}
              </div>
            ) : (
              <ul className="list-disc pl-5 text-[14px] text-muted-foreground">
                {e.models_text.map((t) => <li key={t}>{t}</li>)}
              </ul>
            )}
            <p className="mt-3 text-[12px] font-light text-muted-foreground/70">
              Só os carros com este motor e produzidos em {e.affected_years} são abrangidos; o mesmo modelo com outro
              motor, ou de outros anos, não.
            </p>
          </Section>
        )}

        <Section title="Fontes">
          <ul className="space-y-1.5 text-[14px]">
            {e.sources.map((s) => (
              <li key={s.url}>
                <a href={s.url} rel="nofollow noopener" target="_blank" className="text-muted-foreground underline hover:text-gold">
                  {s.label}
                </a>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[12px] font-light text-muted-foreground/70">
            Cada entrada foi verificada contra estas fontes antes de ser publicada.
          </p>
        </Section>

        <div className="mt-14 rounded-lg border border-gold/30 bg-gold/[0.05] p-6">
          <p className="font-display text-[19px] font-bold text-foreground">Estás a ver um carro com este motor?</p>
          <p className="mt-1 text-[14px] font-light leading-relaxed text-muted-foreground">
            Cola o link do anúncio. Dizemos-te se este problema se aplica àquele carro, se o preço é justo e quanto oferecer.
          </p>
          <Link
            href="/analisar"
            className="mt-4 inline-block rounded-full bg-gold px-5 py-2.5 text-[13px] font-medium text-background transition-opacity hover:opacity-90"
          >
            Analisar um anúncio
          </Link>
        </div>
      </main>
    </div>
  )
}
