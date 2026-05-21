"""
LLM Client — abstraction layer for Gemini Flash.

Usage:
    from app.services.llm_client import generate_text, LLMError

    result = generate_text(prompt, max_tokens=800)
    # Returns str on success, raises LLMError on failure after retries.

Fallback:
    If GEMINI_API_KEY is not set, or quota/network errors occur after retries,
    LLMError is raised and callers must fall back to rule-based templates.

Config (env vars):
    GEMINI_API_KEY       — required for LLM calls
    LLM_MODEL            — default: gemini-2.5-flash
    LLM_MAX_RETRIES      — default: 1 (conservative to save quota)
"""

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_MODEL   = os.getenv("LLM_MODEL", "gemini-2.5-flash")
_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "1"))  # reduced: save quota on free tier
_API_KEY = os.getenv("GEMINI_API_KEY", "")
_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "45"))  # seconds per API call

# Lazy-initialised client — avoids import errors when SDK not installed
_client: Any = None

# Quota cooldown: when we get a 429, stop retrying for this many seconds
_quota_exhausted_until: float = 0.0


class LLMError(Exception):
    """Raised when LLM call fails after all retries."""
    pass


class QuotaExhaustedError(LLMError):
    """Raised specifically when the API quota is exhausted (429)."""
    pass


def _get_client():
    global _client
    if _client is None:
        if not _API_KEY:
            raise LLMError("GEMINI_API_KEY not set")
        try:
            import google.generativeai as genai
            genai.configure(api_key=_API_KEY)
            _client = genai.GenerativeModel(_MODEL)
        except ImportError:
            raise LLMError("google-generativeai package not installed")
    return _client


def generate_text(prompt: str, max_tokens: int = 1024) -> str:
    """
    Call Gemini and return the response text.
    Retries up to LLM_MAX_RETRIES times on transient errors.
    Raises LLMError on failure, QuotaExhaustedError on 429.
    """
    global _quota_exhausted_until

    # Short-circuit if we recently hit quota limits
    now = time.monotonic()
    if now < _quota_exhausted_until:
        remaining = int(_quota_exhausted_until - now)
        raise QuotaExhaustedError(
            f"Gemini quota cooldown active ({remaining}s remaining). "
            "Upgrade to paid tier: https://ai.google.dev/gemini-api/docs/rate-limits"
        )

    client = _get_client()

    import google.generativeai as genai
    config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=0.7,
    )

    last_err = None
    for attempt in range(_RETRIES + 1):
        try:
            response = client.generate_content(
                prompt,
                generation_config=config,
                request_options={"timeout": _TIMEOUT},
            )
            # Safety check: response may have no candidates (blocked)
            if not response.candidates:
                block_reason = getattr(response.prompt_feedback, 'block_reason', 'unknown')
                raise LLMError(f"Gemini blocked response: {block_reason}")
            text = response.text.strip()
            if not text:
                raise LLMError("Empty response from Gemini")
            return text
        except LLMError:
            raise
        except Exception as e:
            last_err = e
            err_str = str(e)

            # Detect quota exhaustion (429) — enter cooldown, don't retry
            if "429" in err_str or "ResourceExhausted" in type(e).__name__:
                # Parse retry_delay if available, default to 60s cooldown
                cooldown = 60
                import re
                delay_match = re.search(r"retry in (\d+)", err_str, re.IGNORECASE)
                if delay_match:
                    cooldown = int(delay_match.group(1)) + 5  # add buffer
                _quota_exhausted_until = time.monotonic() + cooldown
                print(f"[LLM] Gemini quota exhausted — cooldown {cooldown}s. "
                      f"Upgrade billing: https://ai.google.dev/pricing")
                raise QuotaExhaustedError(
                    f"Gemini API quota exceeded (free tier: 20 req/day). "
                    f"Cooldown {cooldown}s. Upgrade to paid tier for production use."
                )

            if attempt < _RETRIES:
                time.sleep(2.0 * (attempt + 1))
            print(f"[LLM] Gemini attempt {attempt + 1}/{_RETRIES + 1} failed: "
                  f"{type(e).__name__}: {err_str[:200]}")

    raise LLMError(f"Gemini failed after {_RETRIES + 1} attempts: "
                   f"{type(last_err).__name__}: {last_err}")


def generate_json(prompt: str, max_tokens: int = 1024) -> dict:
    """
    Call Gemini expecting JSON output. Strips markdown fences if present.
    Raises LLMError if response cannot be parsed as JSON.
    """
    text = generate_text(prompt, max_tokens=max_tokens)

    # Strip ```json ... ``` fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"Gemini returned invalid JSON: {e}\nRaw: {text[:300]}")


def llm_available() -> bool:
    """Quick check — returns True if GEMINI_API_KEY is configured."""
    return bool(_API_KEY)


def llm_selftest() -> str:
    """
    Run a minimal Gemini call to verify the API key and model work.
    Returns a short status string. Only call on-demand (costs 1 API call).
    """
    if not _API_KEY:
        return "skip:no_api_key"
    try:
        result = generate_text("Responde apenas com a palavra OK.", max_tokens=10)
        return f"ok:model={_MODEL},response={result[:30]}"
    except QuotaExhaustedError as e:
        return f"quota_exhausted:{e}"
    except LLMError as e:
        return f"fail:{e}"
    except Exception as e:
        return f"error:{type(e).__name__}:{e}"
