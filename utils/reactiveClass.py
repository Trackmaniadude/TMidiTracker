"""
Gives a class a Changed event, fired when any value is changed.
"""

import logging
import tkinter as tk
from json import JSONEncoder
from tkinter import ttk
from typing import Any

from interface.utilities.headerFrame import HeaderFrame
from utils.event import Event

_logger = logging.getLogger(__name__)


class ReactiveContainerJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, ReactiveContainer):
            return o._container
        return super().default(o)


class ReactiveContainer[TContainer, TKey, TContent]:
    def __init__(self, container: TContainer) -> None:
        self.Changed: Event[[TKey, TContent, TContent]] = Event(
            f"{self.__class__.__name__}.Changed"
        )
        """Event(index: int, old: T, new: T)"""
        self._container = container

        for name in dir(self._container):
            if name.startswith("_"):
                continue
            if name in dir(self):
                continue

            def a(name):
                setattr(
                    self,
                    name,
                    lambda *args, **kwargs: getattr(self._container, name)(
                        *args, **kwargs
                    ),
                )

            a(name)

    def __contains__(self, v):
        return v in self._container

    def __str__(self) -> str:
        return "r" + str(self._container)

    def __len__(self) -> int:
        return len(self._container)  # pyright: ignore[reportArgumentType]

    def __iter__(self):
        return iter(self._container)  # type: ignore

    # TODO: iter


class ReactiveSet[TContent](ReactiveContainer):
    def __init__(self, container: set[TContent]) -> None:
        super().__init__(container)

    def add(self, item):
        t = item not in self._container
        self._container.add(item)
        if t:
            self.Changed.fire(None, None, item)

    def remove(self, item):
        t = item in self._container
        self._container.remove(item)
        if t:
            self.Changed.fire(None, item, None)


class ReactiveList[TContent](ReactiveContainer):
    def __init__(self, container: list[TContent]) -> None:
        super().__init__(container)

    def __getitem__(self, index: int) -> TContent:
        return self._container[index]

    def __setitem__(self, index: int, value: TContent):
        old = self._container[index] if index in self._container else None
        self._container[index] = value
        if old != value:
            self.Changed.fire(index, old, value)


class ReactiveDict[TKey, TContent](ReactiveContainer):
    def __init__(self, container: dict[TKey, TContent]) -> None:
        super().__init__(container)

    def __getitem__(self, key: TKey) -> TContent:
        return self._container[key]

    def __setitem__(self, key: TKey, value: TContent):
        old = self._container[key] if key in self._container else None
        self._container[key] = value
        if old != value:
            self.Changed.fire(key, old, value)

    def __delitem__(self, key: Any):
        old = self._container[key]
        del self._container[key]
        self.Changed.fire(key, old, None)


attribute = object()


class ReactiveClass:
    """
    Automatically generate changed events for values in a class.
    """

    def __init__(self) -> None:
        self.Changed: Event[[str, Any, Any, Any]] = Event(
            f"{self.__class__.__name__}.Changed"
        )
        """
        Fired when any attribute is changed. (name: str, key: Any, old: Any, new: Any)
        Key is set if a container was changed. Otherwise it is the attribute singleton.
        """
        self.__individualChangeEvents: dict[str, Event[[Any, Any, Any]]] = dict()
        """
        Events fired for individual attributes (when requested).
        (key: Any, old: Any, new: Any)
        """

        self.changeFilter: set[str] | None = None
        """Set of attributes Changed will fire on. Set to None (default) to fire on all."""

        def individualHandler(changedName: str, key: Any, old: Any, new: Any):
            if changedName in self.__individualChangeEvents:
                self.__individualChangeEvents[changedName].fire(key, old, new)

        self.Changed.connect(individualHandler)

        # if _logger.getEffectiveLevel() >= logging.DEBUG:
        #     self.Changed.connect(lambda *_: _logger.debug(_))

    def setupContainerListen(self):
        for name in dir(self):
            if name.startswith("_"):
                continue
            obj = getattr(self, name)
            if type(obj) is list:
                r = ReactiveList(obj)
            elif type(obj) is dict:
                r = ReactiveDict(obj)
            elif type(obj) is set:
                r = ReactiveSet(obj)
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
        if not hasattr(self, name):
            _logger.warning(
                f"Attempt to bind to non-existant attribute '{name}' in {self}"
            )
        if name not in self.__individualChangeEvents:
            # _logger.debug(f"Generating attribute change event for {name} ({self})")
            e = Event(f"{self.__class__.__name__}.{name}.Changed")
            self.__individualChangeEvents[name] = e

        return self.__individualChangeEvents[name]

    def __setattr__(self, name: str, value: Any) -> None:
        # Filter
        if (
            hasattr(self, "changeFilter")
            and self.changeFilter is not None
            and name not in self.changeFilter
        ):
            super().__setattr__(name, value)
            return

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
    """
    Easy view of data in a ReactiveClass instance.
    """

    REMOVE = {"Changed"}

    def __init__(
        self,
        parent: tk.Misc,
        target: ReactiveClass,
        *,
        title: str | None = None,
        fields: set[str] | None = None,
        recursionLevel: int = 0,
    ):
        super().__init__(parent)

        hf = HeaderFrame(self, title or target.__class__.__qualname__)
        hf.pack(fill="both", expand=True)

        if fields is None:
            fields = {
                name
                for name in target.__dict__.keys()
                if not (name.startswith("_") or name in self.REMOVE)
            }

        for i, field in enumerate(fields):

            def setup(field):
                targetVal = getattr(target, field)

                if isinstance(targetVal, ReactiveClass) and recursionLevel > 0:
                    view = ReactiveClassView(
                        hf.content,
                        targetVal,
                        title=field,
                        recursionLevel=recursionLevel - 1,
                    )
                    view.grid(row=i, column=0, columnspan=2)
                else:
                    ttk.Label(hf.content, text=field, justify="left").grid(
                        row=i, column=0, sticky="nesw"
                    )
                    view = ttk.Label(hf.content, justify="left")
                    view.grid(row=i, column=1, sticky="nesw")

                    def g():
                        targetVal = getattr(target, field)
                        view.config(text=str(targetVal))

                    g()
                    target.getAttributeChangedEvent(field).connect(lambda *_: g())

            setup(field)
