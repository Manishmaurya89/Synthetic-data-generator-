import pytest

import main


def test_parse_pages():
    assert main.parse_pages("3") == 3

    for bad in ("0", "-1", "two"):
        with pytest.raises(ValueError):
            main.parse_pages(bad)


def test_parse_language():
    assert main.parse_language(" HIN ") == "hin"

    with pytest.raises(ValueError):
        main.parse_language("fra")
