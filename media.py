from gtts import gTTS
import csv
import os

from config import GTTS_LANG_MAP, OUTPUT_DIR


def generate_audio_dataset(data, folder=os.path.join(OUTPUT_DIR, "audio")):
    os.makedirs(folder, exist_ok=True)

    rows = []

    for i, (lang, text) in enumerate(data):
        filename = f"{i}.mp3"

        try:
            tts = gTTS(text=text, lang=GTTS_LANG_MAP[lang])
            tts.save(os.path.join(folder, filename))
        except Exception as e:
            print(f"Audio failed for sample {i} ({lang}): {e}")
            continue

        rows.append([filename, lang, text])

    # Metadata file
    with open(os.path.join(folder, "metadata.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "language", "text"])
        writer.writerows(rows)

    print(f"Audio dataset created: {len(rows)} of {len(data)} clips saved in {folder}")

    return len(rows)
