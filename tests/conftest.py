import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def output_dir(tmp_path, monkeypatch):
    import main
    import output

    monkeypatch.setattr(output, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(main, "OUTPUT_DIR", str(tmp_path))
    return tmp_path
