"""The fetch relay: off without config; a 403 from Standvirtual goes to the
relay once instead of retrying from the refused address."""
import asyncio

import httpx

from app.scrapers import relay, standvirtual

NEXT = ('<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"advert":{}}}}</script></html>')


async def _nosleep(*_):
    return None


class _Resp:
    def __init__(self, status, text=""):
        self.status_code, self.text = status, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(str(self.status_code), request=None, response=None)


def _client(responses, calls):
    class C:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, **kw):
            calls.append((url, kw))
            return responses.pop(0)
    return C


def test_relay_off_without_config(monkeypatch):
    monkeypatch.delenv("FETCH_RELAY_URL", raising=False)
    monkeypatch.delenv("FETCH_RELAY_TOKEN", raising=False)
    assert not relay.relay_enabled()
    assert asyncio.run(relay.relay_fetch("https://www.standvirtual.com/carros/anuncio/x")) is None


def test_sv_403_uses_relay_once(monkeypatch):
    monkeypatch.setenv("FETCH_RELAY_URL", "https://relay.example/api/fetch-ad")
    monkeypatch.setenv("FETCH_RELAY_TOKEN", "t0ken")
    monkeypatch.setattr(standvirtual.asyncio, "sleep", _nosleep)
    calls = []
    # direct fetch refused, then the relay answers with the page
    fake = _client([_Resp(403), _Resp(200, NEXT)], calls)
    monkeypatch.setattr(standvirtual.httpx, "AsyncClient", fake)
    monkeypatch.setattr(relay.httpx, "AsyncClient", fake)
    url = "https://www.standvirtual.com/carros/anuncio/peugeot-208-ID1.html"
    out = asyncio.run(standvirtual.fetch_listing_detail(url))
    assert len(calls) == 2                       # no retries from the refused address
    assert calls[1][0] == "https://relay.example/api/fetch-ad"
    assert calls[1][1]["params"] == {"url": url}
    assert calls[1][1]["headers"] == {"x-relay-token": "t0ken"}
    assert out.get("_extraction_method") != "fetch_failed"


def test_sv_403_without_relay_still_reports_fetch_failed(monkeypatch):
    monkeypatch.delenv("FETCH_RELAY_URL", raising=False)
    monkeypatch.setattr(standvirtual.asyncio, "sleep", _nosleep)
    calls = []
    monkeypatch.setattr(standvirtual.httpx, "AsyncClient", _client([_Resp(403)], calls))
    out = asyncio.run(standvirtual.fetch_listing_detail("https://www.standvirtual.com/carros/anuncio/x"))
    assert out["_extraction_method"] == "fetch_failed" and len(calls) == 1
