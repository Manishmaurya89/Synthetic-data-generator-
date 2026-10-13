from generator import check_ollama, generate_document
from output import save_pdf
from docling_processor import extract_data
from gliner_processor import extract_entities
from config import DEFAULT_MODEL, OUTPUT_DIR
import json
import os


def save_json(data, filename):
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    topic = "Impact of Artificial Intelligence on Healthcare"
    pages = 2
    language = "eng"  # "eng" or "hin"

    check_ollama()
    print(f"Using local model: {DEFAULT_MODEL}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, "final_output.pdf")

    print("\n--- Generating Structured Document ---\n")
    data = generate_document(topic, pages, language)

    # save JSON (debugging)
    save_json(data, "output.json")

    print("\n--- Generating PDF ---\n")
    save_pdf(data, pdf_path, language)

    print("\n--- Extracting Text with Docling ---\n")
    extracted = extract_data(pdf_path)

    save_json(extracted["json"], "docling_output.json")
    save_json(extracted["sections"], "structured_output.json")

    with open(os.path.join(OUTPUT_DIR, "extracted_text.txt"), "w", encoding="utf-8") as f:
        f.write(extracted["text"])

    print("\n--- Extracting Entities with GLiNER ---\n")
    save_json(extract_entities(extracted["text"]), "entities.json")

    print(f"\nDone. All files saved in {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)
