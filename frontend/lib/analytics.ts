/**
 * Caractr Analytics — fire-and-forget event tracking.
 * Never awaited, never blocks UX. Silently swallows errors.
 */

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Generate or retrieve anonymous ID — persists across visits in localStorage
function getAnonId(): string {
  if (typeof window === "undefined") return "";
  const key = "caractr_anon_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(key, id);
  }
  return id;
}

export function track(
  eventName: string,
  properties?: Record<string, unknown>,
  sessionId?: string
): void {
  // Fire and forget — deliberately not awaited
  fetch(`${API}/api/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_name: eventName,
      session_id: sessionId ?? null,
      anon_id: getAnonId(),
      properties: properties ?? {},
    }),
  }).catch(() => {
    // Silently ignore — analytics are best-effort
  });
}

// Typed event helpers
export const Analytics = {
  selectorStarted: () =>
    track("selector_started"),

  stepCompleted: (step: number, field: string, value: unknown) =>
    track("selector_step_completed", { step, field, value }),

  selectorCompleted: (durationMs: number, budgetMax: number) =>
    track("selector_completed", { duration_ms: durationMs, budget_max: budgetMax }),

  resultsViewed: (sessionId: string, modelCount: number, hadWildcard: boolean, hadStretch: boolean) =>
    track("results_viewed", { model_count: modelCount, had_wildcard: hadWildcard, had_stretch: hadStretch }, sessionId),

  modelClicked: (sessionId: string, modelId: number, rank: number, isWildcard: boolean) =>
    track("model_clicked", { model_id: modelId, rank, is_wildcard: isWildcard }, sessionId),

  adAnalysisRequested: (sessionId: string, modelId: number, listingUrl: string) =>
    track("ad_analysis_requested", { model_id: modelId, listing_url: listingUrl }, sessionId),

  watchlistOptIn: (consentType: string) =>
    track("watchlist_opt_in", { consent_type: consentType }),

  conciergeInterest: (sessionId: string, modelId?: number) =>
    track("concierge_interest", { model_id: modelId }, sessionId),

  feedbackSubmitted: (sessionId: string, satisfaction: string, preferredModelId?: number, emailProvided?: boolean) =>
    track("feedback_submitted", { satisfaction, preferred_model_id: preferredModelId, email_provided: emailProvided }, sessionId),

  // Phase 5 — new events
  analysisShared: (sessionId: string, listingUrl: string, method: string) =>
    track("analysis_shared", { listing_url: listingUrl, method }, sessionId),

  analysisFeedback: (sessionId: string, listingUrl: string, helpful: boolean, reason?: string) =>
    track("analysis_feedback", { listing_url: listingUrl, helpful, reason: reason ?? null }, sessionId),

  profileShown: (sessionId: string) =>
    track("profile_shown", {}, sessionId),

  quickProfileCompleted: (sessionId: string, topDim: string, aversion: string, budget: string) =>
    track("quick_profile_completed", { top_dim: topDim, aversion, budget }, sessionId),

  returnVisit: (sessionId: string, profileAgeDays: number) =>
    track("return_visit", { profile_age_days: profileAgeDays }, sessionId),

  dualVerdictShown: (sessionId: string, dealTier: string, fitTier: string) =>
    track("dual_verdict_shown", { deal_tier: dealTier, fit_tier: fitTier }, sessionId),

  modelExpanded: (sessionId: string, modelId: number, rank: number) =>
    track("model_expanded", { model_id: modelId, rank, timestamp_ms: Date.now() }, sessionId),
};
