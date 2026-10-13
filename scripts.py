from config import SCRIPT_RANGES


def in_script(char, language_code):
    return any(start <= char <= end for start, end in SCRIPT_RANGES[language_code])


def script_share(text, language_code):
    letters = [c for c in text if c.isalpha()]

    if not letters:
        return 0.0

    return sum(in_script(c, language_code) for c in letters) / len(letters)


def has_foreign_letters(text, language_code):
    return any(
        c.isalpha() and not in_script(c, language_code) and not in_script(c, "eng")
        for c in text
    )


def detect_language(text):
    return max(SCRIPT_RANGES, key=lambda code: script_share(text, code))
