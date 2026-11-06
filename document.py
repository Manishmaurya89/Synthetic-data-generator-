import json
import re
import unicodedata

from config import LANG_CODE_MAP, SCRIPT_NAMES
from generator import LIST_MARKER, MIN_SCRIPT_SHARE, call_llm
from scripts import has_foreign_letters, in_script, script_share


WORDS_PER_PAGE = 400
MAX_PAGES = 10
MAX_SECTIONS = 10
MIN_PARAGRAPH_SENTENCES = 3
ATTEMPTS = 3
TEMPERATURE = 0.7

# Sentences are counted, not words: one Malayalam word can carry what takes four in Hindi
SENTENCE_END = re.compile(r"[.!?।۔؟]+(?:\s|$)")
PUNCTUATION_AROUND_WORDS = ".,;:!?()[]\"'“”‘’-–—।۔؟،"

# Sentence-ending mark for languages that don't use "."
FULL_STOPS = {"hin": "।", "nep": "।", "ben": "।", "pan": "।", "urd": "۔"}

# Chinese and Japanese punctuation that models sometimes slip in
WIDE_PUNCTUATION = {"，": ",", "：": ":", "；": ";", "！": "!", "？": "?", "（": "(", "）": ")"}

MARKDOWN = re.compile(r"\*\*|__|`|^#+\s*")


def section_count(pages):
    return min(MAX_SECTIONS, pages + 3)


def paragraph_count(words):
    return max(2, min(5, round(words / 90)))


def clean_text(text, language_code):
    text = str(text).replace("。", FULL_STOPS.get(language_code, "."))

    for wide, narrow in WIDE_PUNCTUATION.items():
        text = text.replace(wide, narrow)

    text = MARKDOWN.sub("", text.strip())
    return " ".join(text.split())


def clean_label(text, language_code):
    # Headings and list items: also drop numbering and bullets the model added
    return LIST_MARKER.sub("", clean_text(text, language_code)).strip()


def in_language(text, language_code):
    return script_share(text, language_code) >= MIN_SCRIPT_SHARE and not has_foreign_letters(text, language_code)


def sentence_count(text):
    return len([sentence for sentence in SENTENCE_END.split(text) if sentence.strip()])


def stray_latin_words(text, language_code):
    # Lowercase Latin words in a non-English text are slips like romanised Hindi ("jiska"),
    # while names and acronyms (Newton, GW) start with a capital and are allowed
    if language_code == "eng":
        return []

    words = (word.strip(PUNCTUATION_AROUND_WORDS) for word in text.split())
    return [word for word in words if len(word) >= 3 and word.islower() and all(in_script(c, "eng") for c in word)]


def parse_json(raw):
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    return data if isinstance(data, dict) else None


def language_rule(language_code):
    language = LANG_CODE_MAP[language_code]
    return f"Write every word in {language}, in {SCRIPT_NAMES[language_code]} script, apart from names, acronyms and numbers."


def outline_schema(count):
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "sections": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "summary": {"type": "string"},
                        "element": {"type": "string", "enum": ["table", "list", "none"]}
                    },
                    "required": ["heading", "summary", "element"]
                }
            }
        },
        "required": ["title", "sections"]
    }


def outline_prompt(topic, pages, count, language_code):
    return f"""
Plan a {pages}-page article about "{topic}" for an educated general reader.

Plan exactly {count} sections:
- The first section introduces the topic and the last section is the conclusion.
- Every section in between covers a different aspect of the topic, with no overlap.
- For each section give a short heading, a one-sentence summary of what it covers, and an "element":
  "table" if the section has facts that fit rows and columns (comparisons, figures, timelines, types),
  "list" if it has steps, examples, causes, effects or tips, otherwise "none".
- Use at least one "table" and at least one "list" in the sections between the introduction and the conclusion.

{language_rule(language_code)} This applies to the title, headings and summaries.
Return only JSON.
"""


