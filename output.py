import json
import csv


# TXT 
def save_txt(data, filename="dataset.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for line in data:
            f.write(line + "\n")


# JSON 
def save_json(data, filename="dataset.json"):
    structured = [{"text": line} for line in data]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)


#  CSV 
def save_csv(data, filename="dataset.csv"):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["text"])

        for line in data:
            writer.writerow([line])


#  PDF (MULTILINGUAL TTF SUPPORT)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# FONT REGISTRATION 
pdfmetrics.registerFont(TTFont("HindiFont", "NotoSansDevanagari.ttf"))
pdfmetrics.registerFont(TTFont("UrduFont", "NotoNaskhArabic-Regular.ttf"))
pdfmetrics.registerFont(TTFont("TeluguFont", "NotoSansTelugu-Regular.ttf"))
pdfmetrics.registerFont(TTFont("TamilFont", "NotoSansTamil-Regular.ttf"))
pdfmetrics.registerFont(TTFont("KannadaFont", "NotoSansKannada-Regular.ttf"))


# SCRIPT DETECTION
def is_urdu(text):
    return any('\u0600' <= c <= '\u06FF' for c in text)

def is_devanagari(text):
    return any('\u0900' <= c <= '\u097F' for c in text)

def is_telugu(text):
    return any('\u0C00' <= c <= '\u0C7F' for c in text)

def is_tamil(text):
    return any('\u0B80' <= c <= '\u0BFF' for c in text)

def is_kannada(text):
    return any('\u0C80' <= c <= '\u0CFF' for c in text)


# PDF FUNCTION 
def save_pdf(data, topic, filename="dataset.pdf"):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="HindiFont",
        fontSize=14
    )

    elements.append(Paragraph(f"<b>{topic}</b>", title_style))
    elements.append(Spacer(1, 15))

    # Content
    for line in data:
        style = ParagraphStyle(
            "NormalStyle",
            parent=styles["Normal"],
            fontSize=11
        )

        if is_urdu(line):
            style.fontName = "UrduFont"

        elif is_telugu(line):
            style.fontName = "TeluguFont"

        elif is_tamil(line):
            style.fontName = "TamilFont"

        elif is_kannada(line):
            style.fontName = "KannadaFont"

        elif is_devanagari(line):
            style.fontName = "HindiFont"

        else:
            style.fontName = "HindiFont"  # fallback

        elements.append(Paragraph(line, style))
        elements.append(Spacer(1, 8))

    doc.build(elements)