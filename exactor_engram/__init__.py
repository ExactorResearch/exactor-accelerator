"""
Exactor Engram Memory - deterministic associative memory of objects.

Evolves Exactor Accelerator (exactor-jev) from a boolean decision classifier into a
neuro-symbolic associative recall system: photos, image segments and data fragments are
projected onto B^64, consolidated by a multimodal Oracle (System 2), persisted in a SQLite
WAL ledger, and addressed afterwards by minimized boolean engrams (System 1).
"""

__version__ = "0.1.0"

from .config import EngramConfig, get_config  # noqa: E402
from .memory import EngramMemory  # noqa: E402

__all__ = ["EngramConfig", "EngramMemory", "get_config", "__version__"]
