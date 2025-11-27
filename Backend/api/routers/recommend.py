"""Recommendation API router and CLI test entrypoint."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.openai_client import generate_book_candidates

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendRequest(BaseModel):
    prompt: str


class Recommendation(BaseModel):
    title: str


def _ensure_api_key_for_api() -> None:
    """Validate presence of OPENAI_API_KEY for API requests."""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set.",
        )


@router.post("", response_model=List[Recommendation])
async def recommend_books(body: RecommendRequest) -> List[Recommendation]:
    """
    Generate book recommendations for the provided prompt.

    Returns a list ordered from most recommended to least recommended.
    """
    _ensure_api_key_for_api()

    try:
        return generate_book_candidates(body.prompt)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - surfaced to client
        raise HTTPException(
            status_code=502, detail=f"Failed to generate recommendations: {exc}"
        ) from exc


def _cli_test(prompt: str) -> None:
    """Simple command-line hook to manually test the OpenAI integration."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY in your environment before running this test.")

    recommendations = generate_book_candidates(prompt)
    print("Raw recommendations:", recommendations)
    for idx, rec in enumerate(recommendations, start=1):
        title = rec.get("title") if isinstance(rec, dict) else str(rec)
        print(f"{idx}. {title}")


if __name__ == "__main__":
    SAMPLE_PROMPT = "I like sci-fi and fantasy with strong worldbuilding."
    try:
        _cli_test(SAMPLE_PROMPT)
    except Exception as err:  # pragma: no cover - CLI convenience
        print(f"Error: {err}")
