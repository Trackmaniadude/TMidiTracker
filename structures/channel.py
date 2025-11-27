"""
Contains channel information and channel playback state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from structures.song import Song

from structures import program
from utils.reactiveClass import ReactiveClass


class Channel(ReactiveClass):
    def __init__(self, song: Song, channel: int) -> None:
        super().__init__()

        self.song = song
        self.channel = channel

        self.noteColumns = 2
        self.effectColumns = 1
