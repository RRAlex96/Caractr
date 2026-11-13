import type { Metadata } from "next"
import "./globals.css"
import { cn } from "@/lib/utils"
import { Navbar } from "@/components/layout/navbar"
import { Footer } from "@/components/layout/footer"
import { TooltipProvider } from "@/components/ui/tooltip"
import { PageViewTracker } from "@/components/shared/page-view-tracker"

const SITE_URL = "https://caractr.pt"
const SITE_NAME = "Caractr"
const TITLE = "CARACTR — O motor de recomendação que te conhece a ti"
const DESCRIPTION =
  "Diz-nos o teu estilo de vida. Recomendamos os 5 modelos certos — com dados de fiabilidade, preço de mercado e análise de anúncios em tempo real."

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE,
    template: `%s — ${SITE_NAME}`,
  },
  description: DESCRIPTION,
  keywords: [
    "carro usado", "recomendação automóvel", "comparador carros", "standvirtual",
    "análise anúncio carro", "preço justo carro", "fiabilidade automóvel",
  ],
  authors: [{ name: SITE_NAME }],
  creator: SITE_NAME,
  openGraph: {
    type: "website",
    locale: "pt_PT",
    url: SITE_URL,
    siteName: SITE_NAME,
    title: TITLE,
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
  // Google Search Console ownership check, when verifying by meta tag.
  verification: { google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  alternates: {
    canonical: "/",   // home only: every section sets its own
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <meta name="theme-color" content="#09090B" />
      </head>
      <body className={cn("min-h-screen bg-background font-sans text-foreground antialiased")}>
        <PageViewTracker />
        <TooltipProvider delay={300}>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </TooltipProvider>
      </body>
    </html>
  )
}
