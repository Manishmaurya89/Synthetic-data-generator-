import csv
import json
from types import SimpleNamespace

import pytest

import main


def test_parse_languages_dedupes_and_validates():
    assert main.parse_languages(" eng, HIN ,eng,") == ["eng", "hin"]

    with pytest.raises(ValueError):
        main.parse_languages("xyz")

    with pytest.raises(ValueError):
        main.parse_languages(" , ")


def test_parse_format_and_topic():
    assert main.parse_format(" PDF ") == "pdf"

    with pytest.raises(ValueError):
        main.parse_format("docx")

    with pytest.raises(ValueError):
        main.parse_topic("   ")


def test_to_int():
    assert main.to_int(" 5 ", 1) == 5

    with pytest.raises(ValueError):
        main.to_int("abc", 1)

    with pytest.raises(ValueError):
        main.to_int("-3", 1)


def test_mix_must_add_up_to_100():
    assert main.parse_mix(["eng", "hin"], [60, 40]) == {"eng": 60, "hin": 40}

    with pytest.raises(ValueError):
        main.parse_mix(["eng", "hin"], [50, 40])

    with pytest.raises(ValueError):
        main.parse_mix(["eng", "hin"], [100])


def test_even_mix():
    assert main.even_mix(["eng", "hin", "urd"]) == {"eng": 34, "hin": 33, "urd": 33}


def test_settings_from_command_line_flags():
    args = SimpleNamespace(langs="hin,eng", samples="500", topic=" water cycle ", format="JSON", mix="60,40")
    assert main.settings_from_args(args) == (["hin", "eng"], 500, {"hin": 60, "eng": 40}, "json", "water cycle")

    args.mix = None
    assert main.settings_from_args(args)[2] == {"hin": 50, "eng": 50}


@pytest.fixture
def fake_generator(monkeypatch):
    def fake(code, count, topic, model):
        if code == "eng":
            return [f"English sentence {i}." for i in range(count)]
        return [f"हिंदी वाक्य संख्या {i}।" for i in range(count)]

    monkeypatch.setattr(main, "generate_sentences", fake)


def test_every_format_is_written(output_dir, fake_generator):
    for format_type in ("txt", "json", "csv", "pdf"):
        main.run_system(["eng", "hin"], 10, {"eng": 30, "hin": 70}, format_type, "Force", "m")

    assert len((output_dir / "dataset.txt").read_text(encoding="utf-8").splitlines()) == 10

    rows = json.loads((output_dir / "dataset.json").read_text(encoding="utf-8"))
    assert [r["language"] for r in rows].count("eng") == 3
    assert [r["language"] for r in rows].count("hin") == 7

    with open(output_dir / "dataset.csv", encoding="utf-8") as f:
        table = list(csv.reader(f))
    assert table[0] == ["text", "language"] and len(table) == 11

    assert (output_dir / "dataset.pdf").stat().st_size > 1000
