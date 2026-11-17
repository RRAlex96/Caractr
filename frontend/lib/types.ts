/**
 * Caractr API Response Types
 * Matches backend response shapes from ad_analysis_service.py and recommendation router.
 */

// ── Analysis Types ──────────────────────────────────────────────────────────

export interface AnalysisListing {
  brand_name: string
  model_name: string
  year: number | null
  km: number | null
  price: number | null
  seller_type: string | null
  photo_count: number | null
  listing_age_days: number | null
}

/**
 * The engine-power band the comparable listings lie in (the car's power ±15%),
 * when the listing states the car's power. pool_count is how many listings of
 * that power were found.
 */
export interface MarketPowerComparison {
  car_power_hp: number
  power_from: number
  power_to: number
  pool_count: number
}

/**
 * How the car's mileage was taken into account in the market comparison.
 *  - band: only listings between km_from and km_to were compared
 *  - pool: too few in the band, but the car's km is typical of the whole pool
 *  - mismatch: nothing comparable in mileage — the price verdict is withheld
 */
export interface MarketKmComparison {
  basis: "band" | "pool" | "mismatch"
  car_km: number
  km_from: number
  km_to: number
  in_band_count: number
  pool_count: number
  pool_median_km: number
}

/**
 * How the mix of model years among the comparable listings was handled.
 *  - adjusted: every listing's price was moved to the car's own year and km
 *    (fit of price on year and km); margin_pct is the 90% margin of the reference
 *  - near: only listings of the car's year ±1 were compared
 *  - typical: the car's year is the middle of the listings' years
 *  - mismatch: the listings are mostly of other years and too few to adjust
 *    for it — the price verdict is withheld
 */
export interface MarketYearComparison {
  basis: "adjusted" | "near" | "typical" | "mismatch"
  car_year: number
  median_year: number
  year_from: number
  year_to: number
  count: number
  /** Why prices were not adjusted (bases other than "adjusted"). */
  not_adjusted?: "unknown" | "few" | "single" | "outside" | "unstable"
  car_km?: number
  km_from?: number
  km_to?: number
  excluded_count?: number
  pool_count?: number
  per_year_pct?: number
  per_10k_km_pct?: number
  margin_pct?: number
}

export interface AnalysisDeal {
  tier: "forte" | "razoavel" | "cuidado" | "evitar"
  score: number
  price_delta: number | null
  price_delta_pct: number | null
  km_per_year: number | null
  market_avg_price: number | null
  market_median_price: number | null
  market_sample_count: number | null
  market_data_source: "live" | "db" | "none"
  market_data_age_days: number | null
  market_data_stale: boolean
  market_fuel_type: string | null
  market_km_comparison?: MarketKmComparison | null
  market_year_comparison?: MarketYearComparison | null
  market_power_comparison?: MarketPowerComparison | null
  generation_year_start: number | null
  generation_year_end: number | null
}

export interface AnalysisDetails {
  verdict: string
  verdict_reason: string | null
  green_flags: string[]
  red_flags: string[]
  seller_analysis: string | null
  profile_fit: string | null
  trim_level: string | null
  spec_tier: string | null
  spec_value_assessment: string | null
  trim_includes: string[]
  optional_extras: string[]
  equipment_note: string | null
  key_extras: string[]
  engine_code: string | null
  engine_analysis: string | null
  extras_analysis: string | null
  negotiation_script: string | null
  verdict_narrative: string | null
  seller_read: string | null
}

export interface DepreciationProjection {
  year: number
  value: number
  pct_of_current: number
  loss: number
}

export interface DepreciationCurvePoint {
  age: number
  pct_of_new: number
  year: number
  p50: number
}

export interface DepreciationData {
  annual_pct: number
  annual_pct_label: string
  holds_value: boolean
  loses_fast: boolean
  curve: DepreciationCurvePoint[]
  as_of: string | null
  future_value?: DepreciationProjection[]
}

export interface FitData {
  fit_score: number
  fit_tier: "excelente" | "bom" | "parcial" | "fraco"
  fit_label: string
  fit_reason: string | null
}

export interface ReliabilityData {
  score: number
  ci_low: number
  ci_high: number
  data_quality: "prior_only" | "limited" | "robust" | "strong_data"
}

export interface DealbreakerRecall {
  title: string
  description: string
  severity: string
  source: string
  source_url: string | null
  date: string | null
  /** Production period the recall covers, e.g. "2013-2024" or "2024+". */
  affected_years?: string | null
  /** Risk tag from the source, e.g. "Risco de ferimentos". */
  risk?: string | null
  /** Airbag-inflator campaign: stressed on the checklist. */
  priority?: boolean
}

export interface DealbreakerIssue {
  /** Engine/gearbox the failure belongs to, e.g. "1.2 PureTech 130 EAT8". */
  engine?: string | null
  description: string
  affected_years: string | null
  fix_cost_estimate: string | null
  source: string
  /** Curated (hand-reviewed, sourced) entry matched to this listing's engine and year. */
  curated?: boolean
  id?: string
  severity?: "critico" | "alto"
  component?: "motor" | "caixa"
  /** One-line title, e.g. "Correia de distribuição em banho de óleo degrada-se cedo". */
  problem?: string
  /** What the buyer should ask or verify before buying. */
  check?: string
  mitigation?: string | null
  sources?: { label: string; url: string }[]
}

