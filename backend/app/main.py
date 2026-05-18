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


def _is_rate_limited(ip: str, path: str) -> bool:
    now   = time.monotonic()
    key   = f"{ip}:{path}"
    limit = _RATE_LIMITS.get(path, _LIMIT_GLOBAL)

    _counters[key] = [t for t in _counters[key] if now - t < _WINDOW]

    if len(_counters[key]) >= limit:
        return True

    _counters[key].append(now)
    return False


# ── Scheduler intervals ────────────────────────────────────────────────────────

_MARKET_REFRESH_INTERVAL_DAYS      = 30
_RELIABILITY_REFRESH_INTERVAL_DAYS = 7


# ── Background loops ───────────────────────────────────────────────────────────

async def _market_refresh_loop() -> None:
    """
    Monthly background task:
    1. Bulk-scrape Standvirtual + OLX listings per generation
    2. Aggregate into p10/p50/p90 + MAD per (generation, year, seller_type)
    3. Denormalise latest p50 + band to generations table
    """
    await asyncio.sleep(_MARKET_REFRESH_INTERVAL_DAYS * 24 * 3600)
    while True:
        db = SessionLocal()
        try:
            print("[SCHEDULER] Starting monthly market data refresh...")

            from app.services.market_scraper_runner import run_market_scraper
            scrape_result = run_market_scraper(db)
            print(f"[SCHEDULER] Scraper: {scrape_result}")

            from app.services.market_aggregator import run_aggregation
            agg_result = run_aggregation(db)
            print(f"[SCHEDULER] Aggregation: {agg_result}")

        except Exception as e:
            print(f"[SCHEDULER] Market refresh error: {e}")
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(_MARKET_REFRESH_INTERVAL_DAYS * 24 * 3600)


async def _reliability_scorer_loop() -> None:
    """
    Weekly background task:
    1. Ingest new EU Safety Gate alerts into reliability_evidence
    2. Ingest NHTSA recalls + complaints (incremental)
    3. Ingest KBA recalls via car-recalls.eu (incremental)
    4. Run the Bayesian scorer for all generations
    """
    await asyncio.sleep(600)  # 10 min cold-start delay
    while True:
        db = SessionLocal()
        try:
            print("[SCHEDULER] Starting weekly reliability update...")

            from app.scrapers.safety_gate import ingest_safety_gate
            sg_stats = ingest_safety_gate(db, max_pages=20, sleep_seconds=1.5)
            print(f"[SCHEDULER] Safety Gate: {sg_stats}")

            from app.scrapers.nhtsa import ingest_nhtsa_all
            nhtsa_stats = ingest_nhtsa_all(db, sleep_seconds=0.4)
            print(f"[SCHEDULER] NHTSA: {nhtsa_stats}")

            from app.scrapers.kba_recalls import ingest_kba_incremental
            kba_stats = ingest_kba_incremental(db, sleep_seconds=2.0)
            print(f"[SCHEDULER] KBA: {kba_stats}")

            from app.services.reliability_runner import run_reliability_scorer
            scorer_stats = run_reliability_scorer(db)
            print(f"[SCHEDULER] Bayesian scorer: {scorer_stats}")

        except Exception as e:
            print(f"[SCHEDULER] Reliability update error: {e}")
            db.rollback()
        finally:
            db.close()

        await asyncio.sleep(_RELIABILITY_REFRESH_INTERVAL_DAYS * 24 * 3600)


async def _data_retention_loop() -> None:
    """
    Daily RGPD data retention enforcement.
    Deletes personal data per the retention periods declared in the privacy policy:
      - recommendation_sessions: 90 days
      - concierge_requests:      12 months
      - analytics_events:        24 months
      - user_feedback:           12 months
    """
    await asyncio.sleep(3600)  # First run 1h after startup
    while True:
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

        await asyncio.sleep(24 * 3600)  # Run daily


# ── App setup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_market_refresh_loop())
    asyncio.create_task(_reliability_scorer_loop())
    asyncio.create_task(_data_retention_loop())
    yield


app = FastAPI(
    title="Caractr API",
    description="Assistente inteligente de compra de carro para Portugal",
    version="4.4.0",
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Token"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    try:
        from app.services.llm_client import llm_available, _MODEL
        llm_ok = llm_available()
        model = _MODEL
    except Exception:
        llm_ok = False
        model = "unknown"
    return {
        "status": "ok",
        "app": "Caractr",
        "version": "4.4.2",
        "llm_available": llm_ok,
        "llm_model": model,
    }


app.include_router(models.router)
app.include_router(recommend.router)
app.include_router(analytics.router)
app.include_router(listings.router)
app.include_router(concierge.router)
