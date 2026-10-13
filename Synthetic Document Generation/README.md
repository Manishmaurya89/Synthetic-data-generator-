# Synthetic Document Generator

**Generate complete structured documents as JSON and PDF with any local LLM in Ollama.**

Part of the [Synthetic Data Generator](../README.md). Give it a topic and it writes a full article with headings,
paragraphs, bullet lists and tables, then renders it as a clean PDF. Because the JSON records exactly what the PDF
contains, every pair works as ready-made test data for document parsers, layout models and RAG pipelines.

## Run it

Reuse the main project's environment:

```bash
cd "Synthetic Document Generation"
../.venv/bin/python main.py
```

Or set it up on its own:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

Then answer the prompts, or press Enter to accept each default:

```
=== Synthetic Document Generator ===

Local Ollama models:
  1. gemma4-32k:latest  (9.6 GB)
  2. llama3:latest  (4.7 GB)
Type a number, or any model name from ollama.com/library to download it.
Model [llama3:latest]:
Using local model: llama3:latest

Topic [Impact of Artificial Intelligence on Healthcare]: Renewable energy in India
Pages [2]: 3
Language (eng/hin) [eng]: hin
```

## Run without questions

Pass any of the settings as flags and the rest use their defaults:

```bash
../.venv/bin/python main.py --topic "Renewable energy in India" --pages 3 --language hin --model gemma4
```

| Flag | Meaning | Default |
| --- | --- | --- |
| `--topic` | What the document is about | Impact of Artificial Intelligence on Healthcare |
| `--pages` | Length, about 400 words per page | `2` |
| `--language` | `eng` or `hin` | `eng` |
| `--model` | Ollama model to use | `llama3` |

## Output

| File | Contents |
| --- | --- |
| `outputs/output.json` | The article: title, then sections with headings, paragraphs, lists and tables |
| `outputs/final_output.pdf` | The same article, rendered with wrapped tables and bullet lists |

## Tips

- **Scale the length** with the page count. Each page asks the model for about 400 words.
- **Pick any model.** Choose from the menu, type a new name to download it, or set `OLLAMA_MODEL` to change the default.
- **Write in Hindi** by choosing `hin`. The PDF uses a Devanagari font with proper letter shaping.

## Test

```bash
../.venv/bin/pytest
```

The Devanagari font in `fonts/` is a [Noto](https://github.com/notofonts) font under the SIL Open Font License 1.1
(see `fonts/OFL.txt`).
