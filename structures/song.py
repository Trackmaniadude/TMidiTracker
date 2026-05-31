"""
Song object.
Contains song information such as speed, pattern length, and author.
Also contains a grid of pattern references, as well as a pattern table.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from structures import program
from structures.channel import Channel
from structures.pattern import Pattern
from utils.constants import CHANNEL_COUNT, CHANNEL_ORDER, CHANNEL_ORDER_INVERSE
from utils.misc import collapse2dDict, intKey2dFromJson, intKey2dToJson
from utils.reactiveClass import ReactiveClass, ReactiveContainerJSONEncoder

_logger = logging.getLogger(__name__)


@dataclass
class SongMetadata:
    title: str = ""
    author: str = ""
    genre: str = ""
    notes: str = ""


class Song(ReactiveClass):
    """
    Contains data pertaining to the song itself.
    (Anything in here makes sense to save to file.)
    """

    def __init__(self) -> None:
        super().__init__()

        self.metadata = SongMetadata()

        self.visibleChannels: int = 4
        self.visibleMatrixRows: int = 4

        self.patternLength: int = 16
        self.majorSubdiv: int = 16
        self.minorSubdiv: int = 4

        self.clock: float = 60
        self.groove: list[int] = [4]
        self.syncGrooveToPattern: bool = True
        """Reset groove pattern at beginning of pattern"""
        self.loopCount: int = 2

        self.channels: list[Channel] = [Channel(self, i) for i in range(CHANNEL_COUNT)]
        self.patternList: dict[tuple[int, int], Pattern] = dict()
        """Pattern lookup. (channel number, pattern number) -> Pattern"""
        self.patternMatrix: dict[tuple[int, int], int] = dict()
        """Locational pattern reference. (channel (x), row (y)) -> pattern number"""

        # Pre-pop default patterns
        for row in range(self.visibleMatrixRows):
            for channel in range(CHANNEL_COUNT):
                self.patternMatrix[channel, row] = 0

        # Other information
        self.highlightedMatrixItems: set[tuple[int, int]] = set()

        self.Changed.connect(
            lambda name, key, old, new: setattr(program.p, "projectModified", True)
        )

        self.setupContainerListen()

    ### File Management

    def toFile(self, path: Path):
        with open(path, "w") as fp:
            json.dump(
                self.toDict(),
                fp,
                cls=ReactiveContainerJSONEncoder,
                indent=None,
                separators=(",", ":"),
            )

    def toJson(self) -> str:
        return json.dumps(
            self.toDict(),
            cls=ReactiveContainerJSONEncoder,
            indent=None,
            separators=(",", ":"),
        )

    def toDict(self) -> dict[str, Any]:

        def getPatternList():
            """Convert the pattern list to a format more sensibly stored in JSON"""
            # return collapse2dDict({k: -1 for k, v in self.patternList.items()}, -1)
            out: dict[int, list] = {
                CHANNEL_ORDER[channel]: [
                    None
                    for _ in range(self.getMaxPatternId(CHANNEL_ORDER[channel]) + 1)
                ]
                for channel in range(self.visibleChannels + 1)
            }

            for pos, pattern in self.patternList.items():
                channel, id = pos
                if channel in out:
                    out[channel][id] = pattern.toDict()

            return out

        def getPatternMatrix():
            """Convert the pattern matrix to a format more sensibly stored in JSON"""
            # return collapse2dDict(self.patternMatrix, -1)
            out = {
                CHANNEL_ORDER[channel]: [-1 for _ in range(self.visibleMatrixRows)]
                for channel in range(self.visibleChannels + 1)
            }
            # Note: while -1 is not allowed when running the software, it should not actually break things.
            # It also probably shouldn't ever actually show up since it's a dense matrix.
            # TODO: famous last words

            for pos, num in self.patternMatrix.items():
                channel, row = pos
                if channel not in out:
                    continue
                if row >= self.visibleMatrixRows:
                    continue
                out[channel][row] = num

            return out

        return {
            "format": 0,
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author,
                "genre": self.metadata.genre,
                "notes": self.metadata.notes,
            },
            "structure": {
                "visibleChannels": self.visibleChannels,
                "visibleMatrixRows": self.visibleMatrixRows,
                "patternLength": self.patternLength,
                "majorSubdiv": self.majorSubdiv,
                "minorSubdiv": self.minorSubdiv,
            },
            "timing": {
                "clock": self.clock,
                "groove": self.groove,
                "syncGrooveToPattern": self.syncGrooveToPattern,
            },
            "songData": {
                "channelData": [
                    channel.toDict()
                    for channel in self.channels
                    if CHANNEL_ORDER_INVERSE[channel.channel] <= self.visibleChannels
                ],
                "patterns": getPatternList(),
                "patternMatrix": getPatternMatrix(),
            },
            "interfaceData": {
                "highlightedMatrixItems": [
                    intKey2dToJson(v) for v in self.highlightedMatrixItems
                ]
            },
        }

    @classmethod
    def fromFile(cls, path: Path) -> Song:
        with open(path) as fp:
            d = json.load(fp)
        return cls.fromDict(d)

    @classmethod
    def fromDict(cls, dct: dict[str, Any]) -> Song:
        s = Song()

        s.metadata.title = dct["metadata"]["title"]
        s.metadata.author = dct["metadata"]["author"]
        s.metadata.genre = dct["metadata"]["genre"]
        s.metadata.notes = dct["metadata"]["notes"]

        s.visibleChannels = dct["structure"]["visibleChannels"]
        s.visibleMatrixRows = dct["structure"]["visibleMatrixRows"]
        s.patternLength = dct["structure"]["patternLength"]
        s.majorSubdiv = dct["structure"]["majorSubdiv"]
        s.minorSubdiv = dct["structure"]["minorSubdiv"]

        s.clock = dct["timing"]["clock"]
        s.groove = dct["timing"]["groove"]
        s.syncGrooveToPattern = dct["timing"]["syncGrooveToPattern"]

        for channelData in dct["songData"]["channelData"]:
            channel = s.channels[channelData["channel"]]
            channel.noteColumns = channelData["noteColumns"]
            channel.effectColumns = channelData["effectColumns"]

        for channel, patternData in dct["songData"]["patterns"].items():
            channel = int(channel)  # dict int key becomes str in json
            for id, data in enumerate(patternData):
                if data is None:
                    continue
                s.patternList[channel, id] = Pattern.fromDict(
                    s, s.channels[channel], data
                )
                # TODO: id like this to use internal mechanisms rather than raw
                # patternObj = s.getPatternByLocation(channel, row)
                # patternObj.updateFromDict(data)

        for channel, channelData in dct["songData"]["patternMatrix"].items():
            channel = int(channel)
            for row, id in enumerate(channelData):
                s.setPatternNumber(channel, row, id)

        for highlight in dct["interfaceData"]["highlightedMatrixItems"]:
            s.highlightedMatrixItems.add(intKey2dFromJson(highlight))

        s.setupContainerListen()
        return s

    ### Pattern Management

    def getPatternID(self, pattern: Pattern) -> tuple[int, int]:
        """Get the channel and pattern number for a given pattern."""
        for key, testPattern in self.patternList.items():
            if testPattern is pattern:
                return key
        raise Exception

    def getPatternUsage(self, pattern: Pattern) -> int:
        count = 0
        for key, patternNumber in self.patternMatrix.items():
            channel, row = key
            testPattern = self.patternList.get((channel, patternNumber))
            if testPattern is pattern:
                count += 1
        return count

    def getPatternIdByLocation(self, channel: int, row: int) -> int:
        """
        Get the pattern number at a location in the pattern matrix. Defaults 0 if not available.
        (Attempting to get a nonexistent pattern (0) will create it.)
        """
        return self.patternMatrix.get((channel, row), 0)

    def setPatternNumber(self, channel: int, row: int, value: int):
        self.patternMatrix[channel, row] = value

    def patternIdExists(self, channel: int, pattern: int) -> bool:
        return (channel, pattern) in self.patternList

    def getPatternById(self, channel: int, pattern: int) -> Pattern:
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
        return self.getPatternById(channel, self.patternMatrix[channel, row])

    def getFreePatternId(self, channel: int) -> int:
        """Get the id of the lowest empty pattern."""
        # TODO: check if pattern is empty, rather than just not existing
        id = 0
        while self.patternIdExists(channel, id):
            id += 1
        return id

    def getFreePattern(self, channel: int) -> Pattern:
        """Get the lowest empty pattern."""
        return self.getPatternById(channel, self.getFreePatternId(channel))

    def getMaxPatternId(self, channel: int) -> int:
        """Get highest used pattern id for a channel. Returns -1 if there are no patterns."""
        # TODO: check if pattern is empty, rather than just not existing
        return max(
            (pt for ch, pt in self.patternList.keys() if ch == channel), default=-1
        )

    ### Matrix Management

    def deleteMatrixRow(self, row: int):
        """Clear matrix entries for the given row. Does not move rows to fill the space."""
        # TODO: good way to know which channels exist in the row?
        for channel in range(0, self.visibleChannels):
            if (channel, row) in self.patternMatrix:
                del self.patternMatrix[channel, row]

    def swapMatrixRows(self, row0, row1):
        """Swap two matrix rows."""
        # TODO: more pythonic?
        for channel in range(program.p.currentSong.visibleChannels):
            i0 = self.getPatternIdByLocation(channel, row0)
            i1 = self.getPatternIdByLocation(channel, row0)
            self.setPatternNumber(channel, row0, i1)
            self.setPatternNumber(channel, row1, i0)

    def shiftMatrixRows(self, row0: int | None, row1: int | None, newRow0: int):
        """Move rows row0-row1 (inclusive) to start at newRow0. Overwrites old rows and leaves blank space."""
        source = self.patternMatrix.copy()
        if row0 is None:
            row0 = 0
        if row1 is None:
            row1 = program.p.currentSong.visibleMatrixRows

        # Remove old rows
        for offset in range((row1 - row0) + 1):
            row = row0 + offset
            self.deleteMatrixRow(row)

        # Replace new rows
        for offset in range((row1 - row0) + 1):
            row = row0 + offset
            newRow = newRow0 + offset
            for channel in range(0, CHANNEL_COUNT):
                if (channel, row) in source:
                    self.patternMatrix[channel, newRow] = source[channel, row]


if __name__ == "__main__":
    import difflib

    from utils.reactiveClass import ReactiveContainer

    TEST_FILE = "test{}.json"
    t11 = Song()  # blank
    t21 = Song()  # edited

    # Metadata

    t21.metadata.title = "generated test song"
    t21.metadata.author = "tractormaniadude"
    t21.metadata.genre = "who knows"
    t21.metadata.notes = "a rather large string\n" * 10

    # Structure

    t21.visibleChannels = 5
    t21.visibleMatrixRows = 12
    t21.patternLength = 24
    t21.majorSubdiv = 12
    t21.minorSubdiv = 3

    # Timing

    t21.clock = 50
    t21.groove = [3, 5]
    t21.syncGrooveToPattern = False

    # Channels

    t21.channels[9].noteColumns = 4
    t21.channels[2].effectColumns = 4

    # Patterns

    t21.getPatternById(0, 0).setEffect(3, 0, (16, 24))

    t21.getPatternById(2, 10).setNote(2, 0, 64)

    t21.getPatternById(9, 1).setNote(2, 0, 64)
    t21.getPatternById(9, 2).setNote(3, 0, 64)
    t21.getPatternById(9, 3).setNote(4, 0, 64)
    t21.getPatternById(9, 4).setNote(5, 0, 64)

    t21.getPatternById(3, 1)
    t21.getPatternById(3, 2).setVelocity(0, 0, 0)
    t21.getPatternById(3, 2).setVelocity(1, 0, 0)
    t21.getPatternById(3, 2).setVelocity(3, 3, 0)
    t21.getPatternById(3, 3)

    # Pattern Matrix

    t21.setPatternNumber(0, 0, 5)
    t21.setPatternNumber(0, 1, 5)
    t21.setPatternNumber(0, 2, 5)

    t21.setPatternNumber(2, 3, 2)

    t21.setPatternNumber(3, 3, 4)

    t21.setPatternNumber(9, 0, 1)
    t21.setPatternNumber(9, 1, 2)
    t21.setPatternNumber(9, 2, 3)
    t21.setPatternNumber(9, 3, 4)

    # Other

    t21.highlightedMatrixItems.add((1, 1))
    t21.highlightedMatrixItems.add((3, 3))
    t21.highlightedMatrixItems.add((2, 4))
    t21.highlightedMatrixItems.add((4, 2))

    t21.setupContainerListen()

    # print(t1.toJSON())
    # print(t1.jsonEncode())

    # t11.toFile(TEST_FILE.format(1))
    # t12 = Song.fromFile(TEST_FILE.format(1))
    # t21.toFile(TEST_FILE.format(2))
    # t22 = Song.fromFile(TEST_FILE.format(2))
    # t22.toFile(TEST_FILE.format(3))

    def test(name: str, a: Song, b: Song):
        def eq[T](a: T, b: T) -> bool:
            if isinstance(a, ReactiveContainer) and isinstance(b, ReactiveContainer):
                return a._container == b._container
            return a == b

        def p(v: Any) -> str:
            if isinstance(v, ReactiveContainer):
                # Get up to four values
                vals = list()
                for i, item in enumerate(v._container):
                    if i >= 4:
                        vals.append("...")
                        break
                    try:
                        vals.append(f"{item}: {v._container[item]}")
                    except:
                        vals.append(str(item))
                return f"{v.__class__.__name__}[{", ".join(vals)}]"
            return str(v)

        # print()
        # print(name)
        # for k in a.__dict__.keys():
        #     aVal = getattr(a, k)
        #     bVal = getattr(b, k)
        #     print(f"{k}: {eq(aVal, bVal)} ({p(aVal)} -> {p(bVal)})")

        af = a.toJson().split("\n")
        bf = b.toJson().split("\n")
        d = difflib.HtmlDiff().make_file(af, bf, context=True)

        with open(f"test{name}.html", "w") as fp:
            fp.write(d)

    # test("Default", t11, t12)
    # test("Modified", t21, t22)

    # TODO: this test needs actual changes to be made cause its just default rn

    # t1r = t1.jsonEncode()
    # t2r = t2.jsonEncode()

    # print(t1r == t2r)

    # print(t)
    # print()
    # print(t.toJSON())
    # print(t.jsonEncode())
    # print(t1.jsonEncode())
    # print(t2.jsonEncode())
