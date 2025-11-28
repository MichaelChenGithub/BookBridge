import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services import openai_client


class FakeMessage:
    def __init__(self, parsed: Any = None, content: Any = None):
        self.parsed = parsed
        self.content = content


class FakeChoice:
    def __init__(self, message: FakeMessage):
        self.message = message


class FakeResponse:
    def __init__(self, message: FakeMessage):
        self.choices = [FakeChoice(message)]


def make_fake_client(create_impl):
    class FakeCompletions:
        def create(self, **kwargs):
            return create_impl(**kwargs)

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeClient:
        def __init__(self):
            self.chat = FakeChat()

    return FakeClient()


def test_generate_book_candidates_success(monkeypatch):
    captured: Dict[str, Any] = {}

    def fake_create(**kwargs):
        captured["kwargs"] = kwargs
        return FakeResponse(
            FakeMessage(parsed={"recommendations": [{"title": "Dune "}, {"title": "The Way of Kings"}]})
        )

    monkeypatch.setattr(openai_client, "_client", make_fake_client(fake_create))

    result = openai_client.generate_book_candidates(
        "Give me sci-fi epics.", history=["User liked Foundation", "User enjoyed Mistborn"]
    )

    assert result == [{"title": "Dune"}, {"title": "The Way of Kings"}]
    messages = captured["kwargs"]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "Give me sci-fi epics."
    # History is threaded as user messages before the final prompt.
    assert any(msg.get("content") == "User liked Foundation" for msg in messages)


def test_generate_book_candidates_network_failure(monkeypatch):
    def fake_create(**kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(openai_client, "_client", make_fake_client(fake_create))

    with pytest.raises(RuntimeError):
        openai_client.generate_book_candidates("Suggest books")


def test_generate_book_candidates_bad_format(monkeypatch):
    def fake_create(**kwargs):
        # recommendations is not a list -> cleaned becomes empty -> ValueError
        return FakeResponse(FakeMessage(parsed={"recommendations": "not-a-list"}))

    monkeypatch.setattr(openai_client, "_client", make_fake_client(fake_create))

    with pytest.raises(ValueError):
        openai_client.generate_book_candidates("Suggest books")


def test_generate_book_candidates_accepts_history_string(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return FakeResponse(FakeMessage(parsed={"recommendations": [{"title": "Dune"}]}))

    monkeypatch.setattr(openai_client, "_client", make_fake_client(fake_create))

    result = openai_client.generate_book_candidates("Suggest books", history="Previous picks: Dune")

    assert result == [{"title": "Dune"}]
    assert captured["messages"][1]["content"] == "Previous picks: Dune"


def test_generate_book_candidates_without_history(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return FakeResponse(FakeMessage(parsed={"recommendations": [{"title": "Dune"}]}))

    monkeypatch.setattr(openai_client, "_client", make_fake_client(fake_create))

    result = openai_client.generate_book_candidates("Suggest books")

    assert result == [{"title": "Dune"}]
    # Only system + current user prompt should be present when no history is provided.
    assert len(captured["messages"]) == 2
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][1]["content"] == "Suggest books"
