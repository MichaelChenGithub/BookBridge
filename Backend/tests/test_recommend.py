import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.routers import recommend
from services.item2vec_client import Item2VecError


def _build_app() -> TestClient:
    app = FastAPI()
    app.include_router(recommend.router)
    return TestClient(app)


def test_recommend_books_returns_details(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    monkeypatch.setattr(
        recommend, "generate_book_candidates", lambda prompt, history=None: [{"title": "Dune"}]
    )
    monkeypatch.setattr(recommend, "get_final_book_ids", lambda recs: ["ID1", "ID2"])
    monkeypatch.setattr(
        recommend,
        "get_book_details",
        lambda ids: [
            {
                "asin": "ID1",
                "title": "Title 1",
                "author_name": "Author 1",
                "average_rating": 4.0,
                "rating_number": 10,
                "primary_image": "img1",
            },
            {
                "asin": "ID2",
                "title": "Title 2",
                "author_name": "Author 2",
                "average_rating": 4.5,
                "rating_number": 20,
                "primary_image": "img2",
            },
        ],
    )

    client = _build_app()
    resp = client.post("/recommendations", json={"prompt": "any", "history": ["h1"]})

    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["asin"] == "ID1"
    assert data[0]["title"] == "Title 1"
    assert data[0]["primary_image"] == "img1"
    assert data[1]["asin"] == "ID2"


def test_recommend_books_handles_item2vec_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    monkeypatch.setattr(
        recommend, "generate_book_candidates", lambda prompt, history=None: [{"title": "Dune"}]
    )

    def _raise(_recs):
        raise Item2VecError("boom")

    monkeypatch.setattr(recommend, "get_final_book_ids", _raise)

    client = _build_app()
    resp = client.post("/recommendations", json={"prompt": "any"})

    assert resp.status_code == 502
