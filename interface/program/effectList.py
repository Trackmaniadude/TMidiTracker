import tkinter as tk
from tkinter import ttk

from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.headerFrame import HeaderFrame
from structures.effects import AbstractEffect, EffectCategory, Effects


class EffectCategoryDisplay(ttk.Frame):
    def __init__(self, parent: tk.Misc, category: type[EffectCategory]):
        super().__init__(parent)
        self.config(relief="raised", borderwidth=2)

        frame = HeaderFrame(self, category.__name__, userCollapsible=True)
        frame.separator.pack_forget()
        frame.pack(side="top", fill="x", expand=True)

        for childClass in category.__dict__.values():
            if isinstance(childClass, type):
                if issubclass(childClass, EffectCategory):
                    f = EffectCategoryDisplay(frame.content, childClass)
                    f.pack(side="top", fill="x")
                elif issubclass(childClass, AbstractEffect):
                    f = EffectDisplay(frame.content, childClass)
                    f.pack(side="top", fill="x")


class EffectDisplay(ttk.Frame):
    def __init__(self, parent: tk.Misc, effect: type[AbstractEffect]):
        super().__init__(parent)
        self.config(relief="ridge", borderwidth=4)

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
        ttk.Label(self, text=effect.help, wraplength=260).pack(side="top", fill="x")


class EffectList(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.config(relief="raised", width=300, height=200, borderwidth=2)
        self.pack_propagate(False)

        sf = DScrollFrame(self, mode="VERTICAL", propagationMode="frameDrivesContent")
        sf.pack(fill="both", expand=True)

        self.__content = sf.content
        self.__content.configure(width=280, height=2000)

        for childClass in Effects.__dict__.values():
            if isinstance(childClass, type):
                if issubclass(childClass, EffectCategory):
                    f = EffectCategoryDisplay(sf.content, childClass)
                    f.pack(side="top", fill="x")
                elif issubclass(childClass, AbstractEffect):
                    f = EffectDisplay(sf.content, childClass)
                    f.pack(side="top", fill="x")

        # for effect in AbstractEffect.__subclasses__():
        #     if type(effect) is type:
        #         if issubclass(effect, AbstractEffect):
        #             f = EffectDisplay(sf.content, effect)
        #             f.pack(side="top", fill="x")
