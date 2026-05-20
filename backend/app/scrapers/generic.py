"""
Caractr — Generic car listing scraper
Extracts structured data from any car dealer website URL.

Extraction priority (per layer):
  1. JSON-LD (schema.org/Car, schema.org/Product, schema.org/Offer) — most reliable
  2. OpenGraph + meta tags
  3. Microdata (itemprop="price" etc.)
  4. Heuristic HTML patterns (price with €, km in params, year detection)
  5. Portuguese label-value regex (dt/dd + page text)
  6. LLM extraction via Gemini (universal fallback, ~$0.001/call)

JS SPA handling:
  - If httpx returns < 200 chars of text → JS-rendered SPA detected
  - Re-fetches with Playwright (headless Chromium) to render JavaScript
  - All 6 extraction layers then run on the fully-rendered HTML
  - Works for omeustand.pt, shakenauto.pt, joaomaiaautomoveis.com, etc.

Handles Portuguese dealer sites: AutoHub, CarsGuru, AutoClick, CarNext,
AutoSapo, SeBe, Flexicar, Soauto, and any site using schema.org markup.
"""

import os
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
    """
    Detect fuel type from text. Uses word-boundary regex to avoid false positives
    like "Vidros Elétricos" matching "elétrico".
    """
    t = text.lower()
    if "híbrido plug" in t or "phev" in t:
        return "híbrido plug-in"
    if "híbrido" in t or "hybrid" in t or "hev" in t:
        return "híbrido"
    # "elétrico" must appear as a standalone fuel reference, not as adjective
    # "Vidros Elétricos", "Espelhos Elétricos" → false positive
    if re.search(r'\b(?:100%\s*)?el[eé]trico\b(?!\s+(?:vidros|espelhos|bancos|teto))', t):
        return "elétrico"
    if "electric" in t or " bev " in t or " ev " in t:
        return "elétrico"
    if "diesel" in t or "gasoleo" in t or "gasóleo" in t:
        return "diesel"
    if "gasolina" in t or "petrol" in t or "gasoline" in t:
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

            # Standalone Product / Offer (CustoJusto uses this)
            elif schema_type in ("product", "offer"):
                result.setdefault("title", item.get("name", ""))
                raw_desc = item.get("description", "")
                result.setdefault("description", raw_desc)

                # Price from offers (CustoJusto: offers.price = "15500")
                offer = item.get("offers") or {}
                if isinstance(offer, list):
                    offer = offer[0] if offer else {}
                if isinstance(offer, dict):
                    price_val = offer.get("price") or offer.get("lowPrice")
                    result.setdefault("price", _parse_price(str(price_val or "")))
                if not result.get("price"):
                    result.setdefault("price", _parse_price(str(item.get("price", ""))))

                # Brand from schema — only trust if it matches a known car brand
                brand_obj = item.get("brand") or {}
                brand_name = brand_obj.get("name", "") if isinstance(brand_obj, dict) else str(brand_obj)
                # CustoJusto sets brand to seller name ("WORKCAR no CustoJusto.pt") — filter that out
                if brand_name:
                    brand_lower = brand_name.lower()
                    is_known = any(b.lower() in brand_lower for b in KNOWN_BRANDS)
                    if is_known:
                        result.setdefault("brand", brand_name)

                # Parse description for car specs (CustoJusto embeds specs in free text)
                # Description has HTML tags like <br /> — strip them first
                if raw_desc:
                    desc_clean = re.sub(r'<[^>]+>', ' ', str(raw_desc))
                    # Year: "Ano 01/2014" or "Ano: 2020"
                    if not result.get("year"):
                        ym = re.search(r'\bAno\s*[:/]?\s*(?:\d{1,2}/)?(\d{4})\b', desc_clean, re.IGNORECASE)
                        if ym:
                            y = int(ym.group(1))
                            if 1990 <= y <= 2030:
                                result["year"] = y
                    # KM: "215.000 kms" or "150 000 km"
                    if not result.get("km"):
                        km_m = re.search(r'(\d[\d\s.]+)\s*kms?\b', desc_clean, re.IGNORECASE)
                        if km_m:
                            km = _parse_km(km_m.group(1))
                            if km:
                                result["km"] = km
                    # Fuel: "Diesel", "Gasolina", etc.
                    if not result.get("fuel_type"):
                        result["fuel_type"] = _detect_fuel(desc_clean)
                    # Power: "200 cv" or "150 hp"
                    if not result.get("engine_power_hp"):
                        hp_m = re.search(r'(\d+)\s*(?:cv|hp)\b', desc_clean, re.IGNORECASE)
                        if hp_m:
                            result["engine_power_hp"] = int(hp_m.group(1))

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


