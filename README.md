# Synthetic Data Generator

Generate synthetic datasets on your own computer with free, open-source LLMs running in [Ollama](https://ollama.com).
No API key, no per-token billing, no daily token cap.

## Why local?

A useful synthetic dataset needs a lot of LLM output. Paid APIs such as OpenRouter or OpenAI bill for every token,
and free tiers limit how many requests or tokens you get per day. That makes large datasets expensive or slow to build.

Running the model on your own machine removes those limits:

- **Free to run.** Once a model is downloaded, generating more data costs only time and electricity.
- **No rate limits or daily caps.** Generate as much as your hardware can handle.
- **Your data stays with you.** Prompts and outputs never go to a third-party API (audio is the one exception, see [What runs offline](#what-runs-offline)).
- **Any open model.** Switch between llama3, Gemma, Qwen and others with one environment variable.

## What it generates

| Tool | Folder | Output |
| --- | --- | --- |
| Multilingual sentence datasets | this folder | Unique sentences on any topic, in one language or a mix, as TXT, JSON, CSV, PDF or audio |
| Synthetic documents | [`Synthetic Document Generation/`](Synthetic%20Document%20Generation/README.md) | Structured articles (headings, paragraphs, lists, tables) as JSON and PDF, parsed back with Docling, with named entities from GLiNER |

### Supported languages

| Code | Language | Code | Language | Code | Language |
| --- | --- | --- | --- | --- | --- |
| `eng` | English | `tel` | Telugu | `mal` | Malayalam |
| `hin` | Hindi | `mar` | Marathi | `kan` | Kannada |
| `ben` | Bengali | `guj` | Gujarati | `nep` | Nepali |
| `urd` | Urdu | `pan` | Punjabi | `sin` | Sinhala |
| `tam` | Tamil | | | | |

## Requirements

- [Ollama](https://ollama.com/download)
- Python 3.13 (the version it's tested with)
- Enough RAM for your model. As a rough guide, 8 GB free for an 8B model like llama3; bigger models need more.

## Quick start

```bash
# 1. Install Ollama, then download a model
ollama pull llama3

# 2. Get the code and install the Python packages
git clone https://github.com/Manishmaurya89/Synthetic-data-generator-.git
cd Synthetic-data-generator-
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Generate a dataset
.venv/bin/python main.py
```

A typical session:

```
=== Synthetic Data Generator ===
Using local model: llama3

Supported language codes:
eng, hin, ben, urd, tam, tel, mar, guj, pan, mal, kan, nep, sin

Enter language code(s) (e.g. eng or eng,hin): eng,hin
Enter number of samples: 200
Enter topic: Newton's laws of motion
Format (txt/json/csv/pdf/audio): json

Enter percentage for each language (must sum to 100):
  eng (%): 50
  hin (%): 50
Generating sentences for: English...
Generating sentences for: Hindi...
JSON dataset generated successfully in .../outputs
```

If Ollama isn't running or the model isn't downloaded, the tool says so and prints the command that fixes it.

## Choosing a model

llama3 is the default. To use any other model you've pulled, set `OLLAMA_MODEL`:

```bash
ollama pull gemma4
OLLAMA_MODEL=gemma4 .venv/bin/python main.py
```

Browse models at [ollama.com/library](https://ollama.com/library). Some tips:

- **Multilingual quality varies a lot between models.** Asked for 27 Urdu sentences, llama3 produced only 9 that
  passed the language check, while a Gemma 4 model produced all 27. If you see a warning that a language came up
  short, try a bigger or more multilingual model.
- **Smaller models are faster, larger ones write better and more varied sentences.** Pick based on your hardware and
  how much data you need.

## Output formats

Files are written to `outputs/`.

| Format | File | Contents |
| --- | --- | --- |
| `txt` | `dataset.txt` | One sentence per line |
| `json` | `dataset.json` | `[{"text": "...", "language": "hin"}, ...]` |
| `csv` | `dataset.csv` | `text` and `language` columns |
| `pdf` | `dataset.pdf` | The topic as a title, then every sentence in its own script's font (Urdu right-to-left) |
| `audio` | `audio/*.mp3` and `audio/metadata.csv` | One clip per sentence, in that language's voice; the CSV links each file to its text |

## Data quality

The LLM is asked for 60 sentences per call, and it keeps calling until it has enough unique sentences. Each one goes
through these checks:

1. **Cleanup:** numbering, bullets and intro lines like "Here are 60 sentences:" are removed.
2. **Language check:** at least 70% of the letters must be in the language's own script, and none can come from a
   third script.
3. **Deduplication:** every sentence in a dataset is unique.

If the model can't produce enough sentences, you get a warning and a smaller dataset, never one padded with
repeats. For mixed datasets, the percentages always add up to the exact number of samples you asked for.

## Synthetic documents

The second tool generates whole documents rather than sentences:

```
LLM → article JSON → PDF → Docling (structure) → GLiNER (named entities)
```

Because you have the original JSON, you know exactly what the PDF contains, which makes the output useful for
building and testing document-parsing and information-extraction pipelines. See its
[README](Synthetic%20Document%20Generation/README.md) for setup.

## What runs offline

| Step | Local? |
| --- | --- |
| Text generation (Ollama) | Yes |
| TXT, JSON, CSV and PDF output | Yes |
| Audio (gTTS) | No, it uses Google's online text-to-speech |
| Docling and GLiNER | Yes, after downloading their models from Hugging Face on the first run |

## Project structure

```
.
├── main.py            asks for your settings and runs everything
├── generator.py       prompts the local LLM, cleans and checks the sentences
├── mixer.py           splits samples between languages and shuffles them
├── output.py          writes TXT, JSON, CSV and PDF files
├── media.py           writes audio clips
├── scripts.py         detects which script a piece of text is written in
├── config.py          languages, fonts, model and paths
├── fonts/             Noto fonts for the PDF output
└── Synthetic Document Generation/
```

## Roadmap

- Offline text-to-speech, so audio datasets don't need the internet either
- Support for other local LLM servers such as LM Studio and llama.cpp

## Contributing

Pull requests are welcome. To add a language:

1. Add its code to every table in `config.py`: `LANG_CODE_MAP`, `GTTS_LANG_MAP`, `SCRIPT_RANGES` and `FONT_FILES`
   (and `RTL_LANGUAGES` if it's written right-to-left).
2. Add a prompt written in that language to `build_prompt()` in `generator.py`.
3. Put a font that covers its script in `fonts/`.

## License

The code is released under the MIT License (see `LICENSE`). The fonts in `fonts/` are
[Noto](https://github.com/notofonts) fonts, licensed under the SIL Open Font License 1.1 (see `fonts/OFL.txt`).
