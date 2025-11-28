"""Recommendation API router and CLI test entrypoint."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.item2vec_client import Item2VecError, get_book_details, get_final_book_ids
from services.openai_client import generate_book_candidates

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendRequest(BaseModel):
    prompt: str
    history: Optional[List[str]] = None


class BookInfo(BaseModel):
    asin: str
    title: str
    author_name: Optional[str] = None
    average_rating: Optional[float] = None
    rating_number: Optional[int] = None
    primary_image: Optional[str] = None


def _ensure_api_key_for_api() -> None:
    """Validate presence of OPENAI_API_KEY for API requests."""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set.",
        )


@router.post("", response_model=List[BookInfo])
async def recommend_books(body: RecommendRequest) -> List[BookInfo]:
    """
    Generate book recommendations for the provided prompt.

    Returns a list of book info objects ordered from most recommended to least recommended.
    """
    _ensure_api_key_for_api()

    try:
        candidates = generate_book_candidates(body.prompt, history=body.history)
        book_ids = get_final_book_ids(candidates)
        return get_book_details(book_ids)
    except HTTPException:
        raise
    except Item2VecError as exc:
        raise HTTPException(status_code=502, detail=f"Item2Vec failed: {exc}") from exc
    except Exception as exc:  # pragma: no cover - surfaced to client
        raise HTTPException(
            status_code=502, detail=f"Failed to generate recommendations: {exc}"
        ) from exc


def _cli_test(prompt: str, history: Optional[List[str]] = None) -> None:
    """Simple command-line hook to manually test the OpenAI + item2vec integration."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY in your environment before running this test.")

    candidates = generate_book_candidates(prompt, history=history)
    print("OpenAI candidates:", candidates)
    book_ids = get_final_book_ids(candidates)
    print("Final book IDs:", book_ids)
    details = get_book_details(book_ids)
    print("Book details:")
    for idx, info in enumerate(details, start=1):
        print(f"{idx}. {info.get('asin')} - {info.get('title')} by {info.get('author_name')}")


if __name__ == "__main__":
    SAMPLE_PROMPT = "I like love stories set in historical Europe. Recommend some books."
    SAMPLE_HISTORY = []
    try:
        _cli_test(SAMPLE_PROMPT, history=SAMPLE_HISTORY)
    except Exception as err:
        print(f"Error: {err}")
