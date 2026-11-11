"""
Curated known engine/gearbox failures (seeds/known_engine_issues.json).

A small, hand-reviewed list of chronic, expensive weaknesses of specific
engines and gearboxes — the thing that genuinely puts a used-car buyer off
(PureTech wet belts, N47 chains, DQ200 mechatronics...). Every entry is
sourced; only `status: approved` entries are ever used by the product.

This module only loads, validates and matches. Matching is deliberately
conservative: an entry matches an engine only when brand AND every rule it
declares agree (fuel, displacement, label/transmission pattern, torque,
model), and only when the production years overlap.
"""
import json
import re
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[2] / "seeds" / "known_engine_issues.json"

SEVERITIES = {"critico", "alto"}
STATUSES = {"draft", "approved", "rejected"}
SOURCE_KINDS = {"official", "press", "trade", "forum"}
# A red deal-breaker must rest on at least one source of these kinds.
AUTHORITATIVE = {"official", "press"}

_REQUIRED = ("id", "status", "severity", "confidence", "component", "name", "years",
             "problem", "detail", "check", "cost_eur", "match", "sources")


def load_issues(path: Path = SEED_PATH, include_drafts: bool = False) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    issues = data["issues"]
    if include_drafts:
        return [i for i in issues if i.get("status") != "rejected"]
    return [i for i in issues if i.get("status") == "approved"]


def validate(issue: dict) -> list[str]:
    """Problems with one entry (empty list = valid)."""
    errs = [f"missing '{k}'" for k in _REQUIRED if k not in issue]
    if errs:
        return errs
    if issue["severity"] not in SEVERITIES:
        errs.append(f"severity '{issue['severity']}' not in {sorted(SEVERITIES)}")
    if issue["status"] not in STATUSES:
        errs.append(f"status '{issue['status']}' not in {sorted(STATUSES)}")
    lo, hi = issue["years"]
    if not (1995 <= lo <= hi <= 2030):
        errs.append(f"bad years {issue['years']}")
    kinds = {s.get("kind") for s in issue["sources"]}
    if not issue["sources"]:
        errs.append("no sources")
    if kinds - SOURCE_KINDS:
        errs.append(f"unknown source kinds {sorted(kinds - SOURCE_KINDS)}")
    if any(not str(s.get("url", "")).startswith("https://") for s in issue["sources"]):
        errs.append("every source needs an https URL")
    if issue["severity"] == "critico" and not (kinds & AUTHORITATIVE):
        errs.append("'critico' needs an official or press source — cap at 'alto'")
    m = issue["match"]
    if not m.get("brands"):
        errs.append("match.brands is required")
    if not any(k in m for k in ("fuel", "displacement_cc", "label_regex", "transmission_regex")):
        errs.append("match needs at least one rule beyond brands")
    for k in ("label_regex", "transmission_regex", "model_regex"):
        if k in m:
            try:
                re.compile(m[k], re.I)
            except re.error as e:
                errs.append(f"match.{k} invalid: {e}")
    cost = issue["cost_eur"]
    for k in ("preventive", "failure"):
        v = cost.get(k)
        if v is not None and not (isinstance(v, list) and len(v) == 2 and v[0] <= v[1]):
            errs.append(f"cost_eur.{k} must be [lo, hi] or null")
    return errs


def _norm(s) -> str:
    return (s or "").strip().lower()


def matches_engine(issue: dict, *, brand: str, model: str = "", label: str = "",
                   fuel: str = "", displacement_cc: int | None = None,
                   transmission: str = "", torque_nm: int | None = None) -> bool:
    """Does `issue` describe this engine? Every declared rule must agree;
    an unknown engine attribute fails the rule that needs it (precision over
    recall — a wrong red flag is worse than a missing one)."""
    m = issue["match"]
    if _norm(brand) not in {_norm(b) for b in m["brands"]}:
        return False
    if "fuel" in m and _norm(fuel) not in {_norm(f) for f in m["fuel"]}:
        return False
    if "displacement_cc" in m:
        lo, hi = m["displacement_cc"]
        if displacement_cc is None or not (lo <= displacement_cc <= hi):
            return False
    if "label_regex" in m and not re.search(m["label_regex"], label or "", re.I):
        return False
    if "transmission_regex" in m:
        haystack = f"{transmission or ''} {label or ''}"
        if not re.search(m["transmission_regex"], haystack, re.I):
            return False
    if "max_torque_nm" in m and (torque_nm is None or torque_nm > m["max_torque_nm"]):
        return False
    if "model_regex" in m and not re.search(m["model_regex"], model or "", re.I):
        return False
    return True


def years_overlap(issue: dict, year_start: int | None, year_end: int | None) -> bool:
    """Does a production span [year_start, year_end] overlap the issue's years?
    An unknown start can't be placed, so it doesn't match."""
    if year_start is None:
        return False
    lo, hi = issue["years"]
    return year_start <= hi and (year_end or 9999) >= lo


def applies_to_year(issue: dict, year: int | None) -> bool:
    if year is None:
        return False
    lo, hi = issue["years"]
    return lo <= year <= hi
