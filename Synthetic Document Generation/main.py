from generator import generate_document
from models import choose_model
from output import save_pdf
from config import LANG_CODE_MAP, OUTPUT_DIR
import json
import os


def ask(prompt, default):
    return input(f"{prompt} [{default}]: ").strip() or default


def get_user_input():
    topic = ask("Topic", "Impact of Artificial Intelligence on Healthcare")

    pages = ask("Pages", "2")

    if not pages.isdigit() or int(pages) < 1:
        raise ValueError(f"Pages must be a whole number of at least 1, got: {pages!r}")

    language = ask(f"Language ({'/'.join(LANG_CODE_MAP)})", "eng").lower()

    if language not in LANG_CODE_MAP:
        raise ValueError(f"Unsupported language code: {language}")

    return topic, int(pages), language


def main():
    print("\n=== Synthetic Document Generator ===")

    model = choose_model()
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
