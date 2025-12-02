"""
View/editor for the pattern matrix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern

import logging
import tkinter as tk
from tkinter import ttk

from interface.theme import MatrixLabel
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from utils.constants import CHANNEL_ORDER

_logger = logging.getLogger(__name__)


class PatternSelector(ttk.Label):
    def __init__(self, parent: tk.Misc, matrix: PatternMatrix, channel: int, row: int):
        super().__init__(parent, relief="sunken")

        self.matrix = matrix

        self.channel = channel
        self.row = row

        self.__style: str = ""
        self.__text: str = ""

        self.bind("<Button-1>", lambda *_: (self.increment(), self.setCurrentRow()))
        self.bind("<Button-2>", lambda *_: (self.copyAbove(), self.setCurrentRow()))
        self.bind("<Button-3>", lambda *_: (self.decrement(), self.setCurrentRow()))

        program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
            lambda key, *_: self.refresh()
        )
        program.p.currentSong.getAttributeChangedEvent("highlightedMatrixRows").connect(
            lambda key, *_: self.refresh()
        )
        program.p.getAttributeChangedEvent("currentMatrixRow").connect(
            lambda key, *_: self.refresh()
        )
        self.refresh()

    def setCurrentRow(self):
        program.p.currentMatrixRow = self.row

    def getPattern(self) -> int:
        return program.p.currentSong.getPatternIdByLocation(self.channel, self.row)

    def setPattern(self, pattern: int):
        program.p.currentSong.setPatternNumber(self.channel, self.row, pattern)

    def increment(self):
        self.setPattern(self.getPattern() + 1)

    def decrement(self):
        self.setPattern(max(0, self.getPattern() - 1))

    def beginSet(self):
        pass

    def endSet(self):
        pass

    def copyAbove(self):
        if self.row == 0:
            return
        p = program.p.currentSong.getPatternIdByLocation(self.channel, self.row - 1)
        self.setPattern(p)

    def refresh(self):
        if self.row == program.p.currentMatrixRow:
            style = MatrixLabel.Target
        elif self.row in program.p.currentSong.highlightedMatrixRows:
            style = MatrixLabel.Highlight
        else:
            style = (
                MatrixLabel.DefaultEven
                if self.channel % 2 == 1
                else MatrixLabel.DefaultOdd
            )

        self.text = str(self.getPattern())
        self.style = cast(str, style)

    def destroy(self) -> None:
        return super().destroy()

    @property
    def style(self) -> str:
        return self.__style

    @style.setter
    def style(self, newStyle: str):
        if newStyle != self.__style:
            self.__style = newStyle
            self.config(style=self.style)

    @property
    def text(self) -> str:
        return self.__text

    @text.setter
    def text(self, newText: str):
        if newText != self.__text:
            self.__text = newText
            self.config(text=self.__text)


class PatternMatrix(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=300, height=200)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.pack_propagate(False)

        self.__content = sf.content

        self.__labels: dict[tuple[int, int], ttk.Label] = dict()
        """(row, col) -> PatternSelector"""

        self.refresh()

    def setMatrixRow(self, row: int):
        program.p.currentMatrixRow = row

    def toggleRowHighlight(self, row: int):
        if row in program.p.currentSong.highlightedMatrixRows:
            program.p.currentSong.highlightedMatrixRows.remove(row)
        else:
            program.p.currentSong.highlightedMatrixRows.add(row)

    def refresh(self):
        rows = program.p.currentSong.visibleMatrixRows
        cols = program.p.currentSong.visibleChannels

        # Clear old ones
        for p, label in self.__labels.items():
            row, col = p
            if row > rows or col > cols:
                label.destroy()

        # Labels
        for row in range(rows):
            if (row, -1) in self.__labels:
                continue
            label = ttk.Label(self.__content, text=hex(row)[2:].upper(), width=3)
            label.grid(row=row + 1, column=0)
            self.__labels[row, -1] = label

            def _(row):
                label.bind("<Button-1>", lambda *_: self.setMatrixRow(row))
                label.bind("<Button-3>", lambda *_: self.toggleRowHighlight(row))

            _(row)
        for col in range(cols):
            if (-1, col) in self.__labels:
                continue
            label = ttk.Label(self.__content, text=CHANNEL_ORDER[col] + 1, width=3)
            label.grid(row=0, column=col + 1)
            self.__labels[-1, col] = label

        # Edits
        for row in range(rows):
            for col in range(cols):
                if (row, col) in self.__labels:
                    continue
                label = PatternSelector(self.__content, self, CHANNEL_ORDER[col], row)
                label.grid(row=row + 1, column=col + 1, sticky="nesw")
                self.__labels[row, col] = label
