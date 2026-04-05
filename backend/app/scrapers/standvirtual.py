"""
Caractr — Standvirtual scraper
Fetches used car listings for a given model search.

Usage:
    listings = asyncio.run(fetch_listings("BMW", "Serie 3", budget_max=30000, max_results=20))

Rate limiting: 2–3s delays, rotating user-agents.
Results cached in raw_listings table (refresh if scraped_at > 24h).
"""

import httpx
import asyncio
import re
import json
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Optional

try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False


async def _render_page(url: str, wait_selector: str, timeout: int = 12000) -> str:
    """Launch headless Chromium, wait for selector to appear, return rendered HTML."""
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


def _build_search_url(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> str:
    brand_slug = BRAND_SLUGS.get(brand, brand.lower().replace(" ", "-").replace("-benz", ""))
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

            # Price
            price = None
            for sel in ["[class*='price']", "strong", "[data-price]"]:
                p = card.select_one(sel)
                if p:
                    price = _parse_price(p.get_text(strip=True))
                    if price:
                        break

            # Rendered HTML: SV uses "29 990 EUR" format with obfuscated class names.
            # Fall back to scanning all short text nodes that contain EUR or €.
            if not price:
                for tag in card.find_all(True):
                    t = tag.get_text(strip=True)
                    if ("EUR" in t or "€" in t) and len(t) < 35 and re.search(r"\d{3}", t):
                        candidate = _parse_price(t)
                        # Sanity check: car prices are 1k–500k
                        if candidate and 1000 <= candidate <= 500000:
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
) -> list[dict]:
    """
    Fetch listings from Standvirtual for a given brand/model.
    Uses Playwright to render JS-heavy search pages so prices are populated.
    Falls back to static httpx if Playwright is not installed.
    year_from / year_to are passed as URL filters so only the correct generation
    is fetched at the source — not filtered after the fact.
    """
    search_url = _build_search_url(brand, model, budget_max, year_from, year_to)

    if _PLAYWRIGHT_AVAILABLE:
        try:
            html = await _render_page(search_url, wait_selector="article[data-id]")
            listings = _extract_listings_from_html(html, search_url)
            return listings[:max_results]
        except Exception as e:
            print(f"[SV SCRAPER] Playwright error: {e}")
            return []

    # Fallback: static HTTP (prices likely None on SV search pages)
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": BASE_URL,
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(1.5, 3.0))
            resp = await client.get(search_url)
            resp.raise_for_status()
            return _extract_listings_from_html(resp.text, search_url)[:max_results]
    except Exception as e:
        print(f"[SV SCRAPER] HTTP fallback error: {e}")
        return []


async def fetch_listing_detail(url: str) -> dict:
    """
    Fetch the detail page of a single listing to extract description and more details.
    Returns a dict with: description, photo_count, seller_type, extras.
    """
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Referer": f"{BASE_URL}/carros",
    }
    result = {"description": "", "photo_count": 0, "seller_type": "desconhecido", "extras": []}
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(2.0, 3.5))
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Description
            for sel in ["[class*='description']", "#description", "[itemprop='description']", "section p"]:
                desc = soup.select_one(sel)
                if desc:
                    result["description"] = desc.get_text("\n", strip=True)[:3000]
                    break

            # Photos
            imgs = soup.select("img[src*='photo'], img[src*='image'], [class*='gallery'] img")
            result["photo_count"] = len(imgs)

            # Seller type
            page_text = soup.get_text(" ", strip=True).lower()
            if "particular" in page_text or "privado" in page_text:
                result["seller_type"] = "privado"
            elif any(w in page_text for w in ["stand", "dealer", "concessionário"]):
                result["seller_type"] = "stand"

    except Exception as e:
        print(f"[SCRAPER] Detail fetch error for {url}: {e}")

    return result
