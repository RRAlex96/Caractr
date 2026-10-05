# Deploying Caractr (free, persistent)

The stack is split so nothing ever lapses on you:

| Piece | Host | Cost | Notes |
|-------|------|------|-------|
| Frontend (Next.js) | Vercel | free | already live at caractr.pt |
| Backend (FastAPI) | Render (free web service) | free | sleeps after ~15 min idle, cold-starts on next request; never lapses |
| Database (Postgres) | Neon | free | persistent; auto-suspends compute when idle, wakes on connect (`pool_pre_ping` handles it) |

Unlike Railway's credit model, none of these expire — so the demo is still alive when a recruiter clicks it months from now.

---

## 1. Get the data out of Railway first (time-sensitive)

If the Railway Postgres is still reachable (paused ≠ deleted), take a dump now — it's the cleanest migration (exact current catalogue + accumulated data):

```bash
# Railway dashboard → Postgres → "Connect" → copy the connection string
pg_dump "postgresql://…railway…" --no-owner --no-privileges -f caractr_dump.sql
```

If Railway already purged it, skip this — the catalogue is reproducible from the repo (step 3, Option B).

## 2. Create the Neon database

1. neon.tech → new project (free). Copy the connection string (includes `?sslmode=require`).
2. That string is your `DATABASE_URL` everywhere below.

## 3. Load the schema + data into Neon

**Option A — restore the Railway dump (preferred):**
```bash
psql "postgresql://…neon…?sslmode=require" -f caractr_dump.sql
```

**Option B — rebuild from the repo (if no dump):** one command, no `psql` needed —
```bash
cd backend
DATABASE_URL="postgresql://…neon…?sslmode=require" python -m scripts.load_seed
```
It loads `full_deploy_schema.sql` (schema + full catalogue) then
`migration_v51_generations.sql` (generation windows) and prints a sanity count.
Newer columns/tables (price_observations, depreciation, admin_notes,
listing_snapshots) are created automatically on first app boot. Then run
`python -m scripts.monthly_refresh` (see below) to populate live market data.

## 4. Deploy the backend to Render

1. render.com → New → **Blueprint** → connect this repo. It reads `render.yaml`.
2. Set the env vars (marked `sync: false`): `DATABASE_URL` (Neon), `GEMINI_API_KEY`,
   `RESEND_API_KEY`, `OPERATOR_EMAIL`, `ADMIN_TOKEN`, `ALLOWED_ORIGINS`.
3. Deploy. Confirm `https://<your-service>.onrender.com/api/health` returns `{"status":"ok"}`
   (first hit may take ~50s while it cold-starts).

## 5. Point the frontend at the new backend

On Vercel → project → Settings → Environment Variables:
```
NEXT_PUBLIC_API_URL = https://<your-service>.onrender.com
```
Redeploy the frontend. (`frontend/next.config.ts` also has this as a fallback — update it too so local builds match.)

## 6. Monthly data refresh (run from your own machine)

Standvirtual/OLX bot-block datacenter IPs, so refresh from a residential connection, pointed at Neon:

```bash
cd backend
DATABASE_URL="postgresql://…neon…?sslmode=require" python -m scripts.monthly_refresh
```

That re-scrapes + aggregates market prices, ingests recalls and re-scores reliability, and prunes per the retention policy. The always-on schedulers stay off (`ENABLE_BACKGROUND_JOBS=false`) so the backend can idle to zero.
