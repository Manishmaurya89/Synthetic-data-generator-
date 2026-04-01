import random


def mix_languages(language_data, mix_ratio):
    mixed = []

    for lang, sentences in language_data.items():
        ratio = mix_ratio.get(lang, 0) / 100
        count = int(len(sentences) * ratio)
        mixed.extend(sentences[:count])

    random.shuffle(mixed)
    return mixed