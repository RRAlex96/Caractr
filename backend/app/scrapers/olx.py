"""
Caractr — OLX Auto Portugal scraper
Fetches used car listings from olx.pt for a given model search.

OLX URL patterns:
  Search: https://www.olx.pt/carros-motos-e-barcos/carros/q-{query}/
  Detail: https://www.olx.pt/d/anuncio/{slug}-ID{id}.html

Rate limiting: 2–3s delays, rotating user-agents.
OLX also exposes a JSON API embedded in the page (window.__PRELOADED_STATE__) — we prefer that
over HTML parsing since it is more stable.
"""

import httpx
import asyncio
import re
import json
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Optional

# Playwright import is lazy — only loaded when actually needed.
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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

BASE_URL  = "https://www.olx.pt"
SEARCH_URL = f"{BASE_URL}/carros-motos-e-barcos/carros/"


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _build_search_url(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> str:
    """OLX uses a keyword query string in the URL path."""
    query = f"{brand} {model}".strip().replace(" ", "-")
    url = f"{SEARCH_URL}q-{query}/"
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
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", str(raw))
    return int(digits) if digits else None


def _parse_km(raw: str) -> Optional[int]:
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", str(raw))
    return int(digits) if digits else None


def _parse_year(raw: str) -> Optional[int]:
    if not raw:
        return None
    m = re.search(r"(20\d{2}|19\d{2})", str(raw))
    return int(m.group(1)) if m else None


def _extract_preloaded_state(html: str) -> Optional[dict]:
    """
    OLX embeds listing data in a JS variable: window.__PRELOADED_STATE__ = {...}
    This is more reliable than CSS-class HTML parsing.
    """
    m = re.search(r"window\.__PRELOADED_STATE__\s*=\s*(\{.+?\});\s*(?:window|</script>)", html, re.DOTALL)
    if not m:
        # Try alternate pattern
        m = re.search(r"__PRELOADED_STATE__\s*=\s*(\{.+\})", html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def _extract_listings_from_preloaded(state: dict, base_url: str) -> list[dict]:
    """Parse OLX __PRELOADED_STATE__ JSON for listing items."""
    results = []
    # OLX state path: listing.listings.listingArray[]
    listing_array = (
        state.get("listing", {}).get("listing", {}).get("ads", []) or
        state.get("listing", {}).get("listings", {}).get("listingArray", []) or
        []
    )

    for item in listing_array:
        try:
            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = base_url + url

            title = item.get("title", "")
            price_raw = item.get("price", {})
            price = None
            if isinstance(price_raw, dict):
                price = _parse_price(str(price_raw.get("value", {}).get("value", "") or price_raw.get("regularPrice", {}).get("value", "")))
            elif isinstance(price_raw, (int, float)):
                price = int(price_raw)
            else:
                price = _parse_price(str(price_raw))

            # Params: year, km, fuel from structured params list
            params = item.get("params", []) or item.get("parameters", [])
            year, km, fuel = None, None, None
            for p in params:
                key = (p.get("key") or p.get("name", "")).lower()
                val = str(p.get("value", {}).get("label", "") or p.get("value", "") or "")
                if key in ("year", "ano") or "ano" in key:
                    year = _parse_year(val)
                elif key in ("mileage", "km", "quilometragem") or "km" in key:
                    km = _parse_km(val)
                elif key in ("fuel", "combustivel") or "combust" in key:
                    fuel = val

            location_obj = item.get("location", {})
            location = location_obj.get("cityName", "") if isinstance(location_obj, dict) else str(location_obj)

            # Photos
            photo_count = len(item.get("photos", []) or item.get("images", []))

            # Seller type
            user_type = (item.get("user", {}) or {}).get("userType", "").lower()
            seller_type = "privado" if user_type in ("private", "particular") else ("stand" if user_type in ("business", "company", "dealer") else "desconhecido")

            if url and (title or price):
                results.append({
                    "source": "olx",
                    "source_url": url,
                    "title": title,
                    "price": price,
                    "year": year,
                    "km": km,
                    "fuel_type": fuel or None,
                    "seller_type": seller_type,
                    "location": location,
                    "photo_count": photo_count,
                    "description": item.get("description", ""),
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            continue

    return results


def _extract_listings_from_html(html: str) -> list[dict]:
    """Fallback HTML parser for OLX search results."""
    soup = BeautifulSoup(html, "lxml")
    results = []

    # OLX uses data-cy="l-card" on listing divs
    cards = (
        soup.select("[data-cy='l-card']") or
        soup.select("[data-testid='listing-grid-item']") or
        soup.select("li[data-aut-id='itemBox']") or
        soup.select("div.css-1ut89at") or   # common OLX card class pattern
        []
    )

    for card in cards:
        try:
            link = card.select_one("a")
            url = ""
            if link:
                href = link.get("href", "")
                url = href if href.startswith("http") else BASE_URL + href

            title = ""
            for sel in ["[data-cy='ad-card-title']", "h6", "h3", "[class*='title']"]:
                t = card.select_one(sel)
                if t:
                    title = t.get_text(strip=True)
                    break

            price = None
            for sel in ["[data-testid='ad-price']", "[class*='price']", "strong", "p[class*='price']"]:
                p = card.select_one(sel)
                if p:
                    price = _parse_price(p.get_text(strip=True))
                    if price:
                        break

            # Year and km from params
            year, km, fuel = None, None, None
            params = card.select("span[class*='param']") or card.select("li")
            for param in params:
                text = param.get_text(strip=True)
                if re.match(r"(20\d{2}|19\d{2})", text):
                    year = _parse_year(text)
                elif "km" in text.lower() and not km:
                    km = _parse_km(text)
                elif any(f in text.lower() for f in ["gasolina", "diesel", "híbrido", "elétrico"]):
                    fuel = text

            location = ""
            loc = card.select_one("[data-testid='location-date']") or card.select_one("[class*='location']")
            if loc:
                location = loc.get_text(strip=True).split("·")[0].strip()

            # Seller — OLX shows "Particular" label on private ads
            card_text = card.get_text(" ", strip=True).lower()
            if "particular" in card_text:
                seller_type = "privado"
            elif any(w in card_text for w in ["stand", "empresa", "profissional"]):
                seller_type = "stand"
            else:
                seller_type = "desconhecido"

            photo_count = len(card.select("img")) - 1  # subtract UI icon
            photo_count = max(0, photo_count)

            if url and (title or price):
                results.append({
                    "source": "olx",
                    "source_url": url,
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
    Fetch search results from OLX for a given brand/model.
    Uses Playwright to render JS-heavy search pages so __PRELOADED_STATE__ is populated.
    Falls back to static httpx if Playwright is not installed.
    year_from / year_to are baked into the search URL so only the correct generation
    is fetched — not filtered post-hoc.
    """
    search_url = _build_search_url(brand, model, budget_max, year_from, year_to)

    if _check_playwright():
        try:
            html = await _render_page(search_url, wait_selector="[data-cy='l-card']")
            # Try __PRELOADED_STATE__ first (most structured data)
            state = _extract_preloaded_state(html)
            if state:
                listings = _extract_listings_from_preloaded(state, BASE_URL)
                if listings:
                    return listings[:max_results]
            # Fallback: parse rendered HTML cards
            return _extract_listings_from_html(html)[:max_results]
        except Exception as e:
            print(f"[OLX SCRAPER] Playwright error: {e}")
            return []

    # Fallback: static HTTP (prices likely None on OLX search pages)
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": BASE_URL,
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(1.5, 3.0))
            resp = await client.get(search_url)
            resp.raise_for_status()
            html = resp.text
            state = _extract_preloaded_state(html)
            if state:
                listings = _extract_listings_from_preloaded(state, BASE_URL)
                if listings:
                    return listings[:max_results]
            return _extract_listings_from_html(html)[:max_results]
    except Exception as e:
        print(f"[OLX SCRAPER] HTTP fallback error: {e}")
        return []


async def fetch_listing_detail(url: str) -> dict:
    """
    Fetch an OLX listing detail page.
    Strategy: __PRELOADED_STATE__ → __NEXT_DATA__ → JSON-LD → HTML parsing.
    Returns: {description, photo_count, seller_type, year, km, price, fuel_type}
    """
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Referer": SEARCH_URL,
    }
    result: dict = {
        "description": "", "photo_count": 0, "seller_type": "desconhecido",
        "year": None, "km": None, "price": None, "fuel_type": None, "title": "",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(2.0, 3.5))
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

            # ── Strategy 1: __PRELOADED_STATE__ ──
            state = _extract_preloaded_state(html)
            if state:
                ad = (
                    state.get("ad", {}).get("ad") or
                    state.get("adview", {}).get("ad") or
                    state.get("listing", {}).get("ad") or
                    state.get("adPage", {}).get("ad") or
                    state.get("adPage", {}).get("advert") or
                    {}
                )
                if ad and (ad.get("title") or ad.get("description")):
                    _extract_from_olx_ad_object(ad, result)
                    if result["price"] or result["year"]:
                        print(f"[OLX SCRAPER] __PRELOADED_STATE__ OK — {result.get('title', '')[:40]}")
                        return result

            # ── Strategy 2: __NEXT_DATA__ (OLX uses Next.js) ──
            next_data = _extract_next_data(html)
            if next_data:
                props = next_data.get("props", {}).get("pageProps", {})
                ad = props.get("ad") or props.get("advert") or props.get("listing") or {}
                if ad and (ad.get("title") or ad.get("description")):
                    _extract_from_olx_ad_object(ad, result)
                    if result["price"] or result["year"]:
                        print(f"[OLX SCRAPER] __NEXT_DATA__ OK — {result.get('title', '')[:40]}")
                        return result

            # ── Strategy 3: JSON-LD ──
            soup = BeautifulSoup(html, "lxml")
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    ld = json.loads(script.string or "")
                    if isinstance(ld, list):
                        ld = ld[0] if ld else {}
                    if ld.get("@type") in ("Product", "Car", "Vehicle", "Offer"):
                        result["title"] = ld.get("name", "")
                        result["description"] = (ld.get("description") or "")[:3000]
                        # Price from JSON-LD
                        offers = ld.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        price_val = offers.get("price") or ld.get("price")
                        if price_val:
                            result["price"] = _parse_price(str(price_val))
                        # Photos
                        images = ld.get("image", [])
                        if isinstance(images, list):
                            result["photo_count"] = len(images)
                        # Year from name/description
                        for txt in [result["title"], result["description"]]:
                            if not result["year"] and txt:
                                yr = _parse_year(txt)
                                if yr:
                                    result["year"] = yr
                        if result["price"]:
                            print(f"[OLX SCRAPER] JSON-LD OK — {result.get('title', '')[:40]}")
                            # Don't return yet — try HTML for km/year if missing
                except (json.JSONDecodeError, TypeError):
                    continue

            # ── Strategy 4: HTML fallback ──
            if not soup:
                soup = BeautifulSoup(html, "lxml")

            # Description
            if not result["description"]:
                for sel in ["[data-cy='ad_description']", "#description", "[class*='description']",
                            "[data-testid='ad-description']", "section[class*='content'] p"]:
                    desc = soup.select_one(sel)
                    if desc:
                        result["description"] = desc.get_text("\n", strip=True)[:3000]
                        break

            # Photos
            if not result["photo_count"]:
                result["photo_count"] = len(soup.select(
                    "[data-cy='ad-photo'] img, [class*='photo'] img, [class*='gallery'] img, "
                    "[data-testid*='photo'] img, picture img, [class*='swiper'] img"
                ))

            # Price (if not already found)
            if not result["price"]:
                for sel in ["[data-testid='ad-price-container']", "h3[class*='price']",
                            "[class*='price-label']", "[data-cy='ad_price']",
                            "[class*='pricelabel']", "[class*='offer-price']"]:
                    p = soup.select_one(sel)
                    if p:
                        result["price"] = _parse_price(p.get_text(strip=True))
                        if result["price"]:
                            break

            # Seller type from page text
            if result["seller_type"] == "desconhecido":
                page_text = soup.get_text(" ", strip=True).lower()
                if "particular" in page_text:
                    result["seller_type"] = "privado"
                elif any(w in page_text for w in ["stand", "empresa", "profissional", "dealer"]):
                    result["seller_type"] = "stand"

            # Year/km from various parameter displays
            param_selectors = [
                "[class*='param'] li", "ul[class*='params'] li",
                "[data-testid*='param']", "[class*='detail'] li",
                "table tr", "[class*='specs'] li", "[class*='attribute'] li",
            ]
            for sel in param_selectors:
                for row in soup.select(sel):
                    text = row.get_text(" ", strip=True)
                    if _parse_year(text) and not result["year"]:
                        result["year"] = _parse_year(text)
                    elif "km" in text.lower() and not result["km"]:
                        result["km"] = _parse_km(text)
                    elif any(f in text.lower() for f in ["gasolina", "diesel", "híbrido", "elétrico", "eletrico"]) and not result["fuel_type"]:
                        result["fuel_type"] = text.strip()

            # Last resort: scan full page text for year/km patterns
            if not result["year"] or not result["km"]:
                page_text = soup.get_text(" ", strip=True)
                if not result["year"]:
                    yr_match = re.search(r'\b(20[0-2]\d|19[89]\d)\b', page_text)
                    if yr_match:
                        result["year"] = int(yr_match.group(1))
                if not result["km"]:
                    km_match = re.search(r'(\d[\d\s.]{2,8})\s*km', page_text, re.IGNORECASE)
                    if km_match:
                        result["km"] = _parse_km(km_match.group(0))

            print(f"[OLX SCRAPER] HTML fallback — price={result['price']} year={result['year']} km={result['km']}")

    except Exception as e:
        print(f"[OLX SCRAPER] Detail fetch error {url}: {e}")

    return result


def _extract_next_data(html: str) -> Optional[dict]:
    """Extract __NEXT_DATA__ JSON from a Next.js page."""
    m = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def _extract_from_olx_ad_object(ad: dict, result: dict) -> None:
    """Extract listing fields from an OLX ad object (shared by __PRELOADED_STATE__ and __NEXT_DATA__)."""
    result["title"] = ad.get("title", "")
    result["description"] = (ad.get("description") or "")[:3000]
    result["photo_count"] = len(ad.get("photos", []) or ad.get("images", []))

    # Price — handle multiple nesting patterns
    price_obj = ad.get("price", {})
    if isinstance(price_obj, dict):
        # Try: price.value.value, price.value, price.regularPrice.value
        raw_price = price_obj.get("value", {})
        if isinstance(raw_price, dict):
            result["price"] = _parse_price(str(raw_price.get("value", "") or raw_price.get("amount", "")))
        else:
            result["price"] = _parse_price(str(raw_price))
        if not result["price"]:
            reg = price_obj.get("regularPrice", {})
            if isinstance(reg, dict):
                result["price"] = _parse_price(str(reg.get("value", "")))
        if not result["price"]:
            result["price"] = _parse_price(str(price_obj.get("displayValue", "")))
    elif isinstance(price_obj, (int, float)):
        result["price"] = int(price_obj)

    # Seller type
    user = ad.get("user", {}) or ad.get("seller", {}) or {}
    user_type = (user.get("userType") or user.get("type") or "").lower()
    result["seller_type"] = (
        "privado" if user_type in ("private", "particular")
        else "stand" if user_type in ("business", "company", "dealer", "professional")
        else "desconhecido"
    )

    # Params — handle both list[{key, value}] and dict formats
    params = ad.get("params", []) or ad.get("parameters", []) or ad.get("attributes", [])
    if isinstance(params, list):
        for p in params:
            key = (p.get("key") or p.get("name") or p.get("code") or "").lower()
            # Value can be: string, {label: str}, {value: str}, nested dict
            raw_val = p.get("value", "")
            if isinstance(raw_val, dict):
                val = str(raw_val.get("label", "") or raw_val.get("key", "") or raw_val.get("value", "") or "")
            else:
                val = str(raw_val)
            # Also check normalizedValue / displayValue
            if not val:
                val = str(p.get("normalizedValue", "") or p.get("displayValue", ""))

            if any(k in key for k in ("ano", "year", "registration")):
                result["year"] = _parse_year(val)
            elif any(k in key for k in ("km", "quilomet", "mileage", "odometer")):
                result["km"] = _parse_km(val)
            elif any(k in key for k in ("combust", "fuel", "motor")):
                result["fuel_type"] = val
    elif isinstance(params, dict):
        # dict format: {"year": "2018", "mileage": "150000", ...}
        for key, val in params.items():
            key_l = key.lower()
            val_s = str(val) if not isinstance(val, dict) else str(val.get("label", val.get("value", "")))
            if any(k in key_l for k in ("ano", "year")):
                result["year"] = _parse_year(val_s)
            elif any(k in key_l for k in ("km", "quilomet", "mileage")):
                result["km"] = _parse_km(val_s)
            elif any(k in key_l for k in ("combust", "fuel")):
                result["fuel_type"] = val_s