def ensure_variety(plans):
    # Every document gets at least one table and one list
    middle = plans[1:-1] or plans

    for element in ("table", "list"):
        if any(plan["element"] == element for plan in plans):
            continue

        spare = [plan for plan in middle if plan["element"] == "none"] or [
            plan for plan in middle
            if sum(other["element"] == plan["element"] for other in plans) > 1
        ]

        if spare:
            spare[len(spare) // 2]["element"] = element

    return plans


def parse_outline(raw, count, language_code):
    data = parse_json(raw)

    if not data or not isinstance(data.get("sections"), list):
        return None

    plans = []

    for section in data["sections"][:count]:
        if not isinstance(section, dict):
            continue

        heading = clean_label(section.get("heading", ""), language_code)
        summary = clean_text(section.get("summary", ""), language_code)
        element = section.get("element") if section.get("element") in ("table", "list") else "none"

        if heading:
            plans.append({"heading": heading, "summary": summary, "element": element})

    title = clean_label(data.get("title", ""), language_code)
    labels = [title] + [plan["heading"] for plan in plans]

    # Check each heading on its own, so one mixed-up heading ("सolar Energy") can't hide among good ones
    if len(plans) < count or not title or not all(
        in_language(label, language_code) and not stray_latin_words(label, language_code) for label in labels
    ):
        return None

    return {"title": title, "sections": ensure_variety(plans)}


def make_outline(topic, pages, language_code, model):
    count = section_count(pages)
    prompt = outline_prompt(topic, pages, count, language_code)

    for _ in range(ATTEMPTS):
        raw = ask(prompt, model, outline_schema(count), 2000)
        outline = parse_outline(raw, count, language_code)

        if outline:
            return outline

    raise ValueError(
        f"The model could not plan a {LANG_CODE_MAP[language_code]} outline after {ATTEMPTS} tries. "
        "Try another model, for example one from the Gemma family for South Asian languages."
    )


def section_schema(paragraphs, element):
    properties = {
        "paragraphs": {"type": "array", "items": {"type": "string"}, "minItems": paragraphs, "maxItems": paragraphs}
    }

    if element == "list":
        properties["items"] = {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 6}

    if element == "table":
        properties["table"] = {
            "type": "object",
            "properties": {
                "headers": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
                "rows": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 6,
                    "items": {"type": "array", "items": {"type": "string"}}
                }
            },
            "required": ["headers", "rows"]
        }

    return {"type": "object", "properties": properties, "required": list(properties)}


ELEMENT_RULES = {
    "list": '- Also give a bullet list ("items") of 3 to 6 short points, under 15 words each, '
            "that add details the paragraphs don't already give.",
    "table": '- Also give a table ("table") with 2 to 4 columns and 3 to 6 rows of specific facts or figures. '
             "Every row has one cell per column.",
    "none": ""
}


def section_prompt(outline, index, paragraphs, words, language_code):
    plan = outline["sections"][index]
    contents = "\n".join(
        f"{i}. {section['heading']}: {section['summary']}"
        for i, section in enumerate(outline["sections"], 1)
    )

    return f"""
You are writing one section of the article "{outline['title']}".

Outline of the whole article:
{contents}

Write section {index + 1}, "{plan['heading']}". It covers: {plan['summary']}

- Write {paragraphs} paragraphs, about {words} words in total. Each paragraph has 4 to 6 complete sentences.
- Use concrete facts, examples and figures. Don't repeat what the other sections cover.
- Don't repeat the heading, and don't start with phrases like "In this section".
{ELEMENT_RULES[plan['element']]}
- {language_rule(language_code)}
- Plain text only, no markdown.
Return only JSON.
"""


def clean_table(table, language_code):
    if not isinstance(table, dict):
        return None

    headers = [clean_text(h, language_code) for h in table.get("headers") or []]
    headers = [h for h in headers if h]
    rows = []

    for row in table.get("rows") or []:
        if not isinstance(row, list):
            continue

        cells = [clean_text(cell, language_code) for cell in row]
        cells = (cells + [""] * len(headers))[:len(headers)]

        if any(cells):
            rows.append(cells)

    return {"headers": headers, "rows": rows}


def parse_section(raw, plan, language_code):
    data = parse_json(raw)

    if not data:
        return None

    paragraphs = [clean_text(p, language_code) for p in data.get("paragraphs") or [] if isinstance(p, str)]
    items = [clean_label(item, language_code) for item in data.get("items") or [] if isinstance(item, str)]

    return {
        "heading": plan["heading"],
        "paragraphs": [p for p in paragraphs if p],
        "list": [item for item in items if item] if plan["element"] == "list" else [],
        "table": clean_table(data.get("table"), language_code) if plan["element"] == "table" else None
    }


