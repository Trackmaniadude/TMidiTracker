"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

from __future__ import annotations

import logging
import math
import tkinter as tk
from itertools import chain
from tkinter import ttk
from typing import Literal, cast

import utils.misc as util
import utils.tk as tkutil
from interface.program.patternViewCanvas import PatternViewCanvas
from interface.program.patternViewUtils import PVLM, PatternViewClipboardChannel, Target
from interface.theme import MatrixSelector
from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.validatedEntryPrebuilts import Prebuilts
from structures import program
from structures.globalEvents import Copy, Cut, Paste, SongReloaded, StructureChanged
from utils.constants import (
    CHANNEL_COUNT,
    CHANNEL_ORDER,
    CHANNEL_ORDER_INVERSE,
    DRUM_CHANNEL,
)
from utils.event import Connection, Event
from utils.misc import flatten, formatPortNameForDisplay, minmax

_logger = logging.getLogger(__name__)


class InfoBar(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)

        self.connections: list[Connection] = list()

        ttk.Label(self, text="OCT:").pack(side="left")
        octave = Prebuilts.Spinbox(
            self, default=program.p.currentOctave, range=(1, 10), increment=1, round=1
        )
        octave.entry.config(width=3)
        octave.entry.pack(side="left")

        ttk.Separator(self, orient="vertical").pack(
            side="left", fill="y", padx=tkutil.DEF_PAD
        )

        ttk.Label(self, text="STEP:").pack(side="left")
        step = Prebuilts.Spinbox(self, default=1, range=(1, 8), increment=1, round=1)
        step.entry.config(width=3)
        step.entry.pack(side="left")

        ttk.Separator(self, orient="vertical").pack(
            side="left", fill="y", padx=tkutil.DEF_PAD
        )

        time = ttk.Label(self)
        time.pack(side="left")

        ttk.Separator(self, orient="vertical").pack(
            side="left", fill="y", padx=tkutil.DEF_PAD
        )

        port = ttk.Label(self, text=formatPortNameForDisplay(program.p.currentPort))
        port.pack(side="right")

        ttk.Separator(self, orient="vertical").pack(
            side="right", fill="y", padx=tkutil.DEF_PAD
        )

        # Behavior
        octave.Changed.connect(
            lambda *_: setattr(program.p, "currentOctave", int(octave.value))
        )
        step.Changed.connect(lambda *_: setattr(program.p, "stepSize", int(step.value)))

        def timeStamp():
            matrixRow = program.p.currentMatrixRow
            patternRow = program.p.currentPatternRow

            s = program.p.currentSong
            avgRowTime = (sum(s.groove) / len(s.groove)) / s.clock
            rows = patternRow + (matrixRow * s.patternLength)
            currentTime = rows * avgRowTime

            text = f"{matrixRow:02d}:{patternRow:02d} ({util.formatTime(currentTime)})"
            time.config(text=text)

        program.p.getAttributeChangedEvent("currentPatternRow").connect(
            lambda *_: timeStamp(), self.connections
        )
        program.p.getAttributeChangedEvent("currentPort").connect(
            lambda *_: port.config(
                text=formatPortNameForDisplay(program.p.currentPort)
            ),
            self.connections,
        )
        timeStamp()

    def destroy(self) -> None:
        for con in self.connections:
            con.disconnect()
        return super().destroy()


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
        SongReloaded.connect(lambda *_: self.rebuild(), self.connections)

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
        for label in self.labels.values():
            label.destroy()
        self.labels.clear()
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
        self.secondaryTarget: Target = self.target

        self.views: list[PatternViewCanvas] = list()

        self.clipboard: list[PatternViewClipboardChannel] = list()

        RowList(self.__content).pack(side="left", fill="y")
        self.showChannels()

        # Info
        InfoBar(self).pack(side="bottom", fill="x", expand=False)

        # Events
        self.songConnections: list[Connection] = list()

        self.TargetChanged = Event()

        def setupSongEventListeners():
            for con in self.songConnections:
                con.disconnect()
            self.songConnections = list()

            program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
                self.matrixChangedEvent, self.songConnections
            )

        SongReloaded.connect(lambda *_: setupSongEventListeners(), self.connections)

        program.p.getAttributeChangedEvent("currentMatrixRow").connect(
            self.onMatrixRowChange, self.connections
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
        Cut.connect(
            lambda focus: (
                (print("CUT"), self.copy(), self.clearSelection())
                if tkutil.isDescendantOf(focus, self)
                else None
            ),
            self.connections,
        )

    def copy(self):
        """Copy selection to clipboard."""
        ### Get all selected indices, and dump them into clipboard entry objects after reformatting to the correct structure.
        _logger.debug("Pattern Editor COPY")
        s = program.p.currentSong

        notes, vels, effects = self.getUsedIndicesInSelection()
        all = lambda: chain(notes, vels, effects)
        ch0, ch1 = minmax(
            [p[0] for p in all()], default=-1
        )  # Can't use the chain directly, as minmax needs to iterate twice

        _logger.debug(f"NOTES: {notes}")
        _logger.debug(f"VELOCITIES: {vels}")
        _logger.debug(f"EFFECTS: {effects}")
        _logger.debug(f"RANGE: {ch0} - {ch1}")

        self.clipboard = list()

        if ch0 == -1:
            _logger.debug("FINISH COPY (NOTHING TO COPY)")
            return

        for channel in range(ch0, ch1 + 1):  # Inclusive
            _logger.debug(f"Copying channel {channel}")
            entry = PatternViewClipboardChannel(channel - ch0)
            pattern = s.getPatternByLocation(channel, program.p.currentMatrixRow)

            entry.notes = {
                (r, c): pattern.getNote(r, c) for (ch, r, c) in notes if ch == channel
            }
            entry.velocities = {
                (r, c): pattern.getVelocity(r, c)
                for (ch, r, c) in vels
                if ch == channel
            }
            entry.effects = {
                (r, c): pattern.getEffect(r, c)
                for (ch, r, c) in effects
                if ch == channel
            }

            _logger.debug(entry)
            self.clipboard.append(entry)

        # Normalize entries (make lowest row # 0, make lowest col # 0 in leftmost channel)
        rowOffset = min(self.target.row, self.secondaryTarget.row)
        for entry in self.clipboard:
            entry.notes = {(r - rowOffset, c): v for (r, c), v in entry.notes.items()}
            entry.velocities = {
                (r - rowOffset, c): v for (r, c), v in entry.velocities.items()
            }
            entry.effects = {
                (r - rowOffset, c): v for (r, c), v in entry.effects.items()
            }

        colOffset = min(self.target.subcolumn, self.secondaryTarget.subcolumn)
        self.clipboard[0].notes = {
            (r, c - colOffset): v for (r, c), v in self.clipboard[0].notes.items()
        }
        self.clipboard[0].velocities = {
            (r, c - colOffset): v for (r, c), v in self.clipboard[0].velocities.items()
        }
        self.clipboard[0].effects = {
            (r, c - colOffset): v for (r, c), v in self.clipboard[0].effects.items()
        }

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

        # if refresh:
        #     self.refreshLabels()

    @property
    def clipboardSize(self):
        """Return size of clipboard (rows, cols)"""
        positions = list(
            chain(
                flatten(e.notes.keys() for e in self.clipboard),
                flatten(e.velocities.keys() for e in self.clipboard),
                flatten(e.effects.keys() for e in self.clipboard),
            )
        )
        rows = max((p[0] for p in positions), default=0) + 1
        cols = max((p[1] for p in positions), default=0) + 1
        return rows, cols

    def paste(self):
        # TODO: make this not a mess
        _logger.debug("Pattern Editor PASTE")

        s = program.p.currentSong

        cRows, cCols = self.clipboardSize

        _logger.debug(f"Clipboard size: {cRows}, {cCols}")
        _logger.debug(self.clipboard)

        t1, t2 = self.target, self.secondaryTarget

        if t2 is None or t1 == t2:
            t2 = Target(
                t1.channel + len(self.clipboard) - 1,
                t1.row + cRows - 1,
                t1.column,
                t1.subcolumn + cCols - 1,
            )

        self.target = t1
        self.secondaryTarget = t2

        ch1, ch2 = minmax(
            CHANNEL_ORDER_INVERSE[t1.channel], CHANNEL_ORDER_INVERSE[t2.channel]
        )
        c1, c2 = minmax(t1.subcolumn, t2.subcolumn)
        r1, r2 = minmax(t1.row, t2.row)

        _logger.debug(t1)
        _logger.debug(t2)

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

            for (row, col), vel in entry.velocities.items():
                row += r1
                if row > r2:
                    continue
                if first:
                    col += c1
                if last:
                    if col > c2:
                        continue
                pattern.setVelocity(row, col, vel)

            for (row, col), effect in entry.effects.items():
                row += r1
                if row > r2:
                    continue
                if first:
                    col += c1
                if last:
                    if col > c2:
                        continue
                pattern.setEffect(row, col, effect)

        self.TargetChanged.fire()
        # self.refreshLabels()

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
        # view.refreshLabels()

    def onMatrixRowChange(self, key, old, new):
        for i, view in enumerate(self.views):
            channel = CHANNEL_ORDER[i]
            view.setPattern(
                program.p.currentSong.getPatternByLocation(
                    channel, program.p.currentMatrixRow
                )
            )

    def setTarget(
        self,
        channel: int | None = None,
        row: int | None = None,
        column: PVLM | None = None,
        subcolumn: int | None = None,
        *,
        boxSelect: bool = False,
    ):
        channel = channel if channel is not None else self.target.channel
        row = row if row is not None else self.target.row
        column = column if column is not None else self.target.column
        subcolumn = subcolumn if subcolumn is not None else self.target.subcolumn

        self.target = Target(channel, row, column, subcolumn)
        if not boxSelect:
            self.secondaryTarget = self.target
        self.TargetChanged.fire()

        # if focus == True:
        #     self.views[CHANNEL_ORDER_INVERSE[channel]].labelLookup[
        #         row, column, subcolumn
        #     ].focus()
        # for view in self.views:
        #     view.refreshLabels()

    def stepTarget(
        self,
        step: int,
        stepPattern: bool = True,
        *,
        direction: Literal["Up", "Down", "Left", "Right"] = "Down",
        boxSelect: bool = False,
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
            self.setTarget(row=newPatternRow, boxSelect=boxSelect)

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
            self.setTarget(row=newPatternRow, boxSelect=boxSelect)

        elif direction == "Left":  # TODO: variable step
            currentChannel = CHANNEL_ORDER_INVERSE[self.target.channel]
            currentChannelObj = program.p.currentSong.channels[self.target.channel]

            if self.target.column == PVLM.NOTE:
                if self.target.subcolumn > 0:
                    self.setTarget(
                        column=PVLM.VELOCITY,
                        subcolumn=self.target.subcolumn - 1,
                        boxSelect=boxSelect,
                    )
                else:  # Move to LEFT channel
                    if currentChannel > 0:
                        nextChannel = CHANNEL_ORDER[currentChannel - 1]
                        nextChannelObj = program.p.currentSong.channels[nextChannel]
                        self.setTarget(
                            channel=nextChannel,
                            column=PVLM.EFFECT,
                            subcolumn=nextChannelObj.effectColumns - 1,
                            boxSelect=boxSelect,
                        )
            elif self.target.column == PVLM.VELOCITY:
                self.setTarget(column=PVLM.NOTE, boxSelect=boxSelect)
            elif self.target.column == PVLM.EFFECT:
                if self.target.subcolumn > 0:
                    self.setTarget(
                        subcolumn=self.target.subcolumn - 1, boxSelect=boxSelect
                    )
                else:
                    self.setTarget(
                        column=PVLM.VELOCITY,
                        subcolumn=currentChannelObj.noteColumns - 1,
                        boxSelect=boxSelect,
                    )

        elif direction == "Right":  # TODO: variable step
            currentChannel = CHANNEL_ORDER_INVERSE[self.target.channel]
            currentChannelObj = program.p.currentSong.channels[self.target.channel]

            if self.target.column == PVLM.NOTE:
                self.setTarget(column=PVLM.VELOCITY, boxSelect=boxSelect)
            elif self.target.column == PVLM.VELOCITY:
                if (
                    self.target.subcolumn >= currentChannelObj.noteColumns - 1
                ):  # Move to EFFECT column
                    self.setTarget(column=PVLM.EFFECT, subcolumn=0, boxSelect=boxSelect)
                else:
                    self.setTarget(
                        column=PVLM.NOTE,
                        subcolumn=self.target.subcolumn + 1,
                        boxSelect=boxSelect,
                    )
            elif self.target.column == PVLM.EFFECT:  # Move to RIGHT channel
                if currentChannel < program.p.currentSong.visibleChannels:
                    if self.target.subcolumn < currentChannelObj.effectColumns - 1:
                        self.setTarget(
                            subcolumn=self.target.subcolumn + 1,
                            boxSelect=boxSelect,
                        )
                    else:
                        self.setTarget(
                            channel=CHANNEL_ORDER[currentChannel + 1],
                            column=PVLM.NOTE,
                            subcolumn=0,
                            boxSelect=boxSelect,
                        )

    @tkutil.tkQueuedAction()
    def showChannels(self, fullRebuild: bool = False):
        currentChannelsShown = len(self.views)
        newList = list[PatternViewCanvas]()
        if fullRebuild:
            for i in range(CHANNEL_COUNT):
                if i < currentChannelsShown:
                    self.views[i].destroy()
                if i <= program.p.currentSong.visibleChannels:
                    view = PatternViewCanvas(
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
                        view = PatternViewCanvas(
                            self.__content,
                            self,
                            program.p.currentSong.getPatternById(CHANNEL_ORDER[i], 0),
                        )
                        view.pack(side="left", expand=True)
                        newList.append(view)
                    else:
                        pass
        self.views = newList

    def refresh(self):
        for view in self.views:
            view.refresh()
