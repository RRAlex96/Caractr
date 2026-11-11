"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const NAV_LINKS = [
  { href: "/analisar", label: "Analisar", match: ["/analisar"] },
  { href: "/escolher", label: "Descobrir", match: ["/escolher", "/resultados"] },
  { href: "/concierge", label: "Concierge", match: ["/concierge"] },
]

export function Navbar() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  // Close menu on route change
  useEffect(() => setOpen(false), [pathname])

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (open) document.body.style.overflow = "hidden"
    else document.body.style.overflow = ""
    return () => { document.body.style.overflow = "" }
  }, [open])

  const isActive = (match: string[]) => match.some((m) => pathname === m)

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          {/* Wordmark */}
          <Link
            href="/"
            className="font-display text-sm font-bold tracking-[0.12em] text-foreground transition-colors hover:text-gold"
          >
            CARACTR
          </Link>

          {/* Nav links — desktop */}
          <div className="hidden items-center gap-1 md:flex">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-full px-4 py-2 text-xs font-medium tracking-wide transition-colors",
                  isActive(link.match)
                    ? "bg-gold/10 text-gold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* CTA — desktop */}
            <Link
              href="/analisar"
              className="hidden h-7 items-center justify-center rounded-full bg-gold px-5 text-xs font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark sm:inline-flex"
            >
              Analisar anúncio
            </Link>

            {/* Hamburger — mobile */}
            <button
              onClick={() => setOpen(!open)}
              aria-label={open ? "Fechar menu" : "Abrir menu"}
              className="relative flex h-8 w-8 items-center justify-center md:hidden"
            >
              <span
                className={cn(
                  "absolute h-px w-4 bg-foreground transition-all duration-200",
                  open ? "rotate-45" : "-translate-y-1"
                )}
              />
              <span
                className={cn(
                  "absolute h-px w-4 bg-foreground transition-all duration-200",
                  open ? "-rotate-45" : "translate-y-1"
                )}
              />
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu overlay */}
      {open && (
        <div className="fixed inset-0 z-40 flex flex-col bg-background pt-16 md:hidden">
          <div className="flex flex-1 flex-col items-center justify-center gap-6">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "font-display text-2xl font-bold tracking-tight transition-colors",
                  isActive(link.match) ? "text-gold" : "text-foreground hover:text-gold"
                )}
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-4 h-px w-12 bg-border" />
            <Link
              href="/analisar"
              className="mt-2 rounded-full bg-gold px-8 py-3 text-sm font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              Analisar anúncio
            </Link>
          </div>
          <div className="pb-8 text-center">
            <span className="font-mono text-[9px] uppercase tracking-[2px] text-muted-foreground/30">
              informar nunca assustar
            </span>
          </div>
        </div>
      )}
    </>
  )
}
