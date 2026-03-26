"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

from __future__ import annotations

import logging
import tkinter as tk
from dataclasses import dataclass
from itertools import chain
from tkinter import ttk
from typing import Literal, cast

import utils.tk as tkutil
from interface.program.patternView import PatternView
from interface.program.patternViewUtils import PVLM, PatternViewClipboardChannel, Target
from interface.theme import MatrixSelector
from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.validatedEntryPrebuilts import Prebuilts
from structures import program
from structures.globalEvents import Copy, Paste, SongReloaded, StructureChanged
from utils.constants import (
    CHANNEL_COUNT,
    CHANNEL_ORDER,
    CHANNEL_ORDER_INVERSE,
    DRUM_CHANNEL,
)
from utils.event import Connection
from utils.misc import flatten, minmax

_logger = logging.getLogger(__name__)


class InfoBar(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)

        ttk.Label(self, text="OCT: ").pack(side="left")
        octave = Prebuilts.Spinbox(
            self, default=program.p.currentOctave, range=(1, 10), increment=1, round=1
        )
        octave.entry.config(width=3)
        octave.entry.pack(side="left")

        ttk.Label(self, text="STEP: ").pack(side="left")
        step = Prebuilts.Spinbox(self, default=1, range=(1, 8), increment=1, round=1)
        step.entry.config(width=3)
        step.entry.pack(side="left")

        time = ttk.Label(self)
        time.pack(side="left")

        # Behavior
        octave.Changed.connect(
            lambda *_: setattr(program.p, "currentOctave", int(octave.value))
        )
        step.Changed.connect(lambda *_: setattr(program.p, "stepSize", int(step.value)))

        def timeStamp():
            matrixRow = program.p.currentMatrixRow
            patternRow = program.p.currentPatternRow
            text = f"{matrixRow}:{patternRow}"
            time.config(text=text)

        program.p.getAttributeChangedEvent("currentPatternRow").connect(
            lambda *_: timeStamp()
        )
        timeStamp()


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
    """Main song editing view; contains patternview objects."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(side="top", fill="both", expand=True)

        self.connections: list[Connection] = list()

        self.__content = sf.content
        self.row = 0

        self.target: Target = Target(2, 3, PVLM.VELOCITY, 1)
        self.secondaryTarget: Target | None = None

        self.views: list[PatternView] = list()

        self.clipboard: list[PatternViewClipboardChannel] = list()

        RowList(self.__content).pack(side="left", fill="y")
        self.showChannels()

        # Info
        InfoBar(self).pack(side="bottom", fill="x", expand=False)

        # Events
        self.songConnections: list[Connection] = list()

        def setupSongEventListeners():
            for con in self.songConnections:
                con.disconnect()
            self.songConnections = list()

            program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
                lambda *a: self.after(0, self.matrixChangedEvent, *a),
                self.songConnections,
            )

        SongReloaded.connect(lambda *_: setupSongEventListeners(), self.connections)

        program.p.getAttributeChangedEvent("currentMatrixRow").connect(
            lambda *a: self.after(0, self.onMatrixRowChange, *a), self.connections
        )

        StructureChanged.connect(lambda *_: self.showChannels(True), self.connections)
        SongReloaded.connect(lambda *_: self.showChannels(True), self.connections)

        Copy.connect(
            lambda focus: self.copy() if tkutil.isDescendantOf(focus, self) else None,
            self.connections,
        )
        Paste.connect(
            lambda focus: self.paste() if tkutil.isDescendantOf(focus, self) else None,
            self.connections,
        )

    def copy(self):
        _logger.debug("Pattern Editor COPY")

        # TODO: redo this with the get selected indices thingy

        t1, t2 = minmax(
            self.target,
            self.secondaryTarget if self.secondaryTarget is not None else self.target,
            key=lambda t: t.horizontalComparisonKey,
        )

        c1, c2 = minmax(
            CHANNEL_ORDER_INVERSE[t1.channel], CHANNEL_ORDER_INVERSE[t2.channel]
        )

        r1, r2 = minmax(t1.row, t2.row)

        self.clipboard = list()
        for channel in range(c1, c2 + 1):  # Inclusive
            offset = c2 - channel

            entry = PatternViewClipboardChannel(offset)
            pattern = program.p.currentSong.getPatternByLocation(
                CHANNEL_ORDER[channel], program.p.currentMatrixRow
            )

            first = channel == c1
            last = channel == c2

            # Fill Entry
            # By copying and then cropping
            # Cause that's easier than only grabbing whats needed
            # Well not rows since thats also easy

            entry.notes = {
                (row - r1, col): v
                for (row, col), v in pattern.notes.items()
                if row >= r1 and row <= r2
            }
            entry.velocities = {
                (row - r1, col): v
                for (row, col), v in pattern.velocities.items()
                if row >= r1 and row <= r2
            }
            entry.effects = {
                (row - r1, col): v
                for (row, col), v in pattern.effects.items()
                if row >= r1 and row <= r2
            }

            if last:
                c = t2.subcolumn
                if t2.column != PVLM.EFFECT:
                    entry.effects = dict()
                    # TODO: indivudial note/vel handling
                    entry.notes = {
                        (row, col): v
                        for (row, col), v in entry.notes.items()
                        if col <= c
                    }
                    entry.velocities = {
                        (row, col): v
                        for (row, col), v in entry.velocities.items()
                        if col <= (c if t2.column == PVLM.VELOCITY else c - 1)
                    }
                else:
                    pass
                    # TODO: do effects

            if first:
                # This shifts columns over so it has to be done after LAST
                c = t1.subcolumn
                if t1.column == PVLM.EFFECT:
                    entry.notes = dict()
                    entry.velocities = dict()
                    # TODO: do effects
                else:
                    # TODO: indivudial note/vel handling
                    entry.notes = {
                        (row, col - c): v
                        for (row, col), v in entry.notes.items()
                        if col >= (c if t1.column == PVLM.NOTE else c + 1)
                    }
                    entry.velocities = {
                        (row, col - c): v
                        for (row, col), v in entry.velocities.items()
                        if col >= c
                    }

            _logger.debug(entry)

            self.clipboard.append(entry)

        _logger.debug("FINISH COPY")

    def clearSelection(self, *, refresh: bool = True):
        s = program.p.currentSong
        notes, vels, effects = self.getUsedIndicesInSelection()

        for channel, row, col in notes:
            pattern = s.getPatternByLocation(channel, program.p.currentMatrixRow)
            pattern.setNote(row, col, None)
        for channel, row, col in vels:
            pattern = s.getPatternByLocation(channel, program.p.currentMatrixRow)
            pattern.setVelocity(row, col, None)
        for channel, row, col in effects:
            pattern = s.getPatternByLocation(channel, program.p.currentMatrixRow)
            pattern.setEffect(row, col, None)

        if refresh:
            self.refreshLabels()

    @property
    def clipboardSize(self):
        """Return size of clipboard (rows, cols)"""
        positions = chain(
            flatten(e.notes.keys() for e in self.clipboard),
            flatten(e.velocities.keys() for e in self.clipboard),
            flatten(e.effects.keys() for e in self.clipboard),
        )
        rows = max((p[0] for p in positions), default=0) + 1
        cols = max((p[1] for p in positions), default=0) + 1
        return rows, cols

    def paste(self):
        _logger.debug("Pattern Editor PASTE")

        s = program.p.currentSong

        cRows, cCols = self.clipboardSize

        _logger.debug(f"Clipboard size: {cRows}, {cCols}")
        _logger.debug(self.clipboard)

        t1, t2 = minmax(
            self.target,
            self.secondaryTarget if self.secondaryTarget is not None else self.target,
            key=lambda t: t.horizontalComparisonKey,
        )

        self.target = t1
        self.secondaryTarget = t2

        if t1 == t2:
            t2.channel = t1.channel + len(self.clipboard) - 1
            t2.subcolumn = t1.subcolumn + cCols - 1
            t2.row = t1.row + cRows - 1

        ch1, ch2 = minmax(
            CHANNEL_ORDER_INVERSE[t1.channel], CHANNEL_ORDER_INVERSE[t2.channel]
        )

        c1, c2 = t1.subcolumn, t2.subcolumn

        r1, r2 = minmax(t1.row, t2.row)

        # TODO: limit/set clear area properly

        # Clear paste area
        self.clearSelection(refresh=False)

        for offset, entry in enumerate(self.clipboard):
            channel = CHANNEL_ORDER[offset + ch1]
            pattern = s.getPatternByLocation(channel, program.p.currentMatrixRow)
            _logger.debug(f"Pasting offset {offset} to pattern {channel}")

            first = offset == 0
            last = offset == len(self.clipboard) - 1

            for (row, col), note in entry.notes.items():
                row += r1
                if row > r2:
                    continue
                if first:
                    col += c1
                if last:
                    if col > c2:
                        continue
                pattern.setNote(row, col, note)

        self.refreshLabels()

    def getUsedIndicesInSelection(self):
        """Get all indices currently targeted that have an entry. Returns three lists of (channel, row, col), for notes, velocities, and effects."""
        notes: list[tuple[int, int, int]] = list()
        velocities: list[tuple[int, int, int]] = list()
        effects: list[tuple[int, int, int]] = list()

        t1, t2 = minmax(
            self.target,
            self.secondaryTarget if self.secondaryTarget is not None else self.target,
            key=lambda t: t.horizontalComparisonKey,
        )
        # ; mwahahahaha evil semicolon >:)
        c1, c2 = minmax(
            CHANNEL_ORDER_INVERSE[t1.channel], CHANNEL_ORDER_INVERSE[t2.channel]
        )

        r1, r2 = minmax(t1.row, t2.row)

        # TODO: this only needs lists/sets, not dicts (copy paste job woohoo!)

        for channel in range(c1, c2 + 1):  # Inclusive
            offset = c2 - channel

            pattern = program.p.currentSong.getPatternByLocation(
                CHANNEL_ORDER[channel], program.p.currentMatrixRow
            )

            first = channel == c1
            last = channel == c2

            _notes = {
                (row, col): v
                for (row, col), v in pattern.notes.items()
                if row >= r1 and row <= r2
            }
            _velocities = {
                (row, col): v
                for (row, col), v in pattern.velocities.items()
                if row >= r1 and row <= r2
            }
            _effects = {
                (row, col): v
                for (row, col), v in pattern.effects.items()
                if row >= r1 and row <= r2
            }

            if last:
                c = t2.subcolumn
                if t2.column != PVLM.EFFECT:
                    _effects = dict()
                    # TODO: indivudial note/vel handling
                    _notes = {
                        (row, col): v for (row, col), v in _notes.items() if col <= c
                    }
                    _velocities = {
                        (row, col): v
                        for (row, col), v in _velocities.items()
                        if col <= (c if t2.column == PVLM.VELOCITY else c - 1)
                    }
                else:
                    pass
                    # TODO: do effects

            if first:
                # This shifts columns over so it has to be done after LAST
                c = t1.subcolumn
                if t1.column == PVLM.EFFECT:
                    _notes = dict()
                    _velocities = dict()
                    # TODO: do effects
                else:
                    # TODO: indivudial note/vel handling
                    _notes = {
                        (row, col): v
                        for (row, col), v in _notes.items()
                        if col >= (c if t1.column == PVLM.NOTE else c + 1)
                    }
                    _velocities = {
                        (row, col): v
                        for (row, col), v in _velocities.items()
                        if col >= c
                    }

            notes += [(CHANNEL_ORDER[channel], row, col) for row, col in _notes]
            velocities += [
                (CHANNEL_ORDER[channel], row, col) for row, col in _velocities
            ]
            effects += [(CHANNEL_ORDER[channel], row, col) for row, col in _effects]

        return notes, velocities, effects

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    def matrixChangedEvent(self, key: tuple[int, int], old: int | None, new: int):
        channel, row = key
        if row != program.p.currentMatrixRow:
            return
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
        focus: bool = False,
        setSecondary: bool = False,
    ):
        channel = channel if channel is not None else self.target.channel
        row = row if row is not None else self.target.row
        column = column if column is not None else self.target.column
        subcolumn = subcolumn if subcolumn is not None else self.target.subcolumn

        if setSecondary:
            if self.secondaryTarget is None:
                self.secondaryTarget = self.target
        else:
            self.secondaryTarget = None

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
        focus: bool = False,
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

    def showChannels(self, fullRebuild: bool = False):
        currentChannelsShown = len(self.views)
        newList = list()
        if fullRebuild:
            for i in range(CHANNEL_COUNT):
                if i < currentChannelsShown:
                    self.views[i].destroy()
                if i <= program.p.currentSong.visibleChannels:
                    view = PatternView(
                        self.__content,
                        self,
                        program.p.currentSong.getPatternById(CHANNEL_ORDER[i], 0),
                    )
                    view.pack(side="left", expand=True)
                    newList.append(view)
        else:
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

    def refreshLabels(self):
        for view in self.views:
            view.refreshLabels()
