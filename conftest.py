"""Pytest configuration: ensure the repository root is importable.

Root-level helper modules (e.g. ``jev_sdk``) are imported by tests living in
``tests/``; this conftest guarantees the project root stays on ``sys.path``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
