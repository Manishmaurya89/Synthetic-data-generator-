from generator import generate_document
from models import choose_model, resolve_model
from output import save_pdf
from config import DEFAULT_MODEL, LANG_CODE_MAP, OUTPUT_DIR
import argparse
import json
import os

DEFAULT_TOPIC = "Impact of Artificial Intelligence on Healthcare"
DEFAULT_PAGES = "2"
DEFAULT_LANGUAGE = "eng"


def ask(prompt, default):
    return input(f"{prompt} [{default}]: ").strip() or default


def parse_pages(text):
    if not str(text).isdigit() or int(text) < 1:
        raise ValueError(f"Pages must be a whole number of at least 1, got: {text!r}")

    return int(text)


def parse_language(text):
    language = text.strip().lower()

    if language not in LANG_CODE_MAP:
        raise ValueError(f"Unsupported language code: {language}")

    return language


def get_user_input():
    topic = ask("Topic", DEFAULT_TOPIC)
    pages = parse_pages(ask("Pages", DEFAULT_PAGES))
    language = parse_language(ask(f"Language ({'/'.join(LANG_CODE_MAP)})", DEFAULT_LANGUAGE))

    return topic, pages, language


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a structured document (JSON and PDF) with a local LLM in Ollama. "
                    "Run without options to answer the questions interactively."
    )
    parser.add_argument("--model", help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--topic", help=f"what the document is about (default: {DEFAULT_TOPIC})")
    parser.add_argument("--pages", help=f"length in pages, about 400 words each (default: {DEFAULT_PAGES})")
    parser.add_argument("--language", help=f"{' or '.join(LANG_CODE_MAP)} (default: {DEFAULT_LANGUAGE})")

    return parser.parse_args()


def main():
    args = parse_args()
    scripted = any(value is not None for value in (args.topic, args.pages, args.language))

    print("\n=== Synthetic Document Generator ===")

    if scripted:
        model = resolve_model(args.model or DEFAULT_MODEL)
        print(f"Using local model: {model}")

        topic = (args.topic or DEFAULT_TOPIC).strip()
        pages = parse_pages(args.pages or DEFAULT_PAGES)
        language = parse_language(args.language or DEFAULT_LANGUAGE)
    else:
        model = resolve_model(args.model) if args.model else choose_model()
        print(f"Using local model: {model}\n")

        topic, pages, language = get_user_input()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, "final_output.pdf")

    print("\n--- Generating Structured Document ---\n")
    data = generate_document(topic, pages, language, model)

    # save JSON (debugging)
    with open(os.path.join(OUTPUT_DIR, "output.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("--- Generating PDF ---\n")
    save_pdf(data, pdf_path, language)

    print(f"\nDone. Files saved in {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\n\nAborted.")
