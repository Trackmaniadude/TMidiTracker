"""
Multi axis scrolling frame
"""

import tkinter as tk
from collections import namedtuple
from tkinter import ttk
from typing import Literal

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from utils.event import Event
from utils.misc import mapRange

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
    ):
        super().__init__(parent, width=0, height=0)

        self.isHorizontal = mode == "DOUBLE" or mode == "HORIZONTAL"
        self.isVertical = mode == "DOUBLE" or mode == "VERTICAL"
        self.propagationMode = propagationMode

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

        if self.propagationMode != "frameDrivesContent":
            self.content.bind("<Configure>", lambda *_: self.moveCanvas())
        self.bind("<Configure>", lambda *_: self.moveCanvas())

    SCROLLBAR_WIDTH = 16
    SCROLLBAR_HEIGHT = SCROLLBAR_WIDTH

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

            if not self.isVertical:
                if self.propagationMode == "contentDrivesFrame":
                    self.pack_propagate(False)
                    self.grid_propagate(False)
                    self.config(
                        width=self.content.winfo_height() + self.SCROLLBAR_HEIGHT
                    )
                elif self.propagationMode == "frameDrivesContent":
                    # self.pack_propagate(False)
                    # self.grid_propagate(False)
                    # self.content.config(width=50)
                    pass

        if self.isVertical:
            self.__vertical.set(
                mapRange(bbox.y1, bbox.y2, 0, 1, view.y1),
                mapRange(bbox.y1, bbox.y2, 0, 1, view.y2),
            )

            if not self.isHorizontal:
                if self.propagationMode == "contentDrivesFrame":
                    self.pack_propagate(False)
                    self.grid_propagate(False)
                    self.config(width=self.content.winfo_width() + self.SCROLLBAR_WIDTH)
                elif self.propagationMode == "frameDrivesContent":
                    # self.content.pack_propagate(False)
                    # self.content.grid_propagate(False)
                    # self.content.config(width=self.winfo_width() - self.SCROLLBAR_WIDTH)
                    pass


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
                width=50 if self.wide else 10, text="WIDE" if self.wide else "thin"
            )

    root = tk.Tk()
    root.title("TEST")
    root.geometry("400x400")

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

    root.mainloop()
