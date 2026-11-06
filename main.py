import argparse

from document import MAX_PAGES, generate_document
from generator import generate_sentences
from models import choose_model, resolve_model
from mixer import allocate_counts, mix_languages
from output import save_txt, save_json, save_csv, save_pdf, save_document_json, save_document_pdf
from media import generate_audio_dataset
from config import DEFAULT_MODEL, LANG_CODE_MAP, OUTPUT_DIR

FORMATS = ("txt", "json", "csv", "pdf", "audio")
DOCUMENT = "document"
DEFAULT_PAGES = 2


def run_system(language_codes, total_samples, mix_ratio, format_type, topic, model):
    if len(language_codes) == 1:
        counts = {language_codes[0]: total_samples}
    else:
        counts = allocate_counts(total_samples, mix_ratio)

    language_data = {}

    for code, count in counts.items():
        if count > 0:
            print(f"Generating sentences for: {LANG_CODE_MAP[code]}...")
            language_data[code] = generate_sentences(code, count, topic, model)

    data = mix_languages(language_data)

    if not data:
        print("No sentences were generated. Is Ollama running?")
        return

    if len(data) < total_samples:
        print(f"Warning: the dataset has {len(data)} of the {total_samples} samples requested")

    if format_type == "txt":
        save_txt(data)
    elif format_type == "json":
        save_json(data)
    elif format_type == "csv":
        save_csv(data)
    elif format_type == "pdf":
        save_pdf(data, topic)
    elif format_type == "audio":
        if generate_audio_dataset(data) == 0:
            print("No audio could be created (gTTS needs an internet connection).")
            return
    else:
        print("Invalid format selected!")
        return

    print(f"{format_type.upper()} dataset generated successfully in {OUTPUT_DIR}")


def run_document(language_code, topic, pages, model):
    print(f"\nWriting a {pages}-page {LANG_CODE_MAP[language_code]} document about \"{topic}\"...")

    document = generate_document(topic, pages, language_code, model)

    save_document_json(document)
    save_document_pdf(document, language_code)

    sections = document["sections"]
    words = sum(len(p.split()) for section in sections for p in section["paragraphs"])
    lists = sum(bool(section["list"]) for section in sections)
    tables = sum(bool(section["table"]) for section in sections)

    counts = [(len(sections), "section"), (words, "word"), (lists, "list"), (tables, "table")]
    summary = ", ".join(f"{n} {name}{'' if n == 1 else 's'}" for n, name in counts)
    print(f"\n\"{document['title']}\": {summary}")
    print(f"Saved document.json and document.pdf in {OUTPUT_DIR}")


def to_int(value, min_value):
    try:
        number = int(str(value).strip())
    except ValueError:
        raise ValueError(f"Expected a whole number, got: {value!r}")

    if number < min_value:
        raise ValueError(f"Expected a number of at least {min_value}, got: {number}")

    return number


def parse_languages(text):
    # Duplicates removed, order kept
    language_codes = list(dict.fromkeys(
        code.strip().lower()
        for code in text.split(",")
        if code.strip()
    ))

    if not language_codes:
        raise ValueError("Enter at least one language code")

    for code in language_codes:
        if code not in LANG_CODE_MAP:
            raise ValueError(f"Unsupported language code: {code}")

    return language_codes


def parse_format(text, formats=FORMATS):
    format_type = text.strip().lower()

    if format_type not in formats:
        raise ValueError(f"Invalid format: {format_type!r}. Choose one of: {', '.join(formats)}")

    return format_type


def parse_document_language(text):
    language_codes = parse_languages(text)

    if len(language_codes) != 1:
        raise ValueError("A document is written in one language. Enter a single language code")

    return language_codes[0]


def parse_pages(value):
    pages = to_int(value, 1)

    if pages > MAX_PAGES:
        raise ValueError(f"A document can be at most {MAX_PAGES} pages, got: {pages}")

    return pages


def parse_topic(text):
    topic = text.strip()

    if not topic:
        raise ValueError("Topic cannot be empty")

    return topic


def parse_mix(language_codes, percents):
    if len(percents) != len(language_codes):
        raise ValueError(f"Give one percentage per language ({len(language_codes)}), got {len(percents)}")

    total = sum(percents)

    if total != 100:
        raise ValueError(f"Total percentage must equal 100, got {total}")

    return dict(zip(language_codes, percents))


def even_mix(language_codes):
    """Split 100% as evenly as possible, giving any remainder to the first languages."""
    base, extra = divmod(100, len(language_codes))
    return {code: base + (1 if i < extra else 0) for i, code in enumerate(language_codes)}


