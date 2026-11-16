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
import os
import re
import unicodedata
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[2] / "seeds" / "known_engine_issues.json"

# Local preview only: show draft entries too. Never set in production — only
# human-approved entries may reach users.
_INCLUDE_DRAFTS_ENV = "KNOWN_ISSUES_INCLUDE_DRAFTS"

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


def _strip(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


def _norm(s) -> str:
    return _strip(s)


def matches_engine(issue: dict, *, brand: str, model: str = "", label: str = "",
                   fuel: str = "", displacement_cc=None,
                   transmission: str = "", torque_nm: int | None = None,
                   power_hp: int | None = None) -> bool:
    """Does `issue` describe this engine? Every declared rule must agree;
    an unknown engine attribute fails the rule that needs it (precision over
    recall — a wrong red flag is worse than a missing one).

    `displacement_cc` is an exact value (catalogue, listing spec sheet) or a
    (lo, hi) interval when only "1.2" is known from the version text."""
    m = issue["match"]
    if _norm(brand) not in {_norm(b) for b in m["brands"]}:
        return False
    if "fuel" in m and _norm(fuel) not in {_norm(f) for f in m["fuel"]}:
        return False
    if "displacement_cc" in m:
        lo, hi = m["displacement_cc"]
        if displacement_cc is None:
            return False
        d_lo, d_hi = (displacement_cc if isinstance(displacement_cc, (tuple, list))
                      else (displacement_cc, displacement_cc))
        if d_hi < lo or d_lo > hi:
            return False
    exact_cc = displacement_cc is not None and not isinstance(displacement_cc, (tuple, list))
    # Some engines are uniquely identified by brand + fuel + exact cc + years
    # (e.g. every 1199 cc Stellantis petrol of 2014-22 is a PureTech), so a
    # spec-sheet cc can stand in for the name. Opt-in per entry, reviewed.
    label_waived = exact_cc and m.get("exact_cc_suffices") and "displacement_cc" in m
    if "label_regex" in m and not label_waived and not re.search(m["label_regex"], label or "", re.I):
        return False
    if "transmission_regex" in m:
        haystack = f"{transmission or ''} {label or ''}"
        if not re.search(m["transmission_regex"], haystack, re.I):
            return False
    if "max_torque_nm" in m:
        if torque_nm is not None:
            if torque_nm > m["max_torque_nm"]:
                return False
        # Listings rarely state torque; power is the declared stand-in.
        elif "max_power_hp" not in m or power_hp is None or power_hp > m["max_power_hp"]:
            return False
    if "model_regex" in m and not re.search(m["model_regex"], model or "", re.I):
        return False
    # A power band known to use a different part (e.g. the 160 cv 2.0 CDTi has
    # the F40 gearbox, not the M32). Only excludes when the power is known.
    if "exclude_power_hp" in m and power_hp is not None:
        lo, hi = m["exclude_power_hp"]
        if lo <= power_hp <= hi:
            return False
    return True


# ── Listings ────────────────────────────────────────────────────────────────

_FUELS = (("diesel", "diesel"), ("gasoleo", "diesel"), ("hibrid", "hibrido"),
          ("hybrid", "hibrido"), ("gasolina", "gasolina"), ("gpl", "gpl"),
          ("eletric", "eletrico"), ("electric", "eletrico"))

# "1.2 PureTech", "2.0 TDI" — a litre figure next to an engine word. In the
# version string any litre figure counts; in free description text it must
# sit next to an engine word, so "1.5 anos de garantia" can't become a 1.5.
_ENGINE_WORDS = (r"tdi|tsi|tfsi|hdi|bluehdi|cdi|crdi|ecoboost|ecoblue|tdci|dci|tce|sce|"
                 r"puretech|thp|vti|multiair|multijet|t-jet|d-4d|d4d|skyactiv|dig-t|"
                 r"cdti|turbo|ingenium|v[0-9]")
_LITRES_ANY = re.compile(r"(?<![\d.,])([0-6])[.,]([0-9])(?![\d.,])")
_LITRES_ENGINE = re.compile(rf"(?<![\d.,])([0-6])[.,]([0-9])\s*(?:{_ENGINE_WORDS})\b", re.I)


def normalize_fuel(fuel) -> str:
    f = _strip(fuel)
    for needle, value in _FUELS:
        if needle in f:
            return value
    return ""


def _litres_interval(version: str, description: str):
    m = _LITRES_ANY.search(version or "") or _LITRES_ENGINE.search(description or "")
    if not m:
        return None
    cc = int(m.group(1)) * 1000 + int(m.group(2)) * 100
    return (cc - 50, cc + 49)


def listing_engine_profile(listing: dict) -> dict:
    """The engine facts a scraped listing gives us, in matcher terms."""
    version = listing.get("version") or ""
    description = (listing.get("description") or "")[:800]
    cc = listing.get("engine_displacement_cc")
    try:
        cc = int(cc) if cc else None
    except (TypeError, ValueError):
        cc = None
    if cc is not None and not (600 <= cc <= 7000):
        cc = None
    try:
        power = int(listing.get("engine_power_hp")) if listing.get("engine_power_hp") else None
    except (TypeError, ValueError):
        power = None
    return {
        "brand": listing.get("brand_name") or "",
        "model": listing.get("model_name") or "",
        "year": listing.get("year"),
        "fuel": normalize_fuel(listing.get("fuel_type")),
        "displacement_cc": cc or _litres_interval(version, description),
        # One line: the match regexes anchor at ^ and use '.', which stops at newlines.
        "label": " ".join(f"{version} {description}".split()),
        "transmission": " ".join(f"{listing.get('transmission') or ''} {version}".split()),
        "power_hp": power,
    }


_cache: dict = {}


def _issues_for_product() -> list[dict]:
    """Approved entries (plus drafts when the local preview flag is set),
    re-read when the seed file changes."""
    drafts = os.getenv(_INCLUDE_DRAFTS_ENV, "").lower() in ("1", "true", "yes")
    key = (SEED_PATH.stat().st_mtime, drafts)
    if _cache.get("key") != key:
        _cache["issues"] = [i for i in load_issues(SEED_PATH, include_drafts=drafts) if not validate(i)]
        _cache["key"] = key
    return _cache["issues"]


def match_listing(listing: dict, issues: list[dict] | None = None) -> list[dict]:
    """Curated issues that apply to this listing. Needs the car's year — an
    issue is only shown for the production years it affects."""
    p = listing_engine_profile(listing)
    try:
        year = int(p["year"]) if p["year"] else None
    except (TypeError, ValueError):
        year = None
    if year is None:
        return []
    pool = _issues_for_product() if issues is None else issues
    out = []
    for i in pool:
        if not applies_to_year(i, year):
            continue
        if matches_engine(i, brand=p["brand"], model=p["model"], label=p["label"], fuel=p["fuel"],
                          displacement_cc=p["displacement_cc"], transmission=p["transmission"],
                          power_hp=p["power_hp"]):
            out.append(i)
    # Red first
    return sorted(out, key=lambda i: i["severity"] != "critico")


def _eur(r) -> str | None:
    if not r:
        return None
    return f"{r[0]:,}–{r[1]:,} €".replace(",", ".")


def to_payload(issue: dict) -> dict:
    """Shape for the API (DealbreakerIssue + curated extras)."""
    lo, hi = issue["years"]
    cost = issue.get("cost_eur") or {}
    prev, fail = _eur(cost.get("preventive")), _eur(cost.get("failure"))
    cost_txt = " · ".join(x for x in (f"preventivo {prev}" if prev else None,
                                      f"se falhar {fail}" if fail else None) if x)
    return {
        "id": issue["id"],
        "curated": True,
        "severity": issue["severity"],
        "component": issue["component"],
        "engine": issue["name"],
        "problem": issue["problem"],
        "description": issue["detail"],
        "check": issue["check"],
        "mitigation": issue.get("mitigation"),
        "affected_years": f"{lo}–{hi}",
        "fix_cost_estimate": cost_txt or None,
        "source": f"{len(issue['sources'])} fontes verificadas",
        "sources": [{"label": s["label"], "url": s["url"]} for s in issue["sources"]],
    }


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
