"""
Caractr — Generic car listing scraper
Extracts structured data from any car dealer website URL.

Extraction priority:
  1. JSON-LD (schema.org/Car, schema.org/Product, schema.org/Offer) — most reliable
  2. OpenGraph + meta tags
  3. Microdata (itemprop="price" etc.)
  4. Heuristic HTML patterns (price with €, km in params, year detection)

Handles Portuguese dealer sites: AutoHub, CarsGuru, AutoClick, CarNext,
AutoSapo, SeBe, Flexicar, Soauto, and any site using schema.org markup.
"""

import re
import json
import random
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urlparse

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


# ── Parsers ──────────────────────────────────────────────────────────────────

def _parse_price(raw: str) -> Optional[int]:
    """Extract integer from price strings: '18 500 €', '18.500€', '18500'."""
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", str(raw))
    val = int(digits) if digits else None
    # Sanity: car prices in Portugal are €500 – €500k
    if val and 500 <= val <= 500_000:
        return val
    return None


def _parse_km(raw: str) -> Optional[int]:
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", str(raw))
    val = int(digits) if digits else None
    if val and 0 <= val <= 1_000_000:
        return val
    return None


def _parse_year(raw: str) -> Optional[int]:
    if not raw:
        return None
    m = re.search(r"\b(20[0-2]\d|19[89]\d)\b", str(raw))
    return int(m.group(1)) if m else None


def _detect_fuel(text: str) -> Optional[str]:
    text = text.lower()
    if "híbrido plug" in text or "phev" in text:
        return "híbrido plug-in"
    if "híbrido" in text or "hybrid" in text or "hev" in text:
        return "híbrido"
    if "elétrico" in text or "electric" in text or "bev" in text:
        return "elétrico"
    if "diesel" in text or "gasoleo" in text:
        return "diesel"
    if "gasolina" in text or "petrol" in text or "gasoline" in text:
        return "gasolina"
    if "gás" in text or "gnv" in text or "glp" in text:
        return "gás"
    return None


def _detect_seller_type(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["particular", "privado", "private"]):
        return "privado"
    if any(w in t for w in ["stand", "dealer", "concessionário", "empresa", "lda", "sa ", " s.a"]):
        return "stand"
    return "desconhecido"


# ── JSON-LD extraction ───────────────────────────────────────────────────────

def _extract_jsonld(soup: BeautifulSoup) -> dict:
    """
    Try all JSON-LD blocks. Handles Car, Vehicle, Product, Offer, BreadcrumbList.
    Returns a unified flat dict with extracted fields.
    """
    result: dict = {}

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or ""
            # Some sites embed multiple objects; try array wrapping
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        # Handle both single objects and arrays
        items = data if isinstance(data, list) else [data]
        for item in items:
            schema_type = str(item.get("@type", "")).lower()

            # Car / Vehicle
            if schema_type in ("car", "vehicle", "motorvehicle", "automobiledealer"):
                result.setdefault("title", item.get("name", ""))
                result.setdefault("description", item.get("description", ""))
                result.setdefault("year", _parse_year(str(item.get("modelDate", item.get("vehicleModelDate", "")))))
                result.setdefault("km", _parse_km(str(item.get("mileageFromOdometer", {}).get("value", "") if isinstance(item.get("mileageFromOdometer"), dict) else item.get("mileageFromOdometer", ""))))
                result.setdefault("fuel_type", item.get("fuelType", None))
                # Brand
                brand_obj = item.get("brand") or item.get("manufacturer") or {}
                if isinstance(brand_obj, dict):
                    result.setdefault("brand", brand_obj.get("name", ""))
                elif isinstance(brand_obj, str):
                    result.setdefault("brand", brand_obj)
                # Model
                result.setdefault("model", item.get("model", ""))
                # Trim / version
                result.setdefault("trim", item.get("vehicleConfiguration", item.get("bodyType", "")))
                # Colour
                result.setdefault("colour", item.get("color", ""))
                # Engine
                engine = item.get("vehicleEngine") or {}
                if isinstance(engine, dict):
                    result.setdefault("engine_power_hp", engine.get("enginePower", {}).get("value") if isinstance(engine.get("enginePower"), dict) else None)

                # Offer / price — may be nested
                offer = item.get("offers") or item.get("offer") or {}
                if isinstance(offer, list):
                    offer = offer[0] if offer else {}
                if isinstance(offer, dict):
                    result.setdefault("price", _parse_price(str(offer.get("price", ""))))
                    result.setdefault("currency", offer.get("priceCurrency", "EUR"))
                    result.setdefault("seller_type", _detect_seller_type(str(offer.get("seller", {}))))

                # Photos
                images = item.get("image", [])
                if isinstance(images, str):
                    images = [images]
                result.setdefault("photo_count", len(images))

            # Standalone Product / Offer
            elif schema_type in ("product", "offer"):
                result.setdefault("title", item.get("name", ""))
                result.setdefault("description", item.get("description", ""))
                price_val = item.get("price") or (item.get("offers", {}) or {}).get("price")
                result.setdefault("price", _parse_price(str(price_val or "")))

    return result