def section_problems(section, plan, paragraphs, language_code):
    problems = []

    if not section["paragraphs"] or not in_language(" ".join(section["paragraphs"]), language_code):
        problems.append("wrong language")

    if len(section["paragraphs"]) < paragraphs:
        problems.append("too few paragraphs")

    if any(sentence_count(p) < MIN_PARAGRAPH_SENTENCES for p in section["paragraphs"]):
        problems.append("paragraphs too short")

    if stray_latin_words(" ".join(section["paragraphs"] + section["list"]), language_code):
        problems.append("stray Latin words")

    if plan["element"] == "list" and len(section["list"]) < 3:
        problems.append("list too short")

    table = section["table"]

    if plan["element"] == "table" and (not table or len(table["headers"]) < 2 or len(table["rows"]) < 2):
        problems.append("table incomplete")

    return problems


def strip_foreign_letters(section, language_code):
    # Some models sprinkle a few Thai or Chinese characters into otherwise clean text
    def strip(text):
        kept = "".join(
            c for c in text
            if in_script(c, language_code) or in_script(c, "eng") or unicodedata.category(c)[0] in "NPSZ"
            or unicodedata.category(c) == "Cf"  # zero-width joiners that Indic scripts need
        )
        return " ".join(kept.split())

    table = section["table"]

    return {
        **section,
        "paragraphs": [strip(p) for p in section["paragraphs"]],
        "list": [strip(item) for item in section["list"]],
        "table": {"headers": [strip(h) for h in table["headers"]],
                  "rows": [[strip(cell) for cell in row] for row in table["rows"]]} if table else None
    }


def write_section(outline, index, words, language_code, model):
    plan = outline["sections"][index]
    paragraphs = paragraph_count(words)
    prompt = section_prompt(outline, index, paragraphs, words, language_code)
    tries = []

    for _ in range(ATTEMPTS):
        section = parse_section(ask(prompt, model, section_schema(paragraphs, plan["element"]), 3000), plan, language_code)

        if section is None:
            continue

        problems = section_problems(section, plan, paragraphs, language_code)

        if not problems:
            return section

        tries.append((section, problems))

    # Never fall back to a try in the wrong language while one in the right language exists
    usable = [(section, problems) for section, problems in tries if "wrong language" not in problems]

    if not usable:
        for section, _ in tries:
            section = strip_foreign_letters(section, language_code)
            problems = section_problems(section, plan, paragraphs, language_code)

            if "wrong language" not in problems:
                usable.append((section, problems + ["stray letters from another script removed"]))

    if not usable:
        raise ValueError(
            f"The model could not write the section \"{plan['heading']}\" in {LANG_CODE_MAP[language_code]} "
            f"after {ATTEMPTS} tries. Try another model."
        )

    best, best_problems = min(usable, key=lambda attempt: len(attempt[1]))
    print(f"  Warning: kept the best of {ATTEMPTS} tries for \"{plan['heading']}\" ({', '.join(best_problems)})")

    # Keep the parts that passed, so the document stays well formed
    if "table incomplete" in best_problems:
        best["table"] = None

    if "list too short" in best_problems:
        best["list"] = []

    return best


def ask(prompt, model, schema, max_tokens):
    raw = call_llm(prompt, model, schema=schema, temperature=TEMPERATURE, max_tokens=max_tokens)

    if raw is None:
        raise RuntimeError("Could not get a reply from Ollama. Is it running?")

    return raw


def generate_document(topic, pages, language_code, model):
    outline = make_outline(topic, pages, language_code, model)
    count = len(outline["sections"])
    words = pages * WORDS_PER_PAGE // count

    print(f"Outline ready: \"{outline['title']}\", {count} sections")

    sections = []

    for index, plan in enumerate(outline["sections"]):
        print(f"  Writing section {index + 1} of {count}: {plan['heading']}")
        sections.append(write_section(outline, index, words, language_code, model))

    return {"title": outline["title"], "topic": topic, "language": language_code, "sections": sections}
