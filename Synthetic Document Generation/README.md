# Synthetic Document Generation

Part of the [Synthetic Data Generator](../README.md): generate synthetic documents with a free local LLM.

It writes a structured article (headings, paragraphs, lists, tables) with a model running in Ollama, renders it as a
PDF, then reads the PDF back with Docling and extracts named entities with GLiNER. Since you keep the original JSON,
you know exactly what each PDF contains, which is what you need to build and test document-parsing pipelines.

```
LLM → article JSON → PDF → Docling (structure) → GLiNER (named entities)
```

## Setup

```bash
ollama pull llama3        # any Ollama model works, see below
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

On the first run, Docling and GLiNER download their models from Hugging Face. After that, everything runs offline.

## Run

Set `topic`, `pages` and `language` (`"eng"` or `"hin"`) in `main.py`, then:

```bash
venv/bin/python main.py
```

To use a different local model:

```bash
OLLAMA_MODEL=gemma4 venv/bin/python main.py
```

Everything is written to `outputs/`:

| File | Contents |
| --- | --- |
| `output.json` | The article as the LLM wrote it |
| `final_output.pdf` | The rendered article |
| `docling_output.json` | Docling's full parse of the PDF |
| `extracted_text.txt` | Cleaned text from the PDF |
| `structured_output.json` | The text grouped into sections by heading |
| `entities.json` | Named entities with their positions in `extracted_text.txt` |

In our test, a two-page article took about 50 seconds end to end with llama3.

## Notes

- `urchade/gliner_base` is an English model. For Hindi documents, `urchade/gliner_multi-v2.1` in
  `gliner_processor.py` will find far more entities.
- The Devanagari font in `fonts/` is a [Noto](https://github.com/notofonts) font, licensed under the
  SIL Open Font License 1.1 (see `fonts/OFL.txt`).
