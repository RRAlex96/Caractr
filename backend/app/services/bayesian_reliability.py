"""
Bayesian Reliability Scorer for Caractr

Computes a Beta-distribution posterior reliability score for each generation/engine.

Prior: calibrated by (fuel_type, age_bucket) — chosen conservatively so that
       the confidence interval is honestly wide when evidence is sparse.

Evidence: rows from reliability_evidence table, each contributing fail_eff/succ_eff
          pseudo-counts weighted by their evidence weight.

Output: score on 1–10 scale + 90% CI + data_quality label
  - 'prior_only':  no real evidence found; score = prior mean, CI is wide
  - 'limited':     1–2 independent sources
  - 'robust':      3+ independent sources

Honesty principle: the CI and data_quality label are ALWAYS shown to the user.
A wide CI with "prior_only" is better than a falsely precise number.
"""

from scipy.stats import beta as beta_dist
import math


# ─────────────────────────────────────────────────────────────
# PRIORS  (mu0, n0)
# mu0: prior mean probability of "no relevant incident in a year"
# n0:  effective prior sample size (higher = more skeptical of evidence)
# ─────────────────────────────────────────────────────────────

PRIORS: dict[tuple[str, str], tuple[float, int]] = {
    # Petrol
    ("gasolina", "0-3"):   (0.91, 50),
    ("gasolina", "4-7"):   (0.88, 55),
    ("gasolina", "8-12"):  (0.84, 65),
    ("gasolina", "13+"):   (0.79, 70),
    # Diesel
    ("diesel",   "0-3"):   (0.90, 50),
    ("diesel",   "4-7"):   (0.86, 55),
    ("diesel",   "8-12"):  (0.81, 65),
    ("diesel",   "13+"):   (0.76, 70),
    # Hybrid
    ("hibrido",  "0-3"):   (0.90, 45),
    ("hibrido",  "4-7"):   (0.87, 50),
    ("hibrido",  "8-12"):  (0.83, 55),
    ("hibrido",  "13+"):   (0.79, 60),
    # BEV — less mechanical complexity but more technology risk
    ("eletrico", "0-3"):   (0.89, 40),
    ("eletrico", "4-7"):   (0.85, 45),
    ("eletrico", "8-12"):  (0.80, 50),
    ("eletrico", "13+"):   (0.74, 55),
    # GPL
    ("gpl",      "0-3"):   (0.89, 50),
    ("gpl",      "4-7"):   (0.85, 55),
    ("gpl",      "8-12"):  (0.81, 60),
    ("gpl",      "13+"):   (0.76, 65),
    # Default fallback
    ("outro",    "0-3"):   (0.88, 45),
    ("outro",    "4-7"):   (0.84, 50),
    ("outro",    "8-12"):  (0.80, 55),
    ("outro",    "13+"):   (0.76, 60),
}

DEFAULT_PRIOR = (0.85, 50)


def _age_bucket(age_years: int | None) -> str:
    if age_years is None:
        return "4-7"
    if age_years <= 3:
        return "0-3"
    if age_years <= 7:
        return "4-7"
    if age_years <= 12:
        return "8-12"
    return "13+"


def _normalise_fuel(fuel_type: str | None) -> str:
    if not fuel_type:
        return "outro"
    f = fuel_type.lower().strip()
    if f in ("gasolina", "petrol", "gasoline"):
        return "gasolina"
    if f in ("diesel", "gasoleo"):
        return "diesel"
    if f in ("hibrido", "hybrid", "hibrido plug-in", "phev"):
        return "hibrido"
    if f in ("eletrico", "electric", "bev", "ev"):
        return "eletrico"
    if f == "gpl":
        return "gpl"
    return "outro"


def compute_reliability_score(
    evidence_rows: list[dict],
    fuel_type: str | None = None,
    age_years: int | None = None,
) -> dict:
    """
    Compute posterior Beta reliability score.

    Args:
        evidence_rows: list of dicts with keys:
            fail_eff (float), succ_eff (float), weight (float), source (str)
        fuel_type:  e.g. 'gasolina', 'diesel', 'eletrico'
        age_years:  age of the generation/cohort in years

    Returns dict with:
        score_1_10, ci_low_1_10, ci_high_1_10,
        alpha, beta_param, p_mean,
        evidence_count, data_quality, sources
    """
    fuel_norm  = _normalise_fuel(fuel_type)
    age_bucket = _age_bucket(age_years)
    mu0, n0    = PRIORS.get((fuel_norm, age_bucket), DEFAULT_PRIOR)

    alpha0 = n0 * mu0
    beta0  = n0 * (1.0 - mu0)

    alpha    = alpha0
    beta_val = beta0
    sources  = []

    for ev in evidence_rows:
        w       = float(ev.get("weight", 1.0) or 1.0)
        fail_e  = float(ev.get("fail_eff", 0) or 0)
        succ_e  = float(ev.get("succ_eff", 0) or 0)
        alpha    += succ_e * w
        beta_val += fail_e * w
        src = ev.get("source")
        if src and src not in sources:
            sources.append(src)

    p_mean  = alpha / (alpha + beta_val)
    ci_low  = beta_dist.ppf(0.05, alpha, beta_val)
    ci_high = beta_dist.ppf(0.95, alpha, beta_val)

    def _to_scale(p: float) -> float:
        return round(float(max(1.0, min(10.0, 1.0 + 9.0 * p))), 2)

    n_evidence = len(evidence_rows)
    n_sources  = len(set(ev.get("source", "") for ev in evidence_rows))

    if n_evidence == 0:
        data_quality = "prior_only"
    elif n_sources < 2 or n_evidence < 3:
        data_quality = "limited"
    else:
        data_quality = "robust"

    return {
        "score_1_10":    _to_scale(p_mean),
        "ci_low_1_10":   _to_scale(ci_low),
        "ci_high_1_10":  _to_scale(ci_high),
        "alpha":         round(alpha, 4),
        "beta_param":    round(beta_val, 4),
        "p_mean":        round(p_mean, 6),
        "evidence_count": n_evidence,
        "data_quality":  data_quality,
        "sources":       sources,
    }


def scores_are_valid(result: dict) -> bool:
    """Basic sanity check on a compute_reliability_score result."""
    s  = result["score_1_10"]
    lo = result["ci_low_1_10"]
    hi = result["ci_high_1_10"]
    return (
        1.0 <= lo <= s <= hi <= 10.0
        and 0.0 < result["p_mean"] < 1.0
        and result["alpha"] > 0
        and result["beta_param"] > 0
    )
