"use client"

import { useEffect } from "react"
import { usePathname } from "next/navigation"

import { Analytics } from "@/lib/analytics"

/**
 * One page_view per route change — the top of the funnel. The admin area is
 * ours, not a visitor's, so it stays out of the numbers.
 */
export function PageViewTracker() {
  const pathname = usePathname()
  useEffect(() => {
    if (!pathname || pathname.startsWith("/admin")) return
    // /analise/123 -> /analise/[id], so shared pages group as one row.
    Analytics.pageView(pathname.replace(/^\/analise\/\d+$/, "/analise/[id]"))
  }, [pathname])
  return null
}
