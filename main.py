import argparse

from generator import generate_sentences
from models import choose_model, resolve_model
from mixer import allocate_counts, mix_languages
from output import save_txt, save_json, save_csv, save_pdf
from media import generate_audio_dataset
from config import DEFAULT_MODEL, LANG_CODE_MAP, OUTPUT_DIR

FORMATS = ("txt", "json", "csv", "pdf", "audio")


def run_system(language_codes, total_samples, mix_ratio, format_type, topic, model):
    # Monolingual
    if len(language_codes) == 1:
        counts = {language_codes[0]: total_samples}

    # Multilingual
    else:
        counts = allocate_counts(total_samples, mix_ratio)

    # Generate data for each language
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

    # Save output
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


def parse_format(text):
    format_type = text.strip().lower()

    if format_type not in FORMATS:
        raise ValueError(f"Invalid format: {format_type!r}. Choose one of: {', '.join(FORMATS)}")

    return format_type


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
    base, extra = divmod(100, len(language_codes))
    return {code: base + (1 if i < extra else 0) for i, code in enumerate(language_codes)}


def get_user_input():
    print("\nSupported language codes:")
    print(", ".join(LANG_CODE_MAP.keys()))

    # Languages
    language_codes = parse_languages(input("\nEnter language code(s) (e.g. eng or eng,hin): "))

    # Dataset size
    total_samples = to_int(input("Enter number of samples: "), 1)

    # Topic
    topic = parse_topic(input("Enter topic: "))

    # Format
    format_type = parse_format(input(f"Format ({'/'.join(FORMATS)}): "))

    # Mixing
    mix_ratio = {}
    if len(language_codes) > 1:
        print("\nEnter percentage for each language (must sum to 100):")
        percents = [to_int(input(f"  {code} (%): "), 0) for code in language_codes]
        mix_ratio = parse_mix(language_codes, percents)

    return language_codes, total_samples, mix_ratio, format_type, topic


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
        description="Generate synthetic sentence datasets with a local LLM in Ollama. "
                    "Run without options to answer the questions interactively.",
        epilog=f"Language codes: {', '.join(LANG_CODE_MAP)}. "
               'Example: python main.py --langs hin,eng --mix 60,40 --samples 500 --topic "water cycle" --format json'
    )
    parser.add_argument("--model", help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--langs", help="language codes, comma-separated, e.g. hin,eng")
    parser.add_argument("--samples", help="number of sentences to generate")
    parser.add_argument("--topic", help="what the sentences should be about")
    parser.add_argument("--format", help=f"output format: {', '.join(FORMATS)}")
    parser.add_argument("--mix", help="percentage per language in --langs order, e.g. 60,40 (default: even split)")

    args = parser.parse_args()

    given = [args.langs, args.samples, args.topic, args.format, args.mix]

    if any(value is not None for value in given) and None in given[:4]:
        parser.error("--langs, --samples, --topic and --format are all required to run without questions")

    return args


def main():
    args = parse_args()

    print("\n=== Synthetic Data Generator ===")

    try:
        if args.langs is not None:
            model = resolve_model(args.model or DEFAULT_MODEL)
            print(f"Using local model: {model}")
            settings = settings_from_args(args)
        else:
            model = resolve_model(args.model) if args.model else choose_model()
            print(f"Using local model: {model}")
            settings = get_user_input()
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)

    language_codes, total_samples, mix_ratio, format_type, topic = settings

    run_system(
        language_codes,
        total_samples,
        mix_ratio,
        format_type,
        topic,
        model
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted.")
