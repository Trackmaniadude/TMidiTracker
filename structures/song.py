"""
Song object.
Contains song information such as speed, pattern length, and author.
Also contains a grid of pattern references, as well as a pattern table.
"""

from structures.channel import Channel
from structures.pattern import Pattern

CHANNEL_COUNT = 16  # TODO: move to a permanent location


class Song:
    def __init__(self) -> None:
        self.patternLength = 64
        self.majorSubdiv = 16
        self.minorSubdiv = 4

        self.channels: list[Channel] = [Channel(self, i) for i in range(CHANNEL_COUNT)]
        self.patterns: dict[int, Pattern] = dict()
        """Pattern lookup."""
        self.patternTable: dict[tuple[int, int], int] = dict()
        """Locational pattern reference."""
