"""
Song object.
Contains song information such as speed, pattern length, and author.
Also contains a grid of pattern references, as well as a pattern table.
"""

import logging

from structures import program
from structures.channel import Channel
from structures.pattern import Pattern
from utils.constants import CHANNEL_COUNT
from utils.reactiveClass import ReactiveClass

_logger = logging.getLogger(__name__)


class Song(ReactiveClass):
    """
    Contains data pertaining to the song itself.
    (Anything in here makes sense to save to file.)
    """

    def __init__(self) -> None:
        super().__init__()

        self.visibleChannels: int = 5
        self.visibleMatrixRows: int = 12

        self.patternLength: int = 32
        self.majorSubdiv: int = 16
        self.minorSubdiv: int = 4
        self.clock: float = 60
        self.groove: list[int] = [4]

        self.channels: list[Channel] = [Channel(self, i) for i in range(CHANNEL_COUNT)]
        self.patternList: dict[tuple[int, int], Pattern] = dict()
        """Pattern lookup. (channel number, pattern number) -> Pattern"""
        self.patternMatrix: dict[tuple[int, int], int] = dict()
        """Locational pattern reference. (channel (x), row (y)) -> pattern number"""

        self.highlightedMatrixRows: set[int] = set([3, 5])

        self.setupContainerListen()

    def getPatternNumberByLocation(self, channel: int, row: int) -> int:
        """
        Get the pattern number at a location in the pattern matrix. Defaults 0 if not available.
        (Attempting to get a nonexistent pattern (0) will create it.)
        """
        return self.patternMatrix.get((channel, row), 0)

    def setPatternNumber(self, channel: int, row: int, value: int):
        self.patternMatrix[channel, row] = value

    def getPattern(self, channel: int, pattern: int) -> Pattern:
        """Get pattern by its number for a given channel. Makes a new one if it does not exist."""
        if (channel, pattern) not in self.patternList:
            _logger.debug(
                f"Created new pattern for channel={channel} with id {pattern}"
            )
            self.patternList[channel, pattern] = Pattern(self, self.channels[channel])
        return self.patternList[channel, pattern]

    def getPatternByLocation(self, channel: int, row: int) -> Pattern:
        """Get pattern by its value in the pattern table. Inits to pattern 0 if not available."""
        if (channel, row) not in self.patternMatrix:
            self.patternMatrix[channel, row] = 0
        return self.getPattern(channel, self.patternMatrix[channel, row])

    # @property
    # def patternMatrixLength(self) -> int:
    #     return max((y for x, y in self.patternMatrix.keys()), default=0)
