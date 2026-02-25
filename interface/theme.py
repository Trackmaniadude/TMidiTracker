from __future__ import annotations

import logging
import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass
from tkinter import ttk
from typing import cast

_logger = logging.getLogger(__name__)


class Style(ABC):
    instances: list[Style] = list()

    def __post_init__(self):
        self.instances.append(self)

    @abstractmethod
    def generate(self, s: ttk.Style): ...

    @classmethod
    def generateAll(cls, s: ttk.Style):
        for instance in cls.instances:
            instance.generate(s)


@dataclass
class StyleDC(Style):
    def __post_init__(self):
        self.name: str = cast(str, None)
        self.owningClass: type = cast(type, None)
        self.base: str = cast(str, None)
        return super().__post_init__()

    def generate(self, s: ttk.Style):
        dct = {field: getattr(self, field) for field in self.__dataclass_fields__}

        trueName = f"{self.owningClass.__name__}{self.name}.{self.base}"

        _logger.debug(f"Generating style '{trueName}': {dct}")
        s.configure(trueName, **dct)

        setattr(self.owningClass, self.name, trueName)


@dataclass
class BasicColor(StyleDC):
    background: str = "white"
    foreground: str = "black"


def StyleBase(base: str):
    def inner(cls):
        for name in dir(cls):
            obj = getattr(cls, name)
            if isinstance(obj, StyleDC):
                obj.name = name
                obj.base = base
                obj.owningClass = cls
        return cls

    return inner


# Colormap
class Colors:
    class BG:
        Default = "#FFFFFF"
        Shade1 = "#EEEEEE"
        Shade2 = "#CCCCCC"

    class Target:
        Default = "#DDDDFF"
        Shade1 = "#CCCCEE"
        Shade2 = "#AAAACC"

    class Select:
        Default = "#0044CC"

    class Highlight:
        Default = "#FFFFCC"


# Styles
@StyleBase("TLabel")
class Note:
    Default = BasicColor(Colors.BG.Default)
    Minor = BasicColor(Colors.BG.Shade1)
    Major = BasicColor(Colors.BG.Shade2)
    DefaultTarget = BasicColor(Colors.Target.Default)
    MinorTarget = BasicColor(Colors.Target.Shade1)
    MajorTarget = BasicColor(Colors.Target.Shade2)


@StyleBase("TLabel")
class MatrixSelector:
    DefaultEven = BasicColor(Colors.BG.Default)
    DefaultOdd = BasicColor(Colors.BG.Shade1)
    Target1 = BasicColor(Colors.Target.Default)
    Target2 = BasicColor(Colors.Target.Shade1)
    TargetAnchor = BasicColor(Colors.Target.Shade2)
    Highlight = BasicColor(Colors.Highlight.Default)
    Selection = BasicColor(Colors.Select.Default)


def generate():
    s = ttk.Style()
    # s.theme_use("clam")

    s.configure(".", font=("TkFixedFont", 10))

    Style.generateAll(s)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(Note.__dict__)
    generate()
    print(Note.__dict__)
    # print(s.theme_names())
