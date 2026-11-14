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

/**
 * Where this visitor first came from: "utm:<source>/<medium>/<campaign>" when
 * the landing URL carried UTM tags, else the referring site's hostname, else
 * "direct". Decided once, on the first event of the first visit, and kept —
 * so a sale three days later is still credited to the Reddit thread that
 * brought the buyer in. No full URLs, nothing personal.
 */
export function acquisitionSource(): string {
  if (typeof window === "undefined") return "";
  const key = "caractr_src";
  try {
    const stored = localStorage.getItem(key);
    if (stored) return stored;
    const q = new URLSearchParams(window.location.search);
    const clean = (v: string | null) =>
      (v || "").toLowerCase().replace(/[^a-z0-9._-]/g, "").slice(0, 40);
    let src = "direct";
    const utm = clean(q.get("utm_source"));
    if (utm) {
      src = `utm:${utm}/${clean(q.get("utm_medium")) || "-"}/${clean(q.get("utm_campaign")) || "-"}`;
    } else if (document.referrer) {
      const host = new URL(document.referrer).hostname.replace(/^www\./, "");
      if (host && host !== window.location.hostname.replace(/^www\./, "")) src = host.slice(0, 60);
    }
    localStorage.setItem(key, src);
    return src;
  } catch {
    return "direct";
  }
}

/**
 * Our own visits must not count as traction. Opening any page once with
 * ?internal=1 marks this browser as internal (?internal=0 undoes it); its
 * events are still sent, flagged, and left out of the funnel report.
 */
function isInternal(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const flag = new URLSearchParams(window.location.search).get("internal");
    if (flag === "1") localStorage.setItem("caractr_internal", "1");
    if (flag === "0") localStorage.removeItem("caractr_internal");
    return localStorage.getItem("caractr_internal") === "1";
  } catch {
    return false;
  }
}

export function track(
  eventName: string,
  properties?: Record<string, unknown>,
  sessionId?: string
): void {
  const internal = isInternal();
  // Fire and forget — deliberately not awaited
  fetch(`${API}/api/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_name: eventName,
      session_id: sessionId ?? null,
      anon_id: getAnonId(),
      properties: {
        ...(properties ?? {}),
        src: acquisitionSource(),
        ...(internal ? { internal: true } : {}),
      },
    }),
  }).catch(() => {
    // Silently ignore — analytics are best-effort
  });
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "invalid";
  }
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

  // Funnel: visit -> analysis -> share -> visit from a share
  pageView: (path: string) =>
    track("page_view", { path }),

  analysisStarted: (listingUrl: string, hasProfile: boolean) =>
    track("analysis_started", { site: hostOf(listingUrl), has_profile: hasProfile }),

  analysisCompleted: (listingUrl: string, tier: string | undefined, fromCache: boolean, analysisId?: number | null) =>
    track("analysis_completed", {
      site: hostOf(listingUrl), tier: tier ?? null, from_cache: fromCache, analysis_id: analysisId ?? null,
    }),

  analysisFailed: (listingUrl: string, reason: string, code?: string, pasted = false) =>
    track("analysis_failed", { site: hostOf(listingUrl), reason: reason.slice(0, 120), code: code ?? null, pasted }),

  sharedAnalysisViewed: (analysisId: number) =>
    track("shared_analysis_viewed", { analysis_id: analysisId }),

  sharedCtaClicked: (analysisId: number) =>
    track("shared_cta_clicked", { analysis_id: analysisId }),
};