# ── OpenGraph / meta extraction ──────────────────────────────────────────────

def _extract_meta(soup: BeautifulSoup) -> dict:
    """Extract OGP and standard meta tags."""
    result: dict = {}

    def meta(name: str, attr: str = "name") -> str:
        tag = soup.find("meta", {attr: name})
        return tag.get("content", "") if tag else ""

    result["title"] = meta("og:title", "property") or meta("title") or (soup.title.string if soup.title else "")
    result["description"] = meta("og:description", "property") or meta("description")

    og_image = meta("og:image", "property")
    if og_image:
        result["photo_count"] = 1  # at least one

    return {k: v for k, v in result.items() if v}


# ── Microdata extraction ─────────────────────────────────────────────────────

def _extract_microdata(soup: BeautifulSoup) -> dict:
    """Extract itemprop microdata attributes."""
    result: dict = {}

    def iprop(name: str) -> str:
        tag = soup.find(itemprop=name)
        if not tag:
            return ""
        return tag.get("content") or tag.get_text(strip=True)

    result["price"]       = _parse_price(iprop("price") or iprop("offers"))
    result["title"]       = iprop("name") or ""
    result["description"] = iprop("description") or ""
    result["brand"]       = iprop("brand") or ""
    result["model"]       = iprop("model") or ""

    return {k: v for k, v in result.items() if v}


# ── Heuristic HTML extraction ────────────────────────────────────────────────

# Selectors tried in order — first match wins
PRICE_SELECTORS = [
    "[class*='price']", "[class*='preco']", "[class*='valor']",
    "[data-price]", "[itemprop='price']",
    "span.price", "div.price", "h2.price", "strong.price",
    ".listing-price", ".car-price", ".veiculo-price",
]

YEAR_KM_SELECTORS = [
    "[class*='spec']", "[class*='detail']", "[class*='info']",
    "[class*='param']", "[class*='detalhe']", "[class*='caracteristica']",
    "table td", "ul.specs li", "dl dt", "dl dd",
]

DESCRIPTION_SELECTORS = [
    "[class*='description']", "[class*='descri']", "[class*='observa']",
    "#description", "#obs", "#observacoes",
    "div.listing-description", "section.description",
    "article p", ".car-obs",
]

GALLERY_SELECTORS = [
    "[class*='gallery']", "[class*='carousel']", "[class*='slider']",
    "[class*='photos']", "[class*='fotos']", "[class*='imagens']",
]

SELLER_SELECTORS = [
    "[class*='seller']", "[class*='vendedor']", "[class*='stand']",
    "[class*='dealer']", "[class*='contact']", "[class*='anunciante']",
]


def _extract_heuristic(soup: BeautifulSoup, page_text: str) -> dict:
    result: dict = {}

    # Price
    for sel in PRICE_SELECTORS:
        el = soup.select_one(sel)
        if el:
            price = _parse_price(el.get_text(strip=True))
            if price:
                result["price"] = price
                break

    # Year and km — scan param/spec areas and full page text
    for sel in YEAR_KM_SELECTORS:
        for el in soup.select(sel):
            text = el.get_text(" ", strip=True)
            if not result.get("year"):
                y = _parse_year(text)
                if y:
                    result["year"] = y
            if not result.get("km") and re.search(r"\d[\d\s.]*\s*km", text, re.IGNORECASE):
                km_match = re.search(r"([\d\s.]+)\s*km", text, re.IGNORECASE)
                if km_match:
                    km = _parse_km(km_match.group(1))
                    if km:
                        result["km"] = km
            if not result.get("year") and not result.get("km"):
                continue

    # Fallback: scan page text for year/km
    if not result.get("year"):
        result["year"] = _parse_year(page_text)
    if not result.get("km"):
        km_m = re.search(r"\b([\d\s.]{4,8})\s*km\b", page_text, re.IGNORECASE)
        if km_m:
            result["km"] = _parse_km(km_m.group(1))

    # Fuel type
    result["fuel_type"] = _detect_fuel(page_text)

    # Description
    for sel in DESCRIPTION_SELECTORS:
        el = soup.select_one(sel)
        if el:
            text = el.get_text("\n", strip=True)
            if len(text) > 50:
                result["description"] = text[:3000]
                break

    # Photo count — count images in gallery areas
    photo_count = 0
    for sel in GALLERY_SELECTORS:
        gallery = soup.select_one(sel)
        if gallery:
            imgs = gallery.select("img")
            photo_count = max(photo_count, len(imgs))
    if not photo_count:
        # fallback: all images that look like car photos (large src)
        all_imgs = soup.select("img[src]")
        photo_count = sum(
            1 for img in all_imgs
            if any(kw in (img.get("src", "") + img.get("class", [""])[0] if img.get("class") else "").lower()
                   for kw in ["photo", "foto", "image", "imagem", "car", "veiculo", "gallery"])
        )
    result["photo_count"] = max(1, photo_count)

    # Seller type
    for sel in SELLER_SELECTORS:
        el = soup.select_one(sel)
        if el:
            st = _detect_seller_type(el.get_text(" ", strip=True))
            if st != "desconhecido":
                result["seller_type"] = st
                break
    if not result.get("seller_type"):
        result["seller_type"] = _detect_seller_type(page_text[:2000])

    # Title (car name)
    if not result.get("title"):
        h1 = soup.select_one("h1")
        if h1:
            result["title"] = h1.get_text(strip=True)

    return result


