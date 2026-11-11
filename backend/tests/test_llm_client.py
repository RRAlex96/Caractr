"""
LLM client resilience — mocked, no network.

Locks in the behaviour that keeps the product demo-proof:
- a retired (404) or overloaded (5xx) primary model falls back to the
  fallback model instead of failing the request;
- a Search-grounding 429 pauses grounding only and never freezes plain
  generation (the curator's closed-book fallback must still work);
- thinking tokens are budgeted on top of the answer's max_tokens.
"""
from types import SimpleNamespace

import pytest

from app.services import llm_client as l


def _resp(text):
    return SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")], text=text,
                           prompt_feedback=None)


class FakeModels:
    def __init__(self, behaviour):
        self.behaviour = behaviour   # model name -> Exception | str
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append((model, config))
        b = self.behaviour[model]
        if isinstance(b, Exception):
            raise b
        return _resp(b)


@pytest.fixture
def client(monkeypatch):
    def install(behaviour):
        fake = SimpleNamespace(models=FakeModels(behaviour))
        monkeypatch.setattr(l, "_client", fake)
        monkeypatch.setattr(l, "_API_KEY", "test-key")
        monkeypatch.setattr(l, "_MODEL", "primary")
        monkeypatch.setattr(l, "_FALLBACK_MODEL", "fallback")
        monkeypatch.setattr(l, "_RETRIES", 0)
        monkeypatch.setattr(l, "_quota_exhausted_until", 0.0)
        monkeypatch.setattr(l, "_grounding_unavailable_until", 0.0)
        return fake.models
    return install


def test_retired_primary_falls_back(client):
    models = client({"primary": Exception("404 NOT_FOUND model retired"), "fallback": "OK"})
    assert l.generate_text("hi", max_tokens=10) == "OK"
    assert [m for m, _ in models.calls] == ["primary", "fallback"]


def test_overloaded_primary_falls_back(client):
    client({"primary": Exception("503 UNAVAILABLE overloaded"), "fallback": "OK"})
    assert l.generate_text("hi", max_tokens=10) == "OK"


def test_thinking_budget_added_on_top_of_answer(client, monkeypatch):
    monkeypatch.setattr(l, "_THINKING", 1024)
    models = client({"primary": "OK", "fallback": "OK"})
    l.generate_text("hi", max_tokens=100)
    cfg = models.calls[0][1]
    assert cfg.max_output_tokens == 100 + 1024
    assert cfg.thinking_config.thinking_budget == 1024


def test_quota_429_raises_quota_error(client):
    client({"primary": Exception("429 RESOURCE_EXHAUSTED"), "fallback": "OK"})
    with pytest.raises(l.QuotaExhaustedError):
        l.generate_text("hi", max_tokens=10)


def test_grounding_429_does_not_freeze_plain_generation(client):
    client({"primary": Exception("429 RESOURCE_EXHAUSTED"), "fallback": "OK"})
    with pytest.raises(l.LLMError) as ei:
        l.generate_grounded("research this")
    assert not isinstance(ei.value, l.QuotaExhaustedError)
    # Plain generation must not be in global cooldown afterwards.
    assert l._quota_exhausted_until == 0.0
    client({"primary": "closed-book OK", "fallback": "OK"})
    l._grounding_unavailable_until = 10**12  # grounding still paused
    assert l.generate_text("hi", max_tokens=10) == "closed-book OK"


def test_grounding_paused_short_circuits(client):
    models = client({"primary": "should not be called", "fallback": "x"})
    l._grounding_unavailable_until = 10**12
    with pytest.raises(l.LLMError):
        l.generate_grounded("research this")
    assert models.calls == []


def test_generate_json_strips_fences(client):
    client({"primary": '```json\n{"ok": true}\n```', "fallback": "x"})
    assert l.generate_json("hi") == {"ok": True}
