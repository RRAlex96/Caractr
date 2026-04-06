# Caractr — Product Overview & Investment Brief

**March 2026**

---

## The Problem

Buying a used car in Portugal is one of the highest-stakes consumer decisions a person makes — typically the second largest purchase after a home — yet the information available to buyers is almost entirely unstructured and unverified.

Marketplaces like Standvirtual and OLX list hundreds of thousands of ads. Each ad is a seller's best self-presentation: cherry-picked photos, optimistic descriptions, and prices set with no obligation to accuracy. The buyer's only tool is intuition and, if they're lucky, a friend who knows cars.

**The result:**
- Buyers overpay because they have no credible price reference
- Buyers miss mechanical red flags buried in listing descriptions
- Buyers can't distinguish a fair dealer from a misleading private seller
- Sellers who price fairly lose to sellers who price aggressively and rely on information asymmetry

This is not a niche problem. The Portuguese used car market transacts over 600,000 vehicles per year. Even a 3% overpayment on a €15,000 car is €450 — real money for real people.

---

## The Solution: Caractr

Caractr is an AI-powered car analysis platform. A buyer pastes the URL of any listing — from Standvirtual, OLX, or any dealer website — and receives a structured, explainable verdict on whether the car is a good deal, at what price, and why.

The output is not a generic score. It is a specific, actionable assessment:

> *"This Golf Mk7 1.6 TDI is priced 8% below the current market median for comparable Mk7 diesel listings (14 samples, 2012–2019). Km/year is normal at 17,100/year. No major red flags in the description. Recommended."*

The platform does in 10 seconds what used to take an experienced buyer 2–3 hours of research.

---

## What Makes Caractr Different

### 1. Generation-Aware Comparison — the Industry's Blind Spot

Every other price reference tool compares a car against all listings of the same model, regardless of generation. This produces systematically wrong benchmarks.

A BMW 320d from 2010 (E90 generation) and a 2017 320d (F30 generation) share a name but nothing else — different chassis, different technology, different market value. Averaging their prices and calling it a benchmark is noise, not intelligence.

Caractr's database contains **354 generation records** across all 200 models in its catalogue, each with OEM chassis codes and precise production year ranges. When a 2010 320d is analysed, the system queries only E90-era listings. When a 2017 320d is analysed, only F30. The comparison is always like-for-like, not name-for-name.

This is not a filter applied after the fact — the generation year range is baked into the search query sent to the marketplace, so the 20-40 listings retrieved for comparison are all from the correct generation from the start.

### 2. Engine Variant Intelligence

A Golf Mk7 1.6 TDI and a Golf Mk7 2.0 TDI are meaningfully different cars with different prices. So are a 1.4 TSI and a 2.0 TSI. Generic searches return all of them.

Caractr extracts the engine variant from the listing description using a regex engine that recognises OEM naming conventions across all major manufacturers — VW Group (TDI, TSI, TFSI), Mercedes (CDI, EQ), Ford (EcoBoost), Renault/PSA (TCe, dCi, PureTech), Hyundai/Kia (T-GDi, CRDI), Toyota (HEV, PHEV), and more.

The engine hint becomes a filter dimension and a cache key dimension — a 1.6 TDI comparison pool never contaminates a 2.0 TSI pool.

### 3. Real-Time Market Data, Not Static Tables

Market prices change. A static database of average prices, even well-maintained, is stale the moment it is written. Caractr scrapes live listings from Standvirtual and OLX using headless Chromium (Playwright) for every analysis — bypassing the client-side rendering that blocks conventional scrapers.

Live data is written back to the database after each analysis, creating a self-reinforcing loop: every user request enriches the market data that serves future users. The database grows more accurate with every use.

### 4. Universal Listing Support

Caractr works on any URL. Standvirtual, OLX, and dealer sites (autosapo.pt, autoscout24.pt, carnext.pt, etc.) are all supported. The generic scraper applies a cascade of extraction strategies — JSON-LD schema.org, OpenGraph metadata, microdata, and heuristic HTML parsing — covering any well-structured car listing on the web.

### 5. AI Analysis with Full Fallback

For users who want a richer narrative, Caractr routes analysis through Claude Haiku when an API key is configured. The LLM receives structured data: the listing, market context, model reliability data (known issues from the engine database), and buyer profile.

The system is architected so that an LLM failure at any point causes an automatic, silent fallback to the deterministic rule engine. The user always gets an answer. There is no spinner-then-error.

