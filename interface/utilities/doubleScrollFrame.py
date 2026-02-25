"""
Multi axis scrolling frame
"""

import logging
import tkinter as tk
from collections import namedtuple
from tkinter import ttk
from typing import Literal

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from utils.misc import clamp, mapRange
from utils.tk import widgetUnderCursor

BBox = namedtuple("BBox", ["x1", "y1", "x2", "y2"])


class DScrollFrame(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        mode: Literal["VERTICAL", "HORIZONTAL", "DOUBLE"],
        propagationMode: Literal[
            "off", "contentDrivesFrame", "frameDrivesContent"
        ] = "off",
        createScrollBindings: bool = True,
    ):
        super().__init__(parent, width=0, height=0)

        self.isHorizontal = mode == "DOUBLE" or mode == "HORIZONTAL"
        self.isVertical = mode == "DOUBLE" or mode == "VERTICAL"
        self.propagationMode = propagationMode

        self.inWindow: bool = False

        self.typeBlockList: set[str] = {"TSpinbox"}
        """Block wheel bindings when over widgets of these types."""
        self.widgetBlockList: set[tk.Widget] = set()
        """Block wheel bindings when over these widgets."""
        self.widgetNameBlockList: set[str] = set()
        """Block wheel bindings when over widgets matching the filter."""

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

        # Bindings
        if createScrollBindings:
            self.bind("<Enter>", lambda *_: setattr(self, "inWindow", True))
            self.bind("<Leave>", lambda *_: setattr(self, "inWindow", False))
            root = self.winfo_toplevel()

            def allowScroll():
                if not self.inWindow:
                    return False
                w = widgetUnderCursor(self)
                if w is None:
                    return True
                if w.winfo_class() in self.typeBlockList:
                    return False
                if w in self.widgetBlockList:
                    return False
                for s in self.widgetNameBlockList:
                    if w.winfo_name().find(s) != -1:
                        return False
                return True

            if self.isVertical:
                root.bind(
                    "<MouseWheel>",
                    lambda e: self.scroll("y", -e.delta) if allowScroll() else None,
                    "+",
                )
                root.bind(
                    "<Button-4>",
                    lambda *_: self.scroll("y", -1) if allowScroll() else None,
                    "+",
                )
                root.bind(
                    "<Button-5>",
                    lambda *_: self.scroll("y", 1) if allowScroll() else None,
                    "+",
                )

            if self.isHorizontal:
                root.bind(
                    "<Shift-MouseWheel>",
                    lambda e: self.scroll("x", -e.delta) if allowScroll() else None,
                    "+",
                )
                root.bind(
                    "<Shift-Button-4>",
                    lambda *_: self.scroll("x", -1) if allowScroll() else None,
                    "+",
                )
                root.bind(
                    "<Shift-Button-5>",
                    lambda *_: self.scroll("x", 1) if allowScroll() else None,
                    "+",
                )

        # Propagation
        if self.propagationMode != "frameDrivesContent":
            self.content.bind("<Configure>", lambda *_: self.moveCanvas())
        self.bind("<Configure>", lambda *_: self.moveCanvas())

    SCROLL_DISTANCE = 8  # TODO: what should this be
    SCROLLBAR_WIDTH = 16
    SCROLLBAR_HEIGHT = SCROLLBAR_WIDTH

    def scroll(self, axis: Literal["x", "y"], direction: int):
        direction = -1 if direction < 0 else 1

        bbox = BBox(*self.__canvas.bbox(self.__windowId))

        if axis == "x":
            self.__x += (
                self.SCROLL_DISTANCE * direction * (self.SCROLL_DISTANCE / bbox.x2)
            )
        elif axis == "y":
            self.__y += (
                self.SCROLL_DISTANCE * direction * (self.SCROLL_DISTANCE / bbox.y2)
            )

        self.moveCanvas()

    def moveCanvas(self):
        # Move canvas
        bbox = BBox(*self.__canvas.bbox(self.__windowId))
        newx = clamp(self.__x * bbox.x2, bbox.x2 - self.winfo_width(), 0)
        newy = clamp(self.__y * bbox.y2, bbox.y2 - self.winfo_height(), 0)
        self.__x = newx / bbox.x2
        self.__y = newy / bbox.y2
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

            if not self.isVertical:
                if self.propagationMode == "contentDrivesFrame":
                    # TODO: this probably shouldn't be here
                    self.pack_propagate(False)
                    self.grid_propagate(False)
                    self.config(
                        height=self.content.winfo_height() + self.SCROLLBAR_HEIGHT
                    )
                elif self.propagationMode == "frameDrivesContent":
                    # TODO: this probably shouldn't be here
                    self.content.pack_propagate(False)
                    self.content.grid_propagate(False)
                    width = sum(
                        child.winfo_width() for child in self.content.winfo_children()
                    )
                    self.content.config(
                        width=width,
                        height=self.content.winfo_height() - self.SCROLLBAR_HEIGHT,
                    )

        if self.isVertical:
            self.__vertical.set(
                mapRange(bbox.y1, bbox.y2, 0, 1, view.y1),
                mapRange(bbox.y1, bbox.y2, 0, 1, view.y2),
            )

            if not self.isHorizontal:
                if self.propagationMode == "contentDrivesFrame":
                    # TODO: this probably shouldn't be here
                    self.pack_propagate(False)
                    self.grid_propagate(False)
                    self.config(width=self.content.winfo_width() + self.SCROLLBAR_WIDTH)
                elif self.propagationMode == "frameDrivesContent":
                    # TODO: this probably shouldn't be here
                    self.content.pack_propagate(False)
                    self.content.grid_propagate(False)
                    height = sum(
                        child.winfo_height() for child in self.content.winfo_children()
                    )
                    self.content.config(
                        width=self.winfo_width() - self.SCROLLBAR_WIDTH, height=height
                    )


