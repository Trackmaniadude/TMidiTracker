"""
Multi axis scrolling frame
"""

import tkinter as tk
from collections import namedtuple
from tkinter import ttk
from typing import Literal

from utils.event import Event
from utils.misc import mapRange

BBox = namedtuple("BBox", ["x1", "y1", "x2", "y2"])


class DScrollFrame(ttk.Frame):
    def __init__(
        self, parent: tk.Misc, *, mode: Literal["VERTICAL", "HORIZONTAL", "DOUBLE"]
    ):
        super().__init__(parent, width=0, height=0)

        self.isHorizontal = mode == "DOUBLE" or mode == "HORIZONTAL"
        self.isVertical = mode == "DOUBLE" or mode == "VERTICAL"

        # Create elements
        self.__canvas = tk.Canvas(self, highlightthickness=0, width=0, height=0)
        self.__canvas.grid(row=0, column=0, sticky="nesw")

        self.__canvas.scan_mark(0, 0)

        self.__x = 0
        self.__y = 0

        if self.isHorizontal:

            def _(_, v):
                self.__x = float(v)
                self.moveCanvas()

            self.__horizontal = ttk.Scrollbar(self, orient="horizontal", command=_)
            self.__horizontal.grid(row=1, column=0, sticky="we")

        if self.isVertical:

            def _(_, v):
                self.__y = float(v)
                self.moveCanvas()

            self.__vertical = ttk.Scrollbar(self, orient="vertical", command=_)
            self.__vertical.grid(row=0, column=1, sticky="ns")

        # Grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Set up window
        self.content = ttk.Frame(self.__canvas, width=0, height=0)
        self.__windowId = self.__canvas.create_window(
            0, 0, window=self.content, anchor="nw"
        )

        self.content.bind("<Configure>", lambda *_: self.moveCanvas())
        self.bind("<Configure>", lambda *_: self.moveCanvas())

    def moveCanvas(self):
        # Move canvas
        bbox = BBox(*self.__canvas.bbox(self.__windowId))
        newx = max(min(self.__x * bbox.x2, bbox.x2 - self.winfo_width()), 0)
        newy = max(min(self.__y * bbox.y2, bbox.y2 - self.winfo_height()), 0)
        self.__canvas.scan_dragto(-int(newx), -int(newy), gain=1)

        # Update scrollbars
        bbox = BBox(*self.__canvas.bbox(self.__windowId))
        view = BBox(
            self.__canvas.canvasx(0),
            self.__canvas.canvasy(0),
            self.__canvas.canvasx(self.winfo_width()),
            self.__canvas.canvasy(self.winfo_height()),
        )

        if self.isHorizontal:
            self.__horizontal.set(
                mapRange(bbox.x1, bbox.x2, 0, 1, view.x1),
                mapRange(bbox.x1, bbox.x2, 0, 1, view.x2),
            )

        if self.isVertical:
            self.__vertical.set(
                mapRange(bbox.y1, bbox.y2, 0, 1, view.y1),
                mapRange(bbox.y1, bbox.y2, 0, 1, view.y2),
            )
