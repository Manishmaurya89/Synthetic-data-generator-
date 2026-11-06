# Changelog

## Unreleased

### Documents

- Generate structured documents from the main tool: choose "Document" at the first question, or pass
  `--format document` with `--pages`
- Write documents in all 13 languages, with right-to-left Urdu in the PDF
- Plan an outline first, then write each section on its own, so length follows the page count and sections don't
  repeat each other
- Plan at least one bullet list and one table in every document, and retry any section that comes back too short,
  incomplete or in the wrong script
- Clean up stray Chinese punctuation and markdown that models slip into the text
- Replace the separate `Synthetic Document Generation/` folder, which only supported English and Hindi

## v1.0.0

The first release of Synthetic Data Generator: free synthetic data from any local LLM.

### Sentence datasets

- Generate unique sentences on any topic in 13 languages: English, Hindi, Bengali, Urdu, Tamil, Telugu, Marathi,
  Gujarati, Punjabi, Malayalam, Kannada, Nepali and Sinhala
- Mix languages by percentage, with counts that always add up exactly
- Export to TXT, JSON, CSV, PDF or MP3 audio with a transcript
- Filter out numbering, intro lines, duplicates and sentences in the wrong language
- Render PDFs in every script, with proper letter shaping and right-to-left Urdu

### Models

- Choose any installed Ollama model from a menu, or download a new one by typing its name
- Set the default model with `OLLAMA_MODEL`

### Automation

- Run without questions using command-line flags (`--langs`, `--samples`, `--topic`, `--format`, `--mix`, `--model`)
- Test suite with GitHub Actions on every push

### Documents

- Generate structured articles with headings, paragraphs, lists and tables as JSON and PDF, in English or Hindi
