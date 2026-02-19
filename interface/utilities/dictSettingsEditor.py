"""(Ideally) easy to use settings generator for interacting with dicts."""

import logging
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Any, Literal

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface.utilities.headerFrame import HeaderFrame
from interface.utilities.validatedEntry import ValidatedEntry, Validators
from interface.utilities.validatedEntryPrebuilts import AbstractPrebuilt, Prebuilts
from utils.event import Event
from utils.template import Templateable, template


class DSEEntry[T](ttk.Frame, Templateable, ABC):
    @abstractmethod
    def set(self, value: T): ...
    @abstractmethod
    def get(self) -> T: ...

    Changed: Event


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


class DictSettingsEditor(HeaderFrame):
    def __init__(
        self,
        parent: tk.Misc,
        dct: dict,
        label: str = "",
        *,
        autoApply: bool = False,
        makeApplyButtons: bool = False,
    ):
        super().__init__(parent, label, userCollapsible=True)
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
        tLabel.grid(row=row, column=0)

        if entry is None:
            _logger.warning("DictEdit type inference unimplemented!")
            return

        tEntry = entry.instantiate(self.gridFrame)
        tEntry.grid(row=row, column=1)

        self.__entries[key] = tEntry

        def onChange(*a, **kw):
            self.__internalDict[key] = tEntry.get()
            if self.__autoApply:
                self.apply()

        tEntry.Changed.connect(onChange)

    def addSubEditor(self, label: str = "", *, dct: dict | None = None):
        sub = DictSettingsEditor(
            self.gridFrame, self.__dct if dct is None else dct, label
        )
        sub.config(relief="groove", borderwidth=2)
        # sub.collapse()
        sub.grid(row=self.getNewRow(), column=0, columnspan=2, sticky="ew")
        print("sib" + label + str(self.gridFrame.winfo_children()))
        self.__subEditors.append(sub)
        return sub

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

    sf = DScrollFrame(root, mode="VERTICAL", propagationMode="contentDrivesFrame")
    sf.pack(fill="both", expand=True)

    set = DictSettingsEditor(sf.content, testDict, "TEST 1", makeApplyButtons=True)
    set.pack(fill="both", expand=True)

    set.addValueEdit(
        "settingInt", DSEEntries.Integer(min=0, max=16, increment=2, round=4)
    )
    set.addValueEdit(
        "settingFloat", DSEEntries.Float(min=0.5, max=3.5, increment=0.5, round=0.1)
    )

    set.addSubEditor("TEST 2").addSubEditor("TEST 3")
    set.addSubEditor("TEST 4")

    set.Applied.connect(lambda changes: print(changes))
    set.Applied.connect(lambda changes: print(testDict))

    root.mainloop()
