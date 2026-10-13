# Examples

Real output from Synthetic Data Generator, unedited. Everything here was generated locally with
`gemma4-32k` (a Gemma 4 build) through Ollama, on the topic "The water cycle".

## [`water-cycle/`](water-cycle)

| File | What it is |
| --- | --- |
| `eng.txt`, `hin.txt`, … `sin.txt` | 25 unique sentences in each of the 13 languages |
| `mixed-hin-eng.json`, `mixed-hin-eng.csv` | A mixed dataset: 12 Hindi and 8 English sentences, shuffled and tagged with their language |
| `all-languages.pdf` | Two sentences in every language in one PDF, including right-to-left Urdu |
| `audio/` | Three MP3 clips (English, Hindi, Urdu) and the `metadata.csv` that links each clip to its text |

Each language file matches what this command produces:

```bash
python main.py --model gemma4-32k --langs hin --samples 25 --topic "The water cycle" --format txt
```

The sentences are exactly as the model wrote them, so they also show the kind of quality to expect. Try a different
model and compare.
