"""(Ideally) easy to use settings generator for interacting with dicts."""

import logging
import tkinter as tk
from abc import ABC, abstractmethod
from enum import Enum, auto
from tkinter import ttk
from typing import Any, Literal

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface.utilities.headerFrame import HeaderFrame
from interface.utilities.validatedEntry import (
    AbstractValidator,
    ValidatedEntry,
    Validators,
)
from interface.utilities.validatedEntryPrebuilts import AbstractPrebuilt, Prebuilts
from utils.event import Event
from utils.template import Templateable, template


class DSEShape(Enum):
    Normal = auto()
    Large = auto()


class DSEEntry[T](ttk.Frame, Templateable, ABC):
    @abstractmethod
    def set(self, value: T): ...
    @abstractmethod
    def get(self) -> T: ...

    Changed: Event
    Shape: DSEShape = DSEShape.Normal


class DSEEntries:
    @template
    class Float(DSEEntry[float]):
        def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            min: float | None = None,
            max: float | None = None,
            increment: float = 1,
            round: float | None = None,
        ):
            super().__init__(parent)
            self.entry = Prebuilts.Spinbox(
                self,
                range=None if min is None or max is None else (min, max),
                increment=increment,
                round=round,
            )
            self.entry.entry.pack(fill="both", expand=True)
            self.Changed = self.entry.Changed

        def set(self, value: float):
            self.entry.value = value

        def get(self) -> float:
            return self.entry.value

    @template
    class Integer(DSEEntry[int]):
        def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            min: int | None = None,
            max: int | None = None,
            increment: int = 1,
            round: int | None = None,
        ):
            super().__init__(parent)
            self.entry = Prebuilts.Spinbox(
                self,
                range=None if min is None or max is None else (min, max),
                increment=increment,
                round=round,
            )
            self.entry.entry.pack(fill="both", expand=True)
            self.Changed = self.entry.Changed

        def set(self, value: int):
            self.entry.value = value

        def get(self) -> int:
            return int(self.entry.value)

    @template
    class List(DSEEntry[str]):
        def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            values: list[str],
        ):
            super().__init__(parent)
            self.entry = Prebuilts.List(self, values)
            self.entry.entry.pack(fill="both", expand=True)
            self.entry.entry.config(width=0)
            self.Changed = self.entry.Changed

        def set(self, value: str):
            self.entry.value = value

        def get(self) -> str:
            return str(self.entry.value)

    @template
    class SmallTextbox(DSEEntry[str]):
        def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            validator: AbstractValidator = Validators.Through(),
        ):
            super().__init__(parent)
            self.entry = ValidatedEntry(ttk.Entry(self, width=0), validator)
            self.entry.entry.pack(fill="both", expand=True)
            self.Changed = self.entry.Changed

        def set(self, value: str):
            self.entry.value = value

        def get(self) -> str:
            return str(self.entry.value)

    @template
    class LargeTextbox(DSEEntry[str]):
        Shape = DSEShape.Large

        def __init__(self, parent: tk.Misc | None = None, *, height: int = 4):
            super().__init__(parent)
            self.entry = tk.Text(self, width=0, height=height)
            self.entry.pack(fill="both", expand=True)

            self.Changed = Event()

            self.entry.bind("<FocusOut>", lambda *_: self.Changed.fire())

            # TODO: fancier support

        def set(self, value: str):
            self.entry.replace("0.0", "end", value)

        def get(self) -> str:
            return self.entry.get("0.0", "end")


