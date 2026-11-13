import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Analisar anúncio",
  description:
    "Cola o link de qualquer anúncio de carro — dizemos-te se o preço é justo, o que preocupa e o que valoriza.",
  alternates: { canonical: "/analisar" },
}

export default function AnalisarLayout({ children }: { children: React.ReactNode }) {
  return children
}
