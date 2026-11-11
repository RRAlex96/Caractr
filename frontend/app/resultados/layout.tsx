import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "A tua shortlist",
  description:
    "As melhores recomendações para o teu perfil — com fiabilidade, preço de mercado e tradeoffs honestos.",
}

export default function ResultadosLayout({ children }: { children: React.ReactNode }) {
  return children
}
