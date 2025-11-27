"""
Gives a class a Changed event, fired when any value is changed.
"""

from typing import Any

from utils.event import Event


class ReactiveClass:
    def __init__(self) -> None:
        self.Changed: Event[[str, Any, Any]] = Event()
        """Fired when any attribute is changed. (name: str, old: Any, new: Any)"""

    def getPropertyChangedEvent(self, name: str) -> Event[[Any, Any]]:
        """
        Get an event that fires when a specific property is changed.
        Event args: (old: Any, new: Any)
        """
        # TODO: Is there a way to type the event?
        e = Event()

        def h(changedName: str, old: Any, new: Any):
            if name == changedName:
                e.fire(old, new)

        self.Changed.connect(h)
        return e

    def __setattr__(self, name: str, value: Any) -> None:
        # Only act on existing values
        if hasattr(self, name):
            old = self.__getattribute__(name)
            super().__setattr__(name, value)
            if old != value:
                self.Changed.fire(name, old, value)
        else:
            super().__setattr__(name, value)