# ── Portuguese label-value extraction (Layer 5) ─────────────────────────────
# Many PT dealer sites render specs as "Ano: 2020", "Quilómetros: 185.000 km"
# or WITHOUT colon: "Quilometragem 207.100 Km" (AutoSapo), "Ano do modelo 2014" (CustoJusto)
# The separator [:/]? is optional to cover both styles.

# Separator: colon, slash, or just whitespace — covers "Ano: 2020", "Ano 2020", "Ano / 2020"
_SEP = r'\s*[:/]?\s+'

# Value capture helpers — stop before the next known label word
_STOP = (r'(?:Ano|Quil[oó]|Combust|Pot[eê]n|Cilind|Caixa|Tipo\s+de|Portas|Lugares|'
         r'Cor\b|Marca|Fabricante|Modelo|Vers[aã]o|Pre[çc]o|Id\s|Descri|Especif|'
         r'Anunciant|Concelho|Freguesia|Sedan|Carro|Venda)')
_VAL_SHORT = r'(\w+(?:[\s/-](?!' + _STOP + r')\w+){0,2})'
_VAL_BRAND = r'(\w[\w-]*(?:\s+(?!' + _STOP + r')\w[\w-]*){0,2})'
_VAL_NUM   = r'([\d\s.]+)'  # digits, spaces, dots

_PT_LABEL_PATTERNS = [
    # (compiled regex, field name, parser lambda)
    # Year — multiple label variants
    (re.compile(r'(?:Ano\s+(?:do\s+)?modelo|Ano|Data\s+da\s+Matr[ií]cula)' + _SEP + r'(\d{4})', re.IGNORECASE), "year", lambda m: int(m.group(1)) if 1990 <= int(m.group(1)) <= 2030 else None),
    # "Ano 01/2014" or "Ano 12/2019" — MM/YYYY format (CustoJusto description)
    (re.compile(r'(?:Ano|Data\s+da\s+Matr[ií]cula)' + _SEP + r'\d{1,2}/(\d{4})', re.IGNORECASE), "year", lambda m: int(m.group(1)) if 1990 <= int(m.group(1)) <= 2030 else None),
    (re.compile(r'(?:Ano\s+de\s+)?[Rr]egisto' + _SEP + r'(\d{4})', re.IGNORECASE), "year", lambda m: int(m.group(1)) if 1990 <= int(m.group(1)) <= 2030 else None),
    (re.compile(r'(?:Ano\s*/\s*)?M[eê]s' + _SEP + r'(\d{1,2})/(\d{4})', re.IGNORECASE), "year", lambda m: int(m.group(2)) if 1990 <= int(m.group(2)) <= 2030 else None),
    # Mileage — "Quilómetros: 185.000 km" OR "Quilómetros 180 000 - 189 999" (range)
    (re.compile(r'Quil[oó]metros?' + _SEP + r'([\d\s.]+)\s*km', re.IGNORECASE), "km", lambda m: _parse_km(m.group(1))),
    (re.compile(r'Quil[oó]metros?' + _SEP + r'(\d[\d\s.]*\d)\s*(?:\s-\s|\s*$)', re.IGNORECASE), "km", lambda m: _parse_km(m.group(1))),
    (re.compile(r'Quil[oó]metragem' + _SEP + _VAL_NUM, re.IGNORECASE), "km", lambda m: _parse_km(m.group(1))),
    # Fuel type — short value (1-3 words: "Diesel", "Gasolina", "Híbrido plug-in")
    (re.compile(r'Combust[ií]vel' + _SEP + _VAL_SHORT, re.IGNORECASE), "fuel_type", lambda m: m.group(1).strip()),
    # Power — "150cv", "150 hp", or just number after label
    (re.compile(r'Pot[eê]ncia' + _SEP + r'(\d+)\s*(?:cv|hp|CV|HP)?', re.IGNORECASE), "engine_power_hp", lambda m: int(m.group(1))),
    # Displacement — "1500 cm³", "1.6", "1968 CC"
    (re.compile(r'Cilindrada(?:\s*\(cm[³3]\))?' + _SEP + r'(\d[\d.\s]*)', re.IGNORECASE), "displacement", lambda m: m.group(1).strip()),
    # Transmission — short value (1-2 words: "Manual", "Automática", "Sequencial")
    (re.compile(r'(?:Tipo\s+de\s+)?[Cc]aixa(?:\s+de\s+velocidades)?' + _SEP + _VAL_SHORT, re.IGNORECASE), "transmission", lambda m: m.group(1).strip()),
    # Doors / seats
    (re.compile(r'Portas' + _SEP + r'(\d)', re.IGNORECASE), "doors", lambda m: m.group(1)),
    (re.compile(r'Lugares' + _SEP + r'(\d)', re.IGNORECASE), "seats", lambda m: m.group(1)),
    # Colour — short (1-2 words: "Preto", "Cinzento escuro")
    (re.compile(r'Cor' + _SEP + _VAL_SHORT, re.IGNORECASE), "colour", lambda m: m.group(1).strip()),
    # Brand — "Marca", "Fabricante" (CustoJusto uses Fabricante)
    (re.compile(r'(?:Marca|Fabricante)' + _SEP + _VAL_BRAND, re.IGNORECASE), "brand", lambda m: m.group(1).strip()),
    # Model — short (1-3 words). Negative lookbehind: skip "Ano do modelo"
    (re.compile(r'(?<!do )(?<!do\s)Modelo' + _SEP + _VAL_SHORT, re.IGNORECASE), "model", lambda m: m.group(1).strip()),
    (re.compile(r'Vers[aã]o' + _SEP + _VAL_SHORT, re.IGNORECASE), "trim", lambda m: m.group(1).strip()),
    # Price label — "Preço: 14 900 €" or "EUR 19000"
    (re.compile(r'Pre[çc]o' + _SEP + r'([\d\s.]+)\s*€', re.IGNORECASE), "price", lambda m: _parse_price(m.group(1))),
    (re.compile(r'EUR\s+([\d\s.]+)', re.IGNORECASE), "price", lambda m: _parse_price(m.group(1))),
]


