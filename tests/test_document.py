import json

import pytest

import document
from document import (
    clean_text, drop_section_number, ensure_variety, generate_document, paragraph_count, section_count,
    section_languages, sentence_count, short_texts_in_language, stray_latin_words
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
        reply["items"] = (["- वाष्पीकरण", "संघनन", "वर्षा"] if sentence == HINDI
                          else ["- Evaporation", "Condensation", "Precipitation"])

    if '"table"' in prompt:
        reply["table"] = (
            {"headers": ["चरण", "कहाँ"], "rows": [["वाष्पीकरण", "महासागर"], ["वर्षा", "ज़मीन"]]} if sentence == HINDI
            else {"headers": ["Stage", "Where"], "rows": [["Evaporation", "Oceans"], [], ["Rain", "Land", "extra"]]}
        )

    return json.dumps(reply)


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []
    contexts = []

    def install(outline_reply, section=section_reply):
        def fake(prompt, model, schema=None, temperature=None, max_tokens=None, context=None):
            calls.append(prompt)
            contexts.append(context)
            return outline_reply if "Plan exactly" in prompt else section(prompt)

        monkeypatch.setattr(document, "call_llm", fake)
        install.contexts = contexts
        return calls

    return install


def test_length_scales_with_pages():
    assert [section_count(p) for p in (1, 2, 5, 10, 11, 30, 50)] == [4, 5, 8, 10, 11, 30, 50]
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


def test_long_documents_get_several_lists_and_tables_spread_out():
    plans = ensure_variety([{"element": "none"} for _ in range(10)])
    elements = [p["element"] for p in plans]

    assert elements.count("table") == 3 and elements.count("list") == 3
    assert elements[0] == elements[-1] == "none"
    assert all(a != b or a == "none" for a, b in zip(elements, elements[1:]))

    # One table and one list from the model are topped up, not replaced
    plans = [{"element": e} for e in ["none", "table", "list"] + ["none"] * 7]
    elements = [p["element"] for p in ensure_variety(plans)]
    assert elements[1:3] == ["table", "list"] and elements.count("table") == elements.count("list") == 3


def test_drops_section_numbers_from_headings():
    assert drop_section_number("IV. Establishing Orbital Infrastructure", 4) == "Establishing Orbital Infrastructure"
    assert drop_section_number("X: Conclusion", 10) == "Conclusion"
    assert drop_section_number("XXIV. Space Law", 24) == "Space Law"
    assert drop_section_number("XLIX. Outlook", 49) == "Outlook"
    assert drop_section_number("ii) जल चक्र", 2) == "जल चक्र"

    # Only the numeral for the section's own place, so real words and initials stay
    assert drop_section_number("C. elegans in research", 3) == "C. elegans in research"
    assert drop_section_number("I. Introduction", 2) == "I. Introduction"
    assert drop_section_number("Ice ages", 1) == "Ice ages"


def test_outline_headings_lose_roman_numerals(fake_llm):
    reply = json.loads(outline(4))
    for i, section in enumerate(reply["sections"]):
        section["heading"] = f"{['I', 'II', 'III', 'IV'][i]}. Part {i + 1}"

    fake_llm(json.dumps(reply))
    doc = generate_document("water cycle", 1, "eng", "m")

    assert [s["heading"] for s in doc["sections"]] == ["Part 1", "Part 2", "Part 3", "Part 4"]


def test_lists_and_tables_must_be_in_the_document_language():
    assert short_texts_in_language(["वाष्पीकरण", "Apollo 11", "1969"], "hin")
    assert short_texts_in_language(["1687", "1903"], "hin")
    assert not short_texts_in_language(["Stage", "Where", "Evaporation", "Oceans"], "hin")
    assert not short_texts_in_language(["वर्षा", "jiska उपयोग"], "hin")


def test_drops_an_english_table_from_a_hindi_document(fake_llm, capsys):
    def section(prompt):
        reply = json.loads(section_reply(prompt, HINDI))

        if "table" in reply:
            reply["table"] = {"headers": ["Stage", "Where"], "rows": [["Evaporation", "Oceans"], ["Rain", "Land"]]}

        return json.dumps(reply)

    fake_llm(outline(4, ["none", "table", "list", "none"], title="जल चक्र", heading="भाग"), section)
    doc = generate_document("जल चक्र", 1, "hin", "m")

    assert doc["sections"][1]["table"] is None and doc["sections"][1]["paragraphs"]
    assert doc["sections"][2]["list"] == ["वाष्पीकरण", "संघनन", "वर्षा"]
    assert "table in wrong language" in capsys.readouterr().out


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


def test_long_documents_get_a_bigger_context_and_a_compact_outline(fake_llm):
    calls = fake_llm(outline(30))
    doc = generate_document("water cycle", 30, "eng", "m")

    assert len(doc["sections"]) == 30
    assert set(fake_llm.contexts) == {document.LONG_CONTEXT}

    # Other sections are listed by heading only, without their summaries
    assert "Section 2: What it covers." not in calls[1] and "2. Section 2" in calls[1]
    assert sum(bool(s["table"]) for s in doc["sections"]) == sum(bool(s["list"]) for s in doc["sections"]) == 9


def test_short_documents_keep_the_default_context(fake_llm):
    calls = fake_llm(outline(5))
    generate_document("water cycle", 2, "eng", "m")

    assert set(fake_llm.contexts) == {None}
    assert "2. Section 2: What it covers." in calls[1]


def test_extra_lists_and_tables_are_trimmed_and_spread():
    plans = ensure_variety([{"element": "table"} for _ in range(30)])
    elements = [p["element"] for p in plans]

    assert elements.count("table") == elements.count("list") == 9
    assert elements[0] == elements[-1] == "none"
    assert max(len(run) for run in "".join("T" if e == "table" else "." for e in elements).split(".")) == 1


def test_introduction_and_conclusion_stay_plain():
    plans = ensure_variety([{"element": e} for e in ("table", "list", "none", "list")])
    assert [p["element"] for p in plans] == ["none", "list", "table", "none"]


def test_sections_with_a_table_or_list_get_fewer_words(fake_llm):
    calls = fake_llm(outline(10, ["none", "table", "list"] + ["none"] * 7))
    generate_document("water cycle", 10, "eng", "m")

    budget = {prompt.split('Write section ')[1].split(',')[0]: prompt.split("about ")[1].split(" words")[0]
              for prompt in calls[1:]}
    assert budget["2"] == "280" and budget["3"] == "360" and budget["1"] == "400"


def test_languages_take_turns_by_their_share():
    assert section_languages(6, {"hin": 50, "eng": 50}) == ["hin", "eng"] * 3

    thirty = section_languages(30, {"hin": 50, "eng": 50})
    assert thirty.count("hin") == thirty.count("eng") == 15

    ten = section_languages(10, {"hin": 70, "eng": 30})
    assert ten.count("hin") == 7 and ten.count("eng") == 3
    assert "eng,eng" not in ",".join(ten)  # the smaller share is spread out, not bunched

    assert section_languages(4, {"hin": 100}) == ["hin"] * 4
    assert section_languages(4, {"hin": 50, "eng": 50, "urd": 0}).count("urd") == 0


def mixed_outline(languages):
    sections = [
        {"heading": "भाग " + str(i) if code == "hin" else f"Part {i}", "summary": "...", "element": "none"}
        for i, code in enumerate(languages, 1)
    ]
    return json.dumps({"title": "जल चक्र", "sections": sections})


def reply_in_section_language(prompt):
    return section_reply(prompt, HINDI if "Write every word in Hindi" in prompt else ENGLISH)


def test_writes_a_document_that_switches_language_between_sections(fake_llm):
    calls = fake_llm(mixed_outline(["hin", "eng"] * 3), reply_in_section_language)
    doc = generate_document("water cycle", 3, {"hin": 50, "eng": 50}, "m")

    assert [s["language"] for s in doc["sections"]] == ["hin", "eng"] * 3
    assert doc["language"] == "hin,eng" and doc["mix"] == {"hin": 50, "eng": 50}
    assert all(s["paragraphs"][0].startswith("जल" if s["language"] == "hin" else "The") for s in doc["sections"])
    assert "1. Hindi (Devanagari script)" in calls[0] and "2. English (Latin script)" in calls[0]


def test_rejects_a_mixed_outline_with_a_heading_in_the_wrong_language(fake_llm):
    fake_llm(mixed_outline(["hin"] * 6), reply_in_section_language)

    with pytest.raises(ValueError, match="Hindi and English outline"):
        generate_document("water cycle", 3, {"hin": 50, "eng": 50}, "m")


def test_single_language_documents_are_unchanged(fake_llm):
    fake_llm(outline(4))
    doc = generate_document("water cycle", 1, "eng", "m")

    assert doc["language"] == "eng" and "mix" not in doc
    assert {s["language"] for s in doc["sections"]} == {"eng"}


def test_drops_english_glosses_after_translated_terms():
    assert clean_text("ईमेल (Email) और विंट सर्फ़ (Vint Cerf) ने टीसीपी (TCP/IP) बनाया।", "hin") == "ईमेल और विंट सर्फ़ ने टीसीपी बनाया।"
    assert clean_text("انٹرنیٹ (Internet) بہت اہم ہے۔", "urd") == "انٹرنیٹ بہت اہم ہے۔"
    assert clean_text("'इंटरनेटवर्किंग' (Inter-networking) की अवधारणा", "hin") == "'इंटरनेटवर्किंग' की अवधारणा"

    # English that stands on its own, brackets in the document's script, and numbers all stay
    assert clean_text("ARPANET का दायरा (1969) बढ़ा, यानी (लगभग) दोगुना।", "hin") == "ARPANET का दायरा (1969) बढ़ा, यानी (लगभग) दोगुना।"
    assert clean_text("ARPANET (Advanced Research) का हिस्सा", "hin") == "ARPANET (Advanced Research) का हिस्सा"
    assert clean_text("Packet switching (PS) was new.", "eng") == "Packet switching (PS) was new."


def test_short_sections_keep_two_thirds_of_their_words_beside_a_table(fake_llm):
    calls = fake_llm(outline(6, ["none", "table", "list", "none", "none", "none"]))
    generate_document("water cycle", 3, "eng", "m")

    budget = {prompt.split('Write section ')[1].split(',')[0]: prompt.split("about ")[1].split(" words")[0]
              for prompt in calls[1:]}
    assert budget["1"] == "200" and budget["2"] == "134" and budget["3"] == "160"
