import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Exemplos de análise de anúncios",
  description:
    "Vê como o Caractr analisa anúncios reais de carros usados: preço face ao mercado, motor, sinais de alerta e margem de negociação.",
  alternates: { canonical: "/exemplos" },
}

export default function ExemplosLayout({ children }: { children: React.ReactNode }) {
  return children
}
