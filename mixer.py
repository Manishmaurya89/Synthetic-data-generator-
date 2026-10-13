import random


def allocate_counts(total_samples, mix_ratio):
    counts = {lang: total_samples * percent // 100 for lang, percent in mix_ratio.items()}
    leftover = total_samples - sum(counts.values())

    by_remainder = sorted(
        mix_ratio,
        key=lambda lang: total_samples * mix_ratio[lang] % 100,
        reverse=True
    )

    for lang in by_remainder[:leftover]:
        counts[lang] += 1

    return counts


def mix_languages(language_data):
    mixed = [
        (lang, sentence)
        for lang, sentences in language_data.items()
        for sentence in sentences
    ]

    random.shuffle(mixed)
    return mixed
