import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

LANG_CODE_MAP = {
    "eng": "English",
    "hin": "Hindi",
    "ben": "Bengali",
    "urd": "Urdu",
    "tam": "Tamil",
    "tel": "Telugu",
    "mar": "Marathi",
    "guj": "Gujarati",
    "pan": "Punjabi",
    "mal": "Malayalam",
    "kan": "Kannada",
    "nep": "Nepali",
    "sin": "Sinhala"
}

# gTTS voice for each language
GTTS_LANG_MAP = {
    "eng": "en",
    "hin": "hi",
    "ben": "bn",
    "urd": "ur",
    "tam": "ta",
    "tel": "te",
    "mar": "mr",
    "guj": "gu",
    "pan": "pa",
    "mal": "ml",
    "kan": "kn",
    "nep": "ne",
    "sin": "si"
}

# Unicode ranges used to check that a sentence is really in the requested language
SCRIPT_RANGES = {
    "eng": [("A", "Z"), ("a", "z"), ("\u00C0", "\u024F")],
    "hin": [("\u0900", "\u097F")],
    "ben": [("\u0980", "\u09FF")],
    "urd": [("\u0600", "\u06FF"), ("\u0750", "\u077F"), ("\uFB50", "\uFDFF"), ("\uFE70", "\uFEFF")],
    "tam": [("\u0B80", "\u0BFF")],
    "tel": [("\u0C00", "\u0C7F")],
    "mar": [("\u0900", "\u097F")],
    "guj": [("\u0A80", "\u0AFF")],
    "pan": [("\u0A00", "\u0A7F")],
    "mal": [("\u0D00", "\u0D7F")],
    "kan": [("\u0C80", "\u0CFF")],
    "nep": [("\u0900", "\u097F")],
    "sin": [("\u0D80", "\u0DFF")]
}

# Noto font in fonts/ for each language; None means the built-in Helvetica
FONT_FILES = {
    "eng": None,
    "hin": "NotoSansDevanagari.ttf",
    "ben": "NotoSansBengali-Regular.ttf",
    "urd": "NotoNaskhArabic-Regular.ttf",
    "tam": "NotoSansTamil-Regular.ttf",
    "tel": "NotoSansTelugu-Regular.ttf",
    "mar": "NotoSansDevanagari.ttf",
    "guj": "NotoSansGujarati-Regular.ttf",
    "pan": "NotoSansGurmukhi-Regular.ttf",
    "mal": "NotoSansMalayalam-Regular.ttf",
    "kan": "NotoSansKannada-Regular.ttf",
    "nep": "NotoSansDevanagari.ttf",
    "sin": "NotoSansSinhala-Regular.ttf"
}

RTL_LANGUAGES = {"urd"}

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_PULL_URL = "http://localhost:11434/api/pull"
