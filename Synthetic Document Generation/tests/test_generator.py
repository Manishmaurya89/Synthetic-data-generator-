import json

import pytest

import generator


class FakeResponse:
    ok = True
    status_code = 200

    def __init__(self, text, done_reason="stop"):
        self.payload = {"response": text, "done_reason": done_reason}

    def json(self):
        return self.payload


def reply_with(monkeypatch, text, done_reason="stop"):
    monkeypatch.setattr(generator.requests, "post", lambda *args, **kwargs: FakeResponse(text, done_reason))


ARTICLE = {"title": "AI in Healthcare", "sections": [{"heading": "Intro", "paragraphs": ["Text."]}]}


def test_strip_code_fences():
    assert generator.strip_code_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert generator.strip_code_fences('{"a": 1}') == '{"a": 1}'


def test_returns_the_article(monkeypatch):
    reply_with(monkeypatch, json.dumps(ARTICLE))
    assert generator.generate_document("AI", 1, "eng", "m") == ARTICLE


def test_accepts_fenced_json(monkeypatch):
    reply_with(monkeypatch, "```json\n" + json.dumps(ARTICLE) + "\n```")
    assert generator.generate_document("AI", 1, "eng", "m")["title"] == "AI in Healthcare"


def test_uses_the_topic_when_the_title_is_missing(monkeypatch):
    reply_with(monkeypatch, json.dumps({"sections": []}))
    assert generator.generate_document("AI", 1, "eng", "m")["title"] == "AI"


def test_reports_invalid_json(monkeypatch):
    reply_with(monkeypatch, "{not json")

    with pytest.raises(ValueError, match="did not return valid JSON"):
        generator.generate_document("AI", 1, "eng", "m")


def test_reports_a_cut_off_article(monkeypatch):
    reply_with(monkeypatch, '{"title": "AI", "sec', done_reason="length")

    with pytest.raises(ValueError, match="cut off"):
        generator.generate_document("AI", 1, "eng", "m")
