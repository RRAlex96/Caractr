"""
Fetch relay for ad pages that refuse our server.

Standvirtual and OLX (same owner, same firewall) answer 403 to every request
from Render's shared addresses, while other networks get the page. When a
direct fetch of an ad page is refused, the backend asks the frontend's host
(Vercel, route /api/fetch-ad) for that single page instead. The relay only
serves ad pages of those two sites and requires a shared secret.

    FETCH_RELAY_URL    https://caractr.pt/api/fetch-ad
    FETCH_RELAY_TOKEN  same value as on Vercel

Without both variables the relay is off and behaviour is unchanged.
"""
import os

import httpx


def relay_enabled() -> bool:
    return bool(os.getenv("FETCH_RELAY_URL") and os.getenv("FETCH_RELAY_TOKEN"))


async def relay_fetch(url: str) -> str | None:
    """The page's HTML via the relay, or None (relay off, refused, or failed)."""
    if not relay_enabled():
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                os.environ["FETCH_RELAY_URL"],
                params={"url": url},
                headers={"x-relay-token": os.environ["FETCH_RELAY_TOKEN"]},
            )
        if resp.status_code == 200 and resp.text:
            print(f"[RELAY] OK {url}")
            return resp.text
        print(f"[RELAY] {resp.status_code} for {url}: {resp.text[:120]}")
    except Exception as e:  # never break an analysis
        print(f"[RELAY] error for {url}: {e}")
    return None
