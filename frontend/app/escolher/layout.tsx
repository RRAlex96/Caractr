import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Descobrir o teu carro",
  description:
    "Responde a 5 perguntas sobre o teu estilo de vida e descobre os modelos que melhor se adequam a ti.",
}

export default function EscolherLayout({ children }: { children: React.ReactNode }) {
  return children
}
