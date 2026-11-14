import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import {
  MODELS, SNAPSHOT, consumptionLabel, dec, depreciation, eur, fuelLabel, getModel, monthYear, num,
  priceSpan, studyLabel, yearsLabel, type ModelPage,
} from "@/lib/models"

const SITE_URL = "https://caractr.pt"

interface PageProps {
  params: Promise<{ slug: string }>
}

export const dynamicParams = false

export function generateStaticParams() {
  return MODELS.map((m) => ({ slug: m.slug }))
}

function name(m: ModelPage) {
  return `${m.brand} ${m.model}`
}

function description(m: ModelPage): string {
  const span = priceSpan(m)
  const parts = [`${name(m)} usado em Portugal`]
  if (span) {
    parts.push(
      span.from.year === span.to.year
        ? `: um de ${span.to.year} custa tipicamente ${eur(span.to.p50)}`
        : `: de ${eur(span.from.p50)} (${span.from.year}) a ${eur(span.to.p50)} (${span.to.year})`,
    )
  }
  parts.push(". Preço real por ano, motores, consumos, gerações e fiabilidade, com fontes.")
  return parts.join("")
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params
  const m = getModel(slug)
  if (!m) return { title: "Modelo não encontrado", robots: { index: false, follow: true } }
  const title = `${name(m)} usado: preço por ano, motores e fiabilidade`
  return {
    title,
    description: description(m),
    alternates: { canonical: `/carros/${m.slug}` },
    robots: m.indexable ? undefined : { index: false, follow: true },
    openGraph: { title, description: description(m), url: `${SITE_URL}/carros/${m.slug}`, type: "article" },
  }
}

// ── small building blocks ─────────────────────────────────────────────────

function Section({ id, title, children }: { id?: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="mt-14">
      <h2 className="mb-4 font-display text-[22px] font-bold tracking-tight text-foreground">{title}</h2>
      {children}
    </section>
  )
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="mt-3 text-[12px] font-light leading-relaxed text-muted-foreground/70">{children}</p>
}

function Figure({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-[17px] text-foreground">{value}</p>
      {hint && <p className="mt-0.5 text-[11px] text-muted-foreground/70">{hint}</p>}
    </div>
  )
}

function Cta({ m }: { m: ModelPage }) {
  return (
    <div className="mt-14 rounded-lg border border-gold/30 bg-gold/[0.05] p-6">
      <p className="font-display text-[19px] font-bold text-foreground">
        Encontraste um {name(m)} à venda?
      </p>
      <p className="mt-1 text-[14px] font-light leading-relaxed text-muted-foreground">
        Cola o link do anúncio. Dizemos-te se o preço é justo para aquele ano, motor e quilometragem,
        o que verificar antes de comprar e quanto oferecer.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          href="/analisar"
          className="rounded-full bg-gold px-5 py-2.5 text-[13px] font-medium text-background transition-opacity hover:opacity-90"
        >
          Analisar um anúncio
        </Link>
        <Link
          href="/escolher"
          className="rounded-full border border-border px-5 py-2.5 text-[13px] text-foreground transition-colors hover:border-gold"
        >
          Ainda não sei que carro quero
        </Link>
      </div>
    </div>
  )
}

// ── page ──────────────────────────────────────────────────────────────────

