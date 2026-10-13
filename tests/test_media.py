import csv

import media


class FakeTTS:
    voices = []

    def __init__(self, text, lang):
        FakeTTS.voices.append(lang)

    def save(self, path):
        open(path, "wb").close()


def test_each_sentence_gets_its_own_voice_and_a_transcript(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "gTTS", FakeTTS)
    data = [("eng", "Force."), ("hin", "बल।"), ("urd", "قوت۔")]

    assert media.generate_audio_dataset(data, folder=str(tmp_path)) == 3
    assert FakeTTS.voices == ["en", "hi", "ur"]

    with open(tmp_path / "metadata.csv", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows == [["file", "language", "text"], ["0.mp3", "eng", "Force."], ["1.mp3", "hin", "बल।"], ["2.mp3", "urd", "قوت۔"]]
