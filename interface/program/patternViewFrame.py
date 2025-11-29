"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

import logging
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from interface.program.patternView import PVLM, PatternView
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


class PatternViewFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.__content = sf.content
        self.row = 0

        self.target: Target = Target(2, 3, PVLM.VELOCITY, 1)

        self.views: list[PatternView] = list()

        self.showChannels()

        def matrixChangedEvent(key: tuple[int, int], old: int | None, new: int):
            channel, row = key
            viewIndex = CHANNEL_ORDER_INVERSE[channel]
            view = self.views[viewIndex]
            view.pattern = program.p.currentSong.getPatternByLocation(channel, row)
            view.refreshLabels()

        program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
            matrixChangedEvent
        )

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
                        program.p.currentSong.getPattern(CHANNEL_ORDER[i], 0),
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
