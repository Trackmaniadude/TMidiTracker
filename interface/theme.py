from __future__ import annotations

import logging
import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass
from tkinter import ttk
from typing import Literal, cast

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


@dataclass
class BasicColorBorder(BasicColor):
    borderwidth: int = 0
    relief: Literal["flat", "groove", "raised", "ridge", "solid", "sunken"] = "flat"


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
    class Grid:
        Highlight = "#FFFFFF"
        Shadow = "#888888"

    class BG:
        Default = "#FFFFFF"
        Shade1 = "#EEEEEE"
        Shade2 = "#CCCCCC"

    class Target:
        Outline = "#000000"
        Default = "#DDDDFF"
        Shade1 = "#CCCCEE"
        Shade2 = "#AAAACC"

    class Select:
        Default = "#0044CC"

    class Highlight:
        Default = "#FFFFBB"
        Shade1 = "#DDDD99"

    class Relevant:
        Major = "#EECCCC"
        Minor = "#FFEEEE"


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

    CurrentRow = BasicColor(Colors.Relevant.Major)
    MatchingPatterns = BasicColor(Colors.Relevant.Minor)


@StyleBase("TLabel")
class Tooltip:
    StickyNote = BasicColorBorder(
        Colors.Highlight.Default, borderwidth=2, relief="groove"
    )


def generate():
    s = ttk.Style()
    s.theme_use("default")
    Style.generateAll(s)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("Available themes: ", print(ttk.Style().theme_names()))
    # print(Note.__dict__)
    generate()
    # print(Note.__dict__)

    # https://stackoverflow.com/a/48933106
    def stylename_elements_options(stylename):
        """Function to expose the options of every element associated to a widget
        stylename."""
        try:
            # Get widget elements
            style = ttk.Style()
            layout = str(style.layout(stylename))
            print("Stylename = {}".format(stylename))
            print("Layout    = {}".format(layout))
            elements = []
            for n, x in enumerate(layout):
                if x == "(":
                    element = ""
                    for y in layout[n + 2 :]:
                        if y != ",":
                            element = element + str(y)
                        else:
                            elements.append(element[:-1])
                            break
            print("\nElement(s) = {}\n".format(elements))

            # Get options of widget elements
            for element in elements:
                print(
                    "{0:30} options: {1}".format(
                        element, style.element_options(element)
                    )
                )

        except tk.TclError:
            print(
                '_tkinter.TclError: "{0}" in function'
                "widget_elements_options({0}) is not a regonised stylename.".format(
                    stylename
                )
            )

    print()
    stylename_elements_options(
        "TLabel"
    )  # For figuring out how these things can be styled
