# Changelog

## Unreleased

### Removed

- The MP3 audio format, along with the gTTS dependency. It was the only part of the tool that needed the internet

### Documents

- Generate structured documents from the main tool: choose "Document" at the first question, or pass
  `--format document` with `--pages`
- Write documents in all 13 languages, with right-to-left Urdu in the PDF
- Mix languages in a document with `--langs hin,eng --mix 50,50`: sections take turns by their share, each written,
  checked and typeset in its own language, with the language recorded on every section in `document.json`
- Plan an outline first, then write each section on its own, so length follows the page count and sections don't
  repeat each other
- Write documents of up to 50 pages, with about one section a page past 10 pages and a larger context window so
  long prompts aren't cut off
- Plan bullet lists and tables for about a third of the sections each, spread through the document, and retry any
  section that comes back too short, incomplete or in the wrong script, including its list and table
- Strip "I.", "II." and other section numbers the model adds to headings
- Start a section on a new page only when its heading would sit at the very bottom, so pages no longer end in gaps
- Ask for fewer words in sections with a table or list, so documents land on the page count they were asked for
- Keep a table's header together with its first two rows instead of leaving them alone at the bottom of a page
- Keep the introduction and conclusion as plain text
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
