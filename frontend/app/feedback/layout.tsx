import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Feedback",
  description: "Ajuda-nos a melhorar o Caractr em 30 segundos.",
}

export default function FeedbackLayout({ children }: { children: React.ReactNode }) {
  return children
}
