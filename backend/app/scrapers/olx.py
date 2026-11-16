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

import os
import httpx
import asyncio
import re
import json
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Optional

from app.scrapers.relay import relay_fetch

# Playwright import is lazy — only loaded when actually needed.
_PLAYWRIGHT_AVAILABLE: Optional[bool] = None


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


def _olx_fuel_keyword(fuel_type: Optional[str]) -> Optional[str]:
    """Portuguese fuel keyword to bias OLX's text search toward the right variant."""
    if not fuel_type:
        return None
    f = fuel_type.lower()
    if "plug" in f:
        return "Híbrido"  # OLX rarely distinguishes plug-in in text; bias to hybrid
    if "híbr" in f or "hibr" in f:
        return "Híbrido"
    if "elétr" in f or "eletr" in f:
        return "Elétrico"
    if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
        return "Diesel"
    if "gasolina" in f:
        return "Gasolina"
    return None


def _build_search_url(
    brand: str,
    model: str,
    budget_max: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fuel_type: Optional[str] = None,
) -> str:
    """OLX uses a keyword query string in the URL path."""
    query = f"{brand} {model}".strip()
    fuel_kw = _olx_fuel_keyword(fuel_type)
    if fuel_kw:
        query = f"{query} {fuel_kw}"
    query = query.replace(" ", "-")
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
    fuel_type: Optional[str] = None,
) -> list[dict]:
    """
    Fetch search results from OLX for a given brand/model.
    Uses Playwright to render JS-heavy search pages so __PRELOADED_STATE__ is populated.
    Falls back to static httpx if Playwright is not installed.
    year_from / year_to / fuel_type are baked into the search query so only the
    correct generation and fuel variant are fetched — not filtered post-hoc.
    """
    search_url = _build_search_url(brand, model, budget_max, year_from, year_to, fuel_type)

    # httpx-first: OLX search pages render listing cards (and often a preloaded
    # state blob) in the static HTML — verified to return complete samples with
    # prices. Avoids Playwright's memory cost.
    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Referer": BASE_URL,
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(0.4, 1.2))
            resp = await client.get(search_url)
            resp.raise_for_status()
            html = resp.text
            state = _extract_preloaded_state(html)
            if state:
                listings = _extract_listings_from_preloaded(state, BASE_URL)
                if listings:
                    return listings[:max_results]
            listings = _extract_listings_from_html(html)[:max_results]
            if listings:
                return listings
    except Exception as e:
        print(f"[OLX SCRAPER] httpx error: {e}")

    # Optional Playwright fallback — off by default (OOMs on small instances).
    if _check_playwright():
        try:
            html = await _render_page(search_url, wait_selector="[data-cy='l-card']")
            state = _extract_preloaded_state(html)
            if state:
                listings = _extract_listings_from_preloaded(state, BASE_URL)
                if listings:
                    return listings[:max_results]
            return _extract_listings_from_html(html)[:max_results]
        except Exception as e:
            print(f"[OLX SCRAPER] Playwright fallback error: {e}")

    return []


