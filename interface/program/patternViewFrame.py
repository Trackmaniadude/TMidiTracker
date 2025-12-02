"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

import logging
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import cast

from interface.program.patternView import PVLM, PatternView
from interface.theme import MatrixLabel
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from utils.constants import (
    CHANNEL_COUNT,
    CHANNEL_ORDER,
    CHANNEL_ORDER_INVERSE,
    DRUM_CHANNEL,
)

_logger = logging.getLogger(__name__)


@dataclass
class Target:
    channel: int
    row: int
    column: PVLM
    subcolumn: int


class RowList(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, padding="0 4")
        self.labels: dict[int, ttk.Label] = dict()
        self.rebuild()

        self.__highlight: int = -1

        program.p.getAttributeChangedEvent("currentPatternRow").connect(
            lambda key, old, new: setattr(self, "highlight", new)
        )

    @property
    def highlight(self) -> int:
        return self.__highlight

    @highlight.setter
    def highlight(self, highlight: int):
        if self.__highlight != highlight:
            if self.__highlight in self.labels:
                self.labels[self.__highlight].configure(
                    style=cast(str, MatrixLabel.DefaultEven)
                )
            if highlight in self.labels:
                self.labels[highlight].configure(style=cast(str, MatrixLabel.Highlight))
        self.__highlight = highlight

    def rebuild(self):
        for i, label in self.labels.items():
            del self.labels[i]
            label.destroy()
        for i in range(program.p.currentSong.patternLength):
            label = ttk.Label(self, text=i, justify="left")
            label.grid(row=i, column=0, sticky="nesw")
            self.labels[i] = label


class PatternViewFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.__content = sf.content
        self.row = 0

        self.target: Target = Target(2, 3, PVLM.VELOCITY, 1)

        self.views: list[PatternView] = list()

        RowList(self.__content).pack(side="left", fill="y")
        self.showChannels()

        program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
            self.matrixChangedEvent
        )

        program.p.getAttributeChangedEvent("currentMatrixRow").connect(
            self.onMatrixRowChange
        )

    def matrixChangedEvent(self, key: tuple[int, int], old: int | None, new: int):
        channel, row = key
        viewIndex = CHANNEL_ORDER_INVERSE[channel]
        view = self.views[viewIndex]
        view.pattern = program.p.currentSong.getPatternByLocation(channel, row)
        view.refreshLabels()

    def onMatrixRowChange(self, key, old, new):
        for i, view in enumerate(self.views):
            channel = CHANNEL_ORDER[i]
            view.pattern = program.p.currentSong.getPatternByLocation(
                channel, program.p.currentMatrixRow
            )
            view.refreshLabels()

    def setTarget(self, channel: int, row: int, column: PVLM, subcolumn: int):
        self.target = Target(channel, row, column, subcolumn)
        for view in self.views:
            view.refreshLabels()

    def showChannels(self):
        currentChannelsShown = len(self.views)
        newList = list()
        for i in range(CHANNEL_COUNT):
            if i < currentChannelsShown:
                if i < program.p.currentSong.visibleChannels:
                    newList.append(self.views[i])
                else:
                    self.views[i].destroy()
            else:
                if i < program.p.currentSong.visibleChannels:
                    view = PatternView(
                        self.__content,
                        self,
                        program.p.currentSong.getPatternById(CHANNEL_ORDER[i], 0),
                    )
                    view.pack(side="left", expand=True)
                    newList.append(view)
                else:
                    pass
        self.views = newList

    def setRow(self, row: int):
        self.row = row

        for channel, view in enumerate(self.views):
            view.setPattern(program.p.currentSong.getPatternByLocation(channel, row))
