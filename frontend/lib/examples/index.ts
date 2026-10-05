// Real analyses captured from the live backend, bundled so the demo shows a
// full result instantly — even while the free-tier backend cold-starts (or if
// it's asleep). These are genuine outputs, not mock-ups.
import type { AnalysisResult } from "@/lib/types"

import corolla from "./corolla-hybrid.json"
import bmw530e from "./bmw-530e.json"
import fiat500x from "./fiat-500x.json"
import astra from "./astra-hybrid.json"

export interface Example {
  slug: string
  data: AnalysisResult
}

export const EXAMPLES: Example[] = [
  { slug: "corolla-hybrid", data: corolla as unknown as AnalysisResult },
  { slug: "bmw-530e", data: bmw530e as unknown as AnalysisResult },
  { slug: "fiat-500x", data: fiat500x as unknown as AnalysisResult },
  { slug: "astra-hybrid", data: astra as unknown as AnalysisResult },
]
