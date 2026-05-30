import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Concierge",
  description:
    "Pesquisamos anuncios reais que se adequam ao teu perfil e enviamos-te uma shortlist curada.",
}

export default function ConciergeLayout({ children }: { children: React.ReactNode }) {
  return children
}
