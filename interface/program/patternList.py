"""
Shows all available patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from interface.theme import MatrixSelector
from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.quickRefresh import QuickRefresh
from utils.constants import CHANNEL_ORDER
from utils.event import Connection

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern

import logging
import tkinter as tk
from tkinter import ttk

from structures import program
from structures.globalEvents import SongReloaded, StructureChanged

_logger = logging.getLogger(__name__)


class PatternSelector(ttk.Label, QuickRefresh):
    def __init__(self, parent: tk.Misc, lst: PatternList, channel: int, pattern: int):
        super().__init__(parent, relief="sunken")

        self.list = lst

        self.channel = channel
        self.pattern = pattern

        self.connections: list[Connection] = list()

        # self.bind("<Button-1>", lambda *_: self.increment())
        # self.bind("<Button-3>", lambda *_: self.decrement())

        self.songConnections: list[Connection] = list()

        def setupSongEventListeners():
            for con in self.songConnections:
                con.disconnect()
            self.songConnections = list()

            program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
                lambda key, *_: self.queueRefresh(), self.songConnections
            )

        SongReloaded.connect(lambda *_: setupSongEventListeners(), self.connections)

        self.refresh()
        StructureChanged.connect(lambda *_: self.refresh(), self.connections)

    # def getPattern(self) -> int:
    #     return program.p.currentSong.getPatternNumberByLocation(self.channel, self.row)

    def refresh(self):
        self.resetRefreshFlag()
        if program.p.currentSong.patternIdExists(self.channel, self.pattern):
            count = program.p.currentSong.getPatternUsage(
                program.p.currentSong.getPatternById(self.channel, self.pattern)
            )
        else:
            count = -1
        style = (
            MatrixSelector.DefaultEven
            if self.channel % 2 == 1
            else MatrixSelector.DefaultOdd
        )
        self.config(
            text=count,
            style=cast(str, style),
            state="normal" if count >= 0 else "disabled",
        )

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()


class PatternList(ttk.Frame, QuickRefresh):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=400, height=200, borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.connections: list[Connection] = list()

        self.pack_propagate(False)

        self.__content = sf.content

        self.__labels: dict[tuple[int, int], ttk.Label] = dict()
        """(row, col) -> PatternSelector"""

        self.songConnections: list[Connection] = list()

        def setupSongEventListeners():
            for con in self.songConnections:
                con.disconnect()
            self.songConnections = list()

            program.p.currentSong.getAttributeChangedEvent("patternList").connect(
                lambda key, *_: self.queueRefresh(), self.songConnections
            )

        SongReloaded.connect(lambda *_: setupSongEventListeners(), self.connections)

        SongReloaded.connect(lambda *_: self.queueRefresh(), self.connections)
        self.refresh()

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    def refresh(self):
        self.resetRefreshFlag()
        rows = program.p.currentSong.visibleChannels + 1
        cols = (
            max(
                (
                    pattern
                    for channel, pattern in program.p.currentSong.patternList.keys()
                ),
                default=0,
            )
            + 1
        )

        # Clear old ones
        for p, label in self.__labels.items():
            row, col = p
            if row > rows or col > cols:
                label.destroy()

        # Labels
        for row in range(rows):
            if (row, -1) in self.__labels:
                continue
            label = ttk.Label(self.__content, text=CHANNEL_ORDER[row] + 1, width=3)
            label.grid(row=row + 1, column=0)
            self.__labels[row, -1] = label
        for col in range(cols):
            if (-1, col) in self.__labels:
                continue
            label = ttk.Label(self.__content, text=hex(col)[2:].upper(), width=3)
            label.grid(row=0, column=col + 1)
            self.__labels[-1, col] = label

        # Edits
        for row in range(rows):
            for col in range(cols):
                if (row, col) not in self.__labels:
                    label = PatternSelector(
                        self.__content, self, CHANNEL_ORDER[row], col
                    )
                    label.grid(row=row + 1, column=col + 1, sticky="nesw")
                    self.__labels[row, col] = label
                # t = self.__labels[row, col]
                # if isinstance(t, PatternSelector):
                #     t.refresh()
