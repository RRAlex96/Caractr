import { ImageResponse } from "next/og"

// The preview card a shared analysis shows in WhatsApp, Messenger or iMessage:
// the car, the verdict and where its price stands. Without the verdict in the
// card, a shared link looks like any other link and is not opened.

export const runtime = "edge"
export const alt = "Análise de anúncio — Caractr"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const TIER: Record<string, { label: string; color: string }> = {
  forte: { label: "NEGÓCIO FORTE", color: "#22C55E" },
  razoavel: { label: "NEGÓCIO RAZOÁVEL", color: "#C8A882" },
  cuidado: { label: "COM RESERVAS", color: "#F59E0B" },
  evitar: { label: "A EVITAR", color: "#EF4444" },
}

function group(n: number): string {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ")
}

async function getAnalysis(id: string) {
  try {
    // The API sleeps on the free tier: a card without the verdict beats no card.
    const res = await fetch(`${API}/api/listings/analyses/${Number(id)}`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(6000),
    })
    if (!res.ok) return null
    const data = await res.json()
    return data?.error ? null : data
  } catch {
    return null
  }
}

export default async function Image({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const data = await getAnalysis(id)
  const l = data?.listing ?? {}
  const car = [l.brand_name, l.model_name, l.year].filter(Boolean).join(" ") || "Análise de anúncio"
  const tier = TIER[data?.deal?.tier as string]
  const pct = data?.deal?.price_delta_pct
  const below = (data?.deal?.price_delta ?? 0) >= 0
  const facts = [l.km ? `${group(l.km)} km` : null, l.price ? `${group(l.price)} €` : null].filter(Boolean).join("  ·  ")

  return new ImageResponse(
    (
      <div
        style={{
          width: "1200px", height: "630px", background: "#0D0C0A", display: "flex", flexDirection: "column",
          justifyContent: "space-between", padding: "72px 80px", fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ width: "48px", height: "3px", background: "#C8A882", borderRadius: "2px", marginBottom: "28px" }} />
          <div style={{ fontSize: "20px", color: "#C8A882", letterSpacing: "0.15em" }}>ANÁLISE DE ANÚNCIO</div>
          <div style={{ fontSize: "68px", fontWeight: 800, color: "#F2EFE9", lineHeight: 1.0, marginTop: "18px" }}>
            {car}
          </div>
          {facts && <div style={{ fontSize: "28px", color: "#9A9590", marginTop: "18px" }}>{facts}</div>}
        </div>

        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {tier ? (
              <div style={{ display: "flex", alignItems: "center" }}>
                <div style={{ width: "22px", height: "22px", borderRadius: "11px", background: tier.color, marginRight: "18px" }} />
                <div style={{ fontSize: "44px", fontWeight: 800, color: tier.color, letterSpacing: "0.04em" }}>{tier.label}</div>
              </div>
            ) : (
              <div style={{ fontSize: "36px", color: "#F2EFE9" }}>O preço é justo? O que verificar?</div>
            )}
            {pct != null && pct !== 0 && (
              <div style={{ fontSize: "30px", color: "#F2EFE9", marginTop: "14px" }}>
                {`${Math.abs(pct)}% ${below ? "abaixo" : "acima"} do preço de mercado`}
              </div>
            )}
          </div>
          <div style={{ fontSize: "22px", color: "#9A9590", letterSpacing: "0.08em" }}>caractr.pt</div>
        </div>
      </div>
    ),
    size,
  )
}
