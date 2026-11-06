import json

import pytest

import document
from document import (
    clean_text, ensure_variety, generate_document, paragraph_count, section_count, sentence_count, stray_latin_words
)

ENGLISH = "The water cycle moves water between the oceans, the air and the land in a loop that never stops."
HINDI = "जल चक्र महासागरों, हवा और ज़मीन के बीच पानी को एक ऐसे चक्र में घुमाता है जो कभी नहीं रुकता और हर दिन चलता है।"


def paragraph(sentence):
    return " ".join([sentence] * 3)


def outline(count, elements=None, title="The Water Cycle", heading="Section"):
    elements = elements or ["none"] * count
    return json.dumps({
        "title": title,
        "sections": [
            {"heading": f"{i + 1}. {heading} {i + 1}", "summary": "What it covers.", "element": elements[i]}
            for i in range(count)
        ]
    })


def section_reply(prompt, sentence=ENGLISH):
    reply = {"paragraphs": [paragraph(sentence)] * 2}

    if '"items"' in prompt:
        reply["items"] = ["- Evaporation", "Condensation", "Precipitation"]

    if '"table"' in prompt:
        reply["table"] = {"headers": ["Stage", "Where"], "rows": [["Evaporation", "Oceans"], [], ["Rain", "Land", "extra"]]}

    return json.dumps(reply)


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []

    def install(outline_reply, section=section_reply):
        def fake(prompt, model, schema=None, temperature=None, max_tokens=None):
            calls.append(prompt)
            return outline_reply if "Plan exactly" in prompt else section(prompt)

        monkeypatch.setattr(document, "call_llm", fake)
        return calls

    return install


def test_length_scales_with_pages():
    assert [section_count(p) for p in (1, 2, 5, 10)] == [4, 5, 8, 10]
    assert [paragraph_count(w) for w in (100, 160, 300, 800)] == [2, 2, 3, 5]


def test_clean_text_fixes_punctuation_and_markdown():
    assert clean_text("पानी भाप बनता है。 **बादल** बनते हैं", "hin") == "पानी भाप बनता है। बादल बनते हैं"
    assert clean_text("  Water evaporates。\n Clouds form， then rain  ", "eng") == "Water evaporates. Clouds form, then rain"
    assert clean_text("## `Heading`", "eng") == "Heading"


def test_counts_sentences_in_any_script():
    assert sentence_count("Water evaporates. It rises to 14.4 km! Then? It rains") == 4
    assert sentence_count("पानी भाप बनता है। बादल बनते हैं। बारिश होती है।") == 3
    assert sentence_count("پانی بخارات بنتا ہے۔ بادل کیسے بنتے ہیں؟ بارش ہوتی ہے۔") == 3


def test_finds_romanised_words_but_allows_names_and_acronyms():
    assert stray_latin_words("भारत में gió की गति तेज है, jiska उपयोग होता है।", "hin") == ["gió", "jiska"]
    assert stray_latin_words("न्यूटन (Newton) ने 14.4 GW और km, COVID-19 की बात की।", "hin") == []
    assert stray_latin_words("the water cycle", "eng") == []


def test_every_document_gets_a_list_and_a_table():
    plans = [{"element": "none"} for _ in range(5)]
    assert [p["element"] for p in ensure_variety(plans)] == ["none", "none", "table", "list", "none"]

    plans = [{"element": e} for e in ("none", "list", "list", "none")]
    assert sorted(p["element"] for p in ensure_variety(plans)) == ["list", "none", "none", "table"]


def test_generates_a_structured_document(fake_llm):
    fake_llm(outline(5, ["none", "list", "none", "table", "none"]))
    doc = generate_document("water cycle", 2, "eng", "m")

    assert doc["title"] == "The Water Cycle" and doc["language"] == "eng" and doc["topic"] == "water cycle"
    assert [s["heading"] for s in doc["sections"]] == [f"Section {i}" for i in range(1, 6)]
    assert all(len(s["paragraphs"]) == 2 for s in doc["sections"])

    assert doc["sections"][1]["list"] == ["Evaporation", "Condensation", "Precipitation"]
    assert doc["sections"][3]["table"] == {
        "headers": ["Stage", "Where"],
        "rows": [["Evaporation", "Oceans"], ["Rain", "Land"]]
    }
    assert doc["sections"][0]["list"] == [] and doc["sections"][0]["table"] is None


def test_retries_a_section_that_is_too_short(fake_llm):
    replies = iter([json.dumps({"paragraphs": ["Too short.", "Also short."]})])

    def section(prompt):
        return next(replies, None) or section_reply(prompt)

    calls = fake_llm(outline(4), section)
    doc = generate_document("water cycle", 1, "eng", "m")

    assert len(calls) == 1 + 4 + 1
    assert all(sentence_count(p) >= 3 for s in doc["sections"] for p in s["paragraphs"])


