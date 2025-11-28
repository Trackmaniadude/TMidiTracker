"""
Song object.
Contains song information such as speed, pattern length, and author.
Also contains a grid of pattern references, as well as a pattern table.
"""

from structures import program
from structures.channel import Channel
from structures.pattern import Pattern
from utils.constants import CHANNEL_COUNT
from utils.reactiveClass import ReactiveClass


class Song(ReactiveClass):
    """
    Contains data pertaining to the song itself.
    (Anything in here makes sense to save to file.)
    """

    def __init__(self) -> None:
        super().__init__()

        self.displayChannelCount: int = 4
        self.patternLength: int = 32
        self.majorSubdiv: int = 16
        self.minorSubdiv: int = 4
        self.clock: float = 60
        self.groove: list[int] = [4]

        self.channels: list[Channel] = [Channel(self, i) for i in range(CHANNEL_COUNT)]
        self.patterns: dict[tuple[int, int], Pattern] = dict()
        """Pattern lookup. (channel number, pattern number) -> Pattern"""
        self.patternTable: dict[tuple[int, int], int] = dict()
        """Locational pattern reference. (channel (x), row (y)) -> pattern number"""

    def getPattern(self, channel: int, pattern: int) -> Pattern:
        """Get pattern by its number for a given channel. Makes a new one if it does not exist."""
        if (channel, pattern) not in self.patterns:
            self.patterns[channel, pattern] = Pattern(self, self.channels[channel])
        return self.patterns[channel, pattern]

    def getPatternByLocation(self, channel: int, row: int) -> Pattern:
        """Get pattern by its value in the pattern table. Inits to pattern 0 if not available."""
        if (channel, row) not in self.patternTable:
            self.patternTable[channel, row] = 0
        return self.getPattern(channel, self.patternTable[channel, row])
