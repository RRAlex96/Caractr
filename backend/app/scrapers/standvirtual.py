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
import re
import json
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Optional

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

# Brand slug mappings (Standvirtual uses lowercase slugs)
BRAND_SLUGS = {
    "BMW": "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Audi": "audi",
    "Volkswagen": "volkswagen",
    "Toyota": "toyota",
    "Honda": "honda",
    "Mazda": "mazda",
    "Volvo": "volvo",
    "Peugeot": "peugeot",
    "Renault": "renault",
    "Ford": "ford",
    "Opel": "opel",
    "SEAT": "seat",
    "Skoda": "skoda",
    "Hyundai": "hyundai",
    "Kia": "kia",
    "Fiat": "fiat",
    "Dacia": "dacia",
    "Citroen": "citroen",
    "Nissan": "nissan",
    "Alfa Romeo": "alfa-romeo",
    "MINI": "mini",
    "Cupra": "cupra",
    "Tesla": "tesla",
    "Subaru": "subaru",
    "Suzuki": "suzuki",
    "Land Rover": "land-rover",
    "Porsche": "porsche",
    "Lexus": "lexus",
    "MG": "mg",
}

# Model slug mappings for common models
MODEL_SLUGS = {
    "Serie 3": "serie-3",
    "Serie 5": "serie-5",
    "Classe A": "classe-a",
    "Classe C": "classe-c",
    "Classe E": "classe-e",
    "Golf": "golf",
    "Passat": "passat",
    "Polo": "polo",
    "Tiguan": "tiguan",
    "Corolla": "corolla",
    "Yaris": "yaris",
    "RAV4": "rav4",
    "Civic": "civic",
    "CR-V": "cr-v",
    "CX-5": "cx-5",
    "XC60": "xc60",
    "308": "308",
    "3008": "3008",
    "Clio": "clio",
    "Megane": "megane",
    "Focus": "focus",
    "Astra": "astra",
    "Leon": "leon",
    "Octavia": "octavia",
    "i30": "i30",
    "Tucson": "tucson",
    "Ceed": "ceed",
    "Sportage": "sportage",
    "Panda": "panda",
    "Duster": "duster",
    "A3": "a3",
    "A4": "a4",
    "Q5": "q5",
    "Giulia": "giulia",
}


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


# Map our canonical fuel names to Standvirtual's fuel-filter enum values, so the
# market pool is segmented by fuel at the source (a 330e hybrid must never be
# priced against base diesels).
_SV_FUEL_ENUM = {
    "diesel": "diesel",
    "gasolina": "petrol",
    "gasóleo": "diesel",
    "gasoleo": "diesel",
    "elétrico": "electric",
    "eletrico": "electric",
    "híbrido": "hybrid",
    "hibrido": "hybrid",
    "híbrido (plug-in)": "plugin-hybrid",
    "híbrido plug-in": "plugin-hybrid",
    "plug-in": "plugin-hybrid",
    "gpl": "petrol-lpg",
}


def _sv_fuel_slug(fuel_type: Optional[str]) -> Optional[str]:
    if not fuel_type:
        return None
    f = fuel_type.lower().strip()
    if f in _SV_FUEL_ENUM:
        return _SV_FUEL_ENUM[f]
    if "plug" in f:
        return "plugin-hybrid"
    if "híbr" in f or "hibr" in f:
        return "hybrid"
    if "elétr" in f or "eletr" in f:
        return "electric"
    if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
        return "diesel"
    if "gpl" in f:
        return "petrol-lpg"
    if "gasolina" in f:
        return "petrol"
    return None


def _build_search_url(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fuel_type: Optional[str] = None,
    model_slug_override: Optional[str] = None,
) -> str:
    brand_slug = BRAND_SLUGS.get(brand, brand.lower().replace(" ", "-").replace("-benz", ""))
    # Prefer SV's own model slug (from the listing) when provided — it's exact
    # for any model, including ones not in our MODEL_SLUGS map (e.g. 'velar').
    if model_slug_override:
        model_slug = model_slug_override.strip()
    else:
        model_clean = model.strip()
        model_slug = MODEL_SLUGS.get(model_clean, model_clean.lower().replace(" ", "-"))
    url = f"{SEARCH_URL}/{brand_slug}/{model_slug}"
    params = []
    if budget_max:
        params.append(f"search[filter_float_price:to]={budget_max}")
    if year_from:
        params.append(f"search[filter_float_year:from]={year_from}")
    if year_to:
        params.append(f"search[filter_float_year:to]={year_to}")
    fuel_slug = _sv_fuel_slug(fuel_type)
    if fuel_slug:
        params.append(f"search[filter_enum_fuel_type][0]={fuel_slug}")
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


async def fetch_listings(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    max_results: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fuel_type: Optional[str] = None,
    model_slug: Optional[str] = None,
) -> list[dict]:
    """
    Fetch listings from Standvirtual for a given brand/model.
    Uses Playwright to render JS-heavy search pages so prices are populated.
    Falls back to static httpx if Playwright is not installed.
    year_from / year_to / fuel_type are passed as URL filters so only the correct
    generation and fuel variant are fetched. model_slug overrides the model path
    with SV's own slug, so models missing from our map still search correctly.
    """
    search_url = _build_search_url(brand, model, budget_max, year_from, year_to, fuel_type, model_slug)

    # httpx-first: SV search pages embed full listing data (JSON-LD ItemList +
    # rendered cards) in the static HTML — no JS needed. Verified to return
    # complete samples with prices. This avoids Playwright's memory cost.
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
            listings = _extract_listings_from_html(resp.text, search_url)[:max_results]
            if listings:
                return listings
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
                resp.raise_for_status()
                html = resp.text
            if html:
                break
        except Exception as e:
            last_err = e
            print(f"[SV] fetch attempt {attempt + 1}/3 failed for {url}: {e}")

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