---

## The Product Experience

The user journey is designed to be frictionless and confident.

**Entry point:** A single text input on the `/analisar` page. Paste a URL. Press analyse.

**Loading state:** Four animated steps — *recolher dados → consultar mercado → calcular valor → compor análise* — give the user a sense of the real work happening behind the request. Perceived wait time drops significantly with progress feedback.

**Result:** A clean, structured report:
- Verdict pill: **forte / razoável / cuidado / evitar** — one word the buyer can act on
- Market comparison: current average, price delta, sample size, generation scope
- Green flags: specific positives from the listing
- Red flags: specific concerns — mechanical, historical, seller behaviour
- Seller analysis: what the seller is claiming vs. what is verifiable
- Specification assessment: is the equipment level appropriate for the price?

The product speaks plainly, in Portuguese, to real buyers. No jargon. No hedge-everything disclaimers. A clear position.

---

## Database & Knowledge Assets

The platform is underpinned by a proprietary knowledge base that represents a significant barrier to replication:

| Asset | Coverage |
|---|---|
| Brands | 38 |
| Vehicle models | 200 |
| Generation records | 354 (with OEM chassis codes) |
| Engine variant recognition | 25+ OEM naming families |
| Known model issues | Populated via engine_issues table, severity-ranked |
| Market price history | Accumulates with every live scrape write-back |

This database is not scraped from a single source — it is curated, structured, and cross-referenced. The generation data (Golf Mk7 on MQB platform, 2012–2019; BMW E90 on E9x, 2005–2011) represents weeks of OEM research that cannot be auto-generated.

---

## Technical Moat

Several architectural choices create durable competitive advantages:

**Generation-at-URL-level filtering.** Competitors that filter post-hoc get thin samples. Caractr retrieves 20–40 generation-correct listings per query because the filter is applied at the source. More data means more reliable statistics.

**Self-enriching database.** Every analysis writes market data back to the DB. A platform with 10,000 monthly users is continuously updating price benchmarks for 200 models. This compounds over time into a proprietary pricing dataset.

**Playwright rendering capability.** Building and maintaining a headless browser scraping infrastructure for client-side rendered sites is a non-trivial engineering investment. It is also a practical barrier — most price APIs scrape static pages and return nothing from SPA-rendered marketplaces.

**Multi-source concurrent scraping.** Standvirtual and OLX are queried simultaneously for every analysis. The merged, deduplicated result pool is larger and more representative than either source alone.

---

## Business Model

**Consumer tier (freemium):**
- Free analysis for occasional buyers (N analyses/month)
- Premium subscription: unlimited analyses, historical price tracking, alerts on price drops for saved models

**Concierge service:**
- Human-reviewed analysis for high-value purchases (€25,000+ cars)
- Pre-purchase inspection coordination
- Import cost estimation (already in the database schema)

**B2B / API tier:**
- Fleet managers needing systematic vehicle valuations
- Insurance companies requiring consistent pre-claim vehicle assessments
- Financing companies needing independent market value references for loan collateral

**Data licensing:**
- The accumulated market price dataset becomes a proprietary asset licensable to dealerships, insurance companies, and leasing companies

---

## Market Opportunity

Portugal's used car market: ~620,000 transactions per year.

At an average transaction value of €14,000, that is ~€8.7 billion in annual transactions where buyers currently have no credible, real-time price intelligence.

Comparable models in larger markets:
- **AutoScout24 / mobile.de** (Germany) — listing aggregators, not analysis tools
- **CarGurus** (UK/US) — price rating based on static avg, no generation awareness
- **AutoTrader** (UK) — valuation tools based on registered data, not live market

None of these operate a real-time, generation-aware, multi-source scraping and analysis pipeline in the Portuguese market. The closest competitor is a human expert — exactly what Caractr replaces.

---

## Current Status

- Backend API fully operational (FastAPI, Python, PostgreSQL)
- Playwright-powered live scraping verified for Standvirtual and OLX
- 200 models × 354 generations database populated and active
- Analysis pipeline live: scrape → generation resolution → market comparison → deal scoring → AI verdict
- Frontend (`/analisar`) built with animated loading state and structured result display
- Monthly background market data refresh operational
- Admin market refresh endpoint live

**Immediate roadmap:**
- User authentication and saved analysis history
- Price drop alerts for watched models
- Mobile-optimised interface
- B2B API packaging

---

*Caractr — knowing what a car is actually worth.*