class DictSettingsEditor(HeaderFrame):
    """Simple way to construct a settings dialog interfacing with a dictionary."""

    def __init__(
        self,
        parent: tk.Misc,
        dct: dict,
        label: str = "",
        *,
        autoApply: bool = False,
        makeApplyButtons: bool = False,
        collapsible: bool = False,
    ):
        super().__init__(parent, label, userCollapsible=collapsible)
        self.__autoApply = autoApply
        self.__dct = dct
        self.__internalDict = self.__dct.copy()

        self.Applied: Event[list[str]] = Event()
        """Fired when changes are applied. Contains a list of all keys that changed."""

        self.__row = 0

        self.__subEditors: list[DictSettingsEditor] = list()
        self.__entries: dict[str, DSEEntry] = dict()

        self.gridFrame = ttk.Frame(self.content)
        self.gridFrame.pack(side="top", fill="both", expand=True)

        if makeApplyButtons:
            frame = ttk.Frame(self.content)
            frame.pack(side="top", fill="both")
            revert = ttk.Button(frame, text="Revert", command=self.revert)
            revert.pack(side="left", fill="both", expand=True)
            apply = ttk.Button(frame, text="Apply", command=self.apply)
            apply.pack(side="left", fill="both", expand=True)

    def getNewRow(self) -> int:
        """Internal helper to make keeping track of grid rows easier."""
        row = self.__row
        self.__row += 1
        return row

    def addValueEdit(
        self, key: str, entry: DSEEntry | None = None, label: str | None = None
    ):
        """Add a value edit. Leaving the entry empty will try to auto infer from type."""
        if label is None:
            label = key

        row = self.getNewRow()

        tLabel = ttk.Label(self.gridFrame, text=label)

        if entry is None:
            _logger.warning("DictEdit type inference unimplemented!")
            return

        tEntry = entry.instantiate(self.gridFrame)

        # Place entry items
        if tEntry.Shape == DSEShape.Normal:
            tLabel.grid(row=row, column=0, sticky="nesw")
            tEntry.grid(row=row, column=1, sticky="nesw")
        elif tEntry.Shape == DSEShape.Large:
            tLabel.grid(row=row, column=0, columnspan=2, sticky="nesw")
            tEntry.grid(row=self.getNewRow(), column=0, columnspan=2, sticky="nesw")

        # TODO: put in a better location
        self.gridFrame.columnconfigure(0, pad=4)
        self.gridFrame.columnconfigure(1, weight=1)

        self.__entries[key] = tEntry

        def onChange(*a, **kw):
            self.__internalDict[key] = tEntry.get()
            if self.__autoApply:
                self.apply()

        tEntry.Changed.connect(onChange)

        # Load in value
        tEntry.set(self.__internalDict[key])

    def addSubEditor(self, label: str = "", *, dct: dict | None = None):
        """Add a labeled subframe."""
        sub = DictSettingsEditor(
            self.gridFrame,
            self.__dct if dct is None else dct,
            label,
            autoApply=self.__autoApply,
            makeApplyButtons=False,
            collapsible=True,
        )
        sub.config(relief="groove", borderwidth=2)
        sub.grid(row=self.getNewRow(), column=0, columnspan=2, sticky="ew")
        self.__subEditors.append(sub)
        return sub

    def addTextbox(self, text: str):
        """Add a textbox."""
        box = ttk.Label(self.gridFrame, text=text, width=0)
        box.grid(row=self.getNewRow(), column=0, columnspan=2, sticky="ew")
        box.config(wraplength=0)
        # TODO: what conditions causes this to break on startup
        box.bind(
            "<Configure>",
            lambda *_: box.config(wraplength=box.winfo_width() - 5),
        )

    def addSeparator(self):
        """Add a horizontal line."""
        ttk.Separator(self.gridFrame, orient="horizontal").grid(
            row=self.getNewRow(), column=0, columnspan=2, sticky="nesw"
        )

    def apply(self):
        """Copy changes to target dict."""
        self.Applied.fire(self._apply())

    def _apply(self) -> list[str]:
        """Do actual apply, return changed fields."""
        changes: list[str] = list()
        # Apply
        for key, entry in self.__entries.items():
            if self.__dct[key] == self.__internalDict[key]:
                continue
            self.__dct[key] = self.__internalDict[key]
            changes.append(key)

        # Apply to subs
        for sub in self.__subEditors:
            changes.extend(sub._apply())
        return changes

    def revert(self):
        """Reload state from target dict."""
        # Revert
        for key, entry in self.__entries.items():
            value = self.__dct[key]
            self.__internalDict[key] = value
            entry.set(value)

        # Revert subs
        for sub in self.__subEditors:
            sub.revert()


if __name__ == "__main__":

    from interface.utilities.doubleScrollFrame import DScrollFrame

    testDict = {
        "settingInt": 0,
        "settingFloat": 0.5,
        "settingBool": True,
        "settingList": "the j",
        "settingSmallText1": "the j",
        "settingSmallText2": "jhe t",
        "settingLargeText": "engineer gaming",
    }

    root = tk.Tk()
    root.title("TEST")
    root.geometry("300x500")

    def focus(event):
        try:
            event.widget.focus_set()
        except AttributeError:
            pass

    root.bind_all("<Button-1>", focus)

    sf = DScrollFrame(root, mode="VERTICAL", propagationMode="frameDrivesContent")
    sf.pack(fill="both", expand=True)

    # set = DictSettingsEditor(sf.content, testDict, "TEST 1", makeApplyButtons=True)
    set = DictSettingsEditor(
        sf.content, testDict, "TEST 1", autoApply=True, makeApplyButtons=True
    )
    set.pack(fill="both", expand=True)

    set.addValueEdit(
        "settingInt", DSEEntries.Integer(min=0, max=16, increment=2, round=4)
    )
    set.addValueEdit(
        "settingFloat", DSEEntries.Float(min=0.5, max=3.5, increment=0.5, round=0.1)
    )

    set.addTextbox(
        "BIG OL TEXTBOX aelt erjtrht s rthgjkser dhgjksr hgjklreshkgjdd hxkfkghkjhgkheskgrh djkg jkshgjk sgjks \nthej \n\nthej #2"
    )
    set.addSeparator()
    set.addTextbox("the j #3333")

    set.addSubEditor("TEST 2").addSubEditor("TEST 3")
    q = set.addSubEditor("TEST 4")

    q.addValueEdit(
        "settingList",
        DSEEntries.List(values=["the j", "bargain bin basement burger", "quenth"]),
    )
    q.addValueEdit("settingSmallText1", DSEEntries.SmallTextbox())
    q.addValueEdit("settingSmallText2", DSEEntries.SmallTextbox())
    q.addValueEdit("settingLargeText", DSEEntries.LargeTextbox())

    set.Applied.connect(lambda changes: print(changes))
    set.Applied.connect(lambda changes: print(testDict))

    root.mainloop()
