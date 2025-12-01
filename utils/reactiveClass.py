"""
Gives a class a Changed event, fired when any value is changed.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any

from interface.utilities.headerFrame import HeaderFrame
from utils.event import Event

_logger = logging.getLogger(__name__)


class ReactiveContainer[TKey, TContent]:
    def __init__(self) -> None:
        self.Changed: Event[[TKey, TContent, TContent]] = Event()
        """Event(index: int, old: T, new: T)"""


class ReactiveList[TContent](ReactiveContainer):
    def __init__(self, list: list[TContent]) -> None:
        super().__init__()
        self.__container = list
        for name in dir(dict):
            if name.startswith("__"):
                continue

            def a(name):
                setattr(
                    self,
                    name,
                    lambda *args, **kwargs: getattr(self.__container, name)(
                        *args, **kwargs
                    ),
                )

            a(name)

    def __getitem__(self, index: int) -> TContent:
        return self.__container[index]

    def __setitem__(self, index: int, value: TContent):
        old = self.__container[index] if index in self.__container else None
        self.__container[index] = value
        if old != value:
            self.Changed.fire(index, old, value)

    def __contains__(self, v):
        return v in self.__container


class ReactiveDict[TKey, TContent](ReactiveContainer):
    def __init__(self, dict: dict[TKey, TContent]) -> None:
        super().__init__()
        self.__container = dict
        for name in dir(dict):
            if name.startswith("__"):
                continue

            def a(name):
                setattr(
                    self,
                    name,
                    lambda *args, **kwargs: getattr(self.__container, name)(
                        *args, **kwargs
                    ),
                )

            a(name)

    def __getitem__(self, key: TKey) -> TContent:
        return self.__container[key]

    def __setitem__(self, key: TKey, value: TContent):
        old = self.__container[key] if key in self.__container else None
        self.__container[key] = value
        if old != value:
            self.Changed.fire(key, old, value)

    def __contains__(self, v):
        return v in self.__container

    def __delitem__(self, key: Any):
        del self.__container[key]


attribute = object()


class ReactiveClass:
    def __init__(self) -> None:
        self.Changed: Event[[str, Any, Any, Any]] = Event()
        """
        Fired when any attribute is changed. (name: str, key: Any, old: Any, new: Any)
        Key is set if a container was changed. Otherwise it is the attribute singleton.
        """
        self.__individualChangeEvents: dict[str, Event] = dict()

        if _logger.getEffectiveLevel() >= logging.DEBUG:
            self.Changed.connect(lambda *_: _logger.debug(_))

    def setupContainerListen(self):
        for name in dir(self):
            if name.startswith("__"):
                continue
            obj = getattr(self, name)
            if type(obj) is list:
                r = ReactiveList(obj)
            elif type(obj) is dict:
                r = ReactiveDict(obj)
            else:
                continue

            def q(name):  # Wonky to make it remember name
                r.Changed.connect(
                    lambda key, old, new: self.Changed.fire(name, key, old, new)
                )

            q(name)
            super().__setattr__(name, r)

    def getAttributeChangedEvent(self, name: str) -> Event[[Any, Any, Any]]:
        """
        Get an event that fires when a specific attribute is changed.
        Event args: (key: Any, old: Any, new: Any)
        """
        if name not in self.__individualChangeEvents:
            # TODO: Is there a way to type the event?
            e = Event()

            def h(changedName: str, key: Any, old: Any, new: Any):
                if name == changedName:
                    e.fire(key, old, new)

            self.Changed.connect(h)
            self.__individualChangeEvents[name] = e

        return self.__individualChangeEvents[name]

    def __setattr__(self, name: str, value: Any) -> None:
        # Only act on existing values
        if hasattr(self, name):
            old = self.__getattribute__(name)
            super().__setattr__(name, value)
            if old != value:
                try:
                    self.Changed.fire(name, attribute, old, value)
                except Exception as e:
                    _logger.error(e)
        else:
            super().__setattr__(name, value)


class ReactiveClassView(ttk.Frame):
    def __init__(
        self, parent: tk.Misc, target: ReactiveClass, title: str | None = None
    ):
        super().__init__(parent)
        self.target = target

        hf = HeaderFrame(self, title or target.__class__.__qualname__)
        hf.pack(fill="both")