def _extract_dt_dd(soup: BeautifulSoup, result: dict) -> None:
    """
    Extract specs from <dt>/<dd> definition lists (used by CustoJusto, etc.).
    Maps Portuguese labels to result fields.
    """
    _DT_LABEL_MAP = {
        "ano": "year", "ano do modelo": "year", "ano de registo": "year",
        "quilómetros": "km", "quilometros": "km", "quilometragem": "km", "km": "km",
        "combustível": "fuel_type", "combustivel": "fuel_type",
        "potência": "engine_power_hp", "potencia": "engine_power_hp",
        "cilindrada": "displacement",
        "tipo de caixa": "transmission", "caixa": "transmission",
        "portas": "doors", "lugares": "seats",
        "cor": "colour",
        "marca": "brand", "modelo": "model", "versão": "trim", "versao": "trim",
    }
    _DT_PARSERS = {
        "year": lambda v: _parse_year(v),
        "km": lambda v: _parse_km(v),
        "fuel_type": lambda v: v.strip(),
        "engine_power_hp": lambda v: int(re.search(r'\d+', v).group()) if re.search(r'\d+', v) else None,
        "displacement": lambda v: v.strip(),
        "transmission": lambda v: v.strip(),
        "doors": lambda v: v.strip()[:1],
        "seats": lambda v: v.strip()[:1],
        "colour": lambda v: v.strip(),
        "brand": lambda v: v.strip(),
        "model": lambda v: v.strip(),
        "trim": lambda v: v.strip(),
    }

    for dt in soup.find_all("dt"):
        label = dt.get_text(strip=True).lower().rstrip(":")
        field = _DT_LABEL_MAP.get(label)
        if not field or (field in result and result[field]):
            continue
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        raw_val = dd.get_text(strip=True)
        if not raw_val:
            continue
        parser = _DT_PARSERS.get(field, lambda v: v.strip())
        try:
            val = parser(raw_val)
            if val is not None:
                result[field] = val
        except (ValueError, TypeError, AttributeError):
            pass


