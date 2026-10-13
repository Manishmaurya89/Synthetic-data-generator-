import os
from xml.sax.saxutils import escape

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import FONT_DIR, FONT_FILES


def get_font(language_code):
    filename = FONT_FILES[language_code]

    if filename is None:
        return None

    font_name = os.path.splitext(filename)[0]

    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, os.path.join(FONT_DIR, filename)))

    return font_name


def text(value):
    return escape(str(value))


def flatten(items):
    if isinstance(items, str):
        items = [items]

    for item in items or []:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


def make_table(table, cell_style, header_style, width):
    headers = list(flatten(table.get("headers")))

    if not headers:
        return None

    columns = len(headers)
    table_data = [[Paragraph(text(h), header_style) for h in headers]]

    for row in table.get("rows") or []:
        if isinstance(row, dict):
            row = [row.get(h, "") for h in headers]

        if not isinstance(row, list) or not any(str(cell).strip() for cell in row):
            continue

        row = (row + [""] * columns)[:columns]
        table_data.append([Paragraph(text(cell), cell_style) for cell in row])

    t = Table(table_data, colWidths=[width / columns] * columns, repeatRows=1)

    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    return t


def save_pdf(data, filename="output.pdf", language_code="eng"):
    doc = SimpleDocTemplate(
        filename,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    font_name = get_font(language_code)
    font = {"fontName": font_name, "shaping": 1} if font_name else {}

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        leading=26,
        spaceAfter=16,
        **font
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=10,
        **font
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=12,
        **font
    )

    cell_style = ParagraphStyle(
        "CellStyle",
        parent=normal_style,
        fontSize=10,
        leading=13,
        spaceAfter=0
    )

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=cell_style,
        textColor=colors.white
    )

    elements = []

    # -------- TITLE --------
    elements.append(Paragraph(text(data.get("title", "")), title_style))
    elements.append(Spacer(1, 12))

    # -------- SECTIONS --------
    for sec in data.get("sections", []):
        if not isinstance(sec, dict):
            continue

        if sec.get("heading"):
            elements.append(Paragraph(text(sec["heading"]), heading_style))

        # paragraphs
        for p in flatten(sec.get("paragraphs")):
            elements.append(Paragraph(text(p), normal_style))

        # lists
        items = list(flatten(sec.get("lists")))

        if items:
            bullet_items = [
                Paragraph(text(item), normal_style)
                for item in items
            ]
            elements.append(ListFlowable(bullet_items, bulletType="bullet"))

        # tables
        for table in sec.get("tables") or []:
            if not isinstance(table, dict):
                continue

            t = make_table(table, cell_style, header_style, doc.width)

            if t is None:
                continue

            elements.append(Spacer(1, 10))
            elements.append(t)
            elements.append(Spacer(1, 12))

    doc.build(elements)

    print(f"PDF saved as {filename}")
