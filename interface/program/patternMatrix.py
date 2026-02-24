"""
View/editor for the pattern matrix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from interface.utilities.quickRefresh import QuickRefresh
from utils.event import Connection

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
from structures.globalEvents import StructureChanged
from utils.constants import CHANNEL_ORDER, CHANNEL_ORDER_INVERSE, PATTERN_DELTAS

_logger = logging.getLogger(__name__)


class PatternSelector(ttk.Label, QuickRefresh):
    def __init__(self, parent: tk.Misc, matrix: PatternMatrix, channel: int, row: int):
        super().__init__(parent, relief="sunken")

        self.matrix = matrix

        self.channel = channel
        self.row = row

        self.connections: list[Connection] = list()

        self.__style: str = ""
        self.__text: str = ""

        # Interaction

        def setupLeftClick():
            self.bind(
                "<Button-1>",
                lambda *_: (
                    self.matrix.selectCell(self.row, self.channel, "set"),
                    self.setCurrentRow(),
                ),
            )
            self.bind(
                "<Control-Button-1>",
                lambda *_: self.matrix.selectCell(self.row, self.channel, "toggle"),
            )

        setupLeftClick()

        # self.refresh()

    # @property
    # def column(self):
    #     return CHANNEL_ORDER_INVERSE[self.channel]

    @property
    def position(self):
        return (self.row, self.channel)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    ###

    def setCurrentRow(self):
        """Set the current matrix row to the row of this selector."""
        program.p.currentMatrixRow = self.row

    def getPatternId(self) -> int:
        """Get the pattern id currently in this selector."""
        return program.p.currentSong.getPatternIdByLocation(self.channel, self.row)

    def setPatternId(self, pattern: int):
        """Set the pattern id this selector references."""
        program.p.currentSong.setPatternNumber(self.channel, self.row, pattern)

    def increment(self, scale: int = 0):
        self.setPatternId(self.getPatternId() + PATTERN_DELTAS[scale])

    def decrement(self, scale: int = 0):
        self.setPatternId(max(0, self.getPatternId() - PATTERN_DELTAS[scale]))

    def copyAbove(self):
        """Set this selector to the same value as the one above it."""
        if self.row == 0:
            return
        p = program.p.currentSong.getPatternIdByLocation(self.channel, self.row - 1)
        self.setPatternId(p)

    ###

    def refresh(self):
        """Reload this selector's visual state."""
        self.resetRefreshFlag()

        ### If chain to determine style to use
        if self.position in self.matrix.selection:
            style = MatrixSelector.Target
        # elif self.row == program.p.currentMatrixRow:
        #     style = MatrixSelector.Target
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


class PatternMatrix(ttk.Frame, QuickRefresh):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=300, height=200, borderwidth=2)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.connections: list[Connection] = list()

        self.pack_propagate(False)

        self.__content = sf.content
        self.__grid = ttk.Frame(self.__content)
        self.__grid.pack(side="top", fill="x")

        self.__colLabels: list[ttk.Label] = list()
        self.__rowLabels: list[ttk.Label] = list()
        self.__selectors: dict[tuple[int, int], PatternSelector] = dict()
        """(row, col) -> PatternSelector"""

        self.selection: set[tuple[int, int]] = {(0, 0)}
        """set[row:int, channel:int] - Currently selected cells."""
        self.selectionAnchor: tuple[int, int] = (0, 0)
        """(row, channel) - Used for box selections"""

        self.refresh()
        StructureChanged.connect(lambda *_: self.queueRefresh(), self.connections)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    ### Selection

    def setSelectionAnchor(self, row: int, channel: int):
        self.selectionAnchor = (row, channel)

    def selectCell(
        self, row: int, channel: int, mode: Literal["add", "sub", "set", "toggle"]
    ):
        """Select a single cell."""
        t = (row, channel)
        if mode == "add":
            self.selection.add(t)
        elif mode == "sub":
            if t in self.selection:
                self.selection.remove(t)
        elif mode == "set":
            self.selection = {t}
        elif mode == "toggle":
            if t in self.selection:
                self.selection.remove(t)
            else:
                self.selection.add(t)
        self.refreshSelectors()

    def selectRow(self, row: int, mode: Literal["add", "sub", "set", "toggle"]):
        """Select a row"""
        cols = range(program.p.currentSong.visibleChannels + 1)
        if mode == "add" or mode == "sub":
            for col in cols:
                self.selectCell(row, col, mode)
        elif mode == "set":
            self.selection = {(row, col) for col in cols}
        elif mode == "toggle":
            _logger.warning("TOGGLE ROW UNIMPLEMENTED")
        self.refreshSelectors()

    # def boxSelect(self, row: int)

    # def setMatrixRow(self, row: int):
    #     program.p.currentPatternRow = 0
    #     program.p.currentMatrixRow = row

    # def toggleRowHighlight(self, row: int):
    #     if row in program.p.currentSong.highlightedMatrixRows:
    #         program.p.currentSong.highlightedMatrixRows.remove(row)
    #     else:
    #         program.p.currentSong.highlightedMatrixRows.add(row)

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

    def refresh(self):
        self.resetRefreshFlag()
        self.rebuild()
        self.refreshSelectors()

    def refreshSelectors(self):
        for sel in self.__selectors.values():
            sel.refresh()

    def rebuild(self):
        """Add/remove labels as needed."""

        currentRows = len(self.__rowLabels)
        currentCols = len(self.__colLabels)
        rows = program.p.currentSong.visibleMatrixRows
        cols = program.p.currentSong.visibleChannels + 1

        # Row Labels
        if rows > currentRows:  # Need more
            _logger.debug("Need more matrix rows")
            for row in range(currentRows, rows):
                label = ttk.Label(self.__grid, text=hex(row)[2:].upper(), width=3)
                pos = self.gridPosition(row, 0, "row label")
                label.grid(row=pos[0], column=pos[1])
                self.__rowLabels.append(label)

                def b(row: int):
                    def c():
                        program.p.currentMatrixRow = row

                    label.bind("<Button-1>", lambda *_: c())

                b(row)
                _logger.debug(row)
        elif rows < currentRows:  # Need less
            for row in range(currentRows, rows, -1):
                label = self.__rowLabels.pop()
                label.destroy()
                _logger.debug(row)

        # Column Labels
        if cols > currentCols:  # Need more
            _logger.debug("Need more matrix cols")
            for col in range(currentCols, cols):
                label = ttk.Label(self.__grid, text=CHANNEL_ORDER[col] + 1, width=3)
                pos = self.gridPosition(0, col, "column label")
                label.grid(row=pos[0], column=pos[1])
                self.__colLabels.append(label)
                _logger.debug(col)
        elif cols < currentCols:  # Need less
            for col in range(currentCols, cols, -1):
                label = self.__colLabels.pop()
                label.destroy()
                _logger.debug(col)

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
                        _logger.debug(f"Adding selector at <{row}, {col}>")
                else:
                    # We don't want a selector here
                    if (row, col) in self.__selectors:
                        # Get rid of it
                        selector = self.__selectors[row, col]
                        selector.destroy()
                        del self.__selectors[row, col]
                        _logger.debug(f"Removing selector at <{row}, {col}>")
