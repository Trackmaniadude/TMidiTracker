"""Modules for data input in DictSettingsEditor"""

import tkinter as tk
from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Any, Literal, cast

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from interface.utilities.validatedEntry import (
    AbstractValidator,
    ValidatedEntry,
    Validators,
)
from interface.utilities.validatedEntryPrebuilts import Prebuilts
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
                integer=True,
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

        def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            height: int = 4,
        ):
            super().__init__(parent)
            self.entry = tk.Text(self, width=0, height=height)
            self.entry.pack(fill="both", expand=True)

            self.Changed = Event(f"{self.__class__.__name__}.Changed")

            self.entry.bind("<FocusOut>", lambda *_: self.Changed.fire())

            # TODO: fancier support

        def set(self, value: str):
            self.entry.replace("0.0", "end", value)

        def get(self) -> str:
            return self.entry.get("0.0", "end")

    @template
    class Folder(DSEEntry[Path]):
        # TODO: re-evaluate usefulness of relativeTo options
        def __init__(
            self,
            parent: tk.Misc | None = None,
            *,
            relativeTo: (
                Path | Literal["base", "normalized", "dynamic"] | None
            ) = "dynamic",
        ):
            super().__init__(parent)

            def choose():
                dir = filedialog.askdirectory()
                if dir == "" or dir == ():
                    return
                self.set(Path(dir))

            self.relativeTo = relativeTo

            # On the usage of Through() - I'd like a Path validator, but turns out validating paths is, well, hard. TODO:
            self.entry = ValidatedEntry(ttk.Entry(self, width=0), Validators.Through())
            self.entry.entry.pack(side="left", fill="both", expand=True)
            # TODO: how to make image work/verify that its working
            self.button = ttk.Button(
                self,
                width=2,
                image=tk.PhotoImage(file="assets/folder.png"),
                command=choose,
            )
            self.button.pack(side="right", fill="none", expand=False)
            self.Changed = self.entry.Changed

        def set(self, value: Path):
            if self.relativeTo is None:
                self.entry.value = str(value)
                return

            if self.relativeTo == "normalized":
                self.entry.value = str(value.resolve())
                return

            if self.relativeTo == "dynamic":
                try:
                    self.entry.value = str(
                        value.absolute().relative_to(Path.cwd().absolute())
                    )
                except ValueError:
                    self.entry.value = str(value.absolute())
                return

            rel = (
                Path.cwd() if self.relativeTo == "base" else cast(Path, self.relativeTo)
            )
            self.entry.value = str(
                value.resolve().relative_to(rel.resolve(), walk_up=True)
            )

        def get(self) -> Path:
            return Path(self.entry.value)

    @template
    class Boolean(DSEEntry[bool]):
        def __init__(
            self,
            parent: tk.Misc | None = None,
        ):
            super().__init__(parent)
            self.variable = tk.BooleanVar(self)
            self.entry = ttk.Checkbutton(
                self, variable=self.variable, command=lambda: self.Changed.fire()
            )
            self.entry.pack(fill="both", expand=True)
            self.Changed = Event[[]]()

        def set(self, value: bool):
            self.variable.set(value)

        def get(self) -> bool:
            return self.variable.get()


if __name__ == "__main__":
    from interface.utilities.dictSettingsEditor import DictSettingsEditor
    from interface.utilities.dictSettingsEditorEntries import (
        DSEEntries,  # For some reason it fails to render without???
    )
    from interface.utilities.doubleScrollFrame import DScrollFrame

    root = tk.Tk()
    root.geometry("400x800")
    root.title("TESTING")

    def focus(event):
        try:
            event.widget.focus_set()
        except AttributeError:
            pass

    root.bind_all("<Button-1>", focus)

    dct = {
        name: None for name, entry in DSEEntries.__dict__.items() if type(entry) is type
    }

    frame = DScrollFrame(root, mode="VERTICAL", propagationMode="frameDrivesContent")
    frame.pack(fill="both", expand=True)

    editor = DictSettingsEditor(
        frame.content, dct, autoApply=True, label="DictSettingsEditorEntries Testing"
    )
    editor.pack(fill="both", expand=True)

    for name, entry in reversed(DSEEntries.__dict__.items()):
        if type(entry) is not type:
            continue
        try:
            editor.addValueEdit(name, entry())
        except Exception as e:
            print(f"{name} failed to init: {e}")

    def onChange(keys):
        for key in keys:
            print(key, dct[key])

    editor.Applied.connect(onChange)

    root.mainloop()