# ── Brand/model inference from title ─────────────────────────────────────────

KNOWN_BRANDS = [
    "BMW", "Mercedes", "Audi", "Volkswagen", "VW", "Toyota", "Honda", "Mazda",
    "Volvo", "Peugeot", "Renault", "Ford", "Opel", "SEAT", "Skoda", "Hyundai",
    "Kia", "Fiat", "Dacia", "Citroen", "Citroën", "Nissan", "MINI", "Mini",
    "Alfa Romeo", "Land Rover", "Porsche", "Tesla", "Subaru", "Suzuki",
    "Cupra", "DS", "Lexus", "Mitsubishi", "Jeep", "Jaguar", "Maserati", "MG",
]

def _infer_brand_model(title: str) -> tuple[str, str]:
    """Heuristically extract brand and model from a car listing title."""
    if not title:
        return "", ""
    for brand in KNOWN_BRANDS:
        pattern = re.compile(r"\b" + re.escape(brand) + r"\b", re.IGNORECASE)
        if pattern.search(title):
            # Model: first word(s) after the brand
            after = pattern.split(title, maxsplit=1)[-1].strip()
            # Take up to 2 words as model name
            model_parts = re.split(r"[\s,|·–\-]", after)
            model = " ".join(p for p in model_parts[:2] if p and not p[0].isdigit()).strip()
            return brand, model
    return "", ""


# ── Main entry point ─────────────────────────────────────────────────────────

async def fetch_listing_detail(url: str) -> dict:
    """
    Universal car listing detail extractor.
    Works on any Portuguese car dealer website.

    Returns dict with:
        title, description, price, year, km, fuel_type,
        seller_type, photo_count, brand, model, trim, colour,
        engine_power_hp, source_domain
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }
    result: dict = {
        "title": "", "description": "", "price": None, "year": None,
        "km": None, "fuel_type": None, "seller_type": "desconhecido",
        "photo_count": 0, "brand": "", "model": "", "trim": "",
        "colour": "", "engine_power_hp": None,
        "source_domain": urlparse(url).netloc.lstrip("www."),
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0, headers=headers) as client:
            await asyncio.sleep(random.uniform(1.0, 2.5))
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as e:
        print(f"[GENERIC SCRAPER] HTTP {e.response.status_code}: {url}")
        return result
    except Exception as e:
        print(f"[GENERIC SCRAPER] Fetch error: {e}")
        return result

    soup = BeautifulSoup(html, "lxml")
    page_text = soup.get_text(" ", strip=True)

    # ── Layer 1: JSON-LD (most reliable) ──
    jsonld = _extract_jsonld(soup)
    for k, v in jsonld.items():
        if v:
            result[k] = v

    # ── Layer 2: Meta tags ──
    meta = _extract_meta(soup)
    for k, v in meta.items():
        if v and not result.get(k):
            result[k] = v

    # ── Layer 3: Microdata ──
    micro = _extract_microdata(soup)
    for k, v in micro.items():
        if v and not result.get(k):
            result[k] = v

    # ── Layer 4: Heuristic HTML ──
    heuristic = _extract_heuristic(soup, page_text)
    for k, v in heuristic.items():
        if v and not result.get(k):
            result[k] = v

    # ── Post-processing: infer brand/model from title if not found ──
    if not result.get("brand") and result.get("title"):
        brand, model = _infer_brand_model(result["title"])
        if brand:
            result.setdefault("brand", brand)
        if model:
            result.setdefault("model", model)

    # Normalise fuel string from schema.org URLs/codes
    fuel = result.get("fuel_type") or ""
    if "diesel" in fuel.lower():
        result["fuel_type"] = "diesel"
    elif "petrol" in fuel.lower() or "gasoline" in fuel.lower():
        result["fuel_type"] = "gasolina"
    elif "electric" in fuel.lower():
        result["fuel_type"] = "elétrico"
    elif "hybrid" in fuel.lower():
        result["fuel_type"] = "híbrido"

    # Trim photo_count sanity
    result["photo_count"] = max(0, result.get("photo_count") or 0)

    return result
