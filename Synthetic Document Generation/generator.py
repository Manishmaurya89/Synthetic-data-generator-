import requests
import json
import re
from config import LANG_CODE_MAP, OLLAMA_URL, OLLAMA_TAGS_URL, DEFAULT_MODEL


WORDS_PER_PAGE = 400
TOKENS_PER_PAGE = 1500


def build_prompt(topic, pages, language_code):
    return f"""
Generate a structured article in JSON format.

Topic: {topic}
Length: about {pages * WORDS_PER_PAGE} words in total
Language: write the title, headings, paragraphs, list items and table cells in {LANG_CODE_MAP[language_code]}. Keep the JSON keys in English.

Output format:
{{
  "title": "",
  "sections": [
    {{
      "heading": "",
      "paragraphs": [],
      "lists": [],
      "tables": []
    }}
  ]
}}

Rules:
- 5–7 sections
- Each section must have 1–3 paragraphs
- Lists only if meaningful, as a flat list of strings
- Tables only if real structured data exists
- Tables format:
  {{
    "headers": [],
    "rows": [[]]
  }}
- No markdown
- No extra text
- Return ONLY valid JSON
"""


def check_ollama():
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        raise RuntimeError("Ollama is not running. Install it from https://ollama.com and start it (or run: ollama serve)")

    installed = [model["name"] for model in response.json().get("models", [])]

    if DEFAULT_MODEL not in installed and f"{DEFAULT_MODEL}:latest" not in installed:
        raise RuntimeError(f"Model '{DEFAULT_MODEL}' is not downloaded. Run: ollama pull {DEFAULT_MODEL}")


def strip_code_fences(text):
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text.strip(), re.DOTALL)
    return match.group(1) if match else text


def generate_document(topic, pages, language_code="eng"):
    prompt = build_prompt(topic, pages, language_code)
    max_tokens = pages * TOKENS_PER_PAGE

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "num_predict": max_tokens
            }
        },
        timeout=(10, 1800)
    )

    if not response.ok:
        raise ValueError(f"Ollama error {response.status_code}: {response.text[:300]}")

    data = response.json()

    if "response" not in data:
        raise ValueError(f"Ollama error: {data}")

    if data.get("done_reason") == "length":
        raise ValueError(
            f"The article was cut off at {max_tokens} tokens, so its JSON is incomplete. "
            "Increase TOKENS_PER_PAGE in generator.py."
        )

    raw = strip_code_fences(data["response"])

    try:
        document = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON ({e}). Output started with: {raw[:200]!r}")

    if not isinstance(document, dict) or not isinstance(document.get("sections"), list):
        raise ValueError(f"LLM JSON has no 'sections' list: {raw[:200]!r}")

    if not document.get("title"):
        document["title"] = topic

    return document
