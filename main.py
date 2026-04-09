from generator import generate_sentences
from mixer import mix_languages
from output import save_txt, save_json, save_csv, save_pdf
from media import generate_audio_dataset
from config import LANG_CODE_MAP


def run_system(language_codes, total_samples, mix_ratio, format_type, topic):
    language_data = {}

    # Generate data for each language
    for code in language_codes:
        print(f"Generating sentences for: {LANG_CODE_MAP[code]}...")
        language_data[code] = generate_sentences(code, total_samples, topic)

    # Monolingual
    if len(language_codes) == 1:
        data = language_data[language_codes[0]]

    # Multilingual
    else:
        data = mix_languages(language_data, mix_ratio)

    if not data:
        print("No data generated. Check your Ollama connection and model.")
        return

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
        generate_audio_dataset(data)
    else:
        print("Invalid format selected!")
        return

    print(f"\n {format_type.upper()} dataset generated successfully!")


def get_user_input():
    print("\n=== Synthetic Data Generator ===")
    print("\nSupported language codes:")
    print(", ".join(LANG_CODE_MAP.keys()))

    # Languages
    language_codes = [
        code.strip().lower()
        for code in input("\nEnter language code(s) (e.g. eng or eng,hin): ").split(",")
    ]

    # Validate codes
    for code in language_codes:
        if code not in LANG_CODE_MAP:
            raise ValueError(f"Unsupported language code: '{code}'")

    # Dataset size
    total_samples = int(input("Enter number of samples: "))
    if total_samples <= 0:
        raise ValueError("Number of samples must be greater than 0.")

    # Topic
    topic = input("Enter topic: ").strip()
    if not topic:
        raise ValueError("Topic cannot be empty.")

    # Format
    format_type = input("Format (txt/json/csv/pdf/audio): ").strip().lower()
    if format_type not in ("txt", "json", "csv", "pdf", "audio"):
        raise ValueError(f"Unsupported format: '{format_type}'")

    # Mixing ratio
    mix_ratio = {}
    if len(language_codes) > 1:
        print("\nEnter percentage for each language (must sum to 100):")
        total = 0

        for code in language_codes:
            percent = int(input(f"  {code} (%): "))
            mix_ratio[code] = percent
            total += percent

        if total != 100:
            raise ValueError(f"Total percentage must equal 100, got {total}.")

    return language_codes, total_samples, mix_ratio, format_type, topic


if __name__ == "__main__":
    try:
        language_codes, total_samples, mix_ratio, format_type, topic = get_user_input()
        run_system(language_codes, total_samples, mix_ratio, format_type, topic)
    except ValueError as e:
        print(f"\n Input error: {e}")
    except KeyboardInterrupt:
        print("\n\nAborted.")
