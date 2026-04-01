# 🌐 Synthetic Data Generator

A multilingual synthetic text dataset generator powered by a local LLM (Ollama). Generate sentence-level datasets in **13 South Asian and global languages** in multiple output formats — ideal for NLP research, model fine-tuning, and language resource development.

---

## 🗣️ Supported Languages

| Code  | Language   |
|-------|------------|
| `eng` | English    |
| `hin` | Hindi      |
| `ben` | Bengali    |
| `urd` | Urdu       |
| `tam` | Tamil      |
| `tel` | Telugu     |
| `mar` | Marathi    |
| `guj` | Gujarati   |
| `pan` | Punjabi    |
| `mal` | Malayalam  |
| `kan` | Kannada    |
| `nep` | Nepali     |
| `sin` | Sinhala    |

---

## 📦 Output Formats

| Format  | Description                        |
|---------|------------------------------------|
| `txt`   | Plain text, one sentence per line  |
| `json`  | Structured `[{"text": "..."}]`     |
| `csv`   | Single-column CSV with header      |
| `pdf`   | Multilingual PDF with font support |
| `audio` | MP3 audio files via gTTS           |

---

## 🛠️ Requirements

### System
- Python 3.8+
- [Ollama](https://ollama.com/) running locally with `llama3` pulled

### Python Dependencies

```bash
pip install requests reportlab gtts
```

### Fonts

Download and place these fonts in the **project root** (or `fonts/` folder):

| Font File                        | Script     | Download |
|----------------------------------|------------|----------|
| `NotoSansDevanagari.ttf`         | Hindi, Marathi, Nepali | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari) |
| `NotoNaskhArabic-Regular.ttf`   | Urdu       | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic) |
| `NotoSansTamil-Regular.ttf`     | Tamil      | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+Tamil) |
| `NotoSansTelugu-Regular.ttf`    | Telugu     | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+Telugu) |
| `NotoSansKannada-Regular.ttf`   | Kannada    | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+Kannada) |

---

## 🚀 Usage

### 1. Start Ollama

```bash
ollama serve
ollama pull llama3
```

### 2. Run the Generator

```bash
python main.py
```

You'll be prompted interactively:

```
Supported language codes:
eng, hin, ben, urd, tam, tel, mar, guj, pan, mal, kan, nep, sin

Enter language code(s) (e.g. eng or eng,hin): hin,eng
Enter number of samples: 100
Enter topic: climate change
Format (txt/json/csv/pdf/audio): json

Enter percentage for each language:
hin: 60
eng: 40
```

---

## 📁 Project Structure

```
synthetic-data-generator/
├── main.py           # Entry point — user input & orchestration
├── generator.py      # LLM prompt builder & sentence generator
├── mixer.py          # Multilingual mixing by ratio
├── formatter.py      # Page-to-sentence count helper
├── output.py         # Save as TXT / JSON / CSV / PDF
├── media.py          # Audio dataset generation (gTTS)
├── config.py         # Language map & model config
├── fonts/            # Place .ttf font files here
├── dataset/          # Output files saved here
└── README.md
```

---

## ⚙️ Configuration

Edit `config.py` to change the default model or Ollama endpoint:

```python
DEFAULT_MODEL = "llama3"           # Any model available in Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
```

---

## 🔧 How It Works

1. **Prompt Generation** — Language-specific prompts are sent to the local LLM via Ollama's REST API.
2. **Output Cleaning** — Removes numbering, short lines, duplicates, and intro phrases.
3. **Data Expansion** — If fewer sentences are returned than requested, the set is shuffled and repeated to meet the target count.
4. **Mixing** — For multilingual datasets, sentences are combined by user-defined percentage ratios and shuffled.
5. **Export** — Dataset is saved in the chosen format with multilingual font support for PDF output.

---

## 📝 Known Limitations

- Audio output (`gtts`) uses a fixed language (`en` by default). Update `media.py` to map language codes to gTTS language tags for accurate TTS.
- PDF output defaults to `HindiFont` as a fallback for unsupported scripts (e.g., Bengali, Malayalam, Gujarati, Punjabi, Sinhala). Add the corresponding Noto fonts to support them.
- Output quality depends on the LLM model used. Larger models (e.g., `llama3:70b`) generally produce better multilingual output.

---

## 🤝 Contributing

Pull requests are welcome! To add a new language:
1. Add its code and name to `LANG_CODE_MAP` in `config.py`
2. Add a prompt block in `generator.py`'s `build_prompt()` function
3. Register the appropriate font in `output.py` and add a script detection function

---

## 📄 License

MIT License — free to use, modify, and distribute.
