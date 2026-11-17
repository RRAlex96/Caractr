"""
Caractr — Standvirtual scraper
Fetches used car listings for a given model search.

Usage:
    listings = asyncio.run(fetch_listings("BMW", "Serie 3", budget_max=30000, max_results=20))

Rate limiting: 2–3s delays, rotating user-agents.
Results cached in raw_listings table (refresh if scraped_at > 24h).
"""

import os
import httpx
import asyncio
import math
import re
import unicodedata
import json
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Optional

from app.scrapers.relay import relay_fetch
from app.scrapers.sv_models import expand_model, find_make, find_model, needs_trim, trim_label
from app.scrapers.sv_series import find_series, find_variant

# Playwright import is lazy — only loaded when fetch_listings actually needs it.
# Importing playwright at module level wastes ~50MB RAM even when unused.
_PLAYWRIGHT_AVAILABLE: Optional[bool] = None  # None = not checked yet


# Playwright is opt-in: it OOMs on small Railway instances. The httpx path
# returns full listings with prices (verified), so it's the default. Set
# ALLOW_PLAYWRIGHT_FALLBACK=true to allow the browser fallback where memory allows.
_ALLOW_PW_FALLBACK = os.getenv("ALLOW_PLAYWRIGHT_FALLBACK", "false").lower() == "true"


def _check_playwright() -> bool:
    if not _ALLOW_PW_FALLBACK:
        return False
    global _PLAYWRIGHT_AVAILABLE
    if _PLAYWRIGHT_AVAILABLE is None:
        try:
            import playwright.async_api  # noqa: F401
            _PLAYWRIGHT_AVAILABLE = True
        except ImportError:
            _PLAYWRIGHT_AVAILABLE = False
    return _PLAYWRIGHT_AVAILABLE


async def _render_page(url: str, wait_selector: str, timeout: int = 12000) -> str:
    """Launch headless Chromium, wait for selector to appear, return rendered HTML."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            locale="pt-PT",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        try:
            await page.wait_for_selector(wait_selector, timeout=timeout)
        except Exception:
            pass  # return whatever rendered so far
        html = await page.content()
        await browser.close()
        return html

# ── User-Agent rotation ──────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

BASE_URL = "https://www.standvirtual.com"
SEARCH_URL = f"{BASE_URL}/carros"

def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _plain_slug(name: str) -> str:
    """A name as a URL slug: no accents, lower case, spaces to hyphens. Only a
    guess — used for a name the site's list does not have."""
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip().lower().replace(" ", "-")


def _make_slug(brand: str) -> str:
    """The site's make id for one of our brand names ("Volkswagen" -> "vw",
    "Citroën" -> "citroen"); a plain slug when the site has no such make."""
    return find_make(brand) or _plain_slug(brand)


def sv_model_slug_for(brand: str, model: str, *texts: Optional[str]) -> Optional[str]:
    """The site's sub-model slug for a car filed under a series ("Serie 3",
    "Classe A"), read from what the listing calls it (title, model as written,
    URL): "BMW 320d Touring" -> "320". None when the model is not a series or
    no sub-model of it is named. See sv_series.find_variant."""
    return find_variant(_make_slug(brand or ""), model, *texts)


def search_needs_trim(brand: str, model: str, model_slug: Optional[str] = None) -> bool:
    """True when the comparables of this car's search must share its trim (the
    MINI hatch: see sv_models). model_slug is the listing's own, when it has one."""
    make = _make_slug(brand or "")
    searched = expand_model(make, model_slug.strip()) if model_slug else find_model(make, model)
    return needs_trim(make, searched)


def is_series_model(brand: str, model: str) -> bool:
    """True when the site files `model` as a series with sub-models."""
    make = _make_slug(brand or "")
    return find_series(make, model) is not None and find_variant(make, model) is None


# Fuel names (ours and the listing pages' own labels) -> the values of the
# site's fuel filter, so the market pool is segmented by fuel at the source (a
# 330e hybrid must never be priced against base diesels). These are the ids the
# site's own filter lists (2026-11): diesel, electric, gaz, gnc, gpl,
# hibride-diesel, hibride-gaz, plugin-hybrid, hidrogen. An id it does not know
# ("petrol", "hybrid") is not an error to the site: the search just comes back
# empty, which is how every petrol and hybrid car lost its live comparison.
_SV_FUEL_VALUES = {
    "diesel": ["diesel"],
    "gasóleo": ["diesel"],
    "gasoleo": ["diesel"],
    "gasolina": ["gaz"],
    "elétrico": ["electric"],
    "eletrico": ["electric"],
    "híbrido": ["hibride-gaz", "hibride-diesel"],
    "hibrido": ["hibride-gaz", "hibride-diesel"],
    "híbrido (gasolina)": ["hibride-gaz"],
    "híbrido (diesel)": ["hibride-diesel"],
    "híbrido (plug-in)": ["plugin-hybrid"],
    "híbrido plug-in": ["plugin-hybrid"],
    "plug-in": ["plugin-hybrid"],
    "gpl": ["gpl"],
    "gnc": ["gnc"],
}


