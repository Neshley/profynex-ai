"""Configuration for running tests."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# pytest configuration
pytestmark = []

# Async test configuration
test_asyncio_mode = "auto"
