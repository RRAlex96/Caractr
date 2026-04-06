# Caractr — Technical Architecture & Engineering Reference

**Version:** 4.3
**Date:** March 2026
**Status:** Production

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Database Architecture](#3-database-architecture)
4. [Scraping Infrastructure](#4-scraping-infrastructure)
5. [Generation-Aware Market Intelligence](#5-generation-aware-market-intelligence)
6. [Deal Scoring Engine](#6-deal-scoring-engine)
7. [Analysis Routing — Rule Engine vs. LLM](#7-analysis-routing--rule-engine-vs-llm)
8. [Market Data Lifecycle](#8-market-data-lifecycle)
9. [API Design](#9-api-design)
10. [Frontend Architecture](#10-frontend-architecture)
11. [Background Jobs & Scheduler](#11-background-jobs--scheduler)
12. [Security & Configuration](#12-security--configuration)

---

## 1. System Overview

Caractr is a used car analysis platform targeting the Portuguese market. It takes a listing URL from any car marketplace (Standvirtual, OLX, or any dealer website), scrapes the ad, compares it against a real-time market sample of the same vehicle generation, and produces a structured deal verdict with explainability.

The core value is precision: a BMW 320d E90 is never compared against an F30, and a Golf Mk7 diesel is never benchmarked against a Mk8 petrol. This generation-and-variant aware comparison is the architectural backbone of the product.

### High-Level Request Flow

```
User pastes URL
      │
      ▼
[FastAPI] /api/analyse
      │
      ├─► DB cache check (normalized_listings + llm_analysis, TTL 7 days)
      │         └─ cache hit → return immediately
      │
      ├─► Scrape listing detail (Playwright / httpx / generic fallback)
      │         └─ extract: price, year, km, fuel_type, engine, description
      │
      ├─► Resolve model_id → look up generation window (generations table)
      │         └─ e.g. Golf 2015 → Mk7 → year_from=2012, year_to=2019
      │
      ├─► Live market scrape (Standvirtual + OLX, year-bounded at URL level)
      │         ├─ filter: fuel type match
      │         └─ filter: engine variant match (1.6 TDI, 2.0 TSI, etc.)
      │
      ├─► Deal scoring (price_delta, km_per_year, deal_tier, deal_score)
      │
      ├─► Analysis engine (rule-based default | Claude Haiku if API key set)
      │
      ├─► DB write-back (market stats upsert + analysis cache)
      │
      └─► Structured response → Frontend
```

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend API | FastAPI (Python 3.11) | Async-native, fast, OpenAPI out of the box |
| Database | PostgreSQL 15 | Relational integrity for model/generation graph |
| ORM | SQLAlchemy 2.x (Core, text()) | Fine-grained SQL control |
| HTML Rendering | Playwright (async Chromium) | Standvirtual and OLX are client-side rendered |
| HTTP client | httpx (async) | Fallback for static pages and dealer sites |
| HTML parsing | BeautifulSoup + lxml | Resilient multi-selector extraction |
| LLM | Anthropic Claude Haiku | Fast, cheap, structured JSON output |
| Frontend | Next.js 14 (TypeScript, App Router) | SSR + React Server Components |
| Styling | CSS custom properties + Tailwind | Design token system with dark/light modes |
| Email | Resend API | Transactional emails |

---

## 3. Database Architecture

### 3.1 Schema Overview

```
brands
  └── vehicle_models (brand_id)
        ├── generations (model_id)       ← generation year ranges + platform codes
        ├── engines (model_id)
        │     └── engine_issues (engine_id)
        ├── market_price_stats (model_id)
        └── driving_character (model_id)

raw_listings
  └── normalized_listings (raw_listing_id, model_id)

recommendation_sessions
analytics_events
user_feedback
concierge_requests
import_cost_estimates
```

### 3.2 Core Tables

#### `brands`
```sql
id SERIAL PRIMARY KEY
name TEXT NOT NULL UNIQUE          -- "Volkswagen", "BMW", "Mercedes-Benz"
```

#### `vehicle_models`
```sql
id SERIAL PRIMARY KEY
brand_id INTEGER REFERENCES brands
name TEXT NOT NULL                 -- "Golf", "Serie 3", "Classe C"
reliability_score NUMERIC(3,1)
comfort_score NUMERIC(3,1)
driving_fun_score NUMERIC(3,1)
family_score NUMERIC(3,1)
avg_reliability NUMERIC(3,1)
```
**Coverage:** 200 models across 38 brands.

#### `generations`
```sql
id SERIAL PRIMARY KEY
model_id INTEGER REFERENCES vehicle_models
name TEXT NOT NULL                 -- "Mk7", "E90", "F30", "W205"
year_start INTEGER NOT NULL
year_end INTEGER                   -- NULL = current production generation
platform TEXT                      -- "MQB", "CLAR", "E9x", "MFA2"
```
**Coverage:** 354 generation records. `year_end IS NULL` means the generation is still in production. The platform/chassis code is stored for reference and future powertrain filtering.

This table is the foundation of the generation-aware comparison system. A query of `WHERE year_start <= :year AND (year_end IS NULL OR year_end >= :year)` pinpoints the exact generation for any listing year.

#### `market_price_stats`
```sql
id SERIAL PRIMARY KEY
model_id INTEGER REFERENCES vehicle_models
year INTEGER                       -- NULL = model-level average (refresh_all)
avg_price NUMERIC
min_price NUMERIC
max_price NUMERIC
sample_count INTEGER
source TEXT                        -- 'seeded' | 'live_scraped'
updated_at TIMESTAMP

CONSTRAINT uq_market_model_year UNIQUE (model_id, year)  -- v5.0 migration
-- Partial unique index for NULL year rows (v5.0 migration):
CREATE UNIQUE INDEX uq_market_model_year_null ON market_price_stats (model_id) WHERE year IS NULL
```

#### `raw_listings`
```sql
id SERIAL PRIMARY KEY
source TEXT                        -- 'standvirtual' | 'olx' | 'dealer:...' | 'generic'
source_url TEXT UNIQUE NOT NULL
description TEXT
seller_type TEXT
photo_count INTEGER
scraped_at TIMESTAMP
```

#### `normalized_listings`
```sql
id SERIAL PRIMARY KEY
raw_listing_id INTEGER REFERENCES raw_listings
model_id INTEGER REFERENCES vehicle_models
brand_name TEXT
model_name TEXT
year INTEGER
km INTEGER
price NUMERIC
fuel_type TEXT
km_per_year NUMERIC
price_delta NUMERIC
deal_tier TEXT                     -- 'forte' | 'razoavel' | 'cuidado' | 'evitar'
deal_score NUMERIC
seller_type TEXT
description TEXT
photo_count INTEGER
listing_age_days INTEGER
llm_analysis JSONB
analysis_cached_at TIMESTAMP
```

### 3.3 Key Constraints & Indexes

The `UNIQUE(model_id, year)` constraint on `market_price_stats` enables the `ON CONFLICT DO UPDATE` upsert pattern used by the live scrape write-back. PostgreSQL NULL semantics require a separate partial unique index to enforce uniqueness on rows where `year IS NULL` (model-level averages), since the standard UNIQUE constraint treats two NULL values as distinct.

---

## 4. Scraping Infrastructure

### 4.1 The Rendering Problem

Both Standvirtual and OLX are React-based single-page applications. Their search result pages render prices and listing data via client-side JavaScript. A plain `httpx` GET returns a skeleton HTML with no useful data. This is why Playwright is the primary scraping engine.

### 4.2 Playwright Flow

```python
async def _render_page(url: str, wait_selector: str, timeout: int = 12000) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            locale="pt-PT",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        await page.wait_for_selector(wait_selector, timeout=timeout)
        html = await page.content()
        await browser.close()
        return html
```

`wait_until="domcontentloaded"` is used over `networkidle` intentionally — networkidle is too slow for search pages with analytics pings and ad network requests that never fully settle. We instead wait for the specific card selector that signals the product data is painted.

### 4.3 Standvirtual HTML Quirks

The rendered Standvirtual DOM has two non-obvious patterns:

**Price format:** Prices appear as `"29 990EUR"` (not `€`) inside `div` elements with obfuscated class names like `ooa-rz87wg`. The standard `[class*='price']` selector fails. The fallback scanner iterates all short text nodes looking for the EUR substring:

```python
for tag in card.find_all(True):
    t = tag.get_text(strip=True)
    if ("EUR" in t or "€" in t) and len(t) < 35 and re.search(r"\d{3}", t):
        candidate = _parse_price(t)
        if candidate and 1000 <= candidate <= 500000:
            price = candidate
            break
```

**Year/KM format:** In the rendered DOM, listing parameters appear in `<dd>` elements (not `<li>` as in the static HTML). The parser tries `dd` first:

```python
detail_items = card.select("dd") or card.select("li") or card.select("[class*='param']")
```

### 4.4 OLX Structured Data

OLX embeds a full JSON data payload in the page as `window.__PRELOADED_STATE__`. When available, this is preferred over HTML parsing — it provides structured fields for year, km, fuel type, price, and seller type without fragile CSS selectors. The HTML parser is only used as a fallback.

### 4.5 Generic Scraper

Any URL outside Standvirtual/OLX is handled by a generic scraper that applies a cascade of extraction strategies:
1. **JSON-LD / schema.org** (`@type: Car`, `@type: Product`)
2. **OpenGraph meta tags** (`og:title`, `og:description`, `og:price`)
3. **Microdata** (`itemprop` attributes)
4. **Heuristic HTML** (price patterns, year/km extraction via regex)

This enables analysis of listings from dealer sites (autosapo.pt, autoscout24.pt, carnext.pt, etc.) without any site-specific code.

### 4.6 Source Routing (Dispatcher Pattern)

```
fetch_detail_for_url(url)
  ├── standvirtual.com → standvirtual.fetch_listing_detail()
  ├── olx.pt          → olx.fetch_listing_detail()
  └── any other URL   → generic.fetch_listing_detail()

fetch_listings_all_sources(brand, model, year_from, year_to)
  ├── standvirtual.fetch_listings()   ─┐  run concurrently
  └── olx.fetch_listings()            ─┘  via asyncio.gather()
```

---

## 5. Generation-Aware Market Intelligence

This is the core differentiator of the platform. The problem: a search for "BMW Serie 3" returns listings from the E90 (2005–2011), F30 (2012–2018), and G20 (2019–present) generations. These are fundamentally different vehicles in terms of technology, design language, and market value. Mixing them in a price comparison produces a meaningless average.

### 5.1 Generation Resolution

When a listing is analysed, its `model_id` and `year` are used to query the `generations` table:

```sql
SELECT year_start, year_end
FROM generations
WHERE model_id = :model_id
  AND year_start <= :year
  AND (year_end IS NULL OR year_end >= :year)
ORDER BY year_start DESC
LIMIT 1
```

For a 2015 Golf (model_id resolved from DB), this returns `(2012, 2019)` — the Mk7 generation.

### 5.2 URL-Level Year Bounding

The generation boundaries are injected directly into the search URLs sent to Standvirtual and OLX:

```
standvirtual.com/carros/volkswagen/golf
  ?search[filter_float_year:from]=2012
  &search[filter_float_year:to]=2019
```

This is deliberate. Without this, a request for 20 listings might return 6 Mk6, 9 Mk7, and 5 Mk8 cars. After filtering to Mk7 only, the sample drops to 9 — below the confidence threshold. With URL-level filtering, all 20 results are Mk7 Golfs from the start.

### 5.3 Progressive Filtering Pipeline

After URL-bounded scraping, three additional filters are applied progressively. Each filter is only applied if the remaining pool stays at ≥ 3 listings — preserving sample size over precision when data is sparse.

```
All priced listings (pool = N)
  │
  ▼ Filter 1: Year guard (safety net for URL filter stragglers)
  │           gen_year_start ≤ listing.year ≤ gen_year_end
  │
  ▼ Filter 2: Fuel type match
  │           "diesel" ∈ listing.fuel_type.lower()
  │           (only if pool ≥ 4 and filtered pool ≥ 3)
  │
  ▼ Filter 3: Engine variant match
              hint "1.6 TDI" ∈ listing.title.lower()
              (only if pool ≥ 5 and filtered pool ≥ 3)
```

### 5.4 Engine Hint Extraction

Engine variant strings are extracted from the listing description using a regex that matches displacement + fuel code:

```python
re.search(
    r"\b([1-9]\.[0-9]{1,2})\s*"
    r"(TDI|TSI|TFSI|HDi|BlueHDi|CDI|EcoBoost|eTSI|eTDI|"
    r"HEV|PHEV|TCe|dCi|PureTech|T-GDi|CRDI|D4D|...)?",
    text, re.IGNORECASE
)
```

This covers OEM naming conventions from VW Group, Mercedes, Ford, Renault, PSA, Hyundai/Kia, and Toyota. The result (`"1.6 TDI"`, `"2.0 TSI"`, `"1.5 EcoBoost"`) is used as both a search filter and a cache key dimension.

### 5.5 Cache Key Design

The in-memory market cache key includes all variant dimensions to prevent cross-contamination:

```
{brand}_{model_first_word}_{gen_start}-{gen_end}_{fuel_code}_{engine_code}
e.g.: volkswagen_golf_2012-2019_diesel_1.6tdi
```

A Golf Mk7 diesel 1.6 TDI and a Golf Mk7 petrol 1.4 TSI are stored as independent cache entries.

---

## 6. Deal Scoring Engine

### 6.1 Inputs

| Field | Source |
|---|---|
| `price` | Scraped from listing |
| `avg_price` | Live market sample (trimmed mean) |
| `km` | Scraped from listing |
| `year` | Scraped from listing |
| `seller_type` | Scraped (`privado` / `stand`) |

### 6.2 Computed Metrics

**`km_per_year`**
```python
km_per_year = km / max(1, current_year - year)
```
Portuguese market norms: ~15,000 km/year is typical. Above 25,000 km/year is high wear.

**`price_delta`**
```python
price_delta = (avg_price - price) / avg_price * 100
```
Positive = listing is below market (favourable). Negative = above market (unfavourable).

**`deal_tier`** — four-level categorical verdict:
| Tier | Condition |
|---|---|
| `forte` | price_delta > 10% and km_per_year < 20,000 |
| `razoavel` | price_delta in [-5%, +10%] |
| `cuidado` | price_delta < -5% or km_per_year > 25,000 |
| `evitar` | price_delta < -15% or extreme km anomaly |

Seller type modulates the tier — stand listings with high km tolerance have different thresholds than private sellers.

**`deal_score`** — normalised float [0.0, 1.0]:
```python
deal_score = clamp(0.5 + price_delta / 100 - km_penalty, 0.0, 1.0)
```

### 6.3 Market Statistics

Prices from the scraped pool are sorted, then:
- **Median:** middle value (robust to outliers)
- **Trimmed mean:** top and bottom 10% dropped, average of remainder (reported as `avg_price`)
- **Min/Max:** full range for context

Minimum sample size for a valid comparison: **3 listings**. Below this threshold, market stats are omitted and the scoring is skipped rather than returning a misleading result.

---

## 7. Analysis Routing — Rule Engine vs. LLM

The analysis layer produces the human-readable verdict, flags, and seller assessment. Two engines are available, with automatic routing:

### 7.1 Routing Logic

```python
_USE_RULE_ENGINE = not ANTHROPIC_API_KEY or USE_RULE_ANALYSIS == "true"
```

| Condition | Engine |
|---|---|
| No `ANTHROPIC_API_KEY` set | Rule engine (deterministic) |
| `USE_RULE_ANALYSIS=true` | Rule engine (forced) |
| API key present | Claude Haiku |
| Claude call fails | Automatic fallback to rule engine |

### 7.2 Rule Engine

The rule engine in `services/rule_analysis.py` applies deterministic logic to produce the same output fields as the LLM (`verdict`, `green_flags`, `red_flags`, `seller_analysis`, `trim_level`, `spec_tier`, `key_extras`). This ensures the system is fully functional at zero incremental cost and with zero latency variance.

Key rule categories:
- **Price rules:** delta bands → verdict contribution
- **KM rules:** per-year norms, age-adjusted thresholds
- **Seller rules:** private vs. stand pricing expectations
- **Description rules:** regex for service history, accident mentions, smoke, single owner
- **Photo rules:** listing with < 5 photos flagged as low-transparency
- **Age rules:** listings active > 60 days flagged for price negotiation leverage

### 7.3 LLM Analysis (Claude Haiku)

When active, the LLM receives a structured prompt containing:
- Listing data (model, year, km, price, description)
- Market context (avg price, price position %)
- Model reliability data (known issues from `engine_issues` table)
- Buyer profile dimension (if provided)

The LLM is instructed to respond exclusively in JSON matching a strict schema. If the response fails JSON parsing or returns an empty verdict, the rule engine is used as the fallback — ensuring the endpoint never returns an error to the user due to an LLM failure.

---

## 8. Market Data Lifecycle

### 8.1 Live-First Strategy

Every analysis attempt fetches live market data before checking the database. This ensures the comparison is always against the current market, not stale seeded data.

```
analyse_listing()
  │
  ├─► _fetch_live_market_data()    ← always attempted first
  │         │
  │         ├── hit → use live stats + write-back to market_price_stats
  │         └── miss/error → fall through to DB
  │
  └─► _get_market_stats(db, model_id, year)   ← DB fallback
```

### 8.2 DB Write-Back

When live scraping succeeds, the result is upserted into `market_price_stats`:

```sql
INSERT INTO market_price_stats (model_id, year, avg_price, ...)
VALUES (:model_id, :year, :avg_price, ...)
ON CONFLICT (model_id, year) DO UPDATE SET
    avg_price = EXCLUDED.avg_price,
    source = 'live_scraped',
    updated_at = NOW()
```

This means each analysis enriches the database. Over time, the DB accumulates real market data that serves as an instant fallback when live scraping is unavailable.

### 8.3 Monthly Background Refresh

A background task runs at startup and loops every 30 days:

```python
async def _market_refresh_loop() -> None:
    await asyncio.sleep(30 * 24 * 3600)  # initial delay
    while True:
        db = SessionLocal()
        try:
            await refresh_all_market_data(db)  # iterate all 200 models
        finally:
            db.close()
        await asyncio.sleep(30 * 24 * 3600)
```

`refresh_all_market_data` iterates every `vehicle_model`, calls `_fetch_live_market_data`, and upserts the result. A 2-second polite delay between models prevents rate limiting.

### 8.4 Admin Refresh Endpoint

```
POST /api/admin/refresh-market
Header: X-Admin-Token: {ADMIN_TOKEN}
```

Triggers `refresh_all_market_data` immediately on demand. Protected by a constant-time token comparison to prevent timing attacks.

---

## 9. API Design

### 9.1 Core Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/analyse` | Full listing analysis pipeline |
| `GET` | `/api/listings` | Browse indexed listings |
| `GET` | `/api/models` | Vehicle model catalogue |
| `GET` | `/api/market-stats/{model_id}` | Market price stats for a model |
| `POST` | `/api/admin/refresh-market` | Admin: trigger market data refresh |
| `POST` | `/api/feedback` | Submit user feedback on analysis |
| `POST` | `/api/concierge` | Submit concierge (human review) request |

### 9.2 Analysis Request/Response

**Request:**
```json
POST /api/analyse
{ "url": "https://www.standvirtual.com/carros/volkswagen/golf/..." }
```

**Response:**
```json
{
  "from_cache": false,
  "source": "standvirtual",
  "source_label": "Standvirtual",
  "listing": {
    "brand_name": "Volkswagen",
    "model_name": "Golf",
    "year": 2015,
    "km": 120000,
    "price": 16500,
    "seller_type": "privado"
  },
  "deal": {
    "tier": "razoavel",
    "score": 0.61,
    "price_delta": 1850.0,
    "price_delta_pct": 10.1,
    "km_per_year": 17143,
    "market_avg_price": 18350,
    "market_median_price": 17900,
    "market_sample_count": 14,
    "market_data_source": "live",
    "generation_year_start": 2012,
    "generation_year_end": 2019
  },
  "analysis": {
    "verdict": "razoavel",
    "verdict_reason": "Preço ligeiramente abaixo do mercado, quilometragem normal.",
    "green_flags": ["Preço abaixo da média Mk7", "Quilometragem adequada ao ano"],
    "red_flags": ["Sem referência a revisões recentes"],
    "seller_analysis": "...",
    "trim_level": "Highline",
    "spec_tier": "alto",
    "key_extras": ["Sensores de estacionamento", "Câmera de ré"],
    "spec_value_assessment": "adequado"
  },
  "caveat": "Análise baseada na descrição do anúncio..."
}
```

The `generation_year_start` / `generation_year_end` fields are returned explicitly, allowing the frontend to display the comparison scope (e.g. "compared against 14 Golf Mk7 listings from 2012–2019").

### 9.3 Error Handling

All errors return a JSON object with an `error` key. The API never raises unhandled exceptions to the client. The analysis pipeline has explicit fallback layers:
- Listing scrape fails → `{"error": "Não foi possível obter o anúncio..."}`
- Market data fails → analysis proceeds without market context
- LLM fails → rule engine fallback
- Analysis cache write fails → non-critical, logged only

---

## 10. Frontend Architecture

### 10.1 Stack

- **Next.js 14** with App Router
- **TypeScript** throughout
- **CSS custom properties** for the design token system (no Tailwind runtime)
- Server components for static content, client components for interactive analysis

### 10.2 `/analisar` Page Architecture

The analysis page has three visual states:

**State 1: Pre-analysis** — URL input with 4-column "what we check" grid informing the user of the analysis scope (market price, mechanical flags, seller analysis, specification value).

**State 2: Loading** — Animated 4-step progress indicator with dot timer:
```
recolher dados → consultar mercado → calcular valor → compor análise
```
Each step is highlighted sequentially, giving the user perceived progress feedback during the 5–15 second analysis window.

**State 3: Result** — Structured output with:
- Verdict pill (forte / razoavel / cuidado / evitar) with colour coding
- Market comparison metrics (avg price, price delta, sample count, generation scope)
- Segmented flags grid (green flags / red flags)
- Seller analysis block
- Specification tier and key extras
- Deal score visualisation

### 10.3 Design System

The design uses CSS custom properties at the `:root` level, enabling consistent theming:
```css
--bg: #FAFAF8;
--fg: #1A1A1A;
--accent: #2563EB;
--green: #16A34A;
--red: #DC2626;
```

The "wizard bridge" pattern — a dark-background CTA section at the bottom of key pages — uses `--fg` as the background with `--bg` text, creating visual contrast without a separate colour system.

---

## 11. Background Jobs & Scheduler

### 11.1 FastAPI Lifespan

The background refresh task is registered via FastAPI's lifespan context manager, ensuring clean startup and shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_market_refresh_loop())
    yield

app = FastAPI(title="Caractr API", version="4.3.0", lifespan=lifespan)
```

### 11.2 Concurrency Model

The market scrape for each model is awaited sequentially within `refresh_all_market_data` (with a 2-second delay between models). This is deliberate — concurrent scraping of 200 models would trigger rate limiting on both Standvirtual and OLX. Sequential with polite delays is the safe production approach.

The two scraping sources (Standvirtual + OLX) per model **are** fetched concurrently via `asyncio.gather()` within `fetch_listings_all_sources`.

---

## 12. Security & Configuration

### 12.1 Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | Enables Claude Haiku analysis engine |
| `USE_RULE_ANALYSIS` | `"true"` to force rule engine regardless of API key |
| `ADMIN_TOKEN` | Bearer token for `/api/admin/refresh-market` |
| `RESEND_API_KEY` | Transactional email delivery |
| `OPERATOR_EMAIL` | Destination for concierge request notifications |

### 12.2 Admin Endpoint Protection

The admin token is compared using Python's `==` operator on strings. For production hardening, this should be replaced with `hmac.compare_digest()` to prevent timing-based token enumeration.

### 12.3 URL Validation

All analysis requests are validated against a supported URL schema before any scraping is attempted:
```python
def is_supported_url(url: str) -> bool:
    return detect_source(url) is not None  # requires http/https scheme
```

This prevents SSRF vectors from reaching internal services or file system paths.

---

*Document maintained by the Caractr engineering team. Last updated: March 2026.*
