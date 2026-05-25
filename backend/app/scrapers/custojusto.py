"""
Caractr — CustoJusto scraper
Second-largest Portuguese marketplace after Standvirtual.
Heavy on private sellers — great for real market prices.

Search results require Playwright (prices render client-side).
Detail pages work with static httpx (JSON-LD + microdata available).

Usage:
    listings = asyncio.run(fetch_listings("Renault", "Clio", max_results=20))
"""

import httpx
import asyncio
import re
import json
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Optional

# Lazy Playwright import — same pattern as standvirtual.py
_PLAYWRIGHT_AVAILABLE: Optional[bool] = None


def _check_playwright() -> bool:
    global _PLAYWRIGHT_AVAILABLE
    if _PLAYWRIGHT_AVAILABLE is None:
        try:
            import playwright.async_api  # noqa: F401
            _PLAYWRIGHT_AVAILABLE = True
        except ImportError:
            _PLAYWRIGHT_AVAILABLE = False
    return _PLAYWRIGHT_AVAILABLE


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

BASE_URL = "https://www.custojusto.pt"

# CustoJusto brand slugs (lowercase, no accents)
BRAND_SLUGS = {
    "BMW": "bmw", "Mercedes-Benz": "mercedes-benz", "Audi": "audi",
    "Volkswagen": "volkswagen", "Toyota": "toyota", "Honda": "honda",
    "Mazda": "mazda", "Volvo": "volvo", "Peugeot": "peugeot",
    "Renault": "renault", "Ford": "ford", "Opel": "opel",
    "SEAT": "seat", "Skoda": "skoda", "Hyundai": "hyundai",
    "Kia": "kia", "Fiat": "fiat", "Dacia": "dacia",
    "Citroen": "citroen", "Nissan": "nissan", "Alfa Romeo": "alfa-romeo",
    "MINI": "mini", "Tesla": "tesla", "Porsche": "porsche",
    "Land Rover": "land-rover", "Suzuki": "suzuki", "Subaru": "subaru",
    "Cupra": "cupra", "MG": "mg", "Lexus": "lexus",
}