export interface Dealbreakers {
  /** True only for critical known failures — recalls never set it. */
  has_dealbreaker: boolean
  /** EU recalls for the checklist (empty on recommendation cards). */
  recall_count: number
  critical_issue_count: number
  recalls: DealbreakerRecall[]
  critical_issues: DealbreakerIssue[]
  /** Curated amber weak points of this engine/gearbox — what to check, never red. */
  watch_items?: DealbreakerIssue[]
}

export interface MarketBand {
  p10?: number
  p90?: number
  sample_count?: number
}

export interface MarketData {
  p50: number
  band?: MarketBand | null
  as_of?: string | null
  /** Registration year the price is for (recommendation cards). */
  year?: number | null
  basis?: "market" | "list"
  source?: string | null
}

export interface NegotiationNumbers {
  asking_price: number
  opening_offer: number
  fair_value: number
  walk_away: number
  potential_saving: number
  leverage: string[]
  confidence: "alta" | "media" | "baixa"
  sample_count: number
}

export interface Anomaly {
  level: "danger" | "warning"
  title: string
  message: string
}

export interface PriceHistory {
  observations: number
  tracked_days: number | null
  first_price: number
  current_price: number
  drop_total: number
  last_change: { from: number; to: number; days_ago: number | null } | null
  relisted_before: boolean
  rollback_suspected: boolean
}

export interface CostOfOwnership {
  monthly_running: number
  monthly_true: number | null
  annual_fuel: number
  annual_iuc: number | null
  annual_maintenance: number | null
  depreciation_monthly: number | null
  assumptions: {
    km_year: number
    consumption: number
    consumption_unit: "l" | "kwh"
    fuel_price: number
  }
}

export interface AnalysisResult {
  analysis_id?: number | null
  from_cache: boolean
  source: string
  source_label: string
  source_url?: string
  listing: AnalysisListing
  deal: AnalysisDeal
  analysis: AnalysisDetails
  inspection_checklist: string[]
  negotiation_tips: string[]
  negotiation_plan?: NegotiationPlan | null
  negotiation?: NegotiationNumbers | null
  anomaly?: Anomaly | null
  price_history?: PriceHistory | null
  cost_of_ownership?: CostOfOwnership | null
  maintenance_estimate: number | null
  reliability: ReliabilityData | null
  dealbreakers?: Dealbreakers | null
  depreciation: DepreciationData | null
  fit: FitData | null
  caveat: string | null
  error?: string
  /** "fetch_failed" | "paste_incomplete": the page could not be read; offer the paste box. */
  error_code?: string
}

// ── Recommendation Types ────────────────────────────────────────────────────

export interface PriceRange {
  min: number
  max: number
  /** Registration year the range is for: the newest the budget buys. */
  year?: number | null
}

export interface Recommendation {
  rank: number
  model_id: number
  model_name: string
  brand_name: string
  full_name: string
  body_type: string | null
  segment: string | null
  headline: string
  reasons: string[]
  tradeoff: string | null
  price_range: PriceRange | null
  is_stretch: boolean
  is_wildcard: boolean
  reliability: ReliabilityData | null
  market: MarketData | null
  dealbreakers?: Dealbreakers | null
  running_cost?: RunningCost | null
}

export interface RunningCost {
  fuel: string
  consumption: number
  unit: string
  km_month: number
  eur_month: number
  eur_month_home?: number
  eur_month_public?: number
  price_note: string
  as_of: string
}

export interface ProfileNarrative {
  summary: string
  priorities: string | null
  tension: string | null
  aversion: string | null
  identity: string | null
  context: string | null
}

export interface ProfileSignals {
  identity_bias: string
  anti_pattern: string
  engagement_bias: string
  latent_override: boolean
}

export interface UserProfile {
  economy: number
  comfort: number
  driving: number
  practical: number
  status: number
  reliability: number
}

export interface RecommendationResult {
  session_id: string
  profile: UserProfile
  profile_signals: ProfileSignals | null
  profile_summary: string | null
  profile_narrative: ProfileNarrative | null
  answers: Record<string, unknown>
  recommendations: Recommendation[]
  suggestions: {
    stretch_budget: number
    models_available: number
  } | null
  refined_from?: string | null
}

export interface DreamCar {
  id: string
  name: string
  identity: string
  score?: number
}

// ── Concierge Types ─────────────────────────────────────────────────────────

export interface ConciergePayload {
  session_id: string | null
  name: string
  email: string
  model_interest: string | null
  model_ids: number[]
  budget_max: number | null
  feedback_tags: string[]
  consent_caractr: boolean
  consent_dealer: boolean
  listing_url: string | null
  listing_verdict: string | null
}

export interface NegotiationPlan {
  numbers: {
    asking: number
    opening: number
    target: number
    ceiling: number
    comparables?: number | null
    confidence?: string | null
  } | null
  note?: string | null
  arguments: { kind: string; eur?: number | null; text: string; conditional?: boolean }[]
  walk_away: { ceiling: number; ceiling_unproven?: number; text: string } | null
  messages: {
    first_contact: string
    offer: string
    offer_no_invoice?: string | null
    no_invoice_topic?: string | null
    counters: { if: string; reply: string }[]
  }
  seller: "stand" | "particular"
}