def _sv_fuel_values(fuel_type: Optional[str]) -> list[str]:
    """Values of the site's fuel filter for a fuel name; [] when unknown (the
    search is then not scoped by fuel)."""
    if not fuel_type:
        return []
    f = fuel_type.lower().strip()
    if f in _SV_FUEL_VALUES:
        return list(_SV_FUEL_VALUES[f])
    if "plug" in f:
        return ["plugin-hybrid"]
    if "híbr" in f or "hibr" in f:
        if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
            return ["hibride-diesel"]
        if "gasolina" in f:
            return ["hibride-gaz"]
        return ["hibride-gaz", "hibride-diesel"]
    if "elétr" in f or "eletr" in f:
        return ["electric"]
    if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
        return ["diesel"]
    if "gpl" in f:
        return ["gpl"]
    if "gasolina" in f:
        return ["gaz"]
    return []


def _build_search_url(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fuel_type: Optional[str] = None,
    model_slug_override: Optional[str] = None,
    page: int = 1,
    power_range: Optional[tuple] = None,
) -> str:
    brand_slug = _make_slug(brand)
    # Prefer SV's own model slug (from the listing) when provided — it's exact
    # for any model, including ones the site's list does not have yet.
    series_id = None
    if model_slug_override:
        # ... widened when the site files the car under a second id as well.
        model_slug = expand_model(brand_slug, model_slug_override.strip())
    else:
        model_clean = model.strip()
        # A model the site files as a sub-model ("530", "A 180") goes in the
        # path; a series ("Serie 5", "Classe A") only works as a filter.
        model_slug = find_variant(brand_slug, model_clean)
        if not model_slug:
            series_id = find_series(brand_slug, model_clean)
        # Any other model: its id in the site's own list ("XC40" -> "xc-40"),
        # else a plain slug, which the site may not know (the search is then
        # discarded as unscoped, see _search_is_scoped).
        if not model_slug and not series_id:
            model_slug = find_model(brand_slug, model_clean) or _plain_slug(model_clean)
    url = f"{SEARCH_URL}/{brand_slug}" + (f"/{model_slug}" if not series_id else "")
    params = []
    if series_id:
        params.append(f"search[filter_enum_model]={series_id}")
    if budget_max:
        params.append(f"search[filter_float_price:to]={budget_max}")
    # The year filter is the first registration year. "filter_float_year" is
    # accepted and echoed back by the site but filters nothing.
    if year_from:
        params.append(f"search[filter_float_first_registration_year:from]={year_from}")
    if year_to:
        params.append(f"search[filter_float_first_registration_year:to]={year_to}")
    for i, value in enumerate(_sv_fuel_values(fuel_type)):
        params.append(f"search[filter_enum_fuel_type][{i}]={value}")
    # Engine power in cv, (from, to): only listings of about the car's power.
    if power_range:
        params.append(f"search[filter_float_engine_power:from]={int(power_range[0])}")
        params.append(f"search[filter_float_engine_power:to]={int(power_range[1])}")
    # No search[order]: the site's default order ("relevance_web") is kept, so
    # the pages fetched are not skewed towards cheap, recent or low-km cars.
    if page > 1:
        params.append(f"page={page}")
    if params:
        url += "?" + "&".join(params)
    return url


def _parse_price(raw: str) -> Optional[int]:
    """Extract integer price from strings like '18 500 €' or '18.500 €'."""
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def _parse_km(raw: str) -> Optional[int]:
    """Extract integer km from strings like '85 000 km'."""
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def _parse_year(raw: str) -> Optional[int]:
    """Extract year from strings like '2019' or '03/2019'."""
    if not raw:
        return None
    m = re.search(r"(20\d{2}|19\d{2})", raw)
    return int(m.group(1)) if m else None


