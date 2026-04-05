"""(Ideally) easy to use settings generator for interacting with dicts."""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface.utilities.dictSettingsEditorEntries import DSEEntry, DSEShape
from interface.utilities.headerFrame import HeaderFrame
from utils.event import Connection, Event


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

        self.connections: list[Connection] = list()

        self.Applied: Event[list[str]] = Event()
        """Fired when changes are applied. Contains a list of all keys that changed."""

        self.__row = 0

        self.__subEditors: list[DictSettingsEditor] = list()
        self.__entries: dict[str, DSEEntry] = dict()

        self.gridFrame = ttk.Frame(self.content)
        self.gridFrame.pack(side="top", fill="both", expand=True)

        self.transforms: dict[
            str, tuple[Callable[[Any], Any], Callable[[Any], Any]]
        ] = dict()

        if makeApplyButtons:
            frame = ttk.Frame(self.content)
            frame.pack(side="top", fill="both")
            revert = ttk.Button(frame, text="Revert", command=self.revert)
            revert.pack(side="left", fill="both", expand=True)
            apply = ttk.Button(frame, text="Apply", command=self.apply)
            apply.pack(side="left", fill="both", expand=True)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    def getNewRow(self) -> int:
        """Internal helper to make keeping track of grid rows easier."""
        row = self.__row
        self.__row += 1
        return row

    def addValueEdit[
        TExt, TInt
    ](
        self,
        key: str,
        entry: DSEEntry | None = None,
        label: str | None = None,
        *,
        transformIn: Callable[[TExt], TInt] = lambda v: v,
        transformOut: Callable[[TInt], TExt] = lambda v: v,
    ):
        """
        Add a value edit. Leaving the entry empty will try to auto infer from type.
        Optional transform functions allow transforming between the display and actual value.
        """
        if label is None:
            label = key

        self.transforms[key] = (transformIn, transformOut)

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
            self.__internalDict[key] = self.transforms[key][1](tEntry.get())
            if self.__autoApply:
                self.apply()

        tEntry.Changed.connect(onChange, self.connections)

        # Load in value
        tEntry.set(self.transforms[key][0](self.__internalDict[key]))

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
            entry.set(self.transforms[key][0](value))

        # Revert subs
        for sub in self.__subEditors:
            sub.revert()

    def rebind(self, dct: dict):
        """Change this editor's target dictionary."""
        self.__dct = dct
        self.__internalDict = self.__dct.copy()
        for sub in self.__subEditors:
            sub.rebind(dct)


if __name__ == "__main__":

    from interface.utilities.dictSettingsEditorEntries import DSEEntries
    from interface.utilities.doubleScrollFrame import DScrollFrame

    testDict = {
        "settingInt": 0,
        "settingFloat": 0.5,
        "settingBool": True,
        "settingList": "the j",
        "settingSmallText1": "the j",
        "settingSmallText2": "jhe t",
        "settingLargeText": "engineer gaming",
        "tfTest": 4,
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
        sf.content, testDict, "TEST 1", autoApply=False, makeApplyButtons=True
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

    qqqq = set.addSubEditor("TEST 2")
    qqqqq = qqqq.addSubEditor("TEST 3")

    qqqqq.addValueEdit(
        "tfTest",
        DSEEntries.Float(),
        "Transform Test",
        transformIn=lambda v: v**2,
        transformOut=lambda v: v**0.5,
    )

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