def test_retries_invalid_json(fake_llm):
    replies = iter(["{not json", "[]"])

    def section(prompt):
        return next(replies, None) or section_reply(prompt)

    calls = fake_llm(outline(4), section)
    generate_document("water cycle", 1, "eng", "m")

    assert len(calls) == 1 + 4 + 2


def test_writes_in_the_requested_language(fake_llm):
    fake_llm(outline(4, title="जल चक्र", heading="भाग"), lambda prompt: section_reply(prompt, HINDI))
    doc = generate_document("जल चक्र", 1, "hin", "m")

    assert doc["title"] == "जल चक्र"
    assert all(s["paragraphs"][0].startswith("जल चक्र") for s in doc["sections"])


def test_retries_a_section_with_romanised_words(fake_llm):
    replies = iter([json.dumps({"paragraphs": [paragraph(HINDI) + " jiska उपयोग होता है।", paragraph(HINDI)]})])

    def section(prompt):
        return next(replies, None) or section_reply(prompt, HINDI)

    calls = fake_llm(outline(4, title="जल चक्र", heading="भाग"), section)
    doc = generate_document("जल चक्र", 1, "hin", "m")

    assert len(calls) == 1 + 4 + 1
    assert "jiska" not in json.dumps(doc, ensure_ascii=False)


def test_gives_up_when_the_model_keeps_using_another_language(fake_llm):
    fake_llm(outline(4, title="जल चक्र", heading="भाग"))

    with pytest.raises(ValueError, match="could not write the section"):
        generate_document("जल चक्र", 1, "hin", "m")


def test_rejects_an_outline_in_the_wrong_language(fake_llm):
    fake_llm(outline(4))

    with pytest.raises(ValueError, match="could not plan"):
        generate_document("जल चक्र", 1, "hin", "m")


def test_keeps_the_best_try_and_drops_an_incomplete_table(fake_llm, capsys):
    def section(prompt):
        reply = json.loads(section_reply(prompt))

        if "table" in reply:
            reply["table"] = {"headers": ["Only one column"], "rows": []}

        return json.dumps(reply)

    fake_llm(outline(4, ["none", "table", "list", "none"]), section)
    doc = generate_document("water cycle", 1, "eng", "m")

    assert doc["sections"][1]["table"] is None
    assert len(doc["sections"][1]["paragraphs"]) == 2
    assert "table incomplete" in capsys.readouterr().out


def test_reports_when_ollama_is_unreachable(monkeypatch):
    monkeypatch.setattr(document, "call_llm", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="Ollama"):
        generate_document("water cycle", 1, "eng", "m")


def test_never_falls_back_to_a_try_in_the_wrong_language(fake_llm, capsys):
    # The first try is Hindi with two small problems; the others are English with only one.
    # Picking "fewest problems" would choose English and then give up on the whole document.
    short_hindi = json.dumps({"paragraphs": ["जल चक्र चलता है। jiska उपयोग होता है।", paragraph(HINDI)]})
    english = json.dumps({"paragraphs": [paragraph(ENGLISH)] * 2})
    replies = iter([short_hindi, english, english])

    def section(prompt):
        return next(replies, None) or section_reply(prompt, HINDI)

    fake_llm(outline(4, title="जल चक्र", heading="भाग"), section)
    doc = generate_document("जल चक्र", 1, "hin", "m")

    assert doc["sections"][0]["paragraphs"][0] == "जल चक्र चलता है। jiska उपयोग होता है।"
    assert "kept the best of 3 tries" in capsys.readouterr().out


def test_removes_stray_thai_and_chinese_letters_as_a_last_resort(fake_llm, capsys):
    sprinkled = paragraph(HINDI).replace("महासागरों,", "महासागरों ร可,")
    fake_llm(outline(4, title="जल चक्र", heading="भाग"), lambda prompt: json.dumps({"paragraphs": [sprinkled] * 2}))
    doc = generate_document("जल चक्र", 1, "hin", "m")

    text = json.dumps(doc, ensure_ascii=False)
    assert "ร" not in text and "可" not in text and "महासागरों" in text
    assert "stray letters from another script removed" in capsys.readouterr().out


def test_retries_an_outline_with_one_mixed_heading(monkeypatch):
    mixed = json.loads(outline(4, title="जल चक्र", heading="भाग"))
    mixed["sections"][2]["heading"] = "सolar Energy in India"
    replies = iter([json.dumps(mixed)])
    calls = []

    def fake(prompt, model, schema=None, temperature=None, max_tokens=None):
        calls.append(prompt)

        if "Plan exactly" in prompt:
            return next(replies, None) or outline(4, title="जल चक्र", heading="भाग")

        return section_reply(prompt, HINDI)

    monkeypatch.setattr(document, "call_llm", fake)
    doc = generate_document("जल चक्र", 1, "hin", "m")

    assert sum("Plan exactly" in c for c in calls) == 2
    assert all("olar" not in s["heading"] for s in doc["sections"])