def _extract_pt_labels(page_text: str, result: dict) -> None:
    """Extract car specs from Portuguese label-value patterns in page text."""
    for pattern, field, parser in _PT_LABEL_PATTERNS:
        if field in result and result[field]:
            continue  # already have a value from a higher-priority layer
        m = pattern.search(page_text)
        if m:
            try:
                val = parser(m)
                if val is not None:
                    result[field] = val
            except (ValueError, TypeError):
                pass

    # Fallback price: "XX.XXX €" anywhere in text (if no price yet)
    if not result.get("price"):
        m = re.search(r'(\d[\d\s.]*)\s*€', page_text)
        if m:
            result["price"] = _parse_price(m.group(1))

    # Fallback year
    if not result.get("year"):
        m = re.search(r'\b(20[0-2]\d|19[89]\d)\b', page_text)
        if m:
            result["year"] = int(m.group(1))

    # Fallback km
    if not result.get("km"):
        m = re.search(r'(\d[\d\s.]{2,8})\s*km\b', page_text, re.IGNORECASE)
        if m:
            result["km"] = _parse_km(m.group(1))


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

    # Fuel type — limit to first 5000 chars to avoid false positives on huge pages
    result["fuel_type"] = _detect_fuel(page_text[:5000])

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
    "BMW", "Mercedes-Benz", "Mercedes", "Audi", "Volkswagen", "VW",
    "Toyota", "Honda", "Mazda", "Volvo", "Peugeot", "Renault", "Ford",
    "Opel", "SEAT", "Skoda", "Škoda", "Hyundai", "Kia", "Fiat", "Dacia",
    "Citroen", "Citroën", "Nissan", "MINI", "Mini",
    "Alfa Romeo", "Land Rover", "Porsche", "Tesla", "Subaru", "Suzuki",
    "Cupra", "DS", "Lexus", "Mitsubishi", "Jeep", "Jaguar", "Maserati", "MG",
    "Smart", "SsangYong", "BYD", "Polestar",
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


# ── LLM-powered extraction (Layer 6) ────────────────────────────────────────

async def _extract_via_llm(page_text: str, url: str) -> dict:
    """
    Universal car data extractor using Gemini.
    When regex/CSS/JSON-LD layers all fail, send the page text to the LLM
    and ask it to extract structured car listing data.

    This is the "any website" solution — no per-site code needed.
    Cost: ~$0.001 per call (Gemini 2.5 Flash, ~800 input tokens + 200 output).
    """
    try:
        from app.services.llm_client import generate_json, llm_available
    except ImportError:
        return {}

    if not llm_available():
        return {}

    # Truncate page text to ~4000 chars to keep cost/latency low
    truncated = page_text[:4000]

    prompt = f"""Extrai os dados deste anúncio de carro usado. Responde APENAS com JSON válido, sem texto extra.

TEXTO DA PÁGINA:
{truncated}

URL: {url}

Extrai o máximo possível. Devolve null para campos que não encontres.
{{
  "brand": "marca do carro (ex: Peugeot, BMW, Mercedes-Benz)",
  "model": "modelo (ex: 308, Série 3, CLA)",
  "year": 2020,
  "km": 150000,
  "price": 18500,
  "fuel_type": "diesel|gasolina|híbrido|elétrico|GPL",
  "transmission": "manual|automática",
  "engine_power_hp": 150,
  "colour": "cor do carro",
  "doors": "5",
  "seller_type": "privado|stand|desconhecido",
  "title": "título do anúncio",
  "description": "descrição resumida do anúncio (máx 500 chars)"
}}"""

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(generate_json, prompt, 500),
            timeout=15,
        )
        if not isinstance(result, dict):
            return {}

        # Parse and validate extracted fields
        extracted: dict = {}
        if result.get("brand"):
            extracted["brand"] = str(result["brand"]).strip()
        if result.get("model"):
            extracted["model"] = str(result["model"]).strip()
        if result.get("year"):
            y = _parse_year(str(result["year"]))
            if y:
                extracted["year"] = y
        if result.get("km"):
            km = _parse_km(str(result["km"]))
            if km:
                extracted["km"] = km
        if result.get("price"):
            p = _parse_price(str(result["price"]))
            if p:
                extracted["price"] = p
        if result.get("fuel_type"):
            extracted["fuel_type"] = str(result["fuel_type"]).strip()
        if result.get("transmission"):
            extracted["transmission"] = str(result["transmission"]).strip()
        if result.get("engine_power_hp"):
            try:
                extracted["engine_power_hp"] = int(result["engine_power_hp"])
            except (ValueError, TypeError):
                pass
        if result.get("colour"):
            extracted["colour"] = str(result["colour"]).strip()
        if result.get("seller_type") and result["seller_type"] != "desconhecido":
            extracted["seller_type"] = str(result["seller_type"]).strip()
        if result.get("title"):
            extracted["title"] = str(result["title"]).strip()
        if result.get("description") and len(str(result["description"])) > 20:
            extracted["description"] = str(result["description"])[:3000]

        print(f"[GENERIC SCRAPER] LLM extracted: price={extracted.get('price')} "
              f"year={extracted.get('year')} km={extracted.get('km')} "
              f"brand={extracted.get('brand')} model={extracted.get('model')}")
        return extracted

    except asyncio.TimeoutError:
        print(f"[GENERIC SCRAPER] LLM extraction timed out (15s)")
        return {}
    except Exception as e:
        print(f"[GENERIC SCRAPER] LLM extraction error: {e}")
        return {}


