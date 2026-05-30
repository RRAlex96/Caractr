import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "A tua shortlist",
  description:
    "As melhores recomendacoes para o teu perfil — com fiabilidade, preco de mercado e tradeoffs honestos.",
}

export default function ResultadosLayout({ children }: { children: React.ReactNode }) {
  return children
}
