"""
Contains channel information and channel playback state.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from structures.song import Song


class Channel:
    def __init__(self, song: Song, channel: int) -> None:
        self.song = song
        self.channel = channel

        self.noteColumns = 1
        self.effectColumns = 1
