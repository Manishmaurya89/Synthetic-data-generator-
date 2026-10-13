from gliner import GLiNER
# Load model once
model = GLiNER.from_pretrained("urchade/gliner_base")

LABELS = [
    "country",
    "person",
    "organization",
    "event",
    "date",
    "caste"
]


def extract_entities(text):
    entities = []
    offset = 0

    for line in text.split("\n"):
        if line.strip():
            for entity in model.predict_entities(line, LABELS):
                entity["start"] += offset
                entity["end"] += offset
                entities.append(entity)

        offset += len(line) + 1

    return entities
