from typing import Literal

note = tuple[int, int] | Literal["stop"]
"""Note message, either a note velocity pair, or stop."""
effect = tuple[int, ...]
"""Tracker effect, may operate internal effects or map to midi messages."""
