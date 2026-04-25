"""
View/editor for the pattern matrix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from utils.event import Connection
from utils.misc import clamp
from utils.tk import tkQueuedAction

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern

import logging
import tkinter as tk
from tkinter import ttk

from interface.theme import MatrixSelector
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from structures.globalEvents import SongReloaded, StructureChanged
from utils.constants import CHANNEL_ORDER, CHANNEL_ORDER_INVERSE, PATTERN_DELTAS

_logger = logging.getLogger(__name__)


class PatternSelector(ttk.Label):
    def __init__(self, parent: tk.Misc, matrix: PatternMatrix, channel: int, row: int):
        super().__init__(parent, relief="sunken")

        self.matrix = matrix

        self.channel = channel
        self.row = row

        self.connections: list[Connection] = list()

        self.__style: str = ""
        self.__text: str = ""

        # Interaction

        self.bind("<FocusIn>", lambda *_: self.refresh())
        self.bind("<FocusOut>", lambda *_: self.refresh())

        def setupIncrement():
            # Linux Scroll
            self.bind("<Button-4>", lambda *_: self.increment(0))
            self.bind("<Button-5>", lambda *_: self.decrement(0))
            self.bind("<Shift-Button-4>", lambda *_: self.increment(1))
            self.bind("<Shift-Button-5>", lambda *_: self.decrement(1))
            self.bind("<Control-Button-4>", lambda *_: self.increment(2))
            self.bind("<Control-Button-5>", lambda *_: self.decrement(2))
            self.bind("<Control-Shift-Button-4>", lambda *_: self.increment(3))
            self.bind("<Control-Shift-Button-5>", lambda *_: self.decrement(3))

            # Not Linux Scroll
            self.bind(
                "<MouseWheel>",
                lambda e: self.increment(0) if e.delta > 0 else self.decrement(0),
            )
            self.bind(
                "<Shift-MouseWheel>",
                lambda e: self.increment(1) if e.delta > 0 else self.decrement(1),
            )
            self.bind(
                "<Control-MouseWheel>",
                lambda e: self.increment(2) if e.delta > 0 else self.decrement(2),
            )
            self.bind(
                "<Control-Shift-MouseWheel>",
                lambda e: self.increment(3) if e.delta > 0 else self.decrement(3),
            )

            # Keyboard
            self.bind("<equal>", lambda *_: self.increment(0, True))
            self.bind("<minus>", lambda *_: self.decrement(0, True))
            self.bind("<plus>", lambda *_: self.increment(1, True))
            self.bind("<underscore>", lambda *_: self.decrement(1, True))
            self.bind("<Control-equal>", lambda *_: self.increment(2, True))
            self.bind("<Control-minus>", lambda *_: self.decrement(2, True))
            self.bind("<Control-plus>", lambda *_: self.increment(3, True))
            self.bind("<Control-underscore>", lambda *_: self.decrement(3, True))

        setupIncrement()

        def setupSelect():
            self.bind("<Button-1>", lambda *_: (self.select(), self.setCurrentRow()))
            self.bind("<space>", lambda *_: (self.select(), self.setCurrentRow()))
            self.bind("<Control-Button-1>", lambda *_: self.toggleSelect())
            self.bind("<Shift-Button-1>", lambda *_: self.boxSelect())
            self.bind("<Control-a>", lambda *_: self.selectAll())
            self.bind("<Control-r>", lambda *_: self.selectRow())

        setupSelect()

        def setupMiddleClick():
            self.bind("<Button-2>", lambda *_: self.setToUnused())
            self.bind("<Shift-Button-2>", lambda *_: self.setPatternId(0))
            self.bind(
                "<E>",
                lambda *_: [
                    sel.setPatternId(0) for sel in self.matrix.getSelectedSelectors()
                ],
            )
            self.bind(
                "<e>",
                lambda *_: [
                    sel.setToUnused() for sel in self.matrix.getSelectedSelectors()
                ],
            )

        setupMiddleClick()

        def setupCopy():

            self.bind("<Button-3>", lambda *_: self.copyToSelected())
            self.bind("<Shift-Button-3>", lambda *_: self.copyFromAbove())
            self.bind("<Shift-c>", lambda *_: self.copyFromAbove())

        setupCopy()

        def setupArrowKeys():
            def getMove(rows: int = 0, cols: int = 0):
                nextRow = clamp(
                    self.row + rows, 0, program.p.currentSong.visibleMatrixRows - 1
                )
                nextChannel = CHANNEL_ORDER[
                    clamp(
                        CHANNEL_ORDER_INVERSE[self.channel] + cols,
                        0,
                        program.p.currentSong.visibleChannels,
                    )
                ]
                return self.matrix.getSelector(nextRow, nextChannel)

            def move(rows: int = 0, cols: int = 0):
                next = getMove(rows, cols)
                self.matrix.selectCell(next.row, next.channel, "set")
                next.focus()

            def moveSelect(rows: int = 0, cols: int = 0):
                next = getMove(rows, cols)
                self.matrix.gridSelectCells(next.row, next.channel)
                next.focus()

            self.bind("<Left>", lambda *_: move(0, -1))
            self.bind("<Right>", lambda *_: move(0, 1))
            self.bind("<Up>", lambda *_: move(-1, 0))
            self.bind("<Down>", lambda *_: move(1, 0))

            self.bind("<Shift-Left>", lambda *_: moveSelect(0, -1))
            self.bind("<Shift-Right>", lambda *_: moveSelect(0, 1))
            self.bind("<Shift-Up>", lambda *_: moveSelect(-1, 0))
            self.bind("<Shift-Down>", lambda *_: moveSelect(1, 0))

        setupArrowKeys()

    @property
    def column(self):
        return CHANNEL_ORDER_INVERSE[self.channel]

    @property
    def position(self):
        return (self.row, self.channel)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    ### Actions

    def setCurrentRow(self):
        """Set the current matrix row to the row of this selector."""
        program.p.currentMatrixRow = self.row

    def getPatternId(self) -> int:
        """Get the pattern id currently in this selector."""
        return program.p.currentSong.getPatternIdByLocation(self.channel, self.row)

    def setPatternId(self, pattern: int):
        """Set the pattern id this selector references."""
        program.p.currentSong.setPatternNumber(self.channel, self.row, pattern)
        self.refresh()

    def increment(self, scale: int = 0, useSelection: bool = False):
        if useSelection:
            for sel in self.matrix.getSelectedSelectors():
                sel.setPatternId(sel.getPatternId() + PATTERN_DELTAS[scale])
        else:
            self.setPatternId(self.getPatternId() + PATTERN_DELTAS[scale])

    def decrement(self, scale: int = 0, useSelection: bool = False):
        if useSelection:
            for sel in self.matrix.getSelectedSelectors():
                sel.setPatternId(max(0, sel.getPatternId() - PATTERN_DELTAS[scale]))
        else:
            self.setPatternId(max(0, self.getPatternId() - PATTERN_DELTAS[scale]))

    def select(self):
        self.matrix.selectCell(self.row, self.channel, "set")

    def boxSelect(self):
        self.matrix.gridSelectCells(self.row, self.channel)

    def toggleSelect(self):
        self.matrix.selectCell(self.row, self.channel, "toggle")

    def selectRow(self):
        for sel in self.matrix.getSelectedSelectors().copy():
            sel.matrix.selectRow(sel.row, "add")

    def selectAll(self):
        for sel in self.matrix.getSelectors().values():
            sel.matrix.selectCell(sel.row, sel.channel, "add")

    def setToUnused(self):
        self.setPatternId(program.p.currentSong.getFreePatternId(self.channel))

    def copyToSelected(self):
        id = self.getPatternId()
        for sel in self.matrix.getSelectedSelectors():
            sel.setPatternId(id)

    def copyFromAbove(self):
        if self.row == 0:
            return
        p = program.p.currentSong.getPatternIdByLocation(self.channel, self.row - 1)
        self.setPatternId(p)

    ###

    @tkQueuedAction()
    def refresh(self):
        """Reload this selector's visual state."""

        ### If chain to determine style to use
        if self.position in self.matrix.getSelection():
            if "focus" in self.state():
                style = MatrixSelector.TargetAnchor
            else:
                style = (
                    MatrixSelector.Target1
                    if self.channel % 2 == 1
                    else MatrixSelector.Target2
                )
        elif (self.row, self.channel) in program.p.currentSong.highlightedMatrixItems:
            style = MatrixSelector.Highlight
        else:
            style = (
                MatrixSelector.DefaultEven
                if self.channel % 2 == 1
                else MatrixSelector.DefaultOdd
            )

        self.text = str(hex(self.getPatternId())[2:].upper())
        self.style = cast(str, style)

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


