from gtts import gTTS
import os

def generate_audio_dataset(data, lang="en"):
    os.makedirs("dataset/audio", exist_ok=True)

    for i, text in enumerate(data):
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(f"dataset/audio/{i}.mp3")
        except:
            continue

    print("Audio dataset created!")