# ── Extraction layers runner ────────────────────────────────────────────────

def _run_extraction_layers(soup: BeautifulSoup, page_text: str, result: dict) -> None:
    """
    Run layers 1-5 of the extraction pipeline on the given HTML/text.
    Modifies result dict in-place, only filling fields not already set.
    """
    # Layer 1: JSON-LD (most reliable)
    jsonld = _extract_jsonld(soup)
    for k, v in jsonld.items():
        if v:
            result[k] = v

    # Layer 2: Meta tags
    meta = _extract_meta(soup)
    for k, v in meta.items():
        if v and not result.get(k):
            result[k] = v

    # Layer 3: Microdata
    micro = _extract_microdata(soup)
    for k, v in micro.items():
        if v and not result.get(k):
            result[k] = v

    # Layer 4: Heuristic HTML
    heuristic = _extract_heuristic(soup, page_text)
    for k, v in heuristic.items():
        if v and not result.get(k):
            result[k] = v

    # Layer 5a: dt/dd definition lists
    _extract_dt_dd(soup, result)

    # Layer 5b: Portuguese label-value patterns in page text
    _extract_pt_labels(page_text, result)


# ── Playwright JS rendering fallback ────────────────────────────────────────

async def _fetch_with_playwright(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Render a JS-heavy page using headless Chromium via Playwright.
    Returns (html_string, error_msg). html is None on failure.

    Uses sync Playwright API in a thread to avoid async-within-async issues
    that can occur in FastAPI's event loop on some platforms.
    Timeout: 30s total (navigate + wait for network idle).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[GENERIC SCRAPER] Playwright not installed — cannot render JS SPA")
        return None, "import_failed"

    def _sync_render() -> tuple[Optional[str], Optional[str]]:
        """Run Playwright synchronously in a thread. Returns (html, error_msg)."""
        pw = None
        browser = None
        try:
            print(f"[GENERIC SCRAPER] Playwright: starting sync_playwright...")
            pw = sync_playwright().start()
            print(f"[GENERIC SCRAPER] Playwright: launching chromium...")
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ]
            # Newer Playwright (1.49+) uses chromium_headless_shell for headless=True,
            # but Railway only has the full chromium binary installed.
            # Find the actual Chrome binary via recursive search.
            # Check PLAYWRIGHT_BROWSERS_PATH first (set in nixpacks.toml),
            # then the default ~/.cache/ms-playwright.
            _exe = None
            _search_bases = [
                os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
                "/ms-playwright",
                os.path.expanduser("~/.cache/ms-playwright"),
            ]
            for _pw_base in _search_bases:
                if not _pw_base or not os.path.isdir(_pw_base):
                    continue
                for _root, _dirs, _files in os.walk(_pw_base):
                    if "headless_shell" in _root:
                        continue
                    for _f in _files:
                        if _f in ("chrome", "chrome.exe", "chromium"):
                            _candidate = os.path.join(_root, _f)
                            if os.access(_candidate, os.X_OK):
                                _exe = _candidate
                                break
                    if _exe:
                        break
                if _exe:
                    break

            if _exe:
                print(f"[GENERIC SCRAPER] Playwright: using chromium at {_exe}")
                browser = pw.chromium.launch(
                    headless=True,
                    executable_path=_exe,
                    args=launch_args,
                )
            else:
                print(f"[GENERIC SCRAPER] Playwright: no binary found in {_search_bases}, using default")
                browser = pw.chromium.launch(headless=True, args=launch_args)
            print(f"[GENERIC SCRAPER] Playwright: chromium launched, creating context...")
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                locale="pt-PT",
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            print(f"[GENERIC SCRAPER] Playwright: navigating to {url[:80]}...")
            page.goto(url, wait_until="networkidle", timeout=25_000)
            # Extra wait for late-loading JS frameworks (Vue/React hydration)
            page.wait_for_timeout(2000)
            html = page.content()
            print(f"[GENERIC SCRAPER] Playwright rendered {len(html)} chars for {url}")
            return html, None
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[GENERIC SCRAPER] Playwright error: {type(e).__name__}: {e}\n{tb}")
            return None, f"{type(e).__name__}:{str(e)[:200]}"
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            if pw:
                try:
                    pw.stop()
                except Exception:
                    pass

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_sync_render),
            timeout=35,  # hard cap: 35s for entire Playwright operation
        )
    except asyncio.TimeoutError:
        print(f"[GENERIC SCRAPER] Playwright hard timeout (35s) for {url}")
        return None, "timeout_35s"
    except Exception as e:
        print(f"[GENERIC SCRAPER] Playwright thread error: {type(e).__name__}: {e}")
        return None, f"thread_{type(e).__name__}:{str(e)[:200]}"


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
        # Explicit timeout: 10s connect, 15s read, 30s total pool wait
        # Wrapped in asyncio.wait_for as a hard cap (25s) to prevent slow-drip attacks
        timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=headers) as client:
            await asyncio.sleep(random.uniform(1.0, 2.5))
            resp = await asyncio.wait_for(client.get(url), timeout=25.0)
            resp.raise_for_status()
            html = resp.text
    except asyncio.TimeoutError:
        print(f"[GENERIC SCRAPER] Hard timeout (25s) for {url}")
        return result
    except httpx.HTTPStatusError as e:
        print(f"[GENERIC SCRAPER] HTTP {e.response.status_code}: {url}")
        return result
    except Exception as e:
        print(f"[GENERIC SCRAPER] Fetch error: {e}")
        return result

    soup = BeautifulSoup(html, "lxml")
    page_text = soup.get_text(" ", strip=True)
    _used_playwright = False

    # ── JS SPA detection (pass 1): httpx got almost no text → Playwright ──
    _pw_debug = None  # capture Playwright status for debugging
    if len(page_text) < 200:
        print(f"[GENERIC SCRAPER] JS SPA detected ({len(page_text)} chars) — trying Playwright for {url}")
        pw_html, pw_err = await _fetch_with_playwright(url)
        if pw_html and len(pw_html) > len(html):
            html = pw_html
            soup = BeautifulSoup(html, "lxml")
            page_text = soup.get_text(" ", strip=True)
            _used_playwright = True
            _pw_debug = f"pass1_ok:{len(page_text)}chars"
            print(f"[GENERIC SCRAPER] Playwright rendered {len(page_text)} chars of text")
        else:
            _pw_debug = f"pass1_fail:err={pw_err}|pw_html={'None' if pw_html is None else f'{len(pw_html)}chars'}"

    # ── Run all extraction layers (1-5) ──
    _run_extraction_layers(soup, page_text, result)

    # ── Client-side rendering detection (pass 2): page has text but NO car data ──
    # Next.js / React SSR sites (CustoJusto, etc.) return boilerplate HTML from httpx
    # but the actual listing data is injected by client-side JavaScript.
    # Price is the strongest signal — almost every real listing has a price.
    # If price AND km are both missing, the page almost certainly needs JS rendering.
    _needs_js_render = (
        not result.get("price")
        and not result.get("km")
    )
    if _needs_js_render and not _used_playwright:
        print(f"[GENERIC SCRAPER] No car data after static extraction — trying Playwright for {url}")
        pw_html, pw_err = await _fetch_with_playwright(url)
        if pw_html and len(pw_html) > len(html):
            html = pw_html
            soup = BeautifulSoup(html, "lxml")
            page_text = soup.get_text(" ", strip=True)
            _used_playwright = True
            _pw_debug = f"pass2_ok:{len(page_text)}chars"
            # Re-run extraction layers on rendered HTML (layers only fill empty fields)
            _run_extraction_layers(soup, page_text, result)
            print(f"[GENERIC SCRAPER] Playwright pass 2: {len(page_text)} chars, "
                  f"price={result.get('price')} year={result.get('year')} km={result.get('km')}")
        else:
            _pw_debug = (_pw_debug or "") + f"|pass2_fail:err={pw_err}|pw_html={'None' if pw_html is None else f'{len(pw_html)}chars'}"

    # ── Layer 6: LLM extraction (universal fallback) ──────────────────────
    # When traditional layers fail to extract key fields, send page text to
    # Gemini and ask it to extract structured car data. Works on ANY site
    # regardless of HTML structure — no per-site code needed.
    # Only fires when we're missing critical data (price OR year OR km).
    _key_missing = not result.get("price") or not result.get("year") or not result.get("km")
    _has_content = len(page_text) > 200  # skip empty shells

    if _key_missing and _has_content:
        llm_data = await _extract_via_llm(page_text, url)
        if llm_data:
            for k, v in llm_data.items():
                if v and not result.get(k):
                    result[k] = v
            print(f"[GENERIC SCRAPER] LLM extraction filled: {[k for k,v in llm_data.items() if v]}")

    # ── Still no data? Flag as JS-limited ──
    _still_empty = not result.get("price") and not result.get("year") and not result.get("km")
    if _still_empty and _used_playwright:
        result["_js_only"] = True
        print(f"[GENERIC SCRAPER] No data even after Playwright ({len(page_text)} chars) — {url}")
    elif _still_empty and not _has_content:
        result["_js_only"] = True
        print(f"[GENERIC SCRAPER] Empty page, Playwright unavailable ({len(page_text)} chars) — {url}")

    # ── Post-processing: validate and infer brand/model ──
    # Validate brand: if it doesn't match any known car brand, clear it
    if result.get("brand"):
        brand_str = result["brand"].lower()
        is_valid = any(b.lower() in brand_str or brand_str in b.lower() for b in KNOWN_BRANDS)
        if not is_valid:
            print(f"[GENERIC SCRAPER] Invalid brand '{result['brand']}' — clearing")
            result["brand"] = ""

    # Infer brand/model from title if not found
    if not result.get("brand") and result.get("title"):
        brand, model = _infer_brand_model(result["title"])
        if brand:
            result["brand"] = brand
        if model and not result.get("model"):
            result["model"] = model

    # Normalise fuel string from schema.org URLs/codes or Portuguese labels
    fuel = (result.get("fuel_type") or "").lower().strip()
    if "diesel" in fuel or "gasóleo" in fuel or "gasoleo" in fuel:
        result["fuel_type"] = "diesel"
    elif "gasolina" in fuel or "petrol" in fuel or "gasoline" in fuel:
        result["fuel_type"] = "gasolina"
    elif "híbrido plug" in fuel or "plug-in" in fuel or "phev" in fuel:
        result["fuel_type"] = "híbrido plug-in"
    elif "híbrido" in fuel or "hibrido" in fuel or "hybrid" in fuel:
        result["fuel_type"] = "híbrido"
    elif "elétrico" in fuel or "eletrico" in fuel or "electric" in fuel or "bev" in fuel:
        result["fuel_type"] = "elétrico"
    elif "gás" in fuel or "gnv" in fuel or "glp" in fuel or "gpl" in fuel:
        result["fuel_type"] = "GPL"

    # Trim photo_count sanity
    result["photo_count"] = max(0, result.get("photo_count") or 0)

    # Debug: Playwright status (temporary — remove after verifying Railway works)
    if _pw_debug:
        result["_pw_debug"] = _pw_debug

    return result
