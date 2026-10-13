from generator import generate_sentences
from models import choose_model
from mixer import allocate_counts, mix_languages
from output import save_txt, save_json, save_csv, save_pdf
from media import generate_audio_dataset
from config import LANG_CODE_MAP, OUTPUT_DIR

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


def ask_int(prompt, min_value):
    value = input(prompt).strip()

    try:
        number = int(value)
    except ValueError:
        raise ValueError(f"Expected a whole number, got: {value!r}")

    if number < min_value:
        raise ValueError(f"Expected a number of at least {min_value}, got: {number}")

    return number


def get_user_input():
    print("\nSupported language codes:")
    print(", ".join(LANG_CODE_MAP.keys()))

    # Languages
    language_codes = list(dict.fromkeys(
        code.strip().lower()
        for code in input("\nEnter language code(s) (e.g. eng or eng,hin): ").split(",")
        if code.strip()
    ))

    if not language_codes:
        raise ValueError("Enter at least one language code")

    # Validate codes
    for code in language_codes:
        if code not in LANG_CODE_MAP:
            raise ValueError(f"Unsupported language code: {code}")

    # Dataset size
    total_samples = ask_int("Enter number of samples: ", 1)

    # Topic
    topic = input("Enter topic: ").strip()

    if not topic:
        raise ValueError("Topic cannot be empty")

    # Format
    format_type = input(f"Format ({'/'.join(FORMATS)}): ").strip().lower()

    if format_type not in FORMATS:
        raise ValueError(f"Invalid format: {format_type!r}. Choose one of: {', '.join(FORMATS)}")

    # Mixing
    mix_ratio = {}
    if len(language_codes) > 1:
        print("\nEnter percentage for each language (must sum to 100):")
        total = 0

        for code in language_codes:
            percent = ask_int(f"  {code} (%): ", 0)
            mix_ratio[code] = percent
            total += percent

        if total != 100:
            raise ValueError(f"Total percentage must equal 100, got {total}")

    return language_codes, total_samples, mix_ratio, format_type, topic


def main():
    print("\n=== Synthetic Data Generator ===")

    try:
        model = choose_model()
        print(f"Using local model: {model}")

        language_codes, total_samples, mix_ratio, format_type, topic = get_user_input()
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)

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
