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
}

export interface DealbreakerIssue {
  description: string
  affected_years: string | null
  fix_cost_estimate: string | null
  source: string
}

export interface Dealbreakers {
  has_dealbreaker: boolean
  recall_count: number
  critical_issue_count: number
  recalls: DealbreakerRecall[]
  critical_issues: DealbreakerIssue[]
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
}

// ── Recommendation Types ────────────────────────────────────────────────────

export interface PriceRange {
  min: number
  max: number
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
