"""
Pattern object. Contains message data.
"""

from utils.types import *


class Pattern:
    def __init__(self) -> None:
        self.notes: dict[tuple[int, int], note] = dict()
        """Play note/stop note commands. (Does not directly map to midi)"""
        self.effects: dict[tuple[int, int], effect] = dict()
        """Tracker effects, like vibrato and playback control. Some effects may map to midi messages."""