class PatternSelectorRowLabel(ttk.Label):
    def __init__(self, parent: tk.Misc, matrix: PatternMatrix, row: int):
        super().__init__(parent, text=str(hex(row)[2:].upper()), width=3)
        self.matrix = matrix
        self.row = row
        self.__style: str = ""

        ### Bindings

        def setupLeftClick():
            self.bind(
                "<Button-1>",
                lambda *_: (
                    self.matrix.selectRow(self.row, "set"),
                    setattr(program.p, "currentMatrixRow", self.row),
                ),
            )
            self.bind(
                "<Shift-Button-1>",
                lambda *_: (self.matrix.gridSelectCells(self.row, None)),
            )
            self.bind(
                "<Control-Button-1>",
                lambda *_: (self.matrix.selectRow(self.row, "toggle")),
            )

        setupLeftClick()

        def setupRightClick():
            def copy():
                ids = {
                    sel.channel: program.p.currentSong.getPatternIdByLocation(
                        sel.channel, sel.row
                    )
                    for sel in self.matrix.getSelectorsInRow(self.row)
                }
                for sel in self.matrix.getSelectedSelectors():
                    sel.setPatternId(ids[sel.channel])

            def copyFromAbove():
                if self.row == 0:
                    return
                for sel in self.matrix.getSelectorsInRow(self.row):
                    p = program.p.currentSong.getPatternIdByLocation(
                        sel.channel, sel.row - 1
                    )
                    sel.setPatternId(p)

            self.bind("<Button-3>", lambda *_: copy())
            self.bind("<Shift-Button-3>", lambda *_: copyFromAbove())

        setupRightClick()

        def setupMiddleClick():
            self.bind(
                "<Button-2>",
                lambda *_: (
                    sel.setPatternId(
                        program.p.currentSong.getFreePatternId(sel.channel)
                    )
                    for sel in self.matrix.getSelectorsInRow(self.row)
                ),
            )
            self.bind(
                "<Shift-Button-2>",
                lambda *_: (
                    sel.setPatternId(0)
                    for sel in self.matrix.getSelectorsInRow(self.row)
                ),
            )

        setupMiddleClick()

        self.refresh()

    @tkQueuedAction()
    def refresh(self):
        if self.row == program.p.currentMatrixRow:
            style = MatrixSelector.Target2
        else:
            highlighted = True
            for channel in range(program.p.currentSong.visibleChannels):
                i = (self.row, channel) in program.p.currentSong.highlightedMatrixItems
                if not i:
                    highlighted = False
                # print(f"{self.row}: {i}")
            if highlighted:
                style = MatrixSelector.Highlight
            else:
                style = MatrixSelector.DefaultOdd
        self.style = cast(str, style)

    @property
    def style(self) -> str:
        return self.__style

    @style.setter
    def style(self, newStyle: str):
        if newStyle != self.__style:
            self.__style = newStyle
            self.config(style=self.style)


