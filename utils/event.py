"""
Basic event system
"""

from __future__ import annotations

import inspect
import logging
import traceback
from dataclasses import dataclass
from typing import Callable

_logger = logging.getLogger(__name__)

dumpEvents = False
"""Set to true to print events as they are fired. Can be turned on globally or used for spot checks."""
warnDoubleDisconnects = True
"""Log a warning when you attempt to disconnect an event that has already been disconnected."""


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

    def isConnected(self):
        """Return if this connection is still connected to it's event."""
        return self.owner.isConnected(self)


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
        elif warnDoubleDisconnects:
            _logger.warning(
                f"Attempt to disconnect disconnected connection ({hex(id(con))} from {self.name} ({hex(id(self))}))."
            )
            _logger.warning("".join(traceback.format_stack()))

    def isConnected(self, con: Connection) -> bool:
        """Check if a connection is connected to this event."""
        return con in self.__connections

    def fire(self, *args: P.args, **kwargs: P.kwargs):
        """Fire the event (calls all registered callbacks with the provided arguments)"""
        if dumpEvents:
            print(
                f"FIRE EVENT: {self.name} ({hex(id(self))}) [{args}, {kwargs}] ({len(self.__connections)} connections)"
            )
        for con in self.__connections.copy():
            if (
                con in self.__connections
            ):  # In case a previous connection disconnected one we're going to do.
                try:
                    con.callback(*args, **kwargs)
                except Exception as e:
                    _logger.error(
                        f"Error occurred during event callback for {self.name}"
                    )
                    _logger.error("Traceback to event handler.")
                    _logger.error("".join(traceback.format_stack()))
                    _logger.error("Traceback in event handler.")
                    _logger.exception(e)
