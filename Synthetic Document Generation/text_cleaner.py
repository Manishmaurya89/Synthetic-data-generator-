import re

LIST_MARKER = re.compile(r"^(?:\d{1,3}[.)]?|[•\-*])\s+")


def clean_text(text, label="text"):
    text = text.strip()

    # remove standalone numbers
    if not text or re.fullmatch(r"\d+", text):
        return ""

    # convert numbered lists → bullet
    if label == "list_item":
        return "* " + LIST_MARKER.sub("", text)

    return text
