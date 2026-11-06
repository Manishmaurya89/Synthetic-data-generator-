import output

SAMPLES = [
    ("eng", "Force changes motion & speed <b>fast."),
    ("hin", "बल वस्तुओं की गति को बदलता है।"),
    ("ben", "বল বস্তুর গতি পরিবর্তন করে, যেমন Newton বলেছিলেন 1687 সালে।"),
    ("urd", "نیوٹن (Isaac Newton) نے 1687 میں حرکت کے قوانین پیش کیے، جو آج بھی اہم ہیں۔"),
    ("tam", "விசை பொருட்களின் இயக்கத்தை மாற்றுகிறது."),
    ("tel", "బలం వస్తువుల చలనాన్ని మారుస్తుంది."),
    ("mar", "बल वस्तूंची गती बदलते."),
    ("guj", "બળ વસ્તુઓની ગતિ બદલે છે."),
    ("pan", "ਬਲ ਵਸਤੂਆਂ ਦੀ ਗਤੀ ਬਦਲਦਾ ਹੈ।"),
    ("mal", "ബലം വസ്തുക്കളുടെ ചലനം മാറ്റുന്നു."),
    ("kan", "ಬಲವು ವಸ್ತುಗಳ ಚಲನೆಯನ್ನು ಬದಲಾಯಿಸುತ್ತದೆ."),
    ("nep", "बलले वस्तुहरूको गति परिवर्तन गर्छ।"),
    ("sin", "බලය වස්තූන්ගේ චලිතය වෙනස් කරයි."),
]


def test_pdf_with_all_13_languages(output_dir):
    output.save_pdf(SAMPLES, "Physics & <Motion>")
    assert (output_dir / "dataset.pdf").stat().st_size > 1000


def test_markup_is_escaped():
    assert output.to_markup("a < b & c", "Helvetica") == "a &lt; b &amp; c"


def test_rtl_words_are_reversed_but_english_runs_keep_their_order():
    words = ["نیوٹن", "Isaac", "Newton", "نے"]
    assert output.visual_order(words, "urd") == ["نے", "Isaac", "Newton", "نیوٹن"]


def test_glued_english_is_split_from_urdu():
    assert output.split_scripts("قاعدهMotion", "urd") == ["قاعده", "Motion"]


DOCUMENT = {
    "title": "Motion & <Force>",
    "sections": [
        {
            "heading": "Newton's laws",
            "paragraphs": ["Force changes motion & speed <b>fast. " * 12, "Mass resists change. " * 10],
            "list": ["Inertia", "Acceleration", "Action and reaction"],
            "table": {"headers": ["Law", "Idea", "Year"],
                      "rows": [["First", "Inertia " * 20, 1687], ["Second"], ["Third", "Reaction", "1687", "extra"]]},
        },
        {"heading": "Empty parts", "paragraphs": [], "list": [], "table": None},
        "not a section",
    ],
}


def test_document_pdf(output_dir):
    output.save_document_pdf(DOCUMENT, "eng")
    assert (output_dir / "document.pdf").stat().st_size > 1000


def test_document_pdf_in_every_language(output_dir):
    for code, sentence in SAMPLES:
        doc = {
            "title": sentence,
            "sections": [{"heading": sentence, "paragraphs": [sentence * 6], "list": [sentence, "1687"],
                          "table": {"headers": [sentence, "1687"], "rows": [[sentence * 3, "Newton"]]}}],
        }
        output.save_document_pdf(doc, code, f"document-{code}.pdf")
        assert (output_dir / f"document-{code}.pdf").stat().st_size > 1000


def test_document_json_keeps_the_script(output_dir):
    output.save_document_json({"title": "जल चक्र", "sections": []})
    assert '"जल चक्र"' in (output_dir / "document.json").read_text(encoding="utf-8")
