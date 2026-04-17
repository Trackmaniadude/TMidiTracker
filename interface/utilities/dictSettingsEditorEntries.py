"""Modules for data input in DictSettingsEditor"""

import tkinter as tk
from abc import ABC, abstractmethod
from enum import Enum, auto
from tkinter import ttk

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

        def __init__(self, parent: tk.Misc | None = None, *, height: int = 4):
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
