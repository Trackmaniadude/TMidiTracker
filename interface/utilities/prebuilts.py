"""Smaller common UI elements"""

import tkinter as tk
from itertools import chain
from tkinter import ttk
from typing import Any, Callable


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

    class Toggle(tk.Button):
        def __init__(self, parent: tk.Misc, command: Callable[[]] = lambda: None):
            super().__init__(parent, width=2, borderwidth=2, relief="raised")
            self.__state: bool = False

            def press():
                self.__setstate(not self.__state)
                self.command()

            self.config(command=press)
            self.command: Callable[[], Any] = command

        def __setstate(self, state: bool):
            self.__state = state
            self.config(relief="groove" if self.__state else "raised")

        def getState(self):
            return self.__state

        def setState(self, state: bool):
            self.__state = state


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
