import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Analisar anuncio",
  description:
    "Cola o link de qualquer anuncio de carro — dizemos-te se o preco e justo, o que preocupa e o que valoriza.",
}

export default function AnalisarLayout({ children }: { children: React.ReactNode }) {
  return children
}
