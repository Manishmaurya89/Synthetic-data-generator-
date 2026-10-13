from mixer import allocate_counts, mix_languages


def test_counts_always_add_up():
    assert sum(allocate_counts(10, {"eng": 33, "hin": 33, "urd": 34}).values()) == 10
    assert sorted(allocate_counts(7, {"eng": 50, "hin": 50}).values()) == [3, 4]


def test_zero_percent_gets_nothing():
    assert allocate_counts(10, {"eng": 100, "hin": 0}) == {"eng": 10, "hin": 0}


def test_mix_tags_every_sentence_with_its_language():
    mixed = mix_languages({"eng": ["a1", "a2"], "hin": ["b1"]})
    assert sorted(mixed) == [("eng", "a1"), ("eng", "a2"), ("hin", "b1")]
