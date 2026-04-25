import sys
from pathlib import Path

import pytest

# Add repo root to sys.path so `from scripts.vision_parser import ...` works
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require live data and external services)",
    )
