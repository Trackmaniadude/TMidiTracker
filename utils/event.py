"""
Basic event system
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Connection[**P]:
    """
    Event connection. Represents the connection and allows disconnecting it.
    """

    owner: Event[P]
    """Event that created this connection."""
    callback: Callable[P]
    """Callback called when the owning event is fired."""

    def disconnect(self):
        """Remove this connection from the owning event's registry."""
        self.owner.disconnect(self)


class Event[**P]:
    """
    Fireable event.
    Calling Fire() will call all callbacks registered through Connect()
    """

    def __init__(self) -> None:
        self.__connections: set[Connection[P]] = set()

    def connect(self, callback: Callable[P], conList: list[Connection] | None = None):
        """Register a callback with the event. A list can be provided to automatically put this connection in."""
        con = Connection(self, callback)
        self.__connections.add(con)
        if conList is not None:
            conList.append(con)
        return con

    def disconnect(self, con: Connection[P]):
        """Remove a connection from the event."""
        if con in self.__connections:
            self.__connections.remove(con)

    def fire(self, *args: P.args, **kwargs: P.kwargs):
        """Fire the event (calls all registered callbacks with the provided arguments)"""
        for con in list(self.__connections):
            con.callback(*args, **kwargs)
