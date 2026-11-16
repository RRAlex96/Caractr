import type { Metadata } from "next"
import "./globals.css"
import { cn } from "@/lib/utils"
import { Navbar } from "@/components/layout/navbar"
import { Footer } from "@/components/layout/footer"
import { TooltipProvider } from "@/components/ui/tooltip"
import { PageViewTracker } from "@/components/shared/page-view-tracker"

const SITE_URL = "https://caractr.pt"
const SITE_NAME = "Caractr"
const TITLE = "Caractr — O preço deste carro usado é justo?"
const DESCRIPTION =
  "Cola o link de um anúncio do Standvirtual ou OLX: dizemos-te se o preço é justo, se aquele motor tem problemas conhecidos e o que verificar antes de comprar. Grátis."

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
