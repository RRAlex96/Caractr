/**
 * Caractr API Client
 * Typed fetch wrappers for all backend endpoints.
 */

import type {
  AnalysisResult,
  RecommendationResult,
  DreamCar,
  Recommendation,
  ConciergePayload,
  UserProfile,
} from "./types"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 * Fire-and-forget ping to wake the free-tier backend (it sleeps after ~15 min
 * idle and cold-starts in ~50s). Called when a user lands on a page that will
 * need the API, so it's warming while they read/answer — masking the cold start.
 */
export function warmBackend(): void {
  try {
    fetch(`${API}/api/health`, { cache: "no-store" }).catch(() => {})
  } catch {
    /* ignore */
  }
}

// ── Analysis ────────────────────────────────────────────────────────────────

export async function analyseUrl(
  listingUrl: string,
  options?: {
    modelId?: number
    userProfile?: UserProfile
    forceRefresh?: boolean
    /** The ad's text, pasted by the buyer when the page could not be fetched. */
    pastedText?: string
  }
): Promise<AnalysisResult> {
  const res = await fetch(`${API}/api/listings/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      listing_url: listingUrl.trim(),
      model_id: options?.modelId,
      user_profile: options?.userProfile,
      force_refresh: options?.forceRefresh ?? false,
      pasted_text: options?.pastedText || undefined,
    }),
  })
  return res.json()
}

export async function fetchAnalysis(analysisId: number): Promise<AnalysisResult> {
  const res = await fetch(`${API}/api/listings/analyses/${analysisId}`)
  if (!res.ok) {
    if (res.status === 404) throw new Error("not_found")
    throw new Error(`Erro ${res.status}`)
  }
  return res.json()
}

// ── Recommendations ─────────────────────────────────────────────────────────

export interface RecommendPayload {
  p1_context: string
  p2_relationship: string
  p3_driving_style: string
  p5_presence: string
  p6_aversion: string
  p7_dream_brand?: string | null
  p8_budget_range?: string | null
  p8_budget_min: number
  p8_budget_max: number
}

export async function recommend(payload: RecommendPayload): Promise<RecommendationResult> {
  const res = await fetch(`${API}/api/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  return res.json()
}

export async function fetchDreamCars(answers: Partial<RecommendPayload>): Promise<DreamCar[]> {
  const res = await fetch(`${API}/api/dream-cars`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      p1_context: answers.p1_context || "misto",
      p2_relationship: answers.p2_relationship || "gosto_conduzir",
      p3_driving_style: answers.p3_driving_style || "confortavel_com_alma",
      p5_presence: answers.p5_presence || "bom_aspeto",
      p6_aversion: answers.p6_aversion || "nenhuma",
      p8_budget_min: answers.p8_budget_min || 8000,
      p8_budget_max: answers.p8_budget_max || 25000,
    }),
  })
  const data = await res.json()
  return data.dream_cars || []
}