def _extract_listings_from_html(html: str, source_url: str) -> list[dict]:
    """
    Parse Standvirtual search results HTML.
    Returns list of raw listing dicts.
    Designed to be resilient — handles missing fields gracefully.
    """
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Standvirtual listing cards — primary selector (OLX-based platform)
    # They use article[data-id] or div[data-id] with offer-item class
    cards = (
        soup.select("article[data-id]") or
        soup.select("[data-id]") or
        soup.select(".offer-item") or
        soup.select("article.ooa-1t80gpj") or  # common SV class pattern
        []
    )

    # Fallback: try to find JSON-LD data
    if not cards:
        scripts = soup.find_all("script", type="application/ld+json")
        for sc in scripts:
            try:
                ld = json.loads(sc.string or "")
                if isinstance(ld, dict) and ld.get("@type") == "ItemList":
                    for item in ld.get("itemListElement", []):
                        thing = item.get("item", {})
                        results.append({
                            "source": "standvirtual",
                            "source_url": thing.get("url", ""),
                            "title": thing.get("name", ""),
                            "price": _parse_price(str(thing.get("price", ""))),
                            "year": None,
                            "km": None,
                            "fuel_type": None,
                            "seller_type": None,
                            "location": None,
                            "photo_count": 0,
                            "description": thing.get("description", ""),
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        })
                    if results:
                        return results
            except Exception:
                pass

    for card in cards:
        try:
            # URL
            link_tag = card.select_one("a[href*='/carros/']") or card.select_one("a")
            listing_url = ""
            if link_tag:
                href = link_tag.get("href", "")
                listing_url = href if href.startswith("http") else BASE_URL + href

            # Title
            title = ""
            for sel in ["h3.offer-title", "h2", "h3", "[class*='title']"]:
                t = card.select_one(sel)
                if t:
                    title = t.get_text(strip=True)
                    break

            # Price — prefer a plausible full asking price and skip financing
            # widgets ("desde 199 €/mês", "entrada 2 000 €") that otherwise got
            # picked up as the price (e.g. an M5 listed at "€2.000").
            def _is_financing(txt: str) -> bool:
                t = txt.lower()
                return any(w in t for w in ("/mês", "/mes", "mensal", "mês", "desde", "entrada", "financ"))

            price = None
            for sel in ["[class*='price']", "strong", "[data-price]"]:
                for p in card.select(sel):
                    txt = p.get_text(" ", strip=True)
                    if _is_financing(txt):
                        continue
                    cand = _parse_price(txt)
                    if cand and 1000 <= cand <= 2_000_000:
                        price = cand
                        break
                if price:
                    break

            # Rendered HTML: SV uses "29 990 EUR" format with obfuscated class names.
            # Fall back to scanning all short text nodes that contain EUR or €.
            if not price:
                for tag in card.find_all(True):
                    t = tag.get_text(strip=True)
                    if ("EUR" in t or "€" in t) and len(t) < 35 and re.search(r"\d{3}", t) and not _is_financing(t):
                        candidate = _parse_price(t)
                        # Sanity check: car prices are 1k–2M
                        if candidate and 1000 <= candidate <= 2_000_000:
                            price = candidate
                            break

            # Year and km — in dd elements (rendered) or li/param elements (static)
            year, km, fuel = None, None, None
            detail_items = card.select("dd") or card.select("li") or card.select("[class*='param']")
            for item in detail_items:
                text = item.get_text(strip=True)
                if re.match(r"(20\d{2}|19\d{2})", text):
                    year = _parse_year(text)
                elif "km" in text.lower() and km is None:
                    km = _parse_km(text)
                elif any(f in text.lower() for f in ["gasolina", "diesel", "híbrido", "elétrico", "gás"]):
                    fuel = text.strip()

            # Location
            location = ""
            for sel in ["[class*='location']", "[class*='city']", "[class*='region']"]:
                loc = card.select_one(sel)
                if loc:
                    location = loc.get_text(strip=True)
                    break

            # Seller type
            seller_type = "desconhecido"
            card_text = card.get_text(" ", strip=True).lower()
            if "particular" in card_text or "privado" in card_text:
                seller_type = "privado"
            elif any(w in card_text for w in ["stand", "dealer", "profissional"]):
                seller_type = "stand"

            # Photo count
            photo_count = 0
            img_count = len(card.select("img"))
            photo_count = max(0, img_count - 1)  # subtract 1 for placeholder

            if listing_url and (title or price):
                results.append({
                    "source": "standvirtual",
                    "source_url": listing_url,
                    "title": title,
                    "price": price,
                    "year": year,
                    "km": km,
                    "fuel_type": fuel,
                    "seller_type": seller_type,
                    "location": location,
                    "photo_count": photo_count,
                    "description": "",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            continue

    return results


# A results page holds 32 listings and says how many the whole search has.
# Further pages are requested a moment apart and must all be back inside this
# budget; whatever is missing then is left out.
_PAGE_SIZE = 32
_PAGE_GAP_SECONDS = 0.5
_MORE_PAGES_BUDGET_SECONDS = 20.0

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def _search_data(html: str) -> Optional[dict]:
    """The search behind a results page (the site's `advertSearch` object:
    totalCount, pageInfo, appliedFilters, edges), read from the page's
    __NEXT_DATA__. None when the page does not carry it."""
    m = _NEXT_DATA_RE.search(html or "")
    if not m:
        return None
    try:
        states = json.loads(m.group(1))["props"]["pageProps"]["urqlState"]
        for entry in states.values():
            data = json.loads(entry.get("data") or "null")
            search = data.get("advertSearch") if isinstance(data, dict) else None
            if isinstance(search, dict) and "totalCount" in search:
                return search
    except Exception:
        return None
    return None


def _search_meta(search: dict) -> dict:
    """{"total": results in the whole search, "page_size", "applied": names of
    the filters the site applied}."""
    return {
        "total": int(search.get("totalCount") or 0),
        "page_size": int((search.get("pageInfo") or {}).get("pageSize") or _PAGE_SIZE),
        "applied": {f.get("name") for f in (search.get("appliedFilters") or [])
                    if isinstance(f, dict)},
        # name -> value: since mid-November 2026 the site applies make and model
        # as one filter, make_model_engine_code = "byd|atto-3" (or "byd").
        "applied_values": {f.get("name"): f.get("value") for f in (search.get("appliedFilters") or [])
                           if isinstance(f, dict)},
    }


def applied_make_model(meta: dict) -> tuple:
    """(make, model) the site actually applied to a search; either may be None.
    Reads both the old filters (filter_enum_make / filter_enum_model) and the
    combined make_model_engine_code ("make|model") the site uses now."""
    values = meta.get("applied_values") or {}
    combined = values.get("make_model_engine_code")
    if combined:
        make, _, model = str(combined).partition("|")
        return (make or None), (model.split("|")[0] or None)
    applied = meta.get("applied") or set()
    return (values.get("filter_enum_make") or ("?" if "filter_enum_make" in applied else None),
            values.get("filter_enum_model") or ("?" if "filter_enum_model" in applied else None))


def _search_is_scoped(meta: dict) -> bool:
    """
    True when the site applied both the make and the model of the search path.
    A slug it does not know is dropped without an error: "/carros/volkswagen/golf"
    returned all 17 626 diesel cars on the site, "/carros/mercedes-benz/classe-a"
    every diesel Mercedes. Such a page is full of priced listings of other cars
    and must never be used as comparables.
    """
    make, model = applied_make_model(meta)
    return bool(make and model)


def _card_power_hp(value: str, display: str) -> Optional[int]:
    """Engine power of a search result in cv ("200" / "200 cv"). A value the
    site labels in kW is converted; anything implausible is dropped."""
    m = re.search(r"\d{2,4}", value or display or "")
    if not m:
        return None
    power = int(m.group(0))
    label = (display or "").lower()
    if "kw" in label and "cv" not in label:
        power = round(power * 1.36)
    return power if 30 <= power <= 1200 else None


def _listings_from_search(search: dict) -> list[dict]:
    """
    Listings of a results page from the search data itself, in the shape
    _extract_listings_from_html returns. Exact where the rendered cards are
    not: on about 1 card in 20 the card parser reads another amount on the card
    as the price (1 200 for a car listed at 12 799).
    """
    results = []
    for edge in search.get("edges") or []:
        node = (edge or {}).get("node") or {}
        url = node.get("url") or ""
        if not url:
            continue
        params = {p.get("key"): p for p in (node.get("parameters") or []) if isinstance(p, dict)}

        def value(key: str, field: str = "value") -> str:
            return str((params.get(key) or {}).get(field) or "")

        amount = ((node.get("price") or {}).get("amount") or {})
        price = amount.get("units") if amount.get("currencyCode") == "EUR" else None
        seller = ((node.get("seller") or {}).get("__typename") or "")
        city = (((node.get("location") or {}).get("city") or {}).get("name") or "")
        results.append({
            "source": "standvirtual",
            "source_url": url,
            "title": node.get("title") or "",
            # The site's model of the listing; for a series search, the sub-model.
            "sv_model_slug": value("model") or None,
            "engine_power_hp": _card_power_hp(value("engine_power"), value("engine_power", "displayValue")),
            "price": int(price) if isinstance(price, (int, float)) and price > 0 else None,
            "year": _parse_year(value("first_registration_year")),
            "km": _parse_km(value("mileage")),
            "fuel_type": value("fuel_type", "displayValue") or None,
            "seller_type": ("privado" if seller == "PrivateSeller"
                            else "stand" if seller == "ProfessionalSeller" else "desconhecido"),
            "location": city,
            "photo_count": 0,
            "description": node.get("shortDescription") or "",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return results


def _parse_search_page(html: str, source_url: str) -> tuple:
    """(listings, meta) of one results page. The listings come from the search
    data when the page carries it, else from the rendered cards; meta is None
    when there is no search data (nothing can be checked, no further pages)."""
    search = _search_data(html)
    if search is None:
        return _extract_listings_from_html(html, source_url), None
    meta = _search_meta(search)
    listings = _listings_from_search(search)
    if not listings and meta["total"] > 0:
        listings = _extract_listings_from_html(html, source_url)
    return listings, meta


def _merge_unique(batches: list) -> list[dict]:
    """Listings of several pages in page order, one per listing URL (a listing
    can move between pages while they are being read)."""
    seen: dict = {}
    for batch in batches:
        for listing in batch:
            url = listing.get("source_url") or ""
            if url and url not in seen:
                seen[url] = listing
    return list(seen.values())


async def _fetch_more_pages(client: httpx.AsyncClient, page_urls: list[str]) -> list:
    """Fetch further result pages concurrently, each request starting a moment
    after the previous one. Returns one list of listings per page that came
    back in time; a page that fails or is late is skipped, never raised."""
    async def one(url: str, delay: float) -> list[dict]:
        await asyncio.sleep(delay)
        resp = await client.get(url)
        resp.raise_for_status()
        return _parse_search_page(resp.text, url)[0]

    tasks = [
        asyncio.create_task(one(url, i * _PAGE_GAP_SECONDS + random.uniform(0.2, 0.5)))
        for i, url in enumerate(page_urls)
    ]
    if not tasks:
        return []
    _, pending = await asyncio.wait(tasks, timeout=_MORE_PAGES_BUDGET_SECONDS)
    for task in pending:
        task.cancel()
    batches = []
    for url, task in zip(page_urls, tasks):
        if task in pending:
            print(f"[SV SCRAPER] page not back in {_MORE_PAGES_BUDGET_SECONDS:.0f}s, skipped: {url}")
        elif task.exception() is not None:
            print(f"[SV SCRAPER] page failed, skipped: {url}: {task.exception()}")
        else:
            batches.append(task.result())
    return batches


async def fetch_listings(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    max_results: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fuel_type: Optional[str] = None,
    model_slug: Optional[str] = None,
    max_pages: int = 1,
    power_range: Optional[tuple] = None,
) -> list[dict]:
    """
    Fetch listings from Standvirtual for a given brand/model.
    year_from / year_to / fuel_type are passed as URL filters so only the correct
    generation and fuel variant are fetched. model_slug overrides the model path
    with SV's own slug, so models missing from our map still search correctly.

    power_range, (from, to) in cv, scopes the search to that engine power.

    max_pages > 1 also fetches the following result pages (up to that many in
    all) when the search reports more results than the first page holds.
    Returns [] when the site did not apply the make or the model of the search
    (see _search_is_scoped): no comparables is better than other cars'.
    """
    def page_url(page: int) -> str:
        return _build_search_url(brand, model, budget_max, year_from, year_to,
                                 fuel_type, model_slug, page, power_range)

    search_url = page_url(1)

    # httpx-first: SV search pages embed the full search result in the static
    # HTML (__NEXT_DATA__, and the rendered cards) — no JS needed. This avoids
    # Playwright's memory cost.
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": BASE_URL,
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(0.4, 1.2))
            resp = await client.get(search_url)
            resp.raise_for_status()
            listings, meta = _parse_search_page(resp.text, search_url)
            if meta is not None and not _search_is_scoped(meta):
                print(f"[SV SCRAPER] make/model not recognised by the site, results discarded: {search_url}")
                return []
            if meta is not None and meta["total"] == 0:
                return []
            if listings:
                if meta is not None and max_pages > 1 and meta["total"] > meta["page_size"]:
                    pages_in_search = math.ceil(meta["total"] / meta["page_size"])
                    more = await _fetch_more_pages(
                        client, [page_url(p) for p in range(2, min(max_pages, pages_in_search) + 1)])
                    listings = _merge_unique([listings, *more])
                    print(f"[SV SCRAPER] {meta['total']} results, {1 + len(more)} of "
                          f"{pages_in_search} pages -> {len(listings)} listings")
                return listings[:max_results]
    except Exception as e:
        print(f"[SV SCRAPER] httpx error: {e}")

    # Optional Playwright fallback — off by default (OOMs on small instances).
    if _check_playwright():
        try:
            html = await _render_page(search_url, wait_selector="article[data-id]")
            return _extract_listings_from_html(html, search_url)[:max_results]
        except Exception as e:
            print(f"[SV SCRAPER] Playwright fallback error: {e}")

    return []


def _extract_next_data_advert(html: str) -> Optional[dict]:
    """
    Standvirtual uses Next.js. Detail pages embed the full ad object in
    <script id="__NEXT_DATA__"> as server-side props — no JS execution needed.
    Returns the 'advert' dict, or None if not a detail page / parse error.
    """
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return None
    try:
        data = json.loads(tag.string)
        return data["props"]["pageProps"].get("advert")
    except Exception:
        return None


def _param_val(params_dict: dict, key: str) -> str:
    """Extract first value label from SV parametersDict entry."""
    entry = params_dict.get(key, {})
    values = entry.get("values", [])
    return values[0].get("value", "") if values else ""


def _param_label(params_dict: dict, key: str) -> str:
    """Extract first value label (human-readable) from SV parametersDict entry."""
    entry = params_dict.get(key, {})
    values = entry.get("values", [])
    return values[0].get("label", "") if values else ""


# ── Data quality scoring ────────────────────────────────────────────────────
# Tracks extraction health so we can detect when __NEXT_DATA__ degrades.

_CRITICAL_FIELDS = ["brand", "model", "price", "year", "km"]
_IMPORTANT_FIELDS = ["fuel_type", "engine_power_hp", "seller_type"]
_NICE_FIELDS = ["colour", "transmission", "description", "photo_count"]


def _compute_data_quality(result: dict) -> dict:
    """
    Score data completeness. Weighted: critical=60%, important=25%, nice=15%.
    Returns dict with score (0.0-1.0), grade (A-F), and missing fields.

    If grade drops below B across multiple scrapes, it signals that the
    primary extraction layer (__NEXT_DATA__) has degraded — time to investigate.
    """
    critical_filled = sum(1 for f in _CRITICAL_FIELDS if result.get(f))
    important_filled = sum(1 for f in _IMPORTANT_FIELDS
                          if result.get(f) and result[f] != "desconhecido")
    nice_filled = sum(1 for f in _NICE_FIELDS
                      if result.get(f) not in (None, "", 0))

    score = (
        (critical_filled / len(_CRITICAL_FIELDS)) * 0.60
        + (important_filled / len(_IMPORTANT_FIELDS)) * 0.25
        + (nice_filled / len(_NICE_FIELDS)) * 0.15
    )

    grade = (
        "A" if score >= 0.85 else
        "B" if score >= 0.70 else
        "C" if score >= 0.50 else
        "D" if score >= 0.30 else
        "F"
    )

    return {
        "score": round(score, 2),
        "grade": grade,
        "critical_filled": f"{critical_filled}/{len(_CRITICAL_FIELDS)}",
        "missing_critical": [f for f in _CRITICAL_FIELDS if not result.get(f)],
    }


# ── Layer 1 helper: parse __NEXT_DATA__ advert ─────────────────────────────

def _parse_advert_data(advert: dict, result: dict) -> None:
    """
    Extract structured fields from SV's __NEXT_DATA__ advert object.
    Only fills fields not already populated (supports layered extraction).
    """
    params = advert.get("parametersDict", {})

    # Brand / Model
    if not result.get("brand"):
        brand = _param_label(params, "make").strip()
        if brand:
            result["brand"] = brand
    if not result.get("model"):
        model = _param_label(params, "model").strip()
        if model:
            result["model"] = model

    # Fallback: infer from title
    if not result.get("brand") and advert.get("title"):
        try:
            from app.scrapers.generic import _infer_brand_model
            b, m = _infer_brand_model(advert["title"])
            if b:
                result["brand"] = b
            if m and not result.get("model"):
                result["model"] = m
        except Exception:
            pass

    # Year
    if not result.get("year"):
        year_raw = _param_val(params, "first_registration_year")
        if year_raw:
            result["year"] = _parse_year(year_raw)

    # Km
    if not result.get("km"):
        km_raw = _param_val(params, "mileage")
        if km_raw:
            result["km"] = _parse_km(km_raw)

    # Price
    if not result.get("price"):
        price_obj = advert.get("price", {}) or {}
        result["price"] = _parse_price(str(price_obj.get("value", "")))

    # Fuel type
    if not result.get("fuel_type"):
        fuel = _param_label(params, "fuel_type")
        if fuel:
            result["fuel_type"] = fuel

    # Engine power — read the unit from the human label so we convert correctly.
    # SV may store the value in cv or kW depending on the field; blindly treating
    # it as kW (×1.36) inflated cv values by 36%. The label looks like "190 cv"
    # or "140 kW" — detect and convert only when it's really kW.
    if not result.get("engine_power_hp"):
        power_label = _param_label(params, "engine_power") or ""
        power_val = _param_val(params, "engine_power") or ""
        src = power_label if re.search(r"\d", power_label) else str(power_val)
        m = re.search(r"(\d{2,4})", src)
        if m:
            try:
                num = int(m.group(1))
                is_kw = "kw" in src.lower() and "cv" not in src.lower()
                hp = round(num * 1.36) if is_kw else num
                if 30 <= hp <= 1200:
                    result["engine_power_hp"] = hp
            except (ValueError, TypeError):
                pass

    # SV's own make/model slugs — used to search the EXACT model market even
    # when it isn't in our DB (e.g. 'velar'), and version/displacement for
    # trim analysis + IUC. These never hurt; they only enrich.
    if not result.get("sv_model_slug"):
        result["sv_model_slug"] = (_param_val(params, "model") or "").strip()
    if not result.get("version"):
        result["version"] = (_param_label(params, "version") or "").strip()
    if not result.get("engine_displacement_cc"):
        cap = _param_val(params, "engine_capacity") or _param_label(params, "engine_capacity")
        if cap:
            digits = re.sub(r"[^\d]", "", str(cap))
            if digits and 600 <= int(digits) <= 8000:
                result["engine_displacement_cc"] = int(digits)

    # Transmission
    if not result.get("transmission"):
        gearbox = _param_label(params, "gearbox")
        if gearbox:
            result["transmission"] = gearbox

    # Colour
    if not result.get("colour"):
        colour = _param_label(params, "colour")
        if colour:
            result["colour"] = colour

    # Seller type
    if result.get("seller_type") in (None, "desconhecido"):
        seller = advert.get("seller", {}) or {}
        seller_type_raw = seller.get("type", "").upper()
        if seller_type_raw == "PRIVATE":
            result["seller_type"] = "privado"
        elif seller_type_raw == "PROFESSIONAL":
            result["seller_type"] = "stand"

    # Photos
    if not result.get("photo_count"):
        photos = (advert.get("images") or {}).get("photos", [])
        result["photo_count"] = len(photos)

    # Description
    if not result.get("description"):
        desc_raw = advert.get("description", "") or ""
        try:
            result["description"] = BeautifulSoup(
                desc_raw, "lxml"
            ).get_text("\n", strip=True)[:3000]
        except Exception:
            result["description"] = re.sub(
                r"<[^>]+>", " ", desc_raw
            ).strip()[:3000]

    # Title (used for brand/model inference in later layers)
    if not result.get("title"):
        result["title"] = advert.get("title", "")

    # Listing age
    if not result.get("listing_age_days"):
        created_at = advert.get("createdAt") or advert.get("originalCreatedAt")
        if created_at:
            try:
                created = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                )
                age_days = (datetime.now(timezone.utc) - created).days
                result["listing_age_days"] = age_days
            except Exception:
                pass


# ── Main detail extractor: 5-layer resilient pipeline ──────────────────────

async def fetch_listing_detail(url: str) -> dict:
    """
    Multi-layer resilient extraction for Standvirtual detail pages.

    If __NEXT_DATA__ breaks tomorrow, data still flows through 4 fallback layers.
    Each layer only fills fields not already populated by a higher-priority layer.

    Layer 1: __NEXT_DATA__ SSR JSON (SV-specific, fastest, most complete)
    Layer 2: JSON-LD structured data + OpenGraph meta tags
    Layer 3: HTML semantic extraction (microdata, price/year/km patterns)
    Layer 4: Portuguese label-value text patterns (dt/dd, regex)
    Layer 5: Playwright render + re-extract all layers (nuclear option)

    Tracks extraction provenance and computes data quality score so we can
    detect degradation — if __NEXT_DATA__ starts failing, the dashboard
    will show quality dropping from A to B/C across scrapes.
    """
    result: dict = {
        "brand": "", "model": "", "year": None, "km": None, "price": None,
        "fuel_type": None, "engine_power_hp": None, "transmission": None,
        "colour": None, "description": "", "photo_count": 0,
        "seller_type": "desconhecido",
    }
    _layers_used: list[str] = []

    # ── Fetch HTML ─────────────────────────────────────────────────────────────
    # Browser-like headers + a few retries with fresh UAs — datacenter IPs
    # (Railway) get intermittently bot-challenged, so a single attempt drops
    # otherwise-valid pages. Retrying with backoff recovers most of them.
    def _headers() -> dict:
        return {
            "User-Agent": _random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Referer": f"{BASE_URL}/carros",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive",
        }

    html = ""
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15.0, headers=_headers()
            ) as client:
                await asyncio.sleep(random.uniform(0.6, 1.6) * (attempt + 1))
                resp = await client.get(url)
                # 404/410 = listing sold/removed — permanent, don't retry.
                if resp.status_code in (404, 410):
                    print(f"[SV] Listing gone ({resp.status_code}) for {url}")
                    result["_extraction_method"] = "listing_gone"
                    result["_gone"] = True
                    result["_data_quality"] = _compute_data_quality(result)
                    return result
                if resp.status_code == 403:
                    # Our server's address is refused outright; retrying from
                    # it won't help — the relay below fetches from elsewhere.
                    last_err = "403 Forbidden"
                    print(f"[SV] 403 for {url}")
                    break
                resp.raise_for_status()
                html = resp.text
            if html:
                break
        except Exception as e:
            last_err = e
            print(f"[SV] fetch attempt {attempt + 1}/3 failed for {url}: {e}")

    if not html:
        html = await relay_fetch(url) or ""

    if not html:
        print(f"[SV] FETCH FAILED for {url}: {last_err}")
        result["_extraction_method"] = "fetch_failed"
        result["_extraction_layers"] = ["fetch:FAILED"]
        result["_data_quality"] = _compute_data_quality(result)
        return result

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 1: __NEXT_DATA__ (SV-specific SSR JSON — the gold standard)
    # ══════════════════════════════════════════════════════════════════════════
    advert = _extract_next_data_advert(html)
    if advert:
        _parse_advert_data(advert, result)
        filled = [f for f in _CRITICAL_FIELDS if result.get(f)]
        _layers_used.append(f"L1:next_data({len(filled)}/5)")
        print(f"[SV] L1 __NEXT_DATA__ OK: {len(filled)}/5 critical fields "
              f"({result.get('brand')} {result.get('model')})")
    else:
        _layers_used.append("L1:next_data:FAILED")
        print(f"[SV] L1 __NEXT_DATA__ FAILED for {url}")

    # ── Check: are critical fields complete? ──
    _missing = [f for f in _CRITICAL_FIELDS if not result.get(f)]
    if not _missing:
        # All critical fields filled by Layer 1 — skip fallbacks
        result["_extraction_method"] = "next_data"
        result["_extraction_layers"] = _layers_used
        result["_data_quality"] = _compute_data_quality(result)
        quality = result["_data_quality"]
        print(f"[SV] DONE (L1 only): {result['brand']} {result['model']} "
              f"{result['year']} {result['km']}km EUR{result['price']} "
              f"| quality={quality['grade']}({quality['score']})")
        return result

    # ══════════════════════════════════════════════════════════════════════════
    # LAYERS 2-4: Generic extraction pipeline (fallback when __NEXT_DATA__
    # is missing or incomplete). Reuses battle-tested code from generic.py.
    # ══════════════════════════════════════════════════════════════════════════
    print(f"[SV] Missing critical: {_missing} — activating fallback layers")

    soup = BeautifulSoup(html, "lxml")
    page_text = soup.get_text(" ", strip=True)

    # Lazy import — only when fallbacks are needed
    from app.scrapers.generic import (
        _extract_jsonld, _extract_meta, _extract_microdata,
        _extract_heuristic, _extract_dt_dd, _extract_pt_labels,
        _infer_brand_model,
    )

    # ── Layer 2: JSON-LD + OpenGraph meta ──────────────────────────────────
    layer2_fills: list[str] = []
    jsonld = _extract_jsonld(soup)
    for k, v in jsonld.items():
        if v and not result.get(k):
            result[k] = v
            layer2_fills.append(k)
    meta = _extract_meta(soup)
    for k, v in meta.items():
        if v and not result.get(k):
            result[k] = v
            layer2_fills.append(k)
    if layer2_fills:
        _layers_used.append(f"L2:jsonld_meta({layer2_fills})")
        print(f"[SV] L2 JSON-LD+meta filled: {layer2_fills}")

    # ── Layer 3: HTML heuristic + Microdata ────────────────────────────────
    _missing = [f for f in _CRITICAL_FIELDS if not result.get(f)]
    if _missing:
        layer3_fills: list[str] = []
        micro = _extract_microdata(soup)
        for k, v in micro.items():
            if v and not result.get(k):
                result[k] = v
                layer3_fills.append(k)
        heuristic = _extract_heuristic(soup, page_text)
        for k, v in heuristic.items():
            if v and not result.get(k):
                result[k] = v
                layer3_fills.append(k)
        if layer3_fills:
            _layers_used.append(f"L3:heuristic({layer3_fills})")
            print(f"[SV] L3 heuristic filled: {layer3_fills}")

    # ── Layer 4: Portuguese label-value patterns + dt/dd ───────────────────
    _missing = [f for f in _CRITICAL_FIELDS if not result.get(f)]
    if _missing:
        before_keys = {k for k, v in result.items() if v}
        _extract_dt_dd(soup, result)
        _extract_pt_labels(page_text, result)
        layer4_fills = [k for k, v in result.items()
                        if v and k not in before_keys]
        if layer4_fills:
            _layers_used.append(f"L4:pt_labels({layer4_fills})")
            print(f"[SV] L4 PT patterns filled: {layer4_fills}")

    # Infer brand/model from title if still missing
    if not result.get("brand"):
        title = result.get("title") or ""
        if title:
            b, m = _infer_brand_model(title)
            if b:
                result["brand"] = b
            if m and not result.get("model"):
                result["model"] = m

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 5: Playwright render + re-extract (nuclear option)
    # Only fires if 3+ critical fields still missing — rendering is expensive.
    # ══════════════════════════════════════════════════════════════════════════
    _missing = [f for f in _CRITICAL_FIELDS if not result.get(f)]
    if len(_missing) >= 3 and _check_playwright():
        print(f"[SV] L5 Playwright: {len(_missing)} critical still missing, "
              f"rendering {url}")
        try:
            pw_html = await _render_page(
                url, wait_selector="[data-testid='ad-price']"
            )
            if pw_html and len(pw_html) > len(html):
                html = pw_html
                soup = BeautifulSoup(html, "lxml")
                page_text = soup.get_text(" ", strip=True)

                # Re-try __NEXT_DATA__ on rendered HTML (sometimes appears
                # after client-side hydration)
                advert = _extract_next_data_advert(html)
                if advert:
                    _parse_advert_data(advert, result)
                    _layers_used.append("L5:playwright+next_data")
                else:
                    # Run generic layers on rendered HTML
                    from app.scrapers.generic import _run_extraction_layers
                    _run_extraction_layers(soup, page_text, result)
                    _layers_used.append("L5:playwright+generic")

                print(f"[SV] L5 Playwright rendered: "
                      f"price={result.get('price')} "
                      f"year={result.get('year')} "
                      f"km={result.get('km')}")
        except Exception as e:
            _layers_used.append(f"L5:playwright:FAILED({e})")
            print(f"[SV] L5 Playwright FAILED: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # Extraction metadata + data quality score
    # ══════════════════════════════════════════════════════════════════════════
    primary = (
        "next_data" if any("L1:next_data(" in l for l in _layers_used)
        else "fallback" if len(_layers_used) > 1
        else "failed"
    )
    result["_extraction_method"] = primary
    result["_extraction_layers"] = _layers_used
    result["_data_quality"] = _compute_data_quality(result)

    quality = result["_data_quality"]
    print(f"[SV] DONE: {result.get('brand')} {result.get('model')} "
          f"{result.get('year')} {result.get('km')}km "
          f"EUR{result.get('price')} "
          f"| quality={quality['grade']}({quality['score']}) "
          f"| layers={[l.split('(')[0] for l in _layers_used]}"
          f"| missing={quality['missing_critical']}")
    return result
