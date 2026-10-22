import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

LANG_CODE_MAP = {
    "eng": "English",
    "hin": "Hindi"
}

# Noto font in fonts/ for each language; None means ReportLab's default font
FONT_FILES = {
    "eng": None,
    "hin": "NotoSansDevanagari.ttf"
}

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_PULL_URL = "http://localhost:11434/api/pull"
