"""
Channel effects
"""

from __future__ import annotations

from mido import Message, MetaMessage

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.channel import Channel

import logging
from abc import ABC, abstractmethod

from structures import program

_logger = logging.getLogger(__name__)


class AbstractEffect:
    prefix: tuple[int, ...]
    color: str = "#000000"
    params: list[str] = [""]
    help: str = "DEFAULT HELP"

    @classmethod
    def actuate(
        cls, channel: Channel, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        """Run effect code. May directly fiddle with channel data, or return MIDI messages."""
        _logger.warning(
            f"UNIMPLEMENTED EFFECT: {cls.__qualname__}, Channel {channel.channel}, Data {data}"
        )


class Effects:
    class RawMidi(AbstractEffect):
        prefix = (0x00,)
        help = "Send an arbitrary midi message."

    class RawControl(AbstractEffect):
        prefix = (0x01,)
        params = ["01xxyy", "x", "Control", "y", "Value"]
        help = "Send an arbitrary control change."

        @classmethod
        def actuate(
            cls, channel: Channel, data: tuple[int, ...]
        ) -> None | list[Message | MetaMessage]:
            try:
                control = data[0]
                value = data[1]
            except ValueError:
                return None
            else:
                return [
                    Message(
                        "control_change",
                        channel=channel.channel,
                        control=control,
                        value=value,
                    )
                ]

    class ChangeInstrument(AbstractEffect):
        prefix = (0x02,)
        params = ["02xx", "x", "Instrument"]
        help = "Change channel instrument."

        @classmethod
        def actuate(
            cls, channel: Channel, data: tuple[int, ...]
        ) -> None | list[Message | MetaMessage]:
            try:
                program = data[0]
            except Exception as e:
                _logger.warning(
                    f"Invalid data for effect {cls.__qualname__}; got {data}, expected form {cls.params}"
                )
                return None
            else:
                return [
                    Message(
                        "program_change",
                        channel=channel.channel,
                        program=program,
                    )
                ]

    class Test(AbstractEffect):
        prefix = (0x03, 0x03, 0x03)


effectsList: dict[tuple[int, ...], type[AbstractEffect]] = {
    c.prefix: c for c in Effects.__dict__.values() if isinstance(c, type)
}


def getEffect(data: tuple[int, ...]) -> type[AbstractEffect] | None:
    for prefix, effect in effectsList.items():
        if data[: len(prefix)] == prefix:
            return effect
    return None


def runEffect(
    data: tuple[int, ...], channel: Channel
) -> None | list[Message | MetaMessage]:
    """Get an effect, and call it's actuate if it exists with data - effect prefix."""
    effect = getEffect(data)
    if effect:
        return effect.actuate(channel, data[len(effect.prefix) :])


if __name__ == "__main__":
    print("effects...")
    for _, effect in effectsList.items():
        print(effect.__qualname__)
        print(effect.prefix)
        print(effect.color)
    print()
    print(getEffect((0, 0, 0)))
    print(getEffect((0, 1, 0)))
    print(getEffect((3, 0, 0)))
    print(getEffect((3, 3, 3, 1)))
