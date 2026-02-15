"""Smaller common UI elements"""

import tkinter as tk
from itertools import chain
from tkinter import ttk


class _AutoTest:
    pass


class Buttons(_AutoTest):
    class Increment(ttk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent, text="+", width=2)

    class Decrement(ttk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent, text="-", width=2)

    class Up(ttk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent, text="▲", width=2)

    class Down(ttk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent, text="▼", width=2)

    class Left(ttk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent, text="◀", width=2)

    class Right(ttk.Button):
        def __init__(self, parent: tk.Misc):
            super().__init__(parent, text="▶", width=2)


if __name__ == "__main__":

    root = tk.Tk()
    root.title("TEST")
    root.geometry("400x400")

    COLS = 4
    SIZE = 100

    # Setup
    classes = chain.from_iterable(
        [v for v in cls.__dict__.values() if isinstance(v, type)]
        for cls in _AutoTest.__subclasses__()
    )
    for i, cls in enumerate(classes):
        if not issubclass(cls, tk.Widget):
            continue
        a = cls(root)  # type: ignore
        a.grid(column=i % COLS, row=i // COLS)

    root.mainloop()