class MatrixActions(ttk.Frame):
    def __init__(self, parent: tk.Misc, matrix: PatternMatrix):
        super().__init__(parent)
        self.matrix = matrix

        sf = DScrollFrame(self, mode="VERTICAL", propagationMode="contentDrivesFrame")
        sf.pack(fill="both", expand=True)

        ttk.Button(
            sf.content, text="Delete Rows", command=lambda *_: self.removeRows()
        ).pack(side="top", fill="x", expand=True)
        ttk.Button(
            sf.content,
            text="New Row Before",
            command=lambda *_: self.addNewRow("before"),
        ).pack(side="top", fill="x", expand=True)
        ttk.Button(
            sf.content, text="New Row After", command=lambda *_: self.addNewRow("after")
        ).pack(side="top", fill="x", expand=True)
        ttk.Button(
            sf.content, text="New Row At End", command=lambda *_: self.addNewRow("end")
        ).pack(side="top", fill="x", expand=True)
        ttk.Button(
            sf.content,
            text="Toggle Highlight",
            command=lambda *_: self.toggleHighlight(),
        ).pack(side="top", fill="x", expand=True)
        # ttk.Button(
        #     sf.content,
        #     text="Clone Rows Before",
        #     command=lambda *_: self.cloneRows("before"),
        # ).pack(side="top", fill="x", expand=True)
        # ttk.Button(
        #     sf.content,
        #     text="Clone Rows After",
        #     command=lambda *_: self.cloneRows("after"),
        # ).pack(side="top", fill="x", expand=True)
        ttk.Button(
            sf.content, text="Clone To End", command=lambda *_: self.cloneRows("end")
        ).pack(side="top", fill="x", expand=True)
        # ttk.Button(
        #     sf.content, text="Move Up", command=lambda *_: self.moveRows("up")
        # ).pack(side="top", fill="x", expand=True)
        # ttk.Button(
        #     sf.content, text="Move Down", command=lambda *_: self.moveRows("down")
        # ).pack(side="top", fill="x", expand=True)

    def toggleHighlight(self):
        # Highlight selected, unless all selected are highlighted, then unhighlight.
        song = program.p.currentSong

        selection = self.matrix.getSelection()
        set = not all(pos in song.highlightedMatrixItems for pos in selection)
        for pos in selection:
            if set:
                song.highlightedMatrixItems.add(pos)
            else:
                song.highlightedMatrixItems.discard(pos)

        self.matrix.refresh()

    def removeRows(self):
        # For each row, remove it and move the rest backwards
        song = program.p.currentSong

        for row in self.matrix.getSelectedRows():
            song.shiftMatrixRows(row + 1, None, row)
            song.visibleMatrixRows -= 1
        self.matrix.clearSelection()
        self.matrix.refresh()

    def addNewRow(self, position: Literal["before", "after", "end"]):
        song = program.p.currentSong

        if position == "before":
            row = min(self.matrix.getSelectedRows(), default=0)
        elif position == "after":
            row = max(self.matrix.getSelectedRows(), default=0) + 1
        elif position == "end":
            row = song.visibleMatrixRows

        song.shiftMatrixRows(row, None, row + 1)

        song.visibleMatrixRows += 1
        self.matrix.refresh()

    def cloneRows(self, position: Literal["before", "after", "end"]):
        song = program.p.currentSong

        rows = list(self.matrix.getSelectedRows())
        newRows = len(rows)
        if newRows == 0:
            return
        rows.sort()

        if position == "before":
            row0 = min(rows)
            for i in range(newRows):
                rows[i] += newRows
        elif position == "after":
            row0 = max(rows) + 1
        elif position == "end":
            row0 = song.visibleMatrixRows

        song.shiftMatrixRows(row0, None, row0 + newRows)

        for i, row in enumerate(rows):
            for channel in range(song.visibleChannels):
                song.setPatternNumber(
                    channel, row0 + i, song.getPatternIdByLocation(channel, row)
                )

        song.visibleMatrixRows += newRows
        self.matrix.refresh()

    # def moveRows(self, direction: Literal["up", "down"]):
    #     song = program.p.currentSong
    #     rows = list(self.matrix.getSelectedRows())
    #     if len(rows) == 0: return

    #     if direction == "up":
    #         for
    #     elif direction == "down":
    #         pass

    #     self.matrix.refresh()