if __name__ == "__main__":

    class Wide(tk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(
                parent, command=lambda *_: self.widen(), relief="groove", borderwidth=2
            )
            self.wide = True
            self.widen()

        def widen(self):
            self.wide = not self.wide
            self.config(
                width=50 if self.wide else 10,
                text="W   I   D   E" if self.wide else "thin",
            )

    root = tk.Tk()
    root.title("TEST")
    root.geometry("400x400")

    root.bind_all("<Button-1>", lambda e: print(e.widget.winfo_class()))

    a = ttk.Frame(root, relief="groove", borderwidth=2)
    a.grid(row=0, column=0, sticky="nesw")

    a1 = ttk.Frame(a, relief="groove", borderwidth=2)
    a1.pack(side="left", fill="both")
    a2 = ttk.Frame(a, relief="groove", borderwidth=2)
    a2.pack(side="left", fill="both", expand=True)
    Wide(a1).pack()
    ttk.Label(a2, width=25, text="LABEL", relief="groove", borderwidth=2).pack(
        fill="x", expand=True
    )

    b = ttk.Frame(root, relief="groove", borderwidth=2)
    b.grid(row=1, column=0, sticky="nesw")

    b1 = DScrollFrame(b, mode="VERTICAL", propagationMode="contentDrivesFrame")
    b2 = DScrollFrame(b, mode="VERTICAL", propagationMode="frameDrivesContent")
    b1.pack(side="left", fill="both")
    b2.pack(side="left", fill="both", expand=True)
    Wide(b1.content).pack(
        side="top",
    )
    Wide(b2.content).pack(
        side="top",
    )
    for i in range(16):
        ttk.Label(
            b1.content, width=25, text=f"LABEL #{i}", relief="groove", borderwidth=2
        ).pack(
            side="top",
        )
        ttk.Label(
            b2.content, width=25, text=f"LABEL #{i}", relief="groove", borderwidth=2
        ).pack(side="top", fill="x", expand=True)

    # z = ttk.Frame(root, relief="raised", borderwidth=2)
    # z.grid(row=0, column=1, sticky="nesw")

    # a = DScrollFrame(root, mode="HORIZONTAL")
    # a.config(relief="raised", borderwidth=2)
    # a.grid(row=0, column=1, sticky="nesw")

    # b = DScrollFrame(root, mode="VERTICAL")
    # b.config(relief="raised", borderwidth=2)
    # b.grid(row=1, column=0, sticky="nesw")

    # c = DScrollFrame(root, mode="DOUBLE")
    # c.config(relief="raised", borderwidth=2)
    # c.grid(row=1, column=1, sticky="nesw")

    root.columnconfigure(0, weight=1)
    # root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=1)

    big = DScrollFrame(root, mode="DOUBLE", propagationMode="off")
    for r in range(8):
        for c in range(24):
            if (r == 1 or c == 3) and not (r == 1 and c == 3):
                ttk.Spinbox(big.content, width=0, to=3000, from_=-3000).grid(
                    row=r, column=c, sticky="we"
                )
            else:
                ttk.Label(big.content, text=f"  [ {r}: {c} ]  ").grid(row=r, column=c)
    big.grid(row=10, column=0, columnspan=2, sticky="nesw")

    root.mainloop()
