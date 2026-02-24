"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

import logging
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Literal, cast

from interface.program.patternView import PVLM, PatternView
from interface.theme import MatrixSelector
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from structures.globalEvents import StructureChanged
from utils.constants import (
    CHANNEL_COUNT,
    CHANNEL_ORDER,
    CHANNEL_ORDER_INVERSE,
    DRUM_CHANNEL,
)
from utils.event import Connection

_logger = logging.getLogger(__name__)


@dataclass
class Target:
    channel: int
    row: int
    column: PVLM
    subcolumn: int


class RowList(ttk.Frame):
    """Vertical list of row numbers on the left side."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.labels: dict[int, ttk.Label] = dict()
        self.rebuild()

        self.__highlight: int = -1

        self.connections: list[Connection] = list()

        program.p.getAttributeChangedEvent("currentPatternRow").connect(
            lambda key, old, new: setattr(self, "highlight", new), self.connections
        )

        ttk.Frame(self, width=0, height=28).grid(row=0, column=0)  # Spacer

        StructureChanged.connect(
            lambda changes: self.rebuild() if "visibleChannels" in changes else None,
            self.connections,
        )

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    @property
    def highlight(self) -> int:
        return self.__highlight

    @highlight.setter
    def highlight(self, highlight: int):
        if self.__highlight != highlight:
            if self.__highlight in self.labels:
                self.labels[self.__highlight].configure(
                    style=cast(str, MatrixSelector.DefaultEven)
                )
            if highlight in self.labels:
                self.labels[highlight].configure(
                    style=cast(str, MatrixSelector.Highlight)
                )
        self.__highlight = highlight

    def rebuild(self):
        for i, label in self.labels.copy().items():
            del self.labels[i]
            label.destroy()
        for i in range(program.p.currentSong.patternLength):
            label = ttk.Label(self, text=i, justify="left")
            label.grid(row=i + 1, column=0, sticky="nesw")
            self.labels[i] = label


class PatternViewFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.connections: list[Connection] = list()

        self.__content = sf.content
        self.row = 0

        self.target: Target = Target(2, 3, PVLM.VELOCITY, 1)

        self.views: list[PatternView] = list()

        RowList(self.__content).pack(side="left", fill="y")
        self.showChannels()

        program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
            lambda *a: self.after(0, self.matrixChangedEvent, *a), self.connections
        )

        program.p.getAttributeChangedEvent("currentMatrixRow").connect(
            lambda *a: self.after(0, self.onMatrixRowChange, *a), self.connections
        )

        StructureChanged.connect(lambda *_: self.showChannels(), self.connections)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    def matrixChangedEvent(self, key: tuple[int, int], old: int | None, new: int):
        channel, row = key
        viewIndex = CHANNEL_ORDER_INVERSE[channel]
        if viewIndex >= len(self.views):
            return
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

    def setTarget(
        self,
        channel: int | None = None,
        row: int | None = None,
        column: PVLM | None = None,
        subcolumn: int | None = None,
        *,
        focus: bool = False
    ):
        channel = channel if channel is not None else self.target.channel
        row = row if row is not None else self.target.row
        column = column if column is not None else self.target.column
        subcolumn = subcolumn if subcolumn is not None else self.target.subcolumn

        self.target = Target(channel, row, column, subcolumn)

        if focus == True:
            self.views[CHANNEL_ORDER_INVERSE[channel]].labelLookup[
                row, column, subcolumn
            ].focus()
        for view in self.views:
            view.refreshLabels()

    def stepTarget(
        self,
        step: int,
        stepPattern: bool = True,
        *,
        direction: Literal["Up", "Down", "Left", "Right"] = "Down",
        focus: bool = False
    ):
        if direction == "Up":
            newPatternRow = self.target.row - step
            if newPatternRow < 0:
                if stepPattern == True:
                    newPatternRow += program.p.currentSong.patternLength
                    if program.p.currentMatrixRow > 0:
                        program.p.currentMatrixRow -= 1
                    else:
                        newPatternRow = 0
                else:
                    newPatternRow = 0
            self.setTarget(row=newPatternRow, focus=focus)

        elif direction == "Down":
            newPatternRow = self.target.row + step
            if newPatternRow >= program.p.currentSong.patternLength:
                if stepPattern == True:
                    newPatternRow -= program.p.currentSong.patternLength
                    if (
                        program.p.currentMatrixRow
                        < program.p.currentSong.visibleMatrixRows - 1
                    ):
                        program.p.currentMatrixRow += 1
                    else:
                        newPatternRow = program.p.currentSong.patternLength - 1
                else:
                    newPatternRow = program.p.currentSong.patternLength - 1
            self.setTarget(row=newPatternRow, focus=focus)

        elif direction == "Left":  # TODO: variable step
            currentChannel = CHANNEL_ORDER_INVERSE[self.target.channel]
            currentChannelObj = program.p.currentSong.channels[currentChannel]

            if self.target.column == PVLM.NOTE:
                if self.target.subcolumn > 0:
                    self.setTarget(
                        column=PVLM.VELOCITY, subcolumn=self.target.subcolumn - 1
                    )
                else:  # Move to LEFT channel
                    if currentChannel > 0:
                        self.setTarget(
                            channel=CHANNEL_ORDER[currentChannel - 1],
                            column=PVLM.EFFECT,
                            subcolumn=currentChannelObj.effectColumns - 1,
                        )
            elif self.target.column == PVLM.VELOCITY:
                self.setTarget(column=PVLM.NOTE)
            elif self.target.column == PVLM.EFFECT:
                if self.target.subcolumn > 0:
                    self.setTarget(subcolumn=self.target.subcolumn - 1)
                else:
                    self.setTarget(
                        column=PVLM.VELOCITY,
                        subcolumn=currentChannelObj.noteColumns - 1,
                    )

        elif direction == "Right":  # TODO: variable step
            currentChannel = CHANNEL_ORDER_INVERSE[self.target.channel]
            currentChannelObj = program.p.currentSong.channels[currentChannel]

            if self.target.column == PVLM.NOTE:
                self.setTarget(column=PVLM.VELOCITY)
            elif self.target.column == PVLM.VELOCITY:
                if (
                    self.target.subcolumn >= currentChannelObj.noteColumns - 1
                ):  # Move to EFFECT column
                    self.setTarget(column=PVLM.EFFECT, subcolumn=0)
                else:
                    self.setTarget(
                        column=PVLM.NOTE, subcolumn=self.target.subcolumn + 1
                    )
            elif self.target.column == PVLM.EFFECT:  # Move to RIGHT channel
                if currentChannel < program.p.currentSong.visibleChannels:
                    self.setTarget(
                        channel=CHANNEL_ORDER[currentChannel + 1],
                        column=PVLM.NOTE,
                        subcolumn=0,
                    )

    def showChannels(self):
        currentChannelsShown = len(self.views)
        newList = list()
        for i in range(CHANNEL_COUNT):
            if i < currentChannelsShown:
                if i <= program.p.currentSong.visibleChannels:
                    newList.append(self.views[i])
                else:
                    self.views[i].destroy()
            else:
                if i <= program.p.currentSong.visibleChannels:
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