export async function refreshRecommendations(
  sessionId: string,
  dismissedModelIds: number[],
  dismissReasons: string[],
  count: number = 3
): Promise<{ recommendations: Recommendation[]; profile_adjusted: boolean }> {
  const res = await fetch(`${API}/api/recommend/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      dismissed_model_ids: dismissedModelIds,
      dismiss_reasons: dismissReasons,
      count,
    }),
  })
  return res.json()
}

// ── Concierge ───────────────────────────────────────────────────────────────

export async function submitConcierge(
  payload: ConciergePayload
): Promise<{ status: string; error?: string }> {
  const res = await fetch(`${API}/api/concierge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  return res.json()
}

// ── Feedback ────────────────────────────────────────────────────────────────

export async function submitFeedback(payload: {
  session_id: string
  overall: number
  accuracy: number
  usefulness: number
  would_recommend: boolean
  comments?: string
}): Promise<{ status: string }> {
  const res = await fetch(`${API}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  return res.json()
}

// ── Sources ─────────────────────────────────────────────────────────────────

export interface AdSource {
  id: string
  name: string
  domain: string
  url: string | null
  native: boolean
}

export async function getSources(): Promise<{ sources: AdSource[] }> {
  const res = await fetch(`${API}/api/listings/sources`)
  return res.json()
}

// ── Admin ──────────────────────────────────────────────────────────────────

export interface ConciergeRequestAdmin {
  id: number
  session_id: string | null
  name: string
  email: string
  model_interest: string | null
  budget_max: number | null
  feedback_tags: string[]
  consent_dealer: boolean
  status: string
  admin_notes: string | null
  created_at: string | null
  delivered_at: string | null
  profile_summary: Record<string, number> | null
  models_shown: { model_id: number; full_name: string }[] | null
}

export interface ConciergeStats {
  total: number
  by_status: Record<string, number>
  free_limit: number
  free_remaining: number
  avg_hours_to_delivery: number | null
}

function adminHeaders(token: string): HeadersInit {
  return { "Content-Type": "application/json", "X-Admin-Token": token }
}

export async function fetchAdminDashboard(
  token: string,
  period: string = "30d"
): Promise<any> {
  const res = await fetch(`${API}/api/admin/dashboard?period=${period}`, {
    headers: adminHeaders(token),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  return res.json()
}

export async function fetchConciergeStats(
  token: string
): Promise<ConciergeStats> {
  const res = await fetch(`${API}/api/admin/concierge/stats`, {
    headers: adminHeaders(token),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  return res.json()
}

export async function fetchConciergeList(
  token: string,
  params?: { status?: string; period?: string }
): Promise<{ count: number; requests: ConciergeRequestAdmin[] }> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set("status", params.status)
  if (params?.period) qs.set("period", params.period)
  const url = `${API}/api/admin/concierge${qs.toString() ? `?${qs}` : ""}`
  const res = await fetch(url, { headers: adminHeaders(token) })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  return res.json()
}

export interface PendingModel {
  id: number
  brand_name: string
  model_name: string
  created_at: string | null
  analyses: number
  generations: number
  has_engines: boolean
}

export async function fetchPendingModels(
  token: string
): Promise<{ count: number; analysed_gap: number; models: PendingModel[] }> {
  const res = await fetch(`${API}/api/admin/models/pending`, {
    headers: adminHeaders(token),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  return res.json()
}

export interface ExtractionHealth {
  status: "ok" | "degraded" | "critical" | "no_data"
  recent_price_pct: number | null
  daily: { day: string | null; total: number; price_pct: number | null; model_pct: number | null }[]
  by_source: { source: string; total: number; price_pct: number | null }[]
}

export async function fetchExtractionHealth(token: string): Promise<ExtractionHealth> {
  const res = await fetch(`${API}/api/admin/extraction-health`, {
    headers: adminHeaders(token),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  return res.json()
}

export interface KnownIssue {
  severity: string
  description: string
  affected_years?: string | null
  fix_cost_estimate?: string | null
}

export interface ModelEnrichment {
  reliability_score?: number | null
  reliability_summary?: string | null
  maintenance_cost_year?: number | null
  year_start?: number | null
  year_end?: number | null
  engine_code?: string | null
  fuel_type?: string | null
  displacement_cc?: number | null
  power_hp?: number | null
  known_issues: KnownIssue[]
}

export async function enrichModelDraft(
  token: string,
  id: number
): Promise<ModelEnrichment> {
  const res = await fetch(`${API}/api/admin/models/${id}/enrich/draft`, {
    method: "POST",
    headers: adminHeaders(token),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Erro ${res.status}`)
  }
  return res.json()
}

export async function enrichModelSave(
  token: string,
  id: number,
  data: ModelEnrichment
): Promise<{ status: string }> {
  const res = await fetch(`${API}/api/admin/models/${id}/enrich/save`, {
    method: "POST",
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Erro ${res.status}`)
  }
  return res.json()
}

export async function updateConcierge(
  token: string,
  id: number,
  data: { status?: string; admin_notes?: string }
): Promise<{ id: number; status: string; admin_notes: string | null; delivered_at: string | null }> {
  const res = await fetch(`${API}/api/admin/concierge/${id}`, {
    method: "PATCH",
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
  if (res.status === 403) throw new Error("Token inválido")
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  return res.json()
}
