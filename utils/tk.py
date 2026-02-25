"""
Docstring for utils.tk
"""

if __name__ == "__main__":
    import sys

    sys.path.append(".")

import tkinter as tk
from tkinter import ttk
from typing import Callable, cast

from utils.event import Event


class SPECIAL_CHARS:
    ARROW_DOWN = "▼"
    ARROW_UP = "▲"


DEF_PAD = 2


def widgetUnderCursor(widget: tk.Misc):
    root = widget.winfo_toplevel()
    x, y = root.winfo_pointerxy()
    return root.winfo_containing(x, y)


def bindOnSizeChange(widget: tk.Misc, callback: Callable[[], None]):
    lastWidth = widget.winfo_width()
    lastHeight = widget.winfo_height()

    def _callback(*_):
        nonlocal lastWidth, lastHeight
        currentWidth = widget.winfo_width()
        currentHeight = widget.winfo_height()
        if currentWidth != lastWidth or currentHeight != lastHeight:
            lastWidth = currentWidth
            lastHeight = currentHeight
            callback()

    widget.bind("<Configure>", _callback, add=True)


tkvar = tk.StringVar | tk.IntVar | tk.BooleanVar | tk.DoubleVar
tkvart = str | int | bool | float


class TKVar[V: tkvar, VT: tkvart]:
    """Tk variable wrapper that uses a mirror value to detect changes coming from the interface."""

    def __init__(self, var: V, default: VT) -> None:
        self.var: V = var
        self.__mirror: VT = default

        self.var.trace_add("write", lambda *_: self.__trace())

        self.Changed: Event[[]] = Event()
        self.ChangedUser: Event[[]] = Event()

    def __trace(self):
        actual = cast(VT, self.var.get())
        if self.__mirror != actual:
            self.__mirror = actual
            self.ChangedUser.fire()
        self.Changed.fire()

    def set(self, v: VT):
        self.__mirror = v
        self.var.set(v)  # pyright: ignore[reportArgumentType]

    def get(self) -> VT:
        return self.var.get()  # pyright: ignore[reportReturnType]


if __name__ == "__main__":
    root = tk.Tk()

    a = TKVar(tk.BooleanVar(), True)
    aa = a.get()
    b = TKVar(tk.StringVar(), "")
    bb = a.get()
