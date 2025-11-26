"""
Pattern object. Contains message data.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel

from utils.types import *


class Pattern:
    def __init__(self, song: Song, channel: Channel) -> None:
        self.song = song
        self.channel = channel

        self.notes: dict[tuple[int, int], note] = dict()
        """Play note/stop note commands. (Does not directly map to midi)"""
        self.effects: dict[tuple[int, int], effect] = dict()
        """Tracker effects, like vibrato and playback control. Some effects may map to midi messages."""