class PatternMatrix(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=500, height=200, borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(side="left", fill="both", expand=True)

        sf.widgetNameBlockList.add("patternselector")

        actions = MatrixActions(self, self)
        actions.pack(side="left", fill="both")

        self.connections: list[Connection] = list()

        self.pack_propagate(False)

        self.__content = sf.content
        self.__grid = ttk.Frame(self.__content)
        self.__grid.pack(side="top", fill="x")

        self.__colLabels: list[ttk.Label] = list()
        self.__rowLabels: list[PatternSelectorRowLabel] = list()
        self.__selectors: dict[tuple[int, int], PatternSelector] = dict()
        """set[row, col] -> PatternSelector"""

        self.__selection: set[tuple[int, int]] = {(0, 0)}
        """set[row:int, channel:int] - Currently selected cells."""
        self.selectionAnchor: tuple[int, int] = (0, 0)
        """(row, channel) - Used for box selections"""

        # self.clipboard: dict[tuple[int, int], int] = dict()
        # """(row, channel) -> pattern id"""

        self.refresh()
        StructureChanged.connect(lambda *_: self.refresh(), self.connections)
        SongReloaded.connect(lambda *_: self.refresh(), self.connections)
        program.p.getAttributeChangedEvent("currentMatrixRow").connect(
            lambda *_: self.refresh()
        )

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    ### Selection

    def getSelection(self) -> set[tuple[int, int]]:
        return self.__selection

    def clearSelection(self):
        self.__selection = set()

    def setSelectionAnchor(self, row: int | None = None, channel: int | None = None):
        if row is None:
            row = self.selectionAnchor[0]
        if channel is None:
            channel = self.selectionAnchor[1]
        self.selectionAnchor = (row, channel)

    def selectCell(
        self, row: int, channel: int, mode: Literal["add", "sub", "set", "toggle"]
    ):
        """Select a single cell."""
        t = (row, channel)
        self.setSelectionAnchor(row, channel)
        if mode == "add":
            self.__selection.add(t)
        elif mode == "sub":
            if t in self.__selection:
                self.__selection.remove(t)
        elif mode == "set":
            self.__selection = {t}
        elif mode == "toggle":
            if t in self.__selection:
                self.__selection.remove(t)
            else:
                self.__selection.add(t)
        self._refresh()

    def gridSelectCells(self, row: int, channel: int | None):
        self.__selection = set()
        r1 = self.selectionAnchor[0]
        r2 = row
        if channel is None:
            c1 = 0
            c2 = program.p.currentSong.visibleMatrixRows
        else:
            c1 = CHANNEL_ORDER_INVERSE[self.selectionAnchor[1]]
            c2 = CHANNEL_ORDER_INVERSE[channel]

        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                self.__selection.add((r, CHANNEL_ORDER[c]))
        self._refresh()

    def selectRow(self, row: int, mode: Literal["add", "sub", "set", "toggle"]):
        """Select a row"""
        self.setSelectionAnchor(row, 9)
        cols = CHANNEL_ORDER[: program.p.currentSong.visibleChannels + 1]
        if mode == "add" or mode == "sub":
            for col in cols:
                self.selectCell(row, col, mode)
        elif mode == "set":
            self.__selection = {(row, col) for col in cols}
        elif mode == "toggle":
            state = all((row, c) in self.__selection for c in cols)
            self.selectRow(row, "sub" if state else "add")
        self._refresh()

    # def copy(self):
    #     pass

    # def paste(self):
    #     pass

    ### Construction

    GRID_POSITIONS = {
        #             col label
        #  insert bar ---------
        #  row label  selector
        #
        "selector": (2, 1),
        "row label": (2, 0),
        "column label": (0, 1),
        "insert bar": (1, 0),
    }
    ROW_STEP = max(p[0] for p in GRID_POSITIONS.values()) + 1
    COL_STEP = max(p[1] for p in GRID_POSITIONS.values()) + 1

    def gridPosition(
        self,
        row: int,
        column: int,
        item: Literal["selector", "row label", "column label", "insert bar"],
    ) -> tuple[int, int]:
        rowOffset = self.GRID_POSITIONS[item][0]
        colOffset = self.GRID_POSITIONS[item][1]
        return ((row * self.ROW_STEP) + rowOffset, (column * self.COL_STEP) + colOffset)

    def getSelector(self, row: int, channel: int) -> PatternSelector:
        return self.__selectors[row, CHANNEL_ORDER_INVERSE[channel]]

    def getSelectorsInRow(self, row: int) -> set[PatternSelector]:
        return {
            self.__selectors[row, col]
            for col in range(program.p.currentSong.visibleChannels + 1)
        }

    def getSelectors(self) -> dict[tuple[int, int], PatternSelector]:
        return self.__selectors

    def getSelectedSelectors(self) -> set[PatternSelector]:
        return {
            self.__selectors[(row, CHANNEL_ORDER_INVERSE[channel])]
            for row, channel in self.__selection
        }

    def getSelectedRows(self) -> set[int]:
        out = set()
        for row, channel in self.__selection:
            out.add(row)
        return out

    @tkQueuedAction()
    def refresh(self):
        self.rebuild()
        self._refresh()

    def _refresh(self):
        for sel in self.__selectors.values():
            sel.refresh()
        for lab in self.__rowLabels:
            lab.refresh()

    def rebuild(self):
        """Add/remove labels as needed."""

        currentRows = len(self.__rowLabels)
        currentCols = len(self.__colLabels)
        rows = program.p.currentSong.visibleMatrixRows
        cols = program.p.currentSong.visibleChannels + 1

        # Row Labels
        if rows > currentRows:  # Need more
            # _logger.debug("Need more matrix rows")
            for row in range(currentRows, rows):
                label = PatternSelectorRowLabel(self.__grid, self, row)
                pos = self.gridPosition(row, 0, "row label")
                label.grid(row=pos[0], column=pos[1])
                self.__rowLabels.append(label)
                # _logger.debug(row)
        elif rows < currentRows:  # Need less
            for row in range(currentRows, rows, -1):
                label = self.__rowLabels.pop()
                label.destroy()
                # _logger.debug(row)

        # Column Labels
        if cols > currentCols:  # Need more
            # _logger.debug("Need more matrix cols")
            for col in range(currentCols, cols):
                label = ttk.Label(self.__grid, text=CHANNEL_ORDER[col] + 1, width=3)
                pos = self.gridPosition(0, col, "column label")
                label.grid(row=pos[0], column=pos[1])
                self.__colLabels.append(label)
                # _logger.debug(col)
        elif cols < currentCols:  # Need less
            for col in range(currentCols, cols, -1):
                label = self.__colLabels.pop()
                label.destroy()
                # _logger.debug(col)

        # Selectors
        for row in range(max(rows, currentRows)):
            for col in range(max(cols, currentCols)):
                if row < rows and col < cols:
                    # We want a selector here
                    if (row, col) not in self.__selectors:
                        # Need a new one
                        selector = PatternSelector(
                            self.__grid, self, CHANNEL_ORDER[col], row
                        )
                        pos = self.gridPosition(row, col, "selector")
                        selector.grid(row=pos[0], column=pos[1], sticky="nesw")
                        self.__selectors[row, col] = selector
                        # _logger.debug(f"Adding selector at <{row}, {col}>")
                else:
                    # We don't want a selector here
                    if (row, col) in self.__selectors:
                        # Get rid of it
                        selector = self.__selectors[row, col]
                        selector.destroy()
                        del self.__selectors[row, col]
                        # _logger.debug(f"Removing selector at <{row}, {col}>")
