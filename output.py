import json
import csv
import os
import re
import unicodedata
from xml.sax.saxutils import escape

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import FONT_DIR, FONT_FILES, OUTPUT_DIR, RTL_LANGUAGES
from scripts import detect_language, in_script


def output_path(filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, filename)


def save_txt(data, filename="dataset.txt"):
    with open(output_path(filename), "w", encoding="utf-8") as f:
        for _, line in data:
            f.write(line + "\n")


def save_json(data, filename="dataset.json"):
    structured = [{"text": line, "language": lang} for lang, line in data]

    with open(output_path(filename), "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)


def save_csv(data, filename="dataset.csv"):
    with open(output_path(filename), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "language"])

        for lang, line in data:
            writer.writerow([line, lang])


# Built into every PDF reader; covers English and other Latin-1 text.
FALLBACK_FONT = "Helvetica"


def get_font(language_code):
    """Register the language's Noto font with ReportLab once and return its name."""
    filename = FONT_FILES[language_code]

    if filename is None:
        return FALLBACK_FONT

    font_name = os.path.splitext(filename)[0]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, os.path.join(FONT_DIR, filename)))

    return font_name


def make_style(name, language_code, font_size, parent):
    return ParagraphStyle(
        name,
        parent=parent,
        fontName=get_font(language_code),
        fontSize=font_size,
        leading=font_size * 1.5,
        shaping=1,
        alignment=TA_RIGHT if language_code in RTL_LANGUAGES else parent.alignment
    )


def fits_fallback_font(word):
    try:
        word.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


def to_markup(text, font_name):
    """Escape text for a Paragraph, switching to Helvetica for words the script font can't draw.

    Some Noto fonts have no Latin letters, so English words inside a Hindi or
    Urdu sentence would otherwise come out as empty boxes.
    """
    if font_name == FALLBACK_FONT:
        return escape(text)

    glyphs = pdfmetrics.getFont(font_name).face.charToGlyph
    parts = []

    for word in re.split(r"(\s+)", text):
        covered = all(
            ord(c) in glyphs or c.isspace() or unicodedata.category(c) == "Cf"
            for c in word
        )

        if covered or not fits_fallback_font(word):
            parts.append(escape(word))
        else:
            parts.append(f'<font name="{FALLBACK_FONT}">{escape(word)}</font>')

    return "".join(parts)


def text_width(text, style):
    paragraph = Paragraph(to_markup(text, style.fontName), style)
    paragraph.wrap(1e6, 1e6)
    return paragraph.getActualLineWidths0()[0]


# ReportLab lays text out left to right only, so right-to-left lines (Urdu) are
# wrapped here and each line's words are reordered before it is drawn.

def split_scripts(word, language_code):
    """Split a word where it switches between the RTL script and Latin letters or digits."""
    parts = [""]
    last = None

    for c in word:
        if c.isalpha() and in_script(c, language_code):
            kind = "rtl"
        elif c.isascii() and c.isalnum():
            kind = "ltr"
        else:
            kind = None

        if kind and last and kind != last:
            parts.append("")

        last = kind or last
        parts[-1] += c

    return parts


def visual_order(words, language_code):
    """Reverse the line for right-to-left reading, keeping runs of LTR words in their own order."""
    runs = []

    for word in words:
        ltr = not any(in_script(c, language_code) for c in word)

        if ltr and runs and runs[-1][0]:
            runs[-1][1].append(word)
        else:
            runs.append((ltr, [word]))

    return [word for _, run in reversed(runs) for word in run]


def rtl_lines(text, style, language_code, max_width):
    """Wrap text to max_width using measured word widths, then put each line in visual order."""
    max_width *= 0.95  # a little slack so ReportLab never re-wraps a line
    space = text_width("a a", style) - 2 * text_width("a", style)

    lines = [[]]
    width = 0

    words = [part for word in text.split() for part in split_scripts(word, language_code)]

    for word in words:
        word_width = text_width(word, style)

        if lines[-1] and width + space + word_width > max_width:
            lines.append([])
            width = 0

        width += word_width + (space if lines[-1] else 0)
        lines[-1].append(word)

    return [" ".join(visual_order(line, language_code)) for line in lines if line]


def paragraphs(text, style, language_code, max_width, bold=False):
    if language_code in RTL_LANGUAGES:
        lines = rtl_lines(text, style, language_code, max_width)
    else:
        lines = [text]

    elements = []

    for line in lines:
        markup = to_markup(line, style.fontName)
        elements.append(Paragraph(f"<b>{markup}</b>" if bold else markup, style))

    return elements


def save_pdf(data, topic, filename="dataset.pdf"):
    doc = SimpleDocTemplate(output_path(filename))
    styles = getSampleStyleSheet()

    elements = []

    # The topic may be typed in any language, so pick the title font from its script.
    title_language = detect_language(topic)
    title_style = make_style("TitleStyle", title_language, 14, styles["Normal"])

    elements.extend(paragraphs(topic, title_style, title_language, doc.width, bold=True))
    elements.append(Spacer(1, 15))

    line_styles = {}

    for lang, line in data:
        if lang not in line_styles:
            line_styles[lang] = make_style(f"NormalStyle-{lang}", lang, 11, styles["Normal"])

        elements.extend(paragraphs(line, line_styles[lang], lang, doc.width))
        elements.append(Spacer(1, 8))

    doc.build(elements)
