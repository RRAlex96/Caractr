"""
Caractr — Scraper dispatcher
Routes fetch calls to the correct scraper based on URL domain.

Native scrapers (optimised, structured-data extraction):
  - standvirtual.com  → scrapers/standvirtual.py
  - olx.pt            → scrapers/olx.py

Generic fallback (works on any website):
  - Any other URL     → scrapers/generic.py
    Uses JSON-LD / schema.org → OpenGraph → microdata → heuristic HTML

Usage:
    detail = await fetch_detail_for_url("https://www.autosapo.pt/...")
    source = detect_source("https://www.standvirtual.com/carros/...")
"""

from urllib.parse import urlparse
from typing import Optional


# ── Native sources (have dedicated scrapers) ─────────────────────────────────

NATIVE_SOURCES = {
    "standvirtual.com": "standvirtual",
    "olx.pt":           "olx",
}

# Known Portuguese dealer/aggregator domains → labelled as "dealer"
# The generic scraper handles all of these — no code needed per site.
KNOWN_DEALER_DOMAINS = {
    "autosapo.pt", "autoscout24.pt", "carsnow.pt", "carsgu.pt",
    "autoclick.pt", "carnext.pt", "flexicar.pt", "soauto.pt",
    "sebe.pt", "autohub.pt", "gruposalvador.pt", "centroauto.pt",
    "caetanoretail.pt", "caetanomoveo.pt", "autogarante.pt",
    "grupojmr.pt", "automotor.pt", "automaster.pt",
}


def detect_source(url: str) -> Optional[str]:
    """
    Return source identifier for a given URL.
    - Known native sources → "standvirtual" | "olx"
    - Known dealer domains → "dealer:<domain>"
    - Any other http(s) URL → "generic"
    - Invalid URL → None
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        host = parsed.netloc.lower().lstrip("www.")
        if not host:
            return None

        # Native scrapers
        for domain, source in NATIVE_SOURCES.items():
            if host == domain or host.endswith(f".{domain}"):
                return source

        # Known dealer domains
        for domain in KNOWN_DEALER_DOMAINS:
            if host == domain or host.endswith(f".{domain}"):
                return f"dealer:{host}"

        # Any other valid URL → generic
        return "generic"

    except Exception:
        return None


def is_supported_url(url: str) -> bool:
    """Any valid http/https URL is now supported via the generic scraper."""
    return detect_source(url) is not None


def get_supported_sources() -> list[str]:
    return list(NATIVE_SOURCES.values()) + ["generic"]


def source_label(source: str) -> str:
    """Human-readable label for a source identifier."""
    if source == "standvirtual":
        return "Standvirtual"
    if source == "olx":
        return "OLX"
    if source and source.startswith("dealer:"):
        domain = source.split(":", 1)[1]
        return domain.replace(".pt", "").replace(".", " ").title()
    return "Anunciante"


# ── Unified detail fetch ─────────────────────────────────────────────────────

async def fetch_detail_for_url(url: str) -> dict:
    """
    Fetch listing detail from the appropriate scraper.
    - standvirtual.com → native standvirtual scraper
    - olx.pt           → native OLX scraper
    - everything else  → generic scraper (JSON-LD → OGP → microdata → heuristic)

    Always returns a dict. Never raises — returns empty dict on total failure.
    """
    source = detect_source(url)

    if source == "standvirtual":
        from app.scrapers.standvirtual import fetch_listing_detail
        return await fetch_listing_detail(url)

    elif source == "olx":
        from app.scrapers.olx import fetch_listing_detail as olx_fetch_detail
        return await olx_fetch_detail(url)

    elif source is not None:
        # Generic: dealer sites, autosapo, autoscout24, any other URL
        from app.scrapers.generic import fetch_listing_detail as generic_fetch
        return await generic_fetch(url)

    else:
        return {"error": "URL inválido. Deve começar com http:// ou https://"}


# ── Unified search ───────────────────────────────────────────────────────────

async def fetch_listings_for_source(
    source: str,
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    max_results: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> list[dict]:
    """
    Fetch search results from a specific source by name.
    source: "standvirtual" | "olx"
    year_from / year_to are baked into the search URL to scope by generation.
    """
    if source == "standvirtual":
        from app.scrapers.standvirtual import fetch_listings
        return await fetch_listings(brand, model, budget_max, max_results, year_from, year_to)

    elif source == "olx":
        from app.scrapers.olx import fetch_listings as olx_fetch
        return await olx_fetch(brand, model, budget_max, max_results, year_from, year_to)

    else:
        raise ValueError(f"Fonte desconhecida: {source}. Opções: standvirtual, olx")


async def fetch_listings_all_sources(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    max_per_source: int = 10,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> list[dict]:
    """
    Fetch from all supported sources concurrently and merge results.
    Deduplicates by source_url.
    year_from / year_to scope both scrapers to the correct generation at the URL level.
    """
    import asyncio

    tasks = [
        fetch_listings_for_source("standvirtual", brand, model, budget_max, max_per_source, year_from, year_to),
        fetch_listings_for_source("olx", brand, model, budget_max, max_per_source, year_from, year_to),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: dict[str, dict] = {}
    for batch in results:
        if isinstance(batch, Exception):
            print(f"[DISPATCHER] Source fetch error: {batch}")
            continue
        for listing in batch:
            url = listing.get("source_url", "")
            if url and url not in merged:
                merged[url] = listing

    return list(merged.values())


# ── Slug extraction for model inference ─────────────────────────────────────

def extract_slugs_from_url(url: str) -> tuple[str, str]:
    """
    Best-effort brand/model slug extraction from a listing URL.

    Standvirtual: /carros/{brand-slug}/{model-slug}/ID...
    OLX: /d/anuncio/{title-with-brand-model}-ID{id}.html
         or /carros-motos-e-barcos/carros/{brand}/{model}/
    Returns (brand_slug, model_slug) — empty strings if not found.
    """
    import re
    source = detect_source(url)
    path = urlparse(url).path.rstrip("/")

    if source == "standvirtual":
        # /carros/bmw/serie-3/ID...
        m = re.search(r"/carros/([^/]+)/([^/]+)(?:/|$)", path)
        if m:
            return m.group(1), m.group(2)

    elif source == "olx":
        # Try /carros-motos-e-barcos/carros/{brand}/{model}/
        m = re.search(r"/carros(?:-motos-e-barcos)?/carros/([^/]+)/([^/]+)", path)
        if m:
            return m.group(1), m.group(2)
        # Fall back to title slug: extract first 2–3 slug segments before -ID
        # OLX IDs can be numeric or alphanumeric: IDxxxxxxx or ID12345
        m = re.search(r"/d/anuncio/([^/]+)-ID[A-Za-z0-9]+", path)
        if m:
            parts = m.group(1).split("-")
            # First token is likely brand, second is model (heuristic)
            return parts[0] if parts else "", parts[1] if len(parts) > 1 else ""

    return "", ""
