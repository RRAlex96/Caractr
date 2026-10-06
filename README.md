# Caractr — a used-car decision engine for Portugal

[![CI](https://github.com/RRAlex96/Caractr/actions/workflows/ci.yml/badge.svg)](https://github.com/RRAlex96/Caractr/actions/workflows/ci.yml)

Caractr helps someone who *doesn't* know cars buy a used one without overpaying or getting burned. You either answer five questions about your life and get a shortlist of models that fit, or you paste any listing and get an honest, data-backed verdict on it — fair price, what to negotiate, what the trim actually includes, what it'll cost to run, and whether anything smells wrong.

It's a personal project: designed, built, and deployed end-to-end. Portuguese used-car buying runs on information asymmetry — the seller always knows more than the buyer — and this is an attempt to flip that. UI is in European Portuguese; this write-up is in English.

> **Status:** frontend live on Vercel; backend being moved to free, persistent hosting (see [`DEPLOY.md`](./DEPLOY.md)). This README doubles as the case study.

---

## What it does

- **Recommend** — a 5-question lifestyle wizard (no specs, no sliders) builds a 6-dimension profile and returns a ranked shortlist of real models, scored on fit, reliability, and driving character.
- **Analyse** — paste a Standvirtual/OLX/dealer listing and get:
  - a **verdict** (strong / fair / caution / avoid) with a one-line reason,
  - **negotiation numbers** — a concrete opening offer, fair value, and walk-away, with the leverage to cite,
  - **equipment** split into *factory trim* vs *optional extras*, explained for a beginner,
  - **cost of ownership** — €/month including exact Portuguese IUC, fuel, and maintenance,
  - a **scam/anomaly badge** when the price is implausible,
  - **price history & relisting** detection once the car has been seen before,
  - **reliability** with a Bayesian confidence interval, not a fake precise score.
- **Concierge** — a human-in-the-loop option to have a car found and vetted for you (kept as a lightweight form).
- **Admin** — analytics, the concierge pipeline, a model-enrichment worklist (AI-drafted, human-reviewed), and an extraction-health monitor.

## Architecture

```
Next.js 16 / React 19 / Tailwind 4          FastAPI + SQLAlchemy              PostgreSQL
(Vercel)                                     (Render, scale-to-zero)          (Neon, free tier)
        │                                             │                              │
  wizard ─────────────► /api/recommend ──► 6D engine over the model catalogue ───────┤
        │                                             │                              │
  paste URL ──────────► /api/listings/analyse         │                              │
                               │                       │                              │
                        httpx scrapers ── Gemini 2.5 Flash ── market aggregator ──────┘
                        (Standvirtual/OLX)   (verdict, narrative)   (fuel-segmented p10/p50/p90)
```

Market data is cached and written back, so repeat analyses don't re-scrape; a monthly script ([`backend/scripts/monthly_refresh.py`](./backend/scripts/monthly_refresh.py)) rebuilds prices and reliability from a residential connection (datacenter IPs get bot-blocked — see below).

## Engineering problems worth reading about

The interesting parts weren't the CRUD — they were making an inherently messy, adversarial data source produce something trustworthy, and being honest in software when the data isn't sure.

- **Resilient extraction pipeline.** Listing detail is parsed through layered fallbacks — `__NEXT_DATA__` SSR JSON → JSON-LD → HTML heuristics → Portuguese label patterns — each scored with a data-quality grade so degradation is *visible*, not silent.
- **Bot protection is real.** Standvirtual/OLX block datacenter IPs. The scrapers are httpx-first (Playwright is an opt-in fallback, not the default), retry with browser-like headers, detect sold/removed listings (HTTP 410) and say so cleanly, and an **extraction-health panel** shows price-completeness over time so a block is seen before users feel it.
- **Market comparison that's actually like-for-like.** Prices are **segmented by fuel at the source** (a plug-in hybrid was being priced against base diesels — a 29%-overpriced verdict that was pure noise), and BMW series are scoped so a "Serie 3" search isn't polluted by the whole BMW range.
- **Self-healing catalogue.** A model not in the database is **registered on first sight** rather than fuzzy-matched to a different one (a Range Rover Velar was resolving to an Evoque on the shared word "range"); a compatibility guard blocks that class of mismatch.
- **Honesty gates.** When the comparable pool is too thin (< 5 listings), the tool *refuses* to drive a price verdict off a noisy median and says "dados limitados" instead of inventing a confident-but-wrong answer. The analysis shows what it compared against ("comparado com 22 anúncios de… 2016–2019") so the number is believable.

## Product thinking (and an honest conclusion)

The most useful decision was a negative one. I prototyped per-analysis pricing and realised it can't work — people browse dozens of listings, so charging per analysis is absurd. I went deep on what a buyer would actually *pay* for and concluded the defensible value is human judgment at the moment of commitment (the concierge), not the data tool — and that the scraped data can never be complete or accurate enough to be a standalone paid product competing with the marketplaces themselves.

So I stopped optimising for revenue and re-cast the project honestly: **a genuinely useful free tool + a portfolio piece that demonstrates product and engineering judgment.** Knowing when something *isn't* a business is itself a product skill, and I'd rather show that than pretend.

## Running it

- Local dev and full deploy (Neon + Render + Vercel): see [`DEPLOY.md`](./DEPLOY.md).
- Monthly data refresh: `cd backend && DATABASE_URL=… python -m scripts.monthly_refresh`.

## Tech

**Frontend:** Next.js 16, React 19, Tailwind 4, shadcn/ui, TypeScript · **Backend:** FastAPI, SQLAlchemy, PostgreSQL · **AI:** Google Gemini 2.5 Flash · **Scraping:** httpx + BeautifulSoup (Playwright optional) · **Hosting:** Vercel · Render · Neon.

## Testing & CI

Unit tests cover the deterministic decision logic — negotiation figures, the
scam/anomaly gate, cost-of-ownership + Portuguese IUC, the model-resolution
compatibility guard, and the listing-extraction parsers — as real regression
tests for the bugs that once broke trust. GitHub Actions runs `pytest` and the
frontend build on every push (`backend/tests`, `.github/workflows/ci.yml`).

## Agentic catalogue curator

The catalogue can never be *complete*, so I built an agent to keep it filled
([`backend/app/services/curator_agent.py`](./backend/app/services/curator_agent.py)).
It's a real agent, not a wrapped prompt: a **goal** (no model without reliability
data), a **loop** that decides per model, four **tools** (read gaps → research →
validate → write), and **confidence-based routing** — it auto-saves what it's
sure of and leaves the rest in the admin's pending list for one-click human
review. The LLM is just the reasoning engine inside one tool; the agent is the
orchestration and the guards around it. Runs on demand (`python -m scripts.curate`),
so it costs nothing to keep alive.

## What I'd do next

- Give the curator's research tool live **web-search grounding** (it's closed-book today) — the tool boundary is already clean, so it's a drop-in upgrade.
- Finer within-fuel variant matching, and surfacing price history more richly as the snapshot log fills.
