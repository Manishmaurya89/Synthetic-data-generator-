import builtins
import json

import pytest
import requests

import models

INSTALLED = [("gemma4:latest", 9_600_000_000), ("llama3:latest", 4_700_000_000)]


@pytest.fixture
def installed(monkeypatch):
    monkeypatch.setattr(models, "list_models", lambda: INSTALLED)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def answer(monkeypatch, *replies):
    replies = iter(replies)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(replies))


def test_find_model_accepts_names_without_a_tag():
    assert models.find_model("llama3", ["llama3:latest"]) == "llama3:latest"
    assert models.find_model("llama3:latest", ["llama3:latest"]) == "llama3:latest"
    assert models.find_model("qwen2.5", ["llama3:latest"]) is None


def test_enter_picks_the_default(installed, monkeypatch):
    answer(monkeypatch, "")
    assert models.choose_model() == "llama3:latest"


def test_pick_by_number_or_name(installed, monkeypatch):
    answer(monkeypatch, "1")
    assert models.choose_model() == "gemma4:latest"

    answer(monkeypatch, "gemma4")
    assert models.choose_model() == "gemma4:latest"


def test_declining_a_download(installed, monkeypatch):
    answer(monkeypatch, "qwen2.5", "n")

    with pytest.raises(ValueError):
        models.choose_model()


class FakePull:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_lines(self):
        for status in ({"status": "pulling manifest"}, {"status": "pulling", "total": 200, "completed": 50}, {"status": "success"}):
            yield json.dumps(status).encode()


def test_downloads_a_new_model(installed, monkeypatch, capsys):
    monkeypatch.setattr(models.requests, "post", lambda *args, **kwargs: FakePull())
    answer(monkeypatch, "qwen2.5", "y")

    assert models.choose_model() == "qwen2.5"
    assert "25%" in capsys.readouterr().out


def test_download_errors_are_reported(monkeypatch):
    class FailedPull(FakePull):
        def iter_lines(self):
            yield json.dumps({"error": "pull model manifest: file does not exist"}).encode()

    monkeypatch.setattr(models.requests, "post", lambda *args, **kwargs: FailedPull())

    with pytest.raises(RuntimeError, match="does not exist"):
        models.pull_model("no-such-model")


def test_resolve_model_needs_the_model_downloaded(installed):
    assert models.resolve_model("llama3") == "llama3:latest"

    with pytest.raises(RuntimeError, match="ollama pull qwen2.5"):
        models.resolve_model("qwen2.5")


def test_ollama_not_running(monkeypatch):
    def refuse(*args, **kwargs):
        raise requests.ConnectionError()

    monkeypatch.setattr(models.requests, "get", refuse)

    with pytest.raises(RuntimeError, match="Ollama is not running"):
        models.list_models()