async def fetch_listing_detail(url: str) -> dict:
    """
    Fetch an OLX listing detail page.
    OLX detail pages use server-rendered HTML with Portuguese label-value pairs:
      "Ano: 2020", "Quilómetros: 185.000 km", "Combustível: Diesel"
    No __PRELOADED_STATE__ or __NEXT_DATA__ on detail pages.
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
            await asyncio.sleep(random.uniform(1.5, 2.5))
            resp = await client.get(url)
            relayed = await relay_fetch(url) if resp.status_code == 403 else None
            if relayed:
                html = relayed
            else:
                resp.raise_for_status()
                html = resp.text

            # ── Try embedded JSON first (some OLX pages have it) ──
            state = _extract_preloaded_state(html)
            if state:
                ad = (
                    state.get("ad", {}).get("ad") or
                    state.get("adview", {}).get("ad") or
                    state.get("adPage", {}).get("ad") or
                    {}
                )
                if ad and (ad.get("title") or ad.get("price")):
                    _extract_from_olx_json(ad, result)
                    if result["price"] or result["year"]:
                        print(f"[OLX SCRAPER] JSON OK — {result.get('title', '')[:50]}")
                        return result

            # ── Primary strategy: HTML text pattern matching ──
            # OLX detail pages render as plain HTML with "Label: Value" pairs
            soup = BeautifulSoup(html, "lxml")
            page_text = soup.get_text(" ", strip=True)

            # Title — first h1 on the page
            h1 = soup.select_one("h1")
            if h1:
                result["title"] = h1.get_text(strip=True)

            # ── Price: find text matching "XX.XXX €" pattern ──
            # OLX shows the asking price in a prominent heading element. Guard
            # against financing widgets ("199 €/mês"), "desde X €", and other
            # non-asking amounts — these were a source of wildly wrong prices.
            price_pattern = re.compile(r'(\d[\d\s.]*)\s*€(\s*/?\s*m[êe]s)?', re.IGNORECASE)

            def _looks_like_monthly(text: str, match: re.Match) -> bool:
                if match.group(2):  # "€/mês" right after the number
                    return True
                ctx = text[max(0, match.start() - 12):match.end() + 12].lower()
                return any(w in ctx for w in ("/mês", "/mes", "mensal", "mês", "desde", "financ"))

            for el in soup.select("h1, h2, h3, [class*='price'], [data-testid*='price']"):
                t = el.get_text(" ", strip=True)
                m = price_pattern.search(t)
                if m and not _looks_like_monthly(t, m):
                    p = _parse_price(m.group(1))
                    if p and p >= 1000:  # cars cost ≥ €1.000; smaller = monthly/fee
                        result["price"] = p
                        break
            # Fallback: scan full page, still skipping monthly amounts
            if not result["price"]:
                for m in price_pattern.finditer(page_text):
                    if _looks_like_monthly(page_text, m):
                        continue
                    p = _parse_price(m.group(1))
                    if p and p >= 1000:
                        result["price"] = p
                        break

            # ── Portuguese label-value pairs ──
            # OLX renders specs as "Ano: 2020", "Quilómetros: 185.000 km", etc.
            _extract_pt_label_values(page_text, result)

            # ── Description ──
            # Look for the section after "Descrição" heading
            desc_heading = soup.find(string=re.compile(r'Descri[çc][ãa]o', re.IGNORECASE))
            if desc_heading:
                # Get the parent and then the next sibling content
                parent = desc_heading.find_parent()
                if parent:
                    next_el = parent.find_next_sibling()
                    if next_el:
                        result["description"] = next_el.get_text("\n", strip=True)[:3000]
            if not result["description"]:
                for sel in ["[data-cy='ad_description']", "[class*='description']", "[class*='descri']"]:
                    desc = soup.select_one(sel)
                    if desc and len(desc.get_text(strip=True)) > 30:
                        result["description"] = desc.get_text("\n", strip=True)[:3000]
                        break

            # ── Photos: count CDN images ──
            cdn_imgs = soup.select("img[src*='olxcdn'], img[src*='apollo'], img[data-src*='olxcdn'], img[data-src*='apollo']")
            if cdn_imgs:
                result["photo_count"] = len(cdn_imgs)
            else:
                # Fallback: count all listing images
                all_imgs = soup.select("[class*='gallery'] img, [class*='photo'] img, [class*='swiper'] img, picture img")
                result["photo_count"] = len(all_imgs)

            # ── Seller type ──
            if "particular" in page_text.lower():
                result["seller_type"] = "privado"
            elif any(w in page_text.lower() for w in ["stand", "empresa", "profissional", "dealer"]):
                result["seller_type"] = "stand"

            extracted = f"price={result['price']} year={result['year']} km={result['km']} fuel={result['fuel_type']}"
            print(f"[OLX SCRAPER] Detail OK — {result.get('title', '')[:40]} | {extracted}")

    except Exception as e:
        print(f"[OLX SCRAPER] Detail fetch error {url}: {e}")

    return result


# ── Portuguese label-value extraction ──────────────────────────────────────

def _norm_fuel(raw: str) -> Optional[str]:
    """Normalise a Portuguese fuel word to a canonical value."""
    r = (raw or "").lower()
    if "elétr" in r or "eletr" in r or "electric" in r:
        return "Elétrico"
    if "plug" in r:
        return "Híbrido (Plug-in)"
    if "híbr" in r or "hibr" in r or "hybrid" in r:
        return "Híbrido"
    if "diesel" in r or "gasóleo" in r or "gasoleo" in r:
        return "Diesel"
    if "gpl" in r:
        return "GPL"
    if "gasolina" in r:
        return "Gasolina"
    return None


def _norm_transmission(raw: str) -> Optional[str]:
    r = (raw or "").lower()
    if "autom" in r:
        return "Automática"
    if "manual" in r:
        return "Manual"
    return None


# Patterns for Portuguese car spec labels as displayed on OLX.
# Values are matched against tight whitelists/anchored groups so a capture never
# bleeds into the *next* label (the cause of "Diesel Potência" garbage).
# NOTE: field names must match what the pipeline reads downstream
# (engine_power_hp, not power).
_PT_LABEL_PATTERNS = [
    (re.compile(r'Ano\s*:?\s*(\d{4})', re.IGNORECASE), "year",
        lambda m: int(m.group(1)) if 1990 <= int(m.group(1)) <= 2030 else None),
    (re.compile(r'Quil[oó]metros?\s*:?\s*([\d\s.]+?)\s*km', re.IGNORECASE), "km",
        lambda m: _parse_km(m.group(1))),
    (re.compile(r'Combust[ií]vel\s*:?\s*(Gasolina|Diesel|Gas[oó]leo|H[ií]brido(?:\s*\(?Plug[- ]?in\)?)?|El[eé]tric[oa]|GPL)',
                re.IGNORECASE), "fuel_type", lambda m: _norm_fuel(m.group(1))),
    # Power: OLX lists it in cv (≈ hp in PT usage). Capture the number only.
    (re.compile(r'Pot[eê]ncia\s*:?\s*(\d{2,4})\s*(?:cv|cav|hp)?', re.IGNORECASE), "engine_power_hp",
        lambda m: int(m.group(1)) if 30 <= int(m.group(1)) <= 1200 else None),
    (re.compile(r'Cilindrada\s*:?\s*([\d.\s]+?)\s*c?m?3?\b', re.IGNORECASE), "displacement",
        lambda m: m.group(1).strip()),
    (re.compile(r'Tipo de Caixa\s*:?\s*(Manual|Autom[áa]tica|Semi[- ]?autom[áa]tica)', re.IGNORECASE),
        "transmission", lambda m: _norm_transmission(m.group(1))),
    (re.compile(r'Portas\s*:?\s*([2-5])\b', re.IGNORECASE), "doors", lambda m: m.group(1)),
    (re.compile(r'Lugares\s*:?\s*([1-9])\b', re.IGNORECASE), "seats", lambda m: m.group(1)),
    (re.compile(r'Cor\s*:?\s*([A-Za-zÀ-ÿ]+)', re.IGNORECASE), "colour", lambda m: m.group(1).strip()),
]


def _extract_pt_label_values(page_text: str, result: dict) -> None:
    """Extract car specs from Portuguese label-value patterns in page text."""
    for pattern, field, parser in _PT_LABEL_PATTERNS:
        if field in result and result[field]:
            continue  # already extracted
        m = pattern.search(page_text)
        if m:
            try:
                val = parser(m)
                if val is not None:
                    result[field] = val
            except (ValueError, TypeError):
                pass

    # Fallback year: scan for 4-digit year near "ano" or standalone
    if not result.get("year"):
        m = re.search(r'\b(20[0-2]\d|19[89]\d)\b', page_text)
        if m:
            result["year"] = int(m.group(1))

    # Fallback km: scan for number followed by "km"
    if not result.get("km"):
        m = re.search(r'(\d[\d\s.]{2,8})\s*km\b', page_text, re.IGNORECASE)
        if m:
            result["km"] = _parse_km(m.group(1))


def _extract_from_olx_json(ad: dict, result: dict) -> None:
    """Extract listing fields from an OLX JSON object (when available)."""
    result["title"] = ad.get("title", "")
    result["description"] = (ad.get("description") or "")[:3000]
    result["photo_count"] = len(ad.get("photos", []) or ad.get("images", []))

    # Price
    price_obj = ad.get("price", {})
    if isinstance(price_obj, dict):
        raw_price = price_obj.get("value", {})
        if isinstance(raw_price, dict):
            result["price"] = _parse_price(str(raw_price.get("value", "") or raw_price.get("amount", "")))
        else:
            result["price"] = _parse_price(str(raw_price))
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

    # Params
    params = ad.get("params", []) or ad.get("parameters", []) or ad.get("attributes", [])
    if isinstance(params, list):
        for p in params:
            key = (p.get("key") or p.get("name") or p.get("code") or "").lower()
            raw_val = p.get("value", "")
            val = str(raw_val.get("label", "") if isinstance(raw_val, dict) else raw_val)
            if any(k in key for k in ("ano", "year")):
                result["year"] = _parse_year(val)
            elif any(k in key for k in ("km", "quilomet", "mileage")):
                result["km"] = _parse_km(val)
            elif any(k in key for k in ("combust", "fuel")):
                result["fuel_type"] = val
