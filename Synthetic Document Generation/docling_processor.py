from docling.document_converter import DocumentConverter
from text_cleaner import clean_text

HEADING_LABELS = {"title", "section_header"}
SKIP_LABELS = {"page_header", "page_footer"}


def extract_sections(items):
    sections = []

    current_section = {
        "heading": "Introduction",
        "content": []
    }

    for label, content in items:
        if label in HEADING_LABELS:
            if current_section["content"]:
                sections.append(current_section)

            current_section = {
                "heading": content,
                "content": []
            }
        else:
            current_section["content"].append(content)

    if current_section["content"]:
        sections.append(current_section)

    return [
        {"heading": section["heading"], "content": "\n".join(section["content"])}
        for section in sections
    ]


def extract_data(file_path):
    converter = DocumentConverter()
    result = converter.convert(file_path)

    doc = result.document

    doc_dict = doc.export_to_dict()

    items = []

    for t in doc_dict.get("texts", []):
        label = t.get("label", "text")

        if label in SKIP_LABELS:
            continue

        content = clean_text(t.get("text", ""), label)

        if content:
            items.append((label, content))

    full_text = "\n".join(content for _, content in items)

    return {
        "text": full_text,
        "json": doc_dict,
        "sections": extract_sections(items)
    }
