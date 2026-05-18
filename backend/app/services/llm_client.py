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
    LLM_MAX_RETRIES      — default: 2
"""

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_MODEL   = os.getenv("LLM_MODEL", "gemini-2.5-flash")
_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
_API_KEY = os.getenv("GEMINI_API_KEY", "")
_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))  # seconds per API call

# Lazy-initialised client — avoids import errors when SDK not installed
_client: Any = None


class LLMError(Exception):
    """Raised when LLM call fails after all retries."""
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
    Raises LLMError on failure.
    """
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
            text = response.text.strip()
            if not text:
                raise LLMError("Empty response from Gemini")
            return text
        except LLMError:
            raise
        except Exception as e:
            last_err = e
            if attempt < _RETRIES:
                time.sleep(1.5 * (attempt + 1))
            logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")

    raise LLMError(f"Gemini failed after {_RETRIES + 1} attempts: {last_err}")


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
