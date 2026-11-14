// The data behind the public model pages (/carros/...), exported from the
// database by backend/scripts/export_model_pages.py. Read at build time only:
// the pages are static and never wait for the API.
import data from "@/data/models.json"

export interface ModelPrice {
  year: number
  p10: number
  p50: number
  p90: number
  n: number
}

export interface ModelEngine {
  code: string
  fuel: "gasolina" | "diesel" | "hibrido" | "eletrico" | "gpl" | string
  plug_in: boolean
  cc: number | null
  hp: number | null
  gearbox: string | null
  consumption: number | null
  co2: number | null
  year_from: number | null
  year_to: number | null
  listings: number | null
  reliability: number | null
  maintenance: number | null
}

export interface ModelGeneration {
  name: string
  from: number
  to: number | null
  fuel_only: string | null
  source: string | null
  depreciation: number | null
}

export interface KnownIssue {
  id: string
  severity: string
  engine: string
  problem: string
  description: string
  check: string
  affected_years: string
  fix_cost_estimate: string | null
  sources: { label: string; url: string }[]
}

export interface ModelPage {
  slug: string
  brand: string
  model: string
  body: string
  segment: string
  character: { comfort: number; fun: number; city: number; highway: number; family: number; text: string } | null
  generations: ModelGeneration[]
  prices: ModelPrice[]
  engines: ModelEngine[]
  on_sale: number
  brand_reliability: { score: number; studies: number; sources: string[] } | null
  known_issues: KnownIssue[]
  indexable: boolean
  related: string[]
}

interface ModelData {
  generated_on: string
  snapshot: { collected_on: string; listings: number } | null
  models: ModelPage[]
}

const DATA = data as unknown as ModelData

export const MODELS: ModelPage[] = DATA.models
export const SNAPSHOT = DATA.snapshot
const BY_SLUG = new Map(MODELS.map((m) => [m.slug, m]))

export function getModel(slug: string): ModelPage | undefined {
  return BY_SLUG.get(slug)
}

export function modelsByBrand(onlyIndexable = true): [string, ModelPage[]][] {
  const groups = new Map<string, ModelPage[]>()
  for (const m of MODELS) {
    if (onlyIndexable && !m.indexable) continue
    groups.set(m.brand, [...(groups.get(m.brand) ?? []), m])
  }
  return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0], "pt"))
}

const MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
  "agosto", "setembro", "outubro", "novembro", "dezembro"]

export function monthYear(iso: string | undefined | null): string {
  if (!iso) return ""
  const [y, m] = iso.split("-").map(Number)
  return `${MONTHS[m - 1]} de ${y}`
}

/** 8 775 → "8 775", 21400 → "21 400": grouped from four digits up (pt-PT
 * leaves 4-digit numbers ungrouped, which reads badly in a column). */
export function num(n: number): string {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ")
}

/** 5.5 → "5,5" */
export function dec(n: number, digits = 1): string {
  return n.toFixed(digits).replace(".", ",")
}

export function eur(n: number | null | undefined): string {
  if (n == null) return "—"
  return `${num(n)} €`
}

export const FUEL_LABEL: Record<string, string> = {
  gasolina: "Gasolina",
  diesel: "Gasóleo",
  hibrido: "Híbrido",
  eletrico: "Elétrico",
  gpl: "GPL",
}

export function fuelLabel(e: Pick<ModelEngine, "fuel" | "plug_in">): string {
  if (e.fuel === "hibrido" && e.plug_in) return "Híbrido plug-in"
  return FUEL_LABEL[e.fuel] ?? e.fuel
}

export function consumptionLabel(e: ModelEngine): string {
  if (e.consumption == null) return "—"
  const v = Number.isInteger(e.consumption) ? String(e.consumption) : dec(e.consumption)
  return e.fuel === "eletrico" ? `${v} kWh/100 km` : `${v} L/100 km`
}

export function yearsLabel(from: number | null, to: number | null): string {
  if (!from) return "—"
  if (!to || to >= new Date().getFullYear()) return `desde ${from}`
  return from === to ? `${from}` : `${from}–${to}`
}

/** The price range a reader most needs: newest and oldest priced years. */
export function priceSpan(m: ModelPage): { from: ModelPrice; to: ModelPrice } | null {
  if (!m.prices.length) return null
  return { from: m.prices[m.prices.length - 1], to: m.prices[0] }
}

/** Typical yearly value lost, from the newest generation that has a measured rate. */
export function depreciation(m: ModelPage): number | null {
  const g = [...m.generations].reverse().find((x) => x.depreciation != null)
  return g?.depreciation ?? null
}

/** The published studies a brand's reliability rests on, as a Portuguese reader knows them. */
export function studyLabel(source: string): string {
  if (/euroconsumers|deco/i.test(source)) return "inquérito DECO PROteste / Euroconsumers"
  if (/what car/i.test(source)) return "What Car? (Reino Unido)"
  if (/t(ü|u)v/i.test(source)) return "TÜV-Report (Alemanha)"
  if (/consumer reports/i.test(source)) return "Consumer Reports (EUA)"
  if (/j\.?\s?d\.? power/i.test(source)) return "J.D. Power (EUA)"
  if (/auto plus/i.test(source)) return "Auto Plus (França)"
  return source
}
