# Contributing

Thanks for helping make free, local synthetic data better. Bug reports, new languages, better prompts and
documentation fixes are all welcome.

## Ground rule

**Everything runs locally.** The project exists so people can generate data without paying per token, so new
features should work with Ollama on the user's own machine, with no API keys and no paid services.

## Set up

```bash
git clone https://github.com/Manishmaurya89/Synthetic-data-generator-.git
cd Synthetic-data-generator-
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
ollama pull llama3
```

## Run the tests

The tests use a fake LLM, so they run in seconds and don't need Ollama:

```bash
.venv/bin/pytest
cd "Synthetic Document Generation" && ../.venv/bin/pytest
```

GitHub Actions runs both suites on every push and pull request.

## Add a language

This is the best first contribution.

1. **Register** the language code in every table in `config.py`: `LANG_CODE_MAP`, `GTTS_LANG_MAP`, `SCRIPT_RANGES`
   and `FONT_FILES` (plus `RTL_LANGUAGES` if it's written right-to-left).
2. **Write** a prompt in that language in `build_prompt()` in `generator.py`. Ask a native speaker to check it if you
   can; a natural prompt gets noticeably better sentences.
3. **Add** a font that covers the script to `fonts/`. [Noto](https://github.com/notofonts) fonts are a good choice,
   and their "full" builds include Latin letters and digits.
4. **Test** it: add a sample sentence to `SAMPLES` in `tests/test_output.py`, run the tests, then generate a small
   dataset and a PDF to check the output by eye.

## Open a pull request

- Keep each pull request focused on one change.
- Add or update tests for any change in behavior.
- Match the style of the surrounding code.
- Describe what you changed and how you tested it.