export default async function ModelPageView({ params }: PageProps) {
  const { slug } = await params
  const m = getModel(slug)
  if (!m) notFound()

  const span = priceSpan(m)
  const dep = depreciation(m)
  const newest = m.prices[0]
  const commonEngine = m.engines.find((e) => (e.listings ?? 0) > 0) ?? m.engines[0]
  const related = m.related.map(getModel).filter((x): x is ModelPage => Boolean(x))
  const when = monthYear(SNAPSHOT?.collected_on)
  const mainGens = m.generations.filter((g) => !g.fuel_only)

  const faq: { q: string; a: string }[] = []
  if (span) {
    faq.push({
      q: `Quanto custa um ${name(m)} usado?`,
      a: `Nos anúncios em Portugal (${when}), um ${name(m)} de ${newest.year} custa tipicamente ${eur(newest.p50)}`
        + (span.from.year !== span.to.year
          ? ` e um de ${span.from.year} cerca de ${eur(span.from.p50)}.`
          : ".")
        + " O preço justo de um carro concreto depende do motor, da quilometragem e do vendedor.",
    })
  }
  if (commonEngine) {
    faq.push({
      q: `Qual é o motor mais comum no ${name(m)} usado?`,
      a: `O ${commonEngine.code} (${fuelLabel(commonEngine).toLowerCase()}${commonEngine.hp ? `, ${commonEngine.hp} cv` : ""})`
        + (commonEngine.listings ? `, presente em ${commonEngine.listings} dos anúncios analisados.` : "."),
    })
  }
  if (dep != null) {
    faq.push({
      q: `Quanto desvaloriza um ${name(m)}?`,
      a: `Cerca de ${dec(dep * 100)}% por ano de idade, medido nos preços dos anúncios desta geração.`,
    })
  }

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Carros usados", item: `${SITE_URL}/carros` },
          { "@type": "ListItem", position: 2, name: name(m), item: `${SITE_URL}/carros/${m.slug}` },
        ],
      },
      ...(faq.length
        ? [{
            "@type": "FAQPage",
            mainEntity: faq.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
          }]
        : []),
    ],
  }

  return (
    <div className="min-h-screen">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <main className="mx-auto max-w-[760px] px-[clamp(20px,5vw,32px)] pb-24 pt-24 md:pt-28">
        <nav className="font-mono text-[10px] uppercase tracking-[1.5px] text-muted-foreground">
          <Link href="/carros" className="transition-colors hover:text-gold">Carros usados</Link>
          <span className="mx-2 text-muted-foreground/40">/</span>
          <span>{m.brand}</span>
        </nav>

        <div className="mb-2 mt-4 h-0.5 w-10 rounded-full bg-gold" />
        <h1 className="font-display text-[clamp(30px,6vw,48px)] font-extrabold leading-[0.95] tracking-tight text-foreground">
          {name(m)} usado
        </h1>
        <p className="mt-3 max-w-[600px] text-[15px] font-light leading-relaxed text-muted-foreground">
          Preço real por ano de matrícula, motores, gerações e fiabilidade
          {SNAPSHOT ? `, a partir de ${num(SNAPSHOT.listings)} anúncios lidos em ${when}` : ""}.
        </p>

        <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4">
          <Figure
            label="Preço típico"
            value={span ? (span.from.year === span.to.year ? eur(span.to.p50)
              : `${num(span.from.p50)}–${eur(span.to.p50)}`) : "—"}
            hint={span ? (span.from.year === span.to.year ? `um de ${span.to.year}`
              : `de ${span.from.year} a ${span.to.year}`) : "sem anúncios suficientes"}
          />
          <Figure label="À venda" value={m.on_sale ? num(m.on_sale) : "—"} hint="anúncios em Portugal" />
          <Figure
            label="Fiabilidade da marca"
            value={m.brand_reliability ? `${dec(m.brand_reliability.score)}/10` : "—"}
            hint={m.brand_reliability?.studies
              ? `${m.brand_reliability.studies} ${m.brand_reliability.studies === 1 ? "estudo publicado" : "estudos publicados"}`
              : "estimativa"}
          />
          <Figure
            label="Desvalorização"
            value={dep != null ? `${dec(dep * 100)}%/ano` : "—"}
            hint={dep != null ? "por ano de idade" : "dados insuficientes"}
          />
        </div>

        {m.character?.text && (
          <p className="mt-8 text-[15px] leading-relaxed text-foreground/90">{m.character.text}</p>
        )}

        {m.known_issues.length > 0 && (
          <Section id="problemas" title="Problemas conhecidos">
            <div className="space-y-4">
              {m.known_issues.map((i) => (
                <div key={i.id} className="rounded-lg border border-danger/30 bg-danger/[0.04] p-4">
                  <p className="font-mono text-[10px] uppercase tracking-[1.5px] text-danger">
                    {i.engine} · {i.affected_years}
                  </p>
                  <p className="mt-1 text-[15px] font-medium text-foreground">{i.problem}</p>
                  <p className="mt-2 text-[14px] font-light leading-relaxed text-muted-foreground">{i.description}</p>
                  <p className="mt-2 text-[14px] leading-relaxed text-foreground/90"><strong>O que verificar:</strong> {i.check}</p>
                  {i.fix_cost_estimate && (
                    <p className="mt-1 font-mono text-[12px] text-muted-foreground">Custo estimado: {i.fix_cost_estimate}</p>
                  )}
                  <Link href={`/motores/${i.page}`} className="mt-2 inline-block text-[13px] text-gold underline-offset-2 hover:underline">
                    Tudo sobre este problema →
                  </Link>
                  <p className="mt-2 text-[12px] text-muted-foreground/70">
                    Fontes:{" "}
                    {i.sources.map((s, k) => (
                      <span key={s.url}>
                        {k > 0 && " · "}
                        <a href={s.url} rel="nofollow noopener" target="_blank" className="underline hover:text-gold">{s.label}</a>
                      </span>
                    ))}
                  </p>
                </div>
              ))}
            </div>
          </Section>
        )}

        {m.prices.length > 0 && (
          <Section id="precos" title={`Quanto custa um ${name(m)} usado`}>
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full whitespace-nowrap text-left text-[13px] sm:text-[14px]">
                <thead className="bg-card font-mono text-[10px] uppercase tracking-[1.2px] text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Ano</th>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Preço típico</th>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Maioria entre</th>
                    <th className="hidden px-3 py-2.5 text-right font-normal sm:table-cell sm:px-4">Anúncios</th>
                  </tr>
                </thead>
                <tbody>
                  {m.prices.map((p) => (
                    <tr key={p.year} className="border-t border-border/60">
                      <td className="px-3 py-2 sm:px-4 font-mono">{p.year}</td>
                      <td className="px-3 py-2 sm:px-4 font-mono text-foreground">{eur(p.p50)}</td>
                      <td className="px-3 py-2 sm:px-4 font-mono text-muted-foreground">{eur(p.p10)} – {eur(p.p90)}</td>
                      <td className="hidden px-3 py-2 text-right font-mono text-muted-foreground sm:table-cell sm:px-4">{p.n}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Note>
              Mediana dos preços pedidos em anúncios em Portugal ({when}), por ano de matrícula; o intervalo
              deixa de fora os 10% mais baratos e os 10% mais caros. Versões desportivas não entram na mediana.
              São preços pedidos, não de venda: um carro concreto vale mais ou menos consoante o motor, os
              quilómetros e o vendedor.
            </Note>
          </Section>
        )}

        {m.engines.length > 0 && (
          <Section id="motores" title="Motores">
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full whitespace-nowrap text-left text-[13px] sm:text-[14px]">
                <thead className="bg-card font-mono text-[10px] uppercase tracking-[1.2px] text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Motor</th>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Combustível</th>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Potência</th>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Consumo</th>
                    <th className="px-3 py-2.5 font-normal sm:px-4">Anos</th>
                  </tr>
                </thead>
                <tbody>
                  {m.engines.map((e) => (
                    <tr key={e.code} className="border-t border-border/60">
                      <td className="px-3 py-2 sm:px-4 text-foreground">{e.code}</td>
                      <td className="px-3 py-2 sm:px-4 text-muted-foreground">{fuelLabel(e)}</td>
                      <td className="px-3 py-2 sm:px-4 font-mono text-muted-foreground">{e.hp ? `${e.hp} cv` : "—"}</td>
                      <td className="px-3 py-2 sm:px-4 font-mono text-muted-foreground">{consumptionLabel(e)}</td>
                      <td className="px-3 py-2 sm:px-4 font-mono text-muted-foreground">{yearsLabel(e.year_from, e.year_to)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Note>
              Consumos homologados (o real costuma ser mais alto); nos híbridos plug-in, com a bateria carregada.
              Os anos são os de matrícula dos carros com esse motor à venda.
            </Note>
          </Section>
        )}

        {mainGens.length > 0 && (
          <Section id="geracoes" title="Gerações">
            <ul className="divide-y divide-border/60 rounded-lg border border-border">
              {m.generations.map((g) => (
                <li key={g.name} className="flex items-baseline justify-between gap-4 px-4 py-2.5 text-[14px]">
                  <span className="text-foreground">
                    {g.name}
                    {g.fuel_only === "eletrico" && <span className="ml-2 text-[12px] text-muted-foreground">(elétrico)</span>}
                  </span>
                  <span className="font-mono text-muted-foreground">
                    {g.to ? `${g.from}–${g.to}` : `desde ${g.from}`}
                    {g.source && (
                      <a href={g.source} rel="nofollow noopener" target="_blank" className="ml-3 text-[11px] underline hover:text-gold">
                        fonte
                      </a>
                    )}
                  </span>
                </li>
              ))}
            </ul>
            <Note>Anos de venda na Europa. Um carro matriculado no ano da mudança pode ser de qualquer das duas.</Note>
          </Section>
        )}

        {m.brand_reliability && (
          <Section id="fiabilidade" title="Fiabilidade">
            <p className="text-[15px] font-light leading-relaxed text-muted-foreground">
              {m.brand_reliability.studies > 0 ? (
                <>
                  A {m.brand} tem {dec(m.brand_reliability.score)}/10 na nossa escala, a partir da
                  posição da marca em {m.brand_reliability.studies} estudo{m.brand_reliability.studies > 1 ? "s" : ""} publicado
                  {m.brand_reliability.studies > 1 ? "s" : ""}: {m.brand_reliability.sources.map(studyLabel).join(", ")}.
                </>
              ) : (
                <>Não encontrámos estudos publicados sobre a {m.brand}; a nota de {dec(m.brand_reliability.score)}/10 é uma estimativa.</>
              )}
            </p>
            <Note>
              É uma medida da marca, não deste modelo nem de um motor em particular. Problemas conhecidos de motores
              concretos só aparecem nesta página depois de verificados e aprovados por uma pessoa.
            </Note>
          </Section>
        )}

        <Cta m={m} />

        {faq.length > 0 && (
          <Section id="perguntas" title="Perguntas frequentes">
            <dl className="space-y-5">
              {faq.map((f) => (
                <div key={f.q}>
                  <dt className="text-[15px] font-medium text-foreground">{f.q}</dt>
                  <dd className="mt-1 text-[14px] font-light leading-relaxed text-muted-foreground">{f.a}</dd>
                </div>
              ))}
            </dl>
          </Section>
        )}

        {related.length > 0 && (
          <Section title="Modelos semelhantes">
            <div className="flex flex-wrap gap-2">
              {related.map((r) => (
                <Link
                  key={r.slug}
                  href={`/carros/${r.slug}`}
                  className="rounded-full border border-border px-3.5 py-2 text-[13px] text-muted-foreground transition-colors hover:border-gold hover:text-foreground"
                >
                  {name(r)}
                </Link>
              ))}
            </div>
          </Section>
        )}
      </main>
    </div>
  )
}
