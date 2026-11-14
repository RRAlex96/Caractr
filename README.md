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
- **Deal-breaker warnings you can trust.** Official recalls (EU Safety Gate, NHTSA) and critical known failures are shown as a loud warning — never a silent exclusion — with the source and the production period, filtered to the listing's year (a 2020 Kuga isn't warned about a 2024-only recall). Recall→car matching is deliberately high-precision: auditing the first live ingest found fuzzy matching pinning an S-Klasse recall on the A-Class and ID.4 on ID.3, so it now accepts whole-word matches only and rejects generations whose production years don't overlap. Every audited false positive is a regression test.
- **Data that can't poison itself.** Marketplace search pages include promoted ads, so a "Golf 2020+" scrape once contained a Ferrari Roma that set a Golf's price at 52 000 €. Listings are now validated (brand, model, generation years, placeholder prices) and published prices use a MAD-trimmed median with a minimum sample, so the worst case is "price not refreshed", never "price wrong".

## Product thinking (and an honest conclusion)

The most useful decision was a negative one. I prototyped per-analysis pricing and realised it can't work — people browse dozens of listings, so charging per analysis is absurd. I went deep on what a buyer would actually *pay* for and concluded the defensible value is human judgment at the moment of commitment (the concierge), not the data tool — and that the scraped data can never be complete or accurate enough to be a standalone paid product competing with the marketplaces themselves.

So I stopped optimising for revenue and re-cast the project honestly: **a genuinely useful free tool + a portfolio piece that demonstrates product and engineering judgment.** Knowing when something *isn't* a business is itself a product skill, and I'd rather show that than pretend.

## Running it

- Local dev and full deploy (Neon + Render + Vercel): see [`DEPLOY.md`](./DEPLOY.md).
- Monthly data refresh: `cd backend && python -m scripts.monthly_refresh` against whatever `backend/.env` points at (market snapshot → prices → engine years → depreciation → recalls → retention; each step isolated, summary + non-zero exit on failure; `--skip market,nhtsa` to skip steps). The [`market-snapshot`](./.github/workflows/market-snapshot.yml) workflow runs it on the 2nd of each month once a `DATABASE_URL` secret is set, after backing up the reference data. The AI curator runs only with `RUN_CURATOR=1`.

## The reference data

Every figure the site shows a buyer comes from a few tables: models and their generations, engines, market prices by model and year, brand reliability. They are kept trustworthy in three layers:

- **Sources.** Generation years and engine specifications were checked row by row against manufacturer pages, Wikipedia or auto-data.net; each row records the page (`generations.source_url`, `engines.source`). Market prices are measured from every Standvirtual listing of the catalogue's makes (`price_observations`, `market_snapshot_runs`). Brand reliability rests on published studies, listed per brand in `brand_reliability`.
- **Constraints.** Postgres refuses a bad row: impossible power, consumption or scores, a model twice under one name, two generations of a model claiming the same year ([`migration_v64_safeties.sql`](./backend/seeds/migration_v64_safeties.sql)).
- **Audit.** `python -m scripts.data_audit` asks the database the questions that have gone wrong before — 46 checks in six dimensions (structure, plausibility, market coverage, freshness, provenance, safeties) — and scores the result. `GET /api/health/data` runs it in production; the daily [`health`](./.github/workflows/health.yml) workflow fails on a critical check, such as a market snapshot gone stale.

Changing the data: write a numbered, idempotent migration in `backend/seeds/`, add it to `scripts/load_seed.py`, rehearse it twice on a copy of production, back up, apply with `psql -v ON_ERROR_STOP=1`, run the audit.

## Tech

**Frontend:** Next.js 16, React 19, Tailwind 4, shadcn/ui, TypeScript · **Backend:** FastAPI, SQLAlchemy, PostgreSQL · **AI:** Google Gemini 3.5 Flash via `google-genai` (automatic fallback model on 404/5xx; template fallback when the LLM is unavailable) · **Scraping:** httpx + BeautifulSoup (Playwright optional) · **Hosting:** Vercel · Render · Neon.

## Testing & CI

About 770 tests cover the deterministic decision logic — the recommendation
engine (profile, constraints, scoring, diversity), negotiation figures, the
scam/anomaly gate, cost-of-ownership + Portuguese IUC, recall and listing
matching, robust price stats, the LLM client's fallback behaviour, and the
extraction parsers — mostly as regression tests for real bugs that once broke
trust. A guard test fails the build on a SQLAlchemy pitfall (`:param::jsonb`
is silently never bound) that had stopped every recall from being saved.
GitHub Actions runs `pytest` (network tests deselected) and the frontend build
on every push (`backend/tests`, `.github/workflows/ci.yml`), and builds the
whole database from the repository on an empty Postgres — schema, every
migration, the recent ones twice — then runs the audit's structural checks.

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

- The curator's research tool supports **web-search grounding**, but Search grounding has little free-tier quota, so it mostly runs closed-book. By design, unsourced findings can never raise a deal-breaker — enabling billing for grounding is the upgrade that unlocks sourced critical-failure warnings.
- Rebuild the KBA recall source (car-recalls.eu was restructured) — lower priority, since German recalls also reach EU Safety Gate.
- Finer within-fuel variant matching, and surfacing price history more richly as the snapshot log fills.
