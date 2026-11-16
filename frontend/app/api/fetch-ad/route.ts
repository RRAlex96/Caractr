import { timingSafeEqual } from "node:crypto"

// Fetch relay for the backend: Standvirtual and OLX answer 403 to every
// request from Render's shared addresses, while other networks get the page.
// The backend asks for a single ad page here only when its own fetch is
// refused. Locked down so it cannot be used as an open proxy:
//   - a shared secret (FETCH_RELAY_TOKEN, set on Vercel and on Render);
//   - only ad pages on standvirtual.com and olx.pt;
//   - one GET, no cookies or headers passed through, size-capped.

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const ALLOWED: { host: RegExp; path: RegExp }[] = [
  { host: /^(www\.)?standvirtual\.com$/, path: /^\/carros\/anuncio\// },
  { host: /^(www\.|m\.)?olx\.pt$/, path: /^\/d\/anuncio\// },
]
const MAX_BYTES = 3_000_000
const PROBE_URL = "https://www.standvirtual.com/carros/peugeot/208"

const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0 Safari/537.36",
  Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
}

function tokenOk(given: string | null): boolean {
  const want = process.env.FETCH_RELAY_TOKEN || ""
  if (!want || !given) return false
  const a = Buffer.from(given)
  const b = Buffer.from(want)
  return a.length === b.length && timingSafeEqual(a, b)
}

function allowed(raw: string): URL | null {
  try {
    const u = new URL(raw)
    if (u.protocol !== "https:") return null
    return ALLOWED.some((r) => r.host.test(u.hostname) && r.path.test(u.pathname)) ? u : null
  } catch {
    return null
  }
}

async function get(url: string) {
  return fetch(url, { headers: HEADERS, redirect: "follow", cache: "no-store", signal: AbortSignal.timeout(15000) })
}

export async function GET(req: Request) {
  const q = new URL(req.url).searchParams

  // Health probe: is this network refused too? Status only, no content.
  if (q.get("probe") === "1") {
    try {
      const r = await get(PROBE_URL)
      const body = await r.text()
      return Response.json({ status: r.status, readable: body.includes("__NEXT_DATA__") })
    } catch (e) {
      return Response.json({ status: 0, error: String(e).slice(0, 120) })
    }
  }

  if (!process.env.FETCH_RELAY_TOKEN) return new Response("relay not configured", { status: 503 })
  if (!tokenOk(req.headers.get("x-relay-token"))) return new Response("forbidden", { status: 403 })
  const target = allowed(q.get("url") || "")
  if (!target) return new Response("url not allowed", { status: 400 })

  try {
    const r = await get(target.toString())
    const body = await r.text()
    if (body.length > MAX_BYTES) return new Response("too large", { status: 502 })
    return new Response(body, {
      status: r.status,
      headers: { "content-type": "text/html; charset=utf-8", "x-upstream-status": String(r.status) },
    })
  } catch (e) {
    return new Response(`upstream error: ${String(e).slice(0, 120)}`, { status: 504 })
  }
}
