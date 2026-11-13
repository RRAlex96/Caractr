import os
import time
import hmac
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import models
from app.routers import recommend
from app.routers import analytics
from app.routers import listings
from app.routers import concierge
from app.routers import admin_dashboard
from app.db.database import SessionLocal

# ── Rate limiting ──────────────────────────────────────────────────────────────
# Sliding-window counter per IP. No external dependencies.
# Limits: 10 req/min on expensive LLM endpoints; 30/min on concierge (spam); 60/min elsewhere.

_RATE_LIMITS: dict[str, int] = {
    "/api/recommend":         int(os.getenv("RATE_LIMIT_LLM",       "10")),
    "/api/listings/analyse":  int(os.getenv("RATE_LIMIT_LLM",       "10")),
    "/api/concierge":         int(os.getenv("RATE_LIMIT_CONCIERGE",  "5")),
}
_LIMIT_GLOBAL = int(os.getenv("RATE_LIMIT_GLOBAL", "60"))
_WINDOW       = 60.0  # seconds

_counters: dict[str, list[float]] = defaultdict(list)
_MAX_COUNTER_KEYS = 10_000  # evict stale keys if dict grows beyond this
_last_eviction = 0.0


def _get_client_ip(request: Request) -> str:
    """
    Resolve the real client IP.
    Only trust X-Forwarded-For when TRUSTED_PROXY_COUNT > 0 (set by your reverse proxy config).
    Without this env var, always use the direct connection IP to prevent spoofing.
    """
    trusted = int(os.getenv("TRUSTED_PROXY_COUNT", "0"))
    if trusted > 0:
        forwarded = request.headers.get("X-Forwarded-For", "")
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        # Take the Nth-from-right IP where N = trusted proxy count
        if len(ips) >= trusted:
            return ips[-trusted]
    return request.client.host if request.client else "unknown"


def _evict_stale_counters() -> None:
    """Remove keys with no recent timestamps. Called periodically to bound memory."""
    global _last_eviction
    now = time.monotonic()
    if now - _last_eviction < 120:  # at most every 2 min
        return
    _last_eviction = now
    stale = [k for k, ts in _counters.items() if not ts or (now - ts[-1]) > _WINDOW * 2]
    for k in stale:
        del _counters[k]


def _is_rate_limited(ip: str, path: str) -> bool:
    now   = time.monotonic()
    key   = f"{ip}:{path}"
    limit = _RATE_LIMITS.get(path, _LIMIT_GLOBAL)

    _counters[key] = [t for t in _counters[key] if now - t < _WINDOW]

    if len(_counters[key]) >= limit:
        return True

    _counters[key].append(now)

    # Periodic eviction to prevent unbounded growth
    if len(_counters) > _MAX_COUNTER_KEYS:
        _evict_stale_counters()

    return False


# ── Scheduler intervals ────────────────────────────────────────────────────────

_MARKET_REFRESH_INTERVAL_DAYS      = 7   # Weekly — non-negotiable for accurate pricing
_RELIABILITY_REFRESH_INTERVAL_DAYS = 7


# ── Background loops ───────────────────────────────────────────────────────────

