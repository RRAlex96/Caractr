import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Descobrir o teu carro",
  description:
    "Responde a 6 perguntas rápidas sobre o teu dia a dia e descobre os modelos que melhor se adequam a ti.",
  alternates: { canonical: "/escolher" },
}

export default function EscolherLayout({ children }: { children: React.ReactNode }) {
  return children
}