MODEL_SLUGS = {
    "Serie 3": "serie-3", "Serie 5": "serie-5",
    "Classe A": "classe-a", "Classe C": "classe-c", "Classe E": "classe-e",
    "Golf": "golf", "Polo": "polo", "Passat": "passat", "Tiguan": "tiguan",
    "Corolla": "corolla", "Yaris": "yaris", "RAV4": "rav4",
    "Civic": "civic", "CR-V": "cr-v", "CX-5": "cx-5",
    "XC60": "xc60", "308": "308", "3008": "3008", "208": "208",
    "Clio": "clio", "Megane": "megane", "Captur": "captur",
    "Focus": "focus", "Astra": "astra", "Leon": "leon",
    "Octavia": "octavia", "Tucson": "tucson", "Sportage": "sportage",
    "Duster": "duster", "Sandero": "sandero",
    "A3": "a3", "A4": "a4", "Q5": "q5",
}


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _build_search_url(
    brand: str,
    model: str,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> str:
    """
    Build CustoJusto search URL.
    Format: /portugal/carros/[brand]/[model]
    Year filters: rs=YYYY (from), re=YYYY (to)
    """
    brand_slug = BRAND_SLUGS.get(brand, brand.lower().replace(" ", "-"))
    model_clean = model.strip()
    model_slug = MODEL_SLUGS.get(model_clean, model_clean.lower().replace(" ", "-"))

    url = f"{BASE_URL}/portugal/carros/{brand_slug}/{model_slug}"
    params = []
    if year_from:
        params.append(f"rs={year_from}")
    if year_to:
        params.append(f"re={year_to}")
    if params:
        url += "?" + "&".join(params)
    return url


def _parse_price(raw: str) -> Optional[int]:
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", raw)
    price = int(digits) if digits else None
    if price and 500 <= price <= 500_000:
        return price
    return None


def _parse_km(raw: str) -> Optional[int]:
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def _parse_year(raw: str) -> Optional[int]:
    if not raw:
        return None
    m = re.search(r"(20\d{2}|19\d{2})", raw)
    return int(m.group(1)) if m else None


def _extract_listings_from_html(html: str) -> list[dict]:
    """
    Parse CustoJusto search results HTML.
    CJ uses a card-based layout with price, title, location, and details.
    """
    soup = BeautifulSoup(html, "lxml")
    results = []

    # CJ listing cards — try multiple selectors
    cards = (
        soup.select("[data-testid='listing-card']")
        or soup.select("a[href*='/carros/']")
        or soup.select(".listing-card")
        or soup.select("[class*='ContentItem']")
        or []
    )

    # Also try JSON-LD for structured results
    if not cards:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                ld = json.loads(script.string or "")
                if isinstance(ld, dict) and ld.get("@type") == "ItemList":
                    for item in ld.get("itemListElement", []):
                        thing = item.get("item", {})
                        price = _parse_price(str(thing.get("price", "")))
                        if price:
                            results.append({
                                "source": "custojusto",
                                "source_url": thing.get("url", ""),
                                "title": thing.get("name", ""),
                                "price": price,
                                "year": None,
                                "km": None,
                                "fuel_type": None,
                                "seller_type": "desconhecido",
                                "location": "",
                                "photo_count": 0,
                                "description": thing.get("description", ""),
                                "scraped_at": datetime.now(timezone.utc).isoformat(),
                            })
                    if results:
                        return results
            except Exception:
                pass

    seen_urls: set[str] = set()

    for card in cards:
        try:
            # URL
            link = card if card.name == "a" else card.select_one("a[href]")
            if not link:
                continue
            href = link.get("href", "")
            listing_url = href if href.startswith("http") else BASE_URL + href
            if not listing_url or listing_url in seen_urls:
                continue
            if "/carros/" not in listing_url and "/veiculos/" not in listing_url:
                continue
            seen_urls.add(listing_url)

            # Title
            title = ""
            for sel in ["h2", "h3", "[class*='title']", "[class*='Title']"]:
                t = card.select_one(sel)
                if t:
                    title = t.get_text(strip=True)
                    break
            if not title:
                title = link.get_text(strip=True)[:100]

            # Price — CJ renders prices in spans/divs with EUR or €
            price = None
            for tag in card.find_all(True):
                text = tag.get_text(strip=True)
                if ("EUR" in text or "€" in text) and len(text) < 35:
                    candidate = _parse_price(text)
                    if candidate:
                        price = candidate
                        break

            # Year / km / fuel from detail text
            year, km, fuel = None, None, None
            card_text = card.get_text(" ", strip=True)
            # Year: 4-digit year
            y_match = re.search(r"\b(19\d{2}|20\d{2})\b", card_text)
            if y_match:
                year = int(y_match.group(1))
            # Km: number followed by "km"
            km_match = re.search(r"([\d\s.]+)\s*km\b", card_text, re.IGNORECASE)
            if km_match:
                km = _parse_km(km_match.group(1))
            # Fuel
            for f_label in ["gasolina", "diesel", "eletrico", "hibrido", "gpl"]:
                if f_label in card_text.lower():
                    fuel = f_label
                    break

            # Location
            location = ""
            for sel in ["[class*='location']", "[class*='Location']", "small"]:
                loc = card.select_one(sel)
                if loc:
                    location = loc.get_text(strip=True)
                    break

            if listing_url and (title or price):
                results.append({
                    "source": "custojusto",
                    "source_url": listing_url,
                    "title": title,
                    "price": price,
                    "year": year,
                    "km": km,
                    "fuel_type": fuel,
                    "seller_type": "desconhecido",
                    "location": location,
                    "photo_count": 0,
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
    Fetch listings from CustoJusto for a given brand/model.
    Uses Playwright to render JS-heavy search pages.
    Falls back to static httpx (prices may be missing).
    """
    search_url = _build_search_url(brand, model, year_from, year_to)

    if _check_playwright():
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(
                    locale="pt-PT",
                    user_agent=_random_ua(),
                )
                page = await ctx.new_page()
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                # Wait for listing cards to render
                try:
                    await page.wait_for_selector(
                        "a[href*='/carros/'], [data-testid='listing-card']",
                        timeout=10000,
                    )
                except Exception:
                    pass
                # Small delay to let prices render
                await asyncio.sleep(1.5)
                html = await page.content()
                await browser.close()

            listings = _extract_listings_from_html(html)
            print(f"[CJ SCRAPER] Playwright: {len(listings)} listings for {brand} {model}")
            return listings[:max_results]
        except Exception as e:
            print(f"[CJ SCRAPER] Playwright error: {e}")

    # Fallback: static HTTP (prices likely missing)
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Referer": BASE_URL,
    }
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=15.0, headers=headers
        ) as client:
            await asyncio.sleep(random.uniform(1.5, 3.0))
            resp = await client.get(search_url)
            resp.raise_for_status()
            listings = _extract_listings_from_html(resp.text)
            print(f"[CJ SCRAPER] Static: {len(listings)} listings for {brand} {model}")
            return listings[:max_results]
    except Exception as e:
        print(f"[CJ SCRAPER] HTTP fallback error: {e}")
        return []
