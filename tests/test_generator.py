import generator
from generator import clean_output, generate_sentences


def test_keeps_sentences_that_start_with_a_number():
    assert clean_output("1990 was the year of the Internet.", "eng") == ["1990 was the year of the Internet."]
    assert clean_output("3.14 is the value of pi.", "eng") == ["3.14 is the value of pi."]


def test_strips_numbering_and_bullets():
    text = "2. Force causes motion.\n1) Gravity pulls objects down.\n- Mass is matter.\n* Speed is distance over time."
    assert clean_output(text, "eng") == [
        "Force causes motion.",
        "Gravity pulls objects down.",
        "Mass is matter.",
        "Speed is distance over time.",
    ]


def test_drops_intro_lines_in_any_language():
    assert clean_output("Here are 60 sentences about physics:\nForce causes motion.", "eng") == ["Force causes motion."]
    assert clean_output("यहाँ कुछ वाक्य हैं:\nबल गति को बदलता है।", "hin") == ["बल गति को बदलता है।"]


def test_strips_indic_digit_numbering():
    assert clean_output("१. बल वस्तुओं की गति बदलता है।", "hin") == ["बल वस्तुओं की गति बदलता है।"]


def test_drops_sentences_in_the_wrong_language():
    assert clean_output("Force is a push.", "hin") == []
    assert clean_output("बल गति बदलता है।", "eng") == []


def test_drops_letters_from_a_third_script():
    assert clean_output("स्थान के लिए कोई力 नहीं है।", "hin") == []


def test_allows_a_few_english_words():
    assert clean_output("न्यूटन के नियम (Newton) गति बताते हैं।", "hin") == ["न्यूटन के नियम (Newton) गति बताते हैं।"]


def test_removes_duplicates_keeping_order():
    assert clean_output("Force causes motion.\nMass is matter.\nForce causes motion.", "eng") == [
        "Force causes motion.",
        "Mass is matter.",
    ]


def test_keeps_calling_until_enough_unique_sentences(monkeypatch):
    calls = []

    def fake_llm(prompt, model):
        start = len(calls) * 30
        calls.append(model)
        return "\n".join(f"Sentence number {i} about force." for i in range(start, start + 60))

    monkeypatch.setattr(generator, "call_llm", fake_llm)
    data = generate_sentences("eng", 100, "force", "test-model")

    assert len(data) == 100
    assert len(set(data)) == 100
    assert set(calls) == {"test-model"}


def test_never_pads_with_duplicates(monkeypatch):
    monkeypatch.setattr(generator, "call_llm", lambda prompt, model: "Same sentence every time.\nAnother fixed one.")
    assert generate_sentences("eng", 50, "x", "m") == ["Same sentence every time.", "Another fixed one."]


def test_stops_when_ollama_is_unreachable(monkeypatch):
    monkeypatch.setattr(generator, "call_llm", lambda prompt, model: None)
    assert generate_sentences("eng", 10, "x", "m") == []
