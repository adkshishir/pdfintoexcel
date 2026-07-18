"""Thin LLM client abstraction for blog generation."""

from __future__ import annotations

import json
import re
from typing import Any

from app.config import get_settings


class LlmError(RuntimeError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    # Strip markdown code fences if present
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LlmError(f"LLM response is not valid JSON: {e}") from e


def complete_json(system: str, user: str) -> dict[str, Any]:
    settings = get_settings()
    provider = settings.blog_llm_provider

    if provider == "gemini":
        return _gemini_complete_json(system, user, settings)
    if provider == "openai":
        return _openai_complete_json(system, user, settings)
    if provider == "anthropic":
        return _anthropic_complete_json(system, user, settings)
    raise LlmError(f"Unknown BLOG_LLM_PROVIDER: {provider}")


def _gemini_complete_json(system: str, user: str, settings: Any) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise LlmError("GEMINI_API_KEY is not configured")
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise LlmError("google-genai package is not installed") from e

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    content = response.text
    if not content:
        raise LlmError("Gemini returned empty content")
    return _extract_json(content)


def _openai_complete_json(system: str, user: str, settings: Any) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise LlmError("OPENAI_API_KEY is not configured")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise LlmError("openai package is not installed") from e

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    content = response.choices[0].message.content
    if not content:
        raise LlmError("OpenAI returned empty content")
    return _extract_json(content)


def _anthropic_complete_json(system: str, user: str, settings: Any) -> dict[str, Any]:
    if not settings.anthropic_api_key:
        raise LlmError("ANTHROPIC_API_KEY is not configured")
    try:
        import anthropic
    except ImportError as e:
        raise LlmError("anthropic package is not installed") from e

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = [b.text for b in response.content if hasattr(b, "text")]
    content = "".join(parts)
    if not content:
        raise LlmError("Anthropic returned empty content")
    return _extract_json(content)
