import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { AnalysisView } from "./analysis-view"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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
      title: "Analise nao encontrada | Caractr",
    }
  }

  const brand = data.listing?.brand_name || ""
  const model = data.listing?.model_name || ""
  const year = data.listing?.year || ""
  const tier = (data.deal?.tier || "").toUpperCase()
  const price = data.listing?.price
    ? `${data.listing.price.toLocaleString("pt-PT")} EUR`
    : ""

  const title = `${brand} ${model} ${year} — Negocio ${tier} | Caractr`
  const description = data.analysis?.verdict_reason
    ? data.analysis.verdict_reason.slice(0, 160)
    : `Analise detalhada de ${brand} ${model} ${year}. ${price ? `Preco: ${price}.` : ""} Verifica se e um bom negocio com o Caractr.`

  return {
    title,
    description,
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
          Analise nao encontrada
        </h1>
        <p className="mb-8 max-w-[400px] text-center text-[15px] font-light text-muted-foreground">
          Esta analise pode ter expirado ou o link pode estar incorreto. Experimenta analisar um anuncio novo.
        </p>
        <a
          href="/analisar"
          className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
        >
          Analisar um anuncio
        </a>
      </main>
    )
  }

  return <AnalysisView data={data} analysisId={numId} />
}