def get_user_input():
    print("\nSupported language codes:")
    print(", ".join(LANG_CODE_MAP.keys()))

    language_codes = parse_languages(input("\nEnter language code(s) (e.g. eng or eng,hin): "))

    total_samples = to_int(input("Enter number of samples: "), 1)

    topic = parse_topic(input("Enter topic: "))

    format_type = parse_format(input(f"Format ({'/'.join(FORMATS)}): "))

    mix_ratio = {}
    if len(language_codes) > 1:
        print("\nEnter percentage for each language (must sum to 100):")
        percents = [to_int(input(f"  {code} (%): "), 0) for code in language_codes]
        mix_ratio = parse_mix(language_codes, percents)

    return language_codes, total_samples, mix_ratio, format_type, topic


def ask_wants_document():
    print("\nWhat do you want to make?")
    print("  1. Sentence dataset: one sentence per line, as TXT, JSON, CSV, PDF or MP3")
    print("  2. Document: a full article with headings, paragraphs, lists and tables, as JSON and PDF")

    choice = input("Choice [1]: ").strip() or "1"

    if choice not in ("1", "2"):
        raise ValueError(f"Choose 1 or 2, got: {choice!r}")

    return choice == "2"


def get_document_input():
    print("\nSupported language codes:")
    print(", ".join(LANG_CODE_MAP.keys()))

    language_code = parse_document_language(input("\nEnter one language code (e.g. eng): "))
    topic = parse_topic(input("Enter topic: "))
    pages = parse_pages(input(f"Number of pages [{DEFAULT_PAGES}]: ").strip() or DEFAULT_PAGES)

    return language_code, topic, pages


def document_settings_from_args(args):
    language_code = parse_document_language(args.langs)
    topic = parse_topic(args.topic)
    pages = parse_pages(args.pages or DEFAULT_PAGES)

    return language_code, topic, pages


def settings_from_args(args):
    language_codes = parse_languages(args.langs)
    total_samples = to_int(args.samples, 1)
    topic = parse_topic(args.topic)
    format_type = parse_format(args.format)

    mix_ratio = {}
    if len(language_codes) > 1:
        if args.mix:
            mix_ratio = parse_mix(language_codes, [to_int(p, 0) for p in args.mix.split(",")])
        else:
            mix_ratio = even_mix(language_codes)

    return language_codes, total_samples, mix_ratio, format_type, topic


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate synthetic sentence datasets or structured documents with a local LLM in Ollama. "
                    "Run without options to answer the questions interactively.",
        epilog=f"Language codes: {', '.join(LANG_CODE_MAP)}. "
               'Examples: python main.py --langs hin,eng --mix 60,40 --samples 500 --topic "water cycle" --format json  |  '
               'python main.py --format document --langs hin --topic "water cycle" --pages 3'
    )
    parser.add_argument("--model", help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--langs", help="language codes, comma-separated, e.g. hin,eng (one code for a document)")
    parser.add_argument("--samples", help="number of sentences to generate")
    parser.add_argument("--topic", help="what the sentences or document should be about")
    parser.add_argument("--format", help=f"output format: {', '.join(FORMATS)}, or {DOCUMENT} for a structured article")
    parser.add_argument("--mix", help="percentage per language in --langs order, e.g. 60,40 (default: even split)")
    parser.add_argument("--pages", help=f"document length, about 400 words per page (default: {DEFAULT_PAGES})")

    args = parser.parse_args()

    given = [args.langs, args.samples, args.topic, args.format, args.mix, args.pages]

    if all(value is None for value in given):
        return args

    if (args.format or "").strip().lower() == DOCUMENT:
        if None in (args.langs, args.topic):
            parser.error("--langs and --topic are required for --format document")

        if args.samples is not None or args.mix is not None:
            parser.error("--samples and --mix are for sentence datasets. Use --pages to set a document's length")

    else:
        if None in (args.langs, args.samples, args.topic, args.format):
            parser.error("--langs, --samples, --topic and --format are all required to run without questions")

        if args.pages is not None:
            parser.error("--pages only applies to --format document")

    return args


def main():
    args = parse_args()

    print("\n=== Synthetic Data Generator ===")

    try:
        if args.langs is not None:
            model = resolve_model(args.model or DEFAULT_MODEL)
            print(f"Using local model: {model}")

            if parse_format(args.format, FORMATS + (DOCUMENT,)) == DOCUMENT:
                run_document(*document_settings_from_args(args), model)
            else:
                run_system(*settings_from_args(args), model)
        else:
            model = resolve_model(args.model) if args.model else choose_model()
            print(f"Using local model: {model}")

            if ask_wants_document():
                run_document(*get_document_input(), model)
            else:
                run_system(*get_user_input(), model)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted.")
