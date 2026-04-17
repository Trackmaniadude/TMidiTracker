import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Callable

from utils.event import Event

ValidateableEntry = tk.Entry | tk.Spinbox | ttk.Entry | ttk.Spinbox | ttk.Combobox
ValidatorFunc = Callable[[str], str | None]


class AbstractValidator(ABC):
    """Abstract class for validators."""

    @abstractmethod
    def validate(self, s: str) -> str | None: ...


class Validators:
    """Collection of validators."""

    class Through(AbstractValidator):
        """Does nothing."""

        def validate(self, s: str) -> str | None:
            return s

    class Function(AbstractValidator):
        """Uses an arbitrary function (if you don't want to make a new validator class)"""

        def __init__(self, func: ValidatorFunc) -> None:
            self.func: ValidatorFunc = func

        def validate(self, s: str) -> str | None:
            return self.func(s)

    class Numeric(AbstractValidator):
        """Requires the entry to be numerical, as well as limits on the number."""

        def __init__(
            self,
            min: float | None = None,
            max: float | None = None,
            *,
            round: float | None = None,
            integer: bool = False,
        ) -> None:
            self.min = min
            self.max = max
            self.round = round
            self.integer = integer

        def validate(self, s: str) -> str | None:
            try:
                v = float(s)
                if self.round:
                    v = round(v / self.round) * self.round
                if self.min is not None:
                    v = max(v, self.min)
                if self.max is not None:
                    v = min(v, self.max)
                return str(int(v)) if self.integer else str(v)
            except:
                return None

    class List(AbstractValidator):
        """Requires the entry to be a member of a list."""

        def __init__(self, values: list[str]) -> None:
            self.values = set(values)

        def validate(self, s: str) -> str | None:
            if s in self.values:
                return s
            return None


class ValidatedEntry[Entry: ValidateableEntry]:
    """Entry wrapper which adds validation logic, as well as some other niceties."""

    def __init__(self, entry: Entry, validator: AbstractValidator) -> None:
        self.__var = tk.StringVar(entry, entry.get())
        self.__validator = validator
        self.__value = self.__var.get()

        def _v(*_):
            val = self.__validator.validate(self.__var.get())
            if val:  # Success
                self.__var.set(val)  # Always set value
                # Otherwise, if an invalid value is entered and then corrected to the current value,
                # the invalid value will be left displaying (even though its correct internally)
                if val != self.__value:  # Don't fire if no actual change happened
                    self.__value = val
                    self.Changed.fire(True)
            else:  # Failure
                self.__var.set(self.__value)
                self.Error.fire(True)

        entry.bind("<Return>", _v)
        entry.bind("<FocusOut>", _v)
        entry.bind("<<ComboboxSelected>>", _v)
        entry.bind("<<Increment>>", _v)
        entry.bind("<<Decrement>>", _v)
        entry.config(textvariable=self.__var)
        self.entry = entry

        self.Changed: Event[[bool]] = Event(f"{self.__class__.__name__}.Changed")
        """Fired on a successful change to the variable. Provides one bool, if the event was caused by user input."""
        self.Error: Event[[bool]] = Event(f"{self.__class__.__name__}.Error")
        """Fired on an unsuccessful change to the variable. Provides one bool, if the event was caused by user input."""

    def get(self) -> str:
        return self.__value

    def set(self, s: str, *, ignoreValidation: bool = False):
        val = self.__validator.validate(s) if not ignoreValidation else s
        if val:  # Success
            if val != self.__value:  # Don't fire if no actual change happened
                self.__value = val
                self.__var.set(val)
                self.Changed.fire(False)
        else:  # Failure
            self.Error.fire(False)

    @property
    def value(self) -> str:
        return self.get()

    @value.setter
    def value(self, s: str):
        self.set(s)
