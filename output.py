import json
import csv
import os
import re
import unicodedata
from xml.sax.saxutils import escape

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
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


ACCENT = colors.HexColor("#1f3b63")
STRIPE = colors.HexColor("#f2f5f9")
GRID = colors.HexColor("#c5cdd8")
CELL_PADDING = 5
BULLET_WIDTH = 14
LIST_INDENT = 12


def save_document_json(document, filename="document.json"):
    with open(output_path(filename), "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)


def document_styles(language_code):
    base = getSampleStyleSheet()
    rtl = language_code in RTL_LANGUAGES

    title = make_style("DocTitle", language_code, 22, base["Title"])
    title.textColor = ACCENT
    title.spaceAfter = 18

    heading = make_style("DocHeading", language_code, 15, base["Heading2"])
    heading.textColor = ACCENT
    heading.spaceBefore = 14
    heading.spaceAfter = 6
    heading.keepWithNext = 1

    body = make_style("DocBody", language_code, 11, base["Normal"])
    body.alignment = TA_RIGHT if rtl else TA_JUSTIFY

    cell = make_style("DocCell", language_code, 10, base["Normal"])

    header = make_style("DocHeader", language_code, 10, base["Normal"])
    header.textColor = colors.white

    return {"title": title, "heading": heading, "body": body, "cell": cell, "header": header}


def bullet_list(items, style, language_code, width):
    rtl = language_code in RTL_LANGUAGES
    text_width = width - LIST_INDENT - BULLET_WIDTH
    bullet_style = ParagraphStyle("Bullet", parent=style, fontName=FALLBACK_FONT, alignment=TA_RIGHT if rtl else TA_LEFT)
    rows = []

    for item in items:
        text = paragraphs(item, style, language_code, text_width)
        bullet = Paragraph("•", bullet_style)
        rows.append([text, bullet] if rtl else [bullet, text])

    t = Table(rows, colWidths=[text_width, BULLET_WIDTH] if rtl else [BULLET_WIDTH, text_width])
    t.hAlign = "LEFT" if rtl else "RIGHT"  # leaves the indent on the side the text starts from
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return t


def data_table(table, styles, language_code, width):
    headers = [str(h) for h in table["headers"]]
    columns = len(headers)
    column_width = width / columns
    text_width = column_width - 2 * CELL_PADDING

    def cells(row, style, bold=False):
        row = ([str(cell) for cell in row] + [""] * columns)[:columns]
        out = [paragraphs(cell, style, language_code, text_width, bold) if cell.strip() else "" for cell in row]

        # Right-to-left tables start from the right
        return out[::-1] if language_code in RTL_LANGUAGES else out

    rows = [row for row in table.get("rows") or [] if isinstance(row, list)]
    data = [cells(headers, styles["header"], bold=True)] + [cells(row, styles["cell"]) for row in rows]

    t = Table(data, colWidths=[column_width] * columns, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), CELL_PADDING),
    ]))

    return t


def save_document_pdf(document, language_code, filename="document.pdf"):
    path = output_path(filename)
    title = str(document.get("title") or "")

    doc = SimpleDocTemplate(path, leftMargin=56, rightMargin=56, topMargin=56, bottomMargin=56, title=title)
    styles = document_styles(language_code)
    width = doc.width

    elements = paragraphs(title, styles["title"], language_code, width, bold=True)

    for section in document.get("sections") or []:
        if not isinstance(section, dict):
            continue

        if section.get("heading"):
            elements.extend(paragraphs(str(section["heading"]), styles["heading"], language_code, width, bold=True))

        for text in section.get("paragraphs") or []:
            elements.extend(paragraphs(str(text), styles["body"], language_code, width))
            elements.append(Spacer(1, 8))

        items = [str(item) for item in section.get("list") or [] if str(item).strip()]

        if items:
            elements.append(bullet_list(items, styles["body"], language_code, width))
            elements.append(Spacer(1, 8))

        table = section.get("table")

        if isinstance(table, dict) and table.get("headers"):
            elements.append(Spacer(1, 4))
            elements.append(data_table(table, styles, language_code, width))
            elements.append(Spacer(1, 12))

    doc.build(elements)
    return path
