import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format price in Portuguese locale: 18500 → "18.500 €" */
export function formatPrice(value: number): string {
  return `${Math.round(value).toLocaleString("pt-PT")} €`
}

/** Format km: 95000 → "95.000 km" */
export function formatKm(value: number): string {
  return `${Math.round(value).toLocaleString("pt-PT")} km`
}

/** Format km/year: 11875 → "11.875" */
export function formatKmYear(value: number): string {
  return Math.round(value).toLocaleString("pt-PT")
}

/** Format percentage: 4.5 → "+4.5%" or "−4.5%" */
export function formatDelta(pct: number, positive: "above" | "below" = "below"): string {
  const sign = positive === "below" ? "−" : "+"
  const inverseSign = positive === "below" ? "+" : "−"
  return pct >= 0 ? `${sign}${Math.abs(pct)}%` : `${inverseSign}${Math.abs(pct)}%`
}

/** Relative date: "esta semana", "há 8 dias", "há 2 meses" */
export function formatRelativeDate(dateStr: string | null | undefined): string {
  if (!dateStr) return ""
  try {
    const d = new Date(dateStr)
    const days = Math.round((Date.now() - d.getTime()) / 86400000)
    if (days <= 7) return "esta semana"
    if (days <= 35) return "este mês"
    const months = Math.round(days / 30)
    return `há ${months} ${months === 1 ? "mês" : "meses"}`
  } catch {
    return ""
  }
}

/** Deal tier config */
export const TIER_CONFIG = {
  forte:    { color: "text-success", bg: "bg-success/10", border: "border-success/30", label: "NEGÓCIO FORTE",  emotion: "Este tipo de negócio não dura muito." },
  razoavel: { color: "text-gold",    bg: "bg-gold/10",    border: "border-gold/30",    label: "RAZOÁVEL",       emotion: "Um negócio justo — avança com confiança." },
  cuidado:  { color: "text-warning", bg: "bg-warning/10", border: "border-warning/30", label: "ATENÇÃO",        emotion: "Há melhores opções no mercado neste momento." },
  evitar:   { color: "text-danger",  bg: "bg-danger/10",  border: "border-danger/30",  label: "EVITAR",         emotion: "Não vale o risco. Continua a procurar." },
} as const

/** Fit tier config */
export const FIT_CONFIG = {
  excelente: { color: "text-success", bg: "bg-success/10" },
  bom:       { color: "text-gold",    bg: "bg-gold/10" },
  parcial:   { color: "text-warning", bg: "bg-warning/10" },
  fraco:     { color: "text-danger",  bg: "bg-danger/10" },
} as const

export type DealTier = keyof typeof TIER_CONFIG
export type FitTier = keyof typeof FIT_CONFIG
