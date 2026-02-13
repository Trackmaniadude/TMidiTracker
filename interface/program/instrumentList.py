import tkinter as tk
from tkinter import ttk

from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.headerFrame import HeaderFrame
from utils.gm import GMDrumKits, GMEntry, GMPrograms


def toHex2D(n: int) -> str:
    s = hex(n)[2:].upper()
    if n < 16:
        return "0" + s
    else:
        return s


class InstrumentList(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.config(relief="raised", width=280, height=20, borderwidth=2)

        sf = DScrollFrame(self, mode="VERTICAL")
        sf.pack(fill="both", expand=True)

        self.pack_propagate(False)

        self.__content = sf.content
        self.__content.configure(width=20, height=20)

        categories: dict[str, list[tuple[int, str]]] = dict()

        def process(cls: type):
            for _, v in cls.__dict__.items():
                if isinstance(v, GMEntry):
                    if v.category not in categories:
                        categories[v.category] = list()
                    categories[v.category].append((v.value, v.name))

        process(GMPrograms)
        process(GMDrumKits)

        for category, data in categories.items():
            mn = min([t[0] for t in data]) - 1
            mx = max([t[0] for t in data]) - 1
            hf = HeaderFrame(
                sf.content,
                f"{category} {toHex2D(mn)} - {toHex2D(mx)}",
                userCollapsible=True,
            )
            hf.collapse()
            hf.pack(side="top", fill="x")
            for entry in data:
                value = entry[0]
                name = entry[1]
                ttk.Label(hf.content, text=f"{toHex2D(value - 1)}: {name}").pack(
                    side="top", fill="x"
                )
