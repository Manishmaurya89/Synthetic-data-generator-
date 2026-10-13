from scripts import detect_language, has_foreign_letters, script_share


def test_detect_language():
    assert detect_language("Physics") == "eng"
    assert detect_language("भौतिकी") == "hin"
    assert detect_language("طبیعیات") == "urd"
    assert detect_language("ভৌতবিজ্ঞান") == "ben"
    assert detect_language("123") == "eng"


def test_script_share():
    assert script_share("बल गति", "hin") == 1.0
    assert script_share("abc", "hin") == 0.0
    assert script_share("", "hin") == 0.0


def test_has_foreign_letters():
    assert has_foreign_letters("कोई力", "hin")
    assert not has_foreign_letters("नियम (Newton)", "hin")
