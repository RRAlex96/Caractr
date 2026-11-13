import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { AnalysisView } from "@/components/analysis/analysis-view"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const TIER_TITLES: Record<string, string> = {
  forte: "negócio forte",
  razoavel: "negócio razoável",
  cuidado: "negócio com reservas",
  evitar: "negócio a evitar",
}

// A shared analysis is about someone else's listing and goes stale when the
// car sells: link previews still work, but it stays out of search results.
const NOINDEX = { index: false, follow: true }

interface PageProps {
  params: Promise<{ id: string }>
}

async function getAnalysis(id: number) {
  try {
    const res = await fetch(`${API}/api/listings/analyses/${id}`, {
      next: { revalidate: 3600 },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params
  const data = await getAnalysis(Number(id))

  if (!data || data.error) {
    return {
      title: "Análise não encontrada",
      robots: NOINDEX,
    }
  }

  const brand = data.listing?.brand_name || ""
  const model = data.listing?.model_name || ""
  const year = data.listing?.year || ""
  const verdict = TIER_TITLES[data.deal?.tier as string] || "análise do anúncio"
  const price = data.listing?.price
    ? `${data.listing.price.toLocaleString("pt-PT")} EUR`
    : ""

  // The root layout appends " — Caractr" to the page title.
  const title = `${[brand, model, year].filter(Boolean).join(" ")}: ${verdict}`
  const description = data.analysis?.verdict_reason
    ? data.analysis.verdict_reason.slice(0, 160)
    : `Análise detalhada de ${brand} ${model} ${year}. ${price ? `Preço: ${price}.` : ""} Verifica se é um bom negócio com o Caractr.`

  return {
    title,
    description,
    alternates: { canonical: `/analise/${id}` },
    robots: NOINDEX,
    openGraph: {
      title,
      description,
      type: "article",
      siteName: "Caractr",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  }
}

export default async function AnalisePage({ params }: PageProps) {
  const { id } = await params
  const numId = Number(id)

  if (isNaN(numId)) notFound()

  const data = await getAnalysis(numId)

  if (!data || data.error) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center px-6">
        <div className="mb-6 h-0.5 w-12 rounded-full bg-gold" />
        <h1 className="mb-3 font-display text-[clamp(28px,5vw,48px)] font-extrabold tracking-tight text-foreground">
          Análise não encontrada
        </h1>
        <p className="mb-8 max-w-[400px] text-center text-[15px] font-light text-muted-foreground">
          Esta análise pode ter expirado ou o link pode estar incorreto. Experimenta analisar um anúncio novo.
        </p>
        <a
          href="/analisar"
          className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
        >
          Analisar um anúncio
        </a>
      </main>
    )
  }

  return <AnalysisView data={data} analysisId={numId} shared />
}