def _check_market_freshness() -> int:
    """
    Check how many days since last market refresh.
    Returns days since last refresh, or 999 if never refreshed.
    Used to skip redundant refreshes on Railway redeploys.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import text
        row = db.execute(text("""
            SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at))) / 86400 AS days_ago
            FROM market_price_stats
            WHERE source = 'live_scraped'
        """)).fetchone()
        if row and row[0] is not None:
            return int(row[0])
        return 999
    except Exception:
        return 999
    finally:
        db.close()


def _run_market_refresh_sync() -> None:
    """Sync wrapper — runs in thread pool so it never blocks the event loop."""
    db = SessionLocal()
    try:
        print("[SCHEDULER] Starting weekly market data refresh...")

        from app.services.market_scraper_runner import run_market_scraper
        scrape_result = run_market_scraper(db)
        print(f"[SCHEDULER] Scraper: {scrape_result}")

        from app.services.market_aggregator import run_aggregation
        agg_result = run_aggregation(db)
        print(f"[SCHEDULER] Aggregation: {agg_result}")

        from app.services.depreciation import run_depreciation_curves
        dep_result = run_depreciation_curves(db)
        print(f"[SCHEDULER] Depreciation: {dep_result}")

    except Exception as e:
        print(f"[SCHEDULER] Market refresh error: {e}")
        db.rollback()
    finally:
        db.close()


async def _market_refresh_loop() -> None:
    """
    Weekly background task:
    1. Bulk-scrape Standvirtual + OLX listings per generation
    2. Aggregate into p10/p50/p90 + MAD per (generation, year, seller_type)
    3. Denormalise latest p50 + band to generations table

    Smart startup: checks if data was refreshed recently. If < 6 days old,
    skips to the next weekly window. Avoids redundant work on Railway redeploys.
    """
    await asyncio.sleep(120)  # 2 min cold-start delay

    # Check freshness — skip if recently refreshed
    days_since = await asyncio.get_event_loop().run_in_executor(
        None, _check_market_freshness
    )
    if days_since < 6:
        next_run = (7 - days_since) * 24 * 3600
        print(f"[SCHEDULER] Market data is {days_since}d old — "
              f"skipping, next refresh in {7 - days_since}d")
        await asyncio.sleep(next_run)
    else:
        print(f"[SCHEDULER] Market data is {days_since}d old — refreshing now")

    while True:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_market_refresh_sync)
        await asyncio.sleep(_MARKET_REFRESH_INTERVAL_DAYS * 24 * 3600)


def _run_reliability_sync() -> None:
    """Sync wrapper — runs in thread pool so it never blocks the event loop."""
    # Each source runs with its own session so one failing (network, site
    # change) never skips the others or the scorer. KBA (car-recalls.eu) is
    # not run: the site was restructured; German recalls reach Safety Gate.
    from app.scrapers.safety_gate import ingest_safety_gate
    from app.scrapers.nhtsa import ingest_nhtsa_all
    from app.services.reliability_runner import run_reliability_scorer

    print("[SCHEDULER] Starting reliability update...")
    for label, step in (
        ("Safety Gate",     lambda db: ingest_safety_gate(db, max_pages=10, sleep_seconds=1.0)),
        ("NHTSA",           lambda db: ingest_nhtsa_all(db, sleep_seconds=0.4)),
        ("Bayesian scorer", run_reliability_scorer),
    ):
        db = SessionLocal()
        try:
            print(f"[SCHEDULER] {label}: {step(db)}")
        except Exception as e:
            print(f"[SCHEDULER] {label} error: {e}")
            db.rollback()
        finally:
            db.close()


async def _reliability_scorer_loop() -> None:
    """
    Weekly background task:
    1. Ingest new EU Safety Gate alerts into reliability_evidence
    2. Ingest NHTSA recalls + complaints (incremental)
    3. Ingest KBA recalls via car-recalls.eu (incremental)
    4. Run the Bayesian scorer for all generations

    All sync work runs in a thread to keep the event loop responsive.
    """
    await asyncio.sleep(600)  # 10 min cold-start delay
    while True:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_reliability_sync)
        await asyncio.sleep(_RELIABILITY_REFRESH_INTERVAL_DAYS * 24 * 3600)


def _run_data_retention_sync() -> None:
    """Sync wrapper — runs in thread pool so it never blocks the event loop."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("""
            WITH
              del_sessions AS (
                DELETE FROM recommendation_sessions
                WHERE created_at < NOW() - INTERVAL '90 days'
                RETURNING id
              ),
              del_concierge AS (
                DELETE FROM concierge_requests
                WHERE created_at < NOW() - INTERVAL '12 months'
                RETURNING id
              ),
              del_analytics AS (
                DELETE FROM analytics_events
                WHERE created_at < NOW() - INTERVAL '24 months'
                RETURNING id
              ),
              del_feedback AS (
                DELETE FROM user_feedback
                WHERE created_at < NOW() - INTERVAL '12 months'
                RETURNING id
              )
            SELECT
              (SELECT COUNT(*) FROM del_sessions)  AS sessions_deleted,
              (SELECT COUNT(*) FROM del_concierge) AS concierge_deleted,
              (SELECT COUNT(*) FROM del_analytics) AS analytics_deleted,
              (SELECT COUNT(*) FROM del_feedback)  AS feedback_deleted
        """))
        row = result.fetchone()
        db.commit()
        if row and any(row):
            print(f"[RETENTION] Deleted: sessions={row[0]}, concierge={row[1]}, analytics={row[2]}, feedback={row[3]}")
    except Exception as e:
        print(f"[RETENTION] Error during data retention cleanup: {e}")
        db.rollback()
    finally:
        db.close()


async def _data_retention_loop() -> None:
    """
    Daily RGPD data retention enforcement.
    Deletes personal data per the retention periods declared in the privacy policy:
      - recommendation_sessions: 90 days
      - concierge_requests:      12 months
      - analytics_events:        24 months
      - user_feedback:           12 months

    SQL runs in a thread to keep the event loop responsive.
    """
    await asyncio.sleep(3600)  # First run 1h after startup
    while True:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_data_retention_sync)
        await asyncio.sleep(24 * 3600)  # Run daily


# ── Playwright bootstrap ──────────────────────────────────────────────────────

_PW_RUNTIME_PATH = "/tmp/.pw-browsers"


def _ensure_playwright_browsers() -> None:
    """
    Install Playwright browsers at runtime if not present.

    Nixpacks discards ~/.cache during the Docker build, so browser binaries
    installed at build time don't survive to the runtime container.

    Installs BOTH chromium (full browser) and chromium-headless-shell
    (the lightweight binary Playwright uses for headless=True in v1.49+).
    Downloads once at startup (~30s) into /tmp, persists until container restart.
    """
    import subprocess

    # Quick check: does the headless shell already exist?
    for base in [
        os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
        _PW_RUNTIME_PATH,
        os.path.expanduser("~/.cache/ms-playwright"),
    ]:
        if base and os.path.isdir(base):
            for root, dirs, files in os.walk(base):
                if "headless_shell" in root and ("chrome-headless-shell" in files or "headless_shell" in files):
                    print(f"[STARTUP] Playwright: found headless shell at {root}")
                    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = base
                    return

    # No headless shell found — install system deps + browsers
    print(f"[STARTUP] Playwright: no browsers found, installing to {_PW_RUNTIME_PATH}...")
    os.makedirs(_PW_RUNTIME_PATH, exist_ok=True)
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": _PW_RUNTIME_PATH}

    # 1. Install system dependencies (needs root — Railway runs as root)
    try:
        result = subprocess.run(
            ["playwright", "install-deps", "chromium"],
            env=env, capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print("[STARTUP] Playwright: system deps installed OK")
        else:
            print(f"[STARTUP] Playwright: install-deps warning: {result.stderr[:200]}")
    except Exception as e:
        print(f"[STARTUP] Playwright: install-deps error: {e}")

    # 2. Install browser binaries
    for browser in ["chromium", "chromium-headless-shell"]:
        try:
            result = subprocess.run(
                ["playwright", "install", browser],
                env=env, capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                print(f"[STARTUP] Playwright: {browser} installed OK")
            else:
                print(f"[STARTUP] Playwright: {browser} install failed: {result.stderr[:200]}")
        except Exception as e:
            print(f"[STARTUP] Playwright: {browser} install error: {e}")

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _PW_RUNTIME_PATH
    print(f"[STARTUP] PLAYWRIGHT_BROWSERS_PATH={_PW_RUNTIME_PATH}")


# ── App setup ──────────────────────────────────────────────────────────────────

def _missing_columns(db, table: str, columns: list[str]) -> bool:
    from sqlalchemy import text
    have = {r[0] for r in db.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table})}
    return any(c not in have for c in columns)


def _run_startup_migrations() -> None:
    """Idempotent schema migrations that run on every deploy.

    Lock-safe: ALTER TABLE takes an ACCESS EXCLUSIVE lock *before* checking
    IF NOT EXISTS, so running it on every boot made a cold start queue behind
    any open transaction on `generations` (e.g. the monthly refresh) — and
    every other query on that table then queued behind the boot. Now the
    column ALTERs only run when a column is actually missing, and the whole
    migration fails fast (lock_timeout) instead of waiting; it simply retries
    on the next boot.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("SET LOCAL lock_timeout = '4s'"))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS price_observations (
                id                SERIAL PRIMARY KEY,
                model_id          INTEGER REFERENCES vehicle_models(id),
                generation_id     INTEGER REFERENCES generations(id),
                vehicle_year      INTEGER,
                km                INTEGER,
                price             INTEGER NOT NULL CHECK (price BETWEEN 500 AND 500000),
                fuel_type         VARCHAR(30),
                seller_type       VARCHAR(20) DEFAULT 'desconhecido',
                source_type       VARCHAR(20) NOT NULL,
                source_domain     VARCHAR(100),
                source_url        TEXT,
                extraction_method VARCHAR(30),
                data_quality      REAL CHECK (data_quality BETWEEN 0 AND 1),
                observation_type  VARCHAR(20) NOT NULL DEFAULT 'user_analysis',
                observed_at       TIMESTAMPTZ DEFAULT now(),
                UNIQUE (source_url)
            )
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_po_model_year
                ON price_observations(model_id, vehicle_year)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_po_observed
                ON price_observations(observed_at DESC)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_po_source_domain
                ON price_observations(source_domain, observed_at DESC)
        """))
        # Market snapshot columns (engine, gearbox, body variant of each listing).
        # The stored-pool fallback of the ad analysis filters on them.
        if _missing_columns(db, "price_observations",
                            ["engine_power_hp", "engine_cc", "gearbox", "powertrain",
                             "variant", "version", "origin", "listed_at"]):
            from app.services.market_snapshot import SNAPSHOT_COLUMNS_SQL
            db.execute(text(SNAPSHOT_COLUMNS_SQL))
        # v54: depreciation columns on generations
        if _missing_columns(db, "generations",
                            ["depreciation_pct_year", "depreciation_curve", "depreciation_as_of"]):
            db.execute(text("""
                ALTER TABLE generations
                    ADD COLUMN IF NOT EXISTS depreciation_pct_year  NUMERIC(5,4),
                    ADD COLUMN IF NOT EXISTS depreciation_curve     JSONB NOT NULL DEFAULT '[]'::jsonb,
                    ADD COLUMN IF NOT EXISTS depreciation_as_of     DATE
            """))
        # Bayesian/curator reliability columns on generations. Older seed
        # snapshots stop at 'platform', so enrichment + the curator agent (and
        # the admin pending query) need these added idempotently.
        if _missing_columns(db, "generations",
                            ["reliability_score", "reliability_ci_low", "reliability_ci_high",
                             "reliability_data_quality", "reliability_sources"]):
            db.execute(text("""
                ALTER TABLE generations
                    ADD COLUMN IF NOT EXISTS reliability_score        NUMERIC(3,1),
                    ADD COLUMN IF NOT EXISTS reliability_ci_low       NUMERIC(3,1),
                    ADD COLUMN IF NOT EXISTS reliability_ci_high      NUMERIC(3,1),
                    ADD COLUMN IF NOT EXISTS reliability_data_quality VARCHAR(20),
                    ADD COLUMN IF NOT EXISTS reliability_sources      JSONB
            """))
        # v59: fuel restriction on a generation (e.g. the electric Fiat 500e, sold
        # alongside the petrol 500) so the year lookup can tell overlapping cars apart.
        if _missing_columns(db, "generations", ["fuel_type"]):
            db.execute(text("""
                ALTER TABLE generations
                    ADD COLUMN IF NOT EXISTS fuel_type VARCHAR(20)
            """))
        # v55: admin_notes for concierge pipeline (internal operator field)
        if _missing_columns(db, "concierge_requests", ["admin_notes"]):
            db.execute(text("""
                ALTER TABLE concierge_requests
                    ADD COLUMN IF NOT EXISTS admin_notes TEXT
            """))
        # v56: append-only listing snapshot log (price history + relisting/rollback moat)
        # Unlike price_observations (one row per URL, overwritten), this NEVER overwrites —
        # every observation is a new row. Foundation for price-history graphs,
        # days-on-market, relisting detection, and odometer-rollback detection.
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS listing_snapshots (
                id                    SERIAL PRIMARY KEY,
                source_url            TEXT NOT NULL,
                source_domain         VARCHAR(100),
                normalized_listing_id INTEGER,
                model_id              INTEGER,
                brand_name            VARCHAR(80),
                model_name            VARCHAR(120),
                year                  INTEGER,
                km                    INTEGER,
                price                 INTEGER,
                fuel_type             VARCHAR(30),
                seller_type           VARCHAR(20),
                photo_count           INTEGER,
                identity_hash         VARCHAR(64),
                observed_at           TIMESTAMPTZ DEFAULT now()
            )
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_snap_url
                ON listing_snapshots(source_url, observed_at DESC)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_snap_identity
                ON listing_snapshots(identity_hash, observed_at DESC)
        """))
        # Reconcile the listings tables. Older seed snapshots created a very
        # different raw_listings/normalized_listings design (url/mileage_km, with
        # NOT NULL columns the app never fills). Detect that by the absence of
        # raw_listings.source_url and recreate both to the current schema. These
        # tables hold only scraped/analysis cache (re-derivable), and the guard
        # means this runs at most once — it's a no-op once the schema is correct.
        _needs_listings_fix = not db.execute(text("""
            SELECT EXISTS(SELECT 1 FROM information_schema.columns
                WHERE table_name = 'raw_listings' AND column_name = 'source_url')
        """)).scalar()
        if _needs_listings_fix:
            db.execute(text("DROP TABLE IF EXISTS normalized_listings CASCADE"))
            db.execute(text("DROP TABLE IF EXISTS raw_listings CASCADE"))
            db.execute(text("""
                CREATE TABLE raw_listings (
                    id          SERIAL PRIMARY KEY,
                    source      VARCHAR(30),
                    source_url  TEXT UNIQUE,
                    description TEXT,
                    seller_type VARCHAR(20),
                    photo_count INTEGER,
                    scraped_at  TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            db.execute(text("""
                CREATE TABLE normalized_listings (
                    id                 SERIAL PRIMARY KEY,
                    raw_listing_id     INTEGER UNIQUE REFERENCES raw_listings(id),
                    model_id           INTEGER,
                    brand_name         VARCHAR(80),
                    model_name         VARCHAR(120),
                    year               INTEGER,
                    km                 INTEGER,
                    price              INTEGER,
                    fuel_type          VARCHAR(30),
                    seller_type        VARCHAR(20),
                    description        TEXT,
                    photo_count        INTEGER,
                    listing_age_days   INTEGER,
                    km_per_year        FLOAT,
                    price_delta        FLOAT,
                    deal_tier          VARCHAR(20),
                    deal_score         FLOAT,
                    llm_analysis       JSONB,
                    analysis_cached_at TIMESTAMPTZ,
                    created_at         TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            print("[STARTUP] Reconciled stale listings tables -> current schema")
        db.commit()
        print("[STARTUP] Migrations OK (price_observations + depreciation + admin_notes + listing_snapshots + listings reconcile)")
    except Exception as e:
        print(f"[STARTUP] Migration error: {e}")
        db.rollback()
    finally:
        db.close()


# Cost controls for the portfolio deploy:
# - Playwright/Chromium is opt-in (scraping is httpx-first), so we skip the
#   heavy browser bootstrap unless it's explicitly enabled.
# - The always-on background loops keep the process busy and defeat Railway's
#   scale-to-zero. Off by default; the monthly refresh runs on demand instead
#   (scripts/monthly_refresh.py or POST /api/admin/refresh). Set
#   ENABLE_BACKGROUND_JOBS=true to restore the in-process schedulers.
_ENABLE_BACKGROUND_JOBS = os.getenv("ENABLE_BACKGROUND_JOBS", "false").lower() == "true"
_ALLOW_PLAYWRIGHT = os.getenv("ALLOW_PLAYWRIGHT_FALLBACK", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run idempotent schema migrations
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_startup_migrations)

    # Bootstrap Playwright browsers only when the browser fallback is enabled —
    # otherwise this is wasted memory/time and blocks a cheap cold start.
    if _ALLOW_PLAYWRIGHT:
        await loop.run_in_executor(None, _ensure_playwright_browsers)

    # LLM selftest removed from startup to conserve API quota.
    # Use GET /api/health/llm for on-demand testing.

    if _ENABLE_BACKGROUND_JOBS:
        asyncio.create_task(_market_refresh_loop())
        asyncio.create_task(_reliability_scorer_loop())
        asyncio.create_task(_data_retention_loop())
        print("[STARTUP] Background jobs ENABLED")
    else:
        print("[STARTUP] Background jobs disabled (scale-to-zero friendly) — "
              "run monthly refresh on demand")
    yield


app = FastAPI(
    title="Caractr API",
    description="Assistente inteligente de compra de carro para Portugal",
    version="4.6.0",
    lifespan=lifespan,
)


# ── Middlewares ────────────────────────────────────────────────────────────────

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]          = "DENY"
    response.headers["Referrer-Policy"]          = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"]         = "1; mode=block"
    response.headers["Permissions-Policy"]       = "geolocation=(), microphone=(), camera=()"
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/"):
        ip = _get_client_ip(request)
        if _is_rate_limited(ip, path):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Tenta novamente em breve."},
                headers={"Retry-After": "60"},
            )
    return await call_next(request)


_raw_origins    = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Token"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    try:
        from app.services.llm_client import llm_available, _MODEL, llm_selftest
        llm_ok = llm_available()
        model = _MODEL
    except Exception:
        llm_ok = False
        model = "unknown"

    # Playwright status
    pw_browsers = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "not_set")

    return {
        "status": "ok",
        "app": "Caractr",
        "version": "4.10.1",
        "llm_available": llm_ok,
        "llm_model": model,
        "playwright_browsers": pw_browsers,
    }


@app.get("/api/health/llm")
def health_llm():
    """Live LLM selftest — calls Gemini with a minimal prompt."""
    try:
        from app.services.llm_client import llm_selftest
        result = llm_selftest()
        return {"llm_selftest": result}
    except Exception as e:
        return {"llm_selftest": f"error:{type(e).__name__}:{e}"}


app.include_router(models.router)
app.include_router(recommend.router)
app.include_router(analytics.router)
app.include_router(listings.router)
app.include_router(concierge.router)
app.include_router(admin_dashboard.router)
