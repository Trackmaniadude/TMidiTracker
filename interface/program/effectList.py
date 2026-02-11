import tkinter as tk
from tkinter import ttk

from interface.utilities.doubleScrollFrame import DScrollFrame
from structures.effects import AbstractEffect, Effects


class EffectDisplay(ttk.Frame):
    def __init__(self, parent: tk.Misc, effect: type[AbstractEffect]):
        super().__init__(parent)
        self.config(relief="raised", borderwidth=2)

        ttk.Frame(self, width=200).pack(side="top", fill="x")
        ttk.Label(self, text=f"#{effect.prefixString()} - {effect.displayName}").pack(
            side="top", fill="x"
        )
        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")
        ttk.Label(self, text=f"Params: {effect.params[0]}").pack(side="top", fill="x")
        for i in range(1, len(effect.params), 2):
            id = effect.params[i]
            name = effect.params[i + 1]
            ttk.Label(self, text=f"{id} = {name}").pack(side="top", fill="x")
        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")
        ttk.Label(self, text=effect.help).pack(side="top", fill="x")


class EffectList(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.config(relief="raised", width=300, height=200, borderwidth=2)

        sf = DScrollFrame(self, mode="VERTICAL")
        sf.pack(fill="both", expand=True)

        self.pack_propagate(False)

        self.__content = sf.content
        self.__content.configure(width=280, height=2000)

        for _, effect in Effects.__dict__.items():
            if type(effect) is type:
                if issubclass(effect, AbstractEffect):
                    f = EffectDisplay(sf.content, effect)
                    f.pack(side="top", fill="x")
