import output

MESSY = {
    "sections": [
        {
            "heading": "AI & <Health>",
            "paragraphs": ["Uses <b>models & data", ["nested paragraph"]],
            "lists": [["diagnosis", "triage"], "R&D"],
            "tables": [
                {
                    "headers": ["Year", "Use case", "Notes"],
                    "rows": [[], [2020, "Imaging"], ["2021", "Triage", "A very long cell " * 30, "extra"],
                             {"Year": 2022, "Use case": "Drug discovery"}],
                },
                {"headers": [], "rows": [["x"]]},
            ],
        },
        "not a dict",
        {"paragraphs": "a single string"},
    ]
}


def test_messy_llm_json_still_builds_a_pdf(tmp_path):
    path = tmp_path / "messy.pdf"
    output.save_pdf(MESSY, str(path))
    assert path.stat().st_size > 1000


def test_hindi_pdf(tmp_path):
    article = {
        "title": "स्वास्थ्य सेवा में कृत्रिम बुद्धिमत्ता",
        "sections": [{"heading": "परिचय", "paragraphs": ["कृत्रिम बुद्धिमत्ता (AI) डॉक्टरों की मदद करती है।"],
                      "lists": ["निदान"], "tables": [{"headers": ["वर्ष", "उपयोग"], "rows": [["2020", "इमेजिंग"]]}]}],
    }
    path = tmp_path / "hindi.pdf"
    output.save_pdf(article, str(path), "hin")
    assert path.stat().st_size > 1000


def test_flatten():
    assert list(output.flatten([["a", ["b"]], "c"])) == ["a", "b", "c"]
    assert list(output.flatten("single")) == ["single"]
    assert list(output.flatten(None)) == []
