import json
import os
import requests
from config import DEFAULT_MODEL, OLLAMA_PULL_URL, OLLAMA_TAGS_URL


def list_models():
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        raise RuntimeError("Ollama is not running. Install it from https://ollama.com and start it (or run: ollama serve)")

    return [(model["name"], model.get("size", 0)) for model in response.json().get("models", [])]


def find_model(name, installed):
    for model in installed:
        if model in (name, f"{name}:latest"):
            return model

    return None


def resolve_model(name):
    model = find_model(name, [installed for installed, _ in list_models()])

    if not model:
        raise RuntimeError(f"Model '{name}' is not downloaded. Run: ollama pull {name}")

    return model


def pull_model(name):
    print(f"\nDownloading {name}. Large models can take a while...")

    with requests.post(OLLAMA_PULL_URL, json={"model": name}, stream=True, timeout=(10, 600)) as response:
        for line in response.iter_lines():
            if not line:
                continue

            status = json.loads(line)

            if "error" in status:
                raise RuntimeError(f"Could not download '{name}': {status['error']}")

            if status.get("total") and status.get("completed"):
                print(f"\r  {status['completed'] * 100 // status['total']}%", end="", flush=True)

    print(f"\r  {name} is ready.")


def choose_model():
    models = list_models()
    installed = [name for name, _ in models]

    print("\nLocal Ollama models:")

    if not models:
        print("  (none downloaded yet)")

    for i, (name, size) in enumerate(models, 1):
        print(f"  {i}. {name}  ({size / 1e9:.1f} GB)")

    default = find_model(DEFAULT_MODEL, installed)

    if not default:
        default = installed[0] if installed and "OLLAMA_MODEL" not in os.environ else DEFAULT_MODEL

    print("Type a number, or any model name from ollama.com/library to download it.")
    choice = input(f"Model [{default}]: ").strip() or default

    if choice.isdigit() and 1 <= int(choice) <= len(installed):
        return installed[int(choice) - 1]

    model = find_model(choice, installed)

    if model:
        return model

    answer = input(f"'{choice}' is not downloaded. Download it now? (y/n): ").strip().lower()

    if answer not in ("y", "yes"):
        raise ValueError("No model selected")

    pull_model(choice)
    return choice
