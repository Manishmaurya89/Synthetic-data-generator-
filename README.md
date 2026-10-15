# Synthetic Data Generator

Make synthetic training data on your own machine with any open-source LLM in Ollama. It's free, and you don't
need an API key.

[![Tests](https://github.com/Manishmaurya89/Synthetic-data-generator-/actions/workflows/tests.yml/badge.svg)](https://github.com/Manishmaurya89/Synthetic-data-generator-/actions/workflows/tests.yml)
![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

I built this because I needed sentence datasets in Indian languages and kept running into free-tier limits on
hosted APIs. With this tool you pick a model you already have, give it a topic, and get a clean, deduplicated
dataset in any of 13 languages. It can also write whole structured documents.

![Demo: choosing a model and generating an English and Hindi dataset](docs/demo.gif)

## Why run it locally

Hosted APIs charge per token and cap how much you can generate on a free plan. A local model costs nothing once
it's downloaded and only stops when your hardware does. Your prompts and data also stay on your machine. The one
exception is the audio format, which uses Google's online text-to-speech (gTTS). And you aren't stuck with one
provider's catalog: any model in the [Ollama library](https://ollama.com/library) works.

## What it can do

- Write unique sentences on any topic in 13 languages.
- Mix languages by percentage, for example 60% Hindi and 40% English, and the counts always add up exactly.
- Let you pick any installed Ollama model from a menu, or download a new one by typing its name.
- Throw out numbering, intro lines, duplicates and sentences in the wrong language.
- Save to TXT, JSON, CSV, PDF or MP3 audio.
- Run without any questions, using command-line flags, so you can script it.
- Render PDFs in every script, with proper letter shaping and right-to-left Urdu.
- Write full structured documents with headings, paragraphs, lists and tables, as JSON and PDF.

## Quick start

1. Install Ollama from [ollama.com/download](https://ollama.com/download) and start it.

2. Clone and set up the project:

   ```bash
   git clone https://github.com/Manishmaurya89/Synthetic-data-generator-.git
   cd Synthetic-data-generator-
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. Run it:

   ```bash
   .venv/bin/python main.py
   ```

Pick a model and answer a few questions: languages, number of samples, topic and format. If you don't have a
model yet, type a name like `llama3` at the model prompt and the tool downloads it for you.

## Running it without questions

Pass the settings as flags to use it in scripts and pipelines:

```bash
.venv/bin/python main.py --langs hin,eng --mix 60,40 --samples 500 --topic "water cycle" --format json --model gemma4
```

| Flag | Meaning | Default |
| --- | --- | --- |
| `--langs` | Language codes, comma-separated | required |
| `--samples` | Number of sentences | required |
| `--topic` | What the sentences are about | required |
| `--format` | `txt`, `json`, `csv`, `pdf` or `audio` | required |
| `--mix` | Percentage per language, in `--langs` order | even split |
| `--model` | Ollama model to use | `llama3` |

Run `python main.py --help` for the full list.

## Choosing a model

Every interactive run starts with a menu of the models you already have. Pick one by number, press Enter for the
default, or type any name from the [Ollama library](https://ollama.com/library) to download it right there:

```
Local Ollama models:
  1. gemma4-32k:latest  (9.6 GB)
  2. llama3:latest  (4.7 GB)
Type a number, or any model name from ollama.com/library to download it.
Model [llama3:latest]: qwen2.5
'qwen2.5' is not downloaded. Download it now? (y/n): y

Downloading qwen2.5. Large models can take a while...
  qwen2.5 is ready.
```

To change which model Enter picks, set `OLLAMA_MODEL`:

```bash
OLLAMA_MODEL=gemma4 .venv/bin/python main.py
```

Some advice from using it:

- `llama3` (4.7 GB) is a good place to start. It's fast and strong in English.
- For South Asian languages, try a different model. When I asked for 27 Urdu sentences, llama3 gave 9 that passed
  the language check, while a Gemma 4 model gave all 27. If you see a warning that a language came up short,
  switch models.
- Match the model to your RAM. Roughly 8 GB for 7–8B models, 16 GB for 13–14B and 32 GB for 30B and up. Bigger
  models write richer, more varied sentences; smaller ones finish faster.

## Supported languages

| Code | Language | Code | Language | Code | Language |
| --- | --- | --- | --- | --- | --- |
| `eng` | English | `tel` | Telugu | `mal` | Malayalam |
| `hin` | Hindi | `mar` | Marathi | `kan` | Kannada |
| `ben` | Bengali | `guj` | Gujarati | `nep` | Nepali |
| `urd` | Urdu | `pan` | Punjabi | `sin` | Sinhala |
| `tam` | Tamil | | | | |

## Output formats

Every file is saved in `outputs/`.

| Format | File | Contents |
| --- | --- | --- |
| `txt` | `dataset.txt` | One sentence per line |
| `json` | `dataset.json` | `[{"text": "...", "language": "hin"}, ...]` |
| `csv` | `dataset.csv` | `text` and `language` columns |
| `pdf` | `dataset.pdf` | The topic as a title, then every sentence in its script's own font |
| `audio` | `audio/*.mp3` + `audio/metadata.csv` | One clip per sentence in that language's voice, plus a CSV linking each clip to its text |

## Example output

The [`examples/`](examples) folder has real, unedited datasets made with this tool: 25 sentences in each of the 13
languages, a mixed Hindi and English dataset in JSON and CSV, the full PDF and a few audio clips.

## How it works

```
Topic + languages + model
  -> Prompt the local LLM in each language, in that language
  -> Clean    strip numbering, bullets and intro lines
  -> Check    keep only sentences written in the right script
  -> Dedupe   drop repeats, then ask again until there are enough unique sentences
  -> Mix      split the samples by your percentages and shuffle
  -> Export   TXT, JSON, CSV, PDF or MP3
```

A few rules keep the data clean. Every sentence in a dataset is unique. If the model can't come up with enough,
you get a warning and a smaller dataset, never one padded with repeats. At least 70% of the letters in each
sentence must be in that language's own script, and a sentence with stray letters from any third script is
rejected. Mixed datasets always add up to exactly the number of samples you asked for.

## Generating structured documents

If you need whole documents instead of sentences, the document generator writes a complete article with
headings, paragraphs, bullet lists and tables, then renders it as a PDF. The JSON records exactly what's in the
PDF, so each pair works as test data for document parsers, text extraction and RAG pipelines.

```bash
cd "Synthetic Document Generation"
../.venv/bin/python main.py
../.venv/bin/python main.py --topic "Renewable energy in India" --pages 3 --language hin
```

It writes `outputs/output.json` and `outputs/final_output.pdf`. There's more in its
[README](Synthetic%20Document%20Generation/README.md).

## Project layout

```
main.py            the entry point: asks for your settings (or reads flags) and runs everything
models.py          lists, picks and downloads Ollama models
generator.py       prompts the LLM, then cleans and checks every sentence
mixer.py           splits samples between languages and shuffles them
output.py          writes TXT, JSON, CSV and PDF files
media.py           writes MP3 clips and their metadata
scripts.py         detects which script a piece of text is written in
config.py          languages, fonts, default model and paths
fonts/             Noto fonts for every supported script
tests/             test suite (runs without Ollama)
examples/          real generated datasets
Synthetic Document Generation/   generates structured documents as JSON and PDF
```

## What's next

- Offline text-to-speech, so audio datasets don't need the internet
- Support for other local servers such as LM Studio and llama.cpp
- More South Asian languages, such as Odia, Assamese and Kashmiri

## Contributing

Pull requests are welcome, and adding a language is a nice first contribution.
[CONTRIBUTING.md](CONTRIBUTING.md) covers setup, tests and a step-by-step guide.

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

## License

MIT (see `LICENSE`). The fonts in `fonts/` are [Noto](https://github.com/notofonts) fonts under the SIL Open
Font License 1.1 (see `fonts/OFL.txt`).
