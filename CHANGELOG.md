# Changelog

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
