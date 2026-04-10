import tkinter as tk
from abc import ABC, abstractmethod
from enum import Enum
from tkinter import ttk

from interface.utilities.validatedEntry import ValidatedEntry, Validators
from utils.event import Event

_BIG_NUM = (
    2**63
)  # Arbitrary, does python have a 'Number that is greater than all others' like Lua's math.huge?


class AbstractPrebuilt[T](ABC):
    """Abstract class for prebuilt entries."""

    vEntry: ValidatedEntry

    @property
    @abstractmethod
    def value(self) -> T: ...
    @value.setter
    @abstractmethod
    def value(self, val: T): ...

    Changed: Event[bool]
    Error: Event[bool]


class Prebuilts:
    """Prebuilt specialized entries."""

    class Spinbox(AbstractPrebuilt):
        """Number input with min/max and rounding."""

        def __init__(
            self,
            parent: tk.Misc,
            *,
            default: float | None = None,
            range: tuple[float, float] | None = None,
            increment: float = 1,
            round: float | None = None,
            integer: bool = False,
        ):
            min = range[0] if range is not None else None
            max = range[1] if range is not None else None

            if default is None:
                if min is not None:
                    default = min
                elif max is not None:
                    default = max
                else:
                    default = 0

            self.entry = ttk.Spinbox(
                parent, from_=min or -_BIG_NUM, to=max or _BIG_NUM, increment=increment
            )
            self.entry.set(default)

            self.vEntry = ValidatedEntry(
                self.entry, Validators.Numeric(min, max, round=round, integer=integer)
            )

            self.Changed = self.vEntry.Changed
            self.Error = self.vEntry.Error

        @property
        def value(self) -> float:
            return float(self.vEntry.value)

        @value.setter
        def value(self, val: float):
            self.vEntry.value = str(val)

    class Enum[T: Enum](AbstractPrebuilt):
        """Select from an enum."""

        def __init__(
            self,
            parent: tk.Misc,
            enum: type[T],
            *,
            default: T | None = None,
        ):
            values = [item.name for item in enum]
            self.enum = enum

            self.entry = ttk.Combobox(parent, values=values)
            self.entry.config(state="readonly")
            self.entry.set(default or values[0])

            self.vEntry = ValidatedEntry(self.entry, Validators.List(values))

            self.Changed = self.vEntry.Changed
            self.Error = self.vEntry.Error

        @property
        def value(self) -> T:
            return self.enum[self.vEntry.value]

        @value.setter
        def value(self, val: T):
            self.vEntry.value = val.name

    class List(AbstractPrebuilt):
        """Select from a list."""

        def __init__(
            self,
            parent: tk.Misc,
            items: list[str],
            *,
            default: str | None = None,
        ):
            self.items = items

            self.entry = ttk.Combobox(parent, values=items)
            self.entry.config(state="readonly")
            self.entry.set(default or items[0])

            self.vEntry = ValidatedEntry(self.entry, Validators.List(items))

            self.Changed = self.vEntry.Changed
            self.Error = self.vEntry.Error

        @property
        def value(self) -> str:
            return self.vEntry.value

        @value.setter
        def value(self, val: str):
            self.vEntry.value = val
