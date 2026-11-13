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


# ── Cost tracking ────────────────────────────────────────────────────────────

def _resp_with_usage(text, inp, out, think):
    r = _resp(text)
    r.usage_metadata = SimpleNamespace(prompt_token_count=inp, candidates_token_count=out,
                                       thoughts_token_count=think)
    return r


def test_cost_estimate_bills_thinking_as_output():
    # 1M in at $1.50 + (0.5M answer + 0.5M thinking) at $9.00
    assert l.estimate_cost_usd("gemini-3.5-flash", 1_000_000, 1_000_000) == 10.5
    usage = l._usage_from(_resp_with_usage("x", 1_000_000, 500_000, 500_000), "gemini-3.5-flash")
    assert usage["cost_usd"] == 10.5
    assert (usage["input_tokens"], usage["output_tokens"], usage["thinking_tokens"]) == \
        (1_000_000, 500_000, 500_000)


def test_flash_lite_is_not_priced_as_flash():
    assert l.estimate_cost_usd("gemini-3.5-flash-lite", 1_000_000, 0) == 0.30
    assert l.estimate_cost_usd("gemini-3.5-flash-lite-001", 0, 1_000_000) == 2.50
    assert l.estimate_cost_usd("gemini-3.5-flash-002", 1_000_000, 0) == 1.50


def test_unknown_model_has_no_cost_rather_than_a_wrong_one():
    assert l.estimate_cost_usd("some-future-model", 1000, 1000) is None


def test_missing_usage_metadata_gives_zeros_not_a_crash():
    usage = l._usage_from(_resp("x"), "gemini-3.5-flash")
    assert usage["input_tokens"] == usage["output_tokens"] == usage["thinking_tokens"] == 0
    assert usage["cost_usd"] == 0


def test_usage_out_reports_the_model_that_actually_answered(client, monkeypatch):
    models = client({"primary": Exception("404 NOT_FOUND"), "fallback": "OK"})
    monkeypatch.setattr(models, "generate_content", _with_usage(models.generate_content, 1200, 300, 80))
    usage: dict = {}
    assert l.generate_text("hi", max_tokens=10, usage_out=usage) == "OK"
    assert usage["model"] == "fallback"
    assert (usage["input_tokens"], usage["output_tokens"], usage["thinking_tokens"]) == (1200, 300, 80)


def _with_usage(fn, inp, out, think):
    def wrapped(model, contents, config):
        r = fn(model, contents, config)
        r.usage_metadata = SimpleNamespace(prompt_token_count=inp, candidates_token_count=out,
                                           thoughts_token_count=think)
        return r
    return wrapped


def test_tokens_only_in_the_total_are_still_billed():
    r = _resp("x")
    r.usage_metadata = SimpleNamespace(prompt_token_count=2000, candidates_token_count=1000,
                                       thoughts_token_count=None, total_token_count=3600)
    usage = l._usage_from(r, "gemini-3.5-flash")
    assert usage["thinking_tokens"] == 600
    assert usage["cost_usd"] == l.estimate_cost_usd("gemini-3.5-flash", 2000, 1600)
