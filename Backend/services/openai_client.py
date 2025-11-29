"""OpenAI client helpers for BookBridge backend."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI()
_DEFAULT_MODEL = "gpt-4.1-mini"
_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "book_recommendations",
        "schema": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"title": {"type": "string"}},
                        "required": ["title"],
                        "additionalProperties": False,
                    },
                    "minItems": 10,
                    "maxItems": 10,
                }
            },
            "required": ["recommendations"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


def _extract_text_content(message_content: Any) -> str:
    """Normalize OpenAI chat message content into a plain string."""
    if message_content is None:
        raise ValueError("OpenAI response contained no message content.")
    if isinstance(message_content, str):
        return message_content

    parts: List[str] = []
    for part in message_content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)

    if not parts:
        raise ValueError("OpenAI response missing text content.")
    return "".join(parts)


def _clean_title(title: Any) -> Optional[str]:
    """Strip noise from a title and drop invalid entries."""
    if not isinstance(title, str):
        return None
    cleaned = " ".join(title.split()).strip(" ,;:{}[]\"'")
    return cleaned or None


def _clean_recommendations(recommendations: Any) -> List[Dict[str, str]]:
    """Ensure recommendations are well-formed and titles are tidy."""
    if not isinstance(recommendations, list):
        return []

    cleaned: List[Dict[str, str]] = []
    for rec in recommendations:
        raw_title = rec.get("title") if isinstance(rec, dict) else rec
        title = _clean_title(raw_title)
        if title:
            cleaned.append({"title": title})
    return cleaned


def generate_book_candidates(prompt: str, history: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Generate 10 ordered book recommendations for the given user prompt.

    Returns:
        A list of clean recommendation dicts sorted from most to least recommended.
    """
    system_instruction = (
        "You are a recommender that suggests books a reader is most likely to enjoy. "
        "Return exactly 10 distinct books ordered from best match to least match. "
        "For each item, output only the canonical book title—no author names, series labels, subtitles, punctuation, or extra text. "
        "All titles must be in English; when a book is known by a non-English title, provide its common English title instead."
    )

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_instruction}]
    history_items: List[str] = []
    if history:
        if isinstance(history, str):
            history_items = [history]
        else:
            history_items = list(history)

    for entry in history_items:
        if not entry:
            continue
        messages.append({"role": "user", "content": str(entry)})

    messages.append({"role": "user", "content": prompt})

    response = _client.chat.completions.create(
        model=_DEFAULT_MODEL,
        temperature=0.4,
        messages=messages,
        response_format=_RESPONSE_FORMAT,
    )

    message = response.choices[0].message
    parsed = getattr(message, "parsed", None)
    if parsed is None:
        content = _extract_text_content(message.content)
        parsed = json.loads(content)
    recommendations = parsed.get("recommendations", [])

    cleaned = _clean_recommendations(recommendations)

    if not cleaned:
        raise ValueError("OpenAI response did not return a recommendations list.")

    return cleaned
