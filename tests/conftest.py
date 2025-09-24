import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def run_from_root(monkeypatch):
    root = Path(__file__).parent.parent
    monkeypatch.chdir(root)
