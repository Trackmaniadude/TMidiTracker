"""
Basic event system
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from typing import Callable

_logger = logging.getLogger(__name__)

dumpEvents = False
"""Set to true to print events as they are fired. Can be turned on globally or used for spot checks."""


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

    def __init__(self, name: str | None = None) -> None:
        self.__connections: set[Connection[P]] = set()
        self.name = (
            name
            if name is not None
            else "-".join(frame.function for frame in inspect.stack()[1:4])
        )
        if dumpEvents:
            print(f"CREATE EVENT: {self.name}")

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
        if dumpEvents:
            print(
                f"FIRE EVENT: {self.name} [{args}, {kwargs}] ({len(self.__connections)} connections)"
            )
        for con in list(self.__connections):
            try:
                con.callback(*args, **kwargs)
            except Exception as e:
                _logger.error(f"Error occurred during event callback for {self.name}")
                _logger.exception(e)
