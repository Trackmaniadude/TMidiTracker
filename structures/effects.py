"""
Channel effects
"""

from __future__ import annotations

from mido import Message, MetaMessage

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.channel import Channel

import logging

from structures import program
from utils.types_ import note

_logger = logging.getLogger(__name__)


class AbstractEffect:
    displayName: str
    """Display name."""
    prefix: tuple[int, ...]
    """Effect prefix. This identifies the effect."""
    color: str = "#000000"
    """Effect display color."""
    params: list[str] = [""]
    """Effect parameters. Should be a string list of the format [parameter layout, [parameter identifier, parameter name]]"""
    help: str = "DEFAULT HELP"
    """Help message."""

    @classmethod
    def actuate(
        cls, channel: Channel, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        """Run effect code. May directly fiddle with channel data, or return MIDI messages."""
        _logger.warning(
            f"UNIMPLEMENTED EFFECT: {cls.__qualname__}, Channel {channel.channel}, Data {data}"
        )

    @classmethod
    def prefixString(cls) -> str:
        out = ""
        for n in cls.prefix:
            if n < 16:
                out += "0" + hex(n)[2:]
            else:
                out += hex(n)[2:]
        return out.upper()


# class EffectCategories:
#     MISC = ("Misc", "#000000")
#     PITCH = ("Pitch", "#000000")
#     TIME = ("Time", "#000000")
#     MISC = ("Misc", "#000000")


class EffectCategory:
    pass


class Effects:
    class Raw(EffectCategory):
        class RawMidi(AbstractEffect):
            displayName = "Raw MIDI Message"
            prefix = (0x00,)
            params = ["00..", "..", "An arbitrary series of hex bytes"]
            help = "Send an arbitrary midi message."

            # TODO: verify
            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                try:
                    r = [Message.from_bytes(data)]
                except Exception:
                    return None
                else:
                    return r  # type: ignore

        class RawControl(AbstractEffect):
            displayName = "Raw MIDI Control"
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
                    r = [
                        Message(
                            "control_change",
                            channel=channel.channel,
                            control=control,
                            value=value,
                        )
                    ]
                except Exception:
                    return None
                else:
                    return r  # type: ignore

    class Timing(EffectCategory):
        class Delay(AbstractEffect):
            displayName = "Delay"
            prefix = (0x10,)
            params = ["10xx[yy]", "x", "Delay (in ticks)", "y", "Column"]
            help = "Delay playback of note(s) in this row (and channel). If no column is specified, applies to all notes."

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                delay = data[0]
                col = data[1] if len(data) == 2 else None
                notes = channel.playbackState.queuedNotes.copy()

                def callback(savedNotes: dict[int, note]):
                    channel.playbackState.queuedNotes.update(savedNotes)

                if col is None:
                    channel.playbackState.queuedNotes.clear()
                    channel.scheduleEffect(delay, callback, notes)
                else:
                    note = channel.playbackState.queuedNotes.pop(col, None)
                    if note is not None:
                        channel.scheduleEffect(delay, callback, {col: note})

        class Arpeggiate(AbstractEffect):
            displayName = "Arpeggiate"
            prefix = (0x11,)
            params = ["11xx", "x", "Delay (in ticks) between notes."]
            help = "Insert delay between notes, with the leftmost note playing immediately and the rightmost note playing last. Only plays one note at a time in the column of the leftmost note."

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                delay = data[0]
                notes = channel.playbackState.queuedNotes.copy()

                def callback(data: tuple[int, int, list[note]]):
                    """(time, col, [note])"""
                    delay, col, notes = data
                    note = notes.pop()
                    channel.playbackState.queuedNotes[col] = note
                    if len(notes) > 0:
                        channel.scheduleEffect(delay, callback, (delay, col, notes))

                channel.playbackState.queuedNotes.clear()
                orderedNotes: list[tuple[int, note]] = [
                    (col, note) for col, note in notes.items()
                ]
                orderedNotes.sort(key=lambda e: e[0])
                orderedNotes.reverse()

                callback(
                    (delay, orderedNotes[-1][0], [pair[1] for pair in orderedNotes])
                )

        class Strum(AbstractEffect):
            displayName = "Strum"
            prefix = (0x12,)
            params = ["12xx", "x", "Delay (in ticks) between notes."]
            help = "Insert delay between notes, with the leftmost note playing immediately and the rightmost note playing last. All notes will ring out."

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                delay = data[0]
                notes = channel.playbackState.queuedNotes.copy()

                def callback(data: tuple[int, list[tuple[int, note]]]):
                    """(time, [(col, note)])"""
                    delay, notes = data
                    col, note = notes.pop()
                    channel.playbackState.queuedNotes[col] = note
                    if len(notes) > 0:
                        channel.scheduleEffect(delay, callback, (delay, notes))

                channel.playbackState.queuedNotes.clear()
                orderedNotes: list[tuple[int, note]] = [
                    (col, note) for col, note in notes.items()
                ]
                orderedNotes.sort(key=lambda e: e[0])
                orderedNotes.reverse()

                callback((delay, orderedNotes))

        class Retrigger(AbstractEffect):
            displayName = "Retrigger"
            prefix = (0x13,)
            params = [
                "13xx[yy][zz]",
                "x",
                "Delay (in ticks)",
                "y",
                "Count",
                "z",
                "Column",
            ]
            help = "Repeat note(s) after a time, y times. If no column is specified, applies to all notes."

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                delay = data[0]
                count = data[1] if len(data) == 2 else 1
                col = data[2] if len(data) == 3 else None
                notes = channel.playbackState.queuedNotes.copy()

                def callback(data: tuple[dict[int, note], int]):
                    notes, count = data
                    channel.playbackState.queuedNotes.update(notes)
                    if count > 0:
                        channel.scheduleEffect(delay, callback, (notes, count - 1))

                if col is None:
                    channel.scheduleEffect(delay, callback, (notes, count - 1))
                else:
                    note = notes.get(col, None)
                    if note is not None:
                        channel.scheduleEffect(
                            delay, callback, ({col: note}, count - 1)
                        )

        class NoteCut(AbstractEffect):
            displayName = "Note Cut"
            prefix = (0x14,)
            params = ["14xx[yy]", "x", "Delay (in ticks)", "y", "Column"]
            help = "Stop playback of note(s) after a time. If no column is specified, applies to all notes. Mainly intended for notes shorter than the row time."

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                delay = data[0]
                col = data[1] if len(data) == 2 else None
                notes = channel.playbackState.queuedNotes.copy()

                def callback(savedNotes: dict[int, note]):
                    channel.playbackState.queuedNotes.update(savedNotes)

                if col is None:
                    channel.scheduleEffect(
                        delay, callback, {n: "stop" for n in notes.keys()}
                    )
                else:
                    if note is not None:
                        channel.scheduleEffect(delay, callback, {col: "stop"})

    class Pitch(EffectCategory):
        class Vibrato:
            pass

        class Arpeggio:
            pass

    class ControlShortcuts(EffectCategory):

        class SetInstrument(AbstractEffect):
            displayName = "Set Instrument"
            prefix = (0x02,)
            params = ["02xx", "x", "Instrument [0-7F]"]
            help = "Set channel instrument."

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                try:
                    program = data[0]
                    r = [
                        Message(
                            "program_change",
                            channel=channel.channel,
                            program=program,
                        )
                    ]
                except Exception:
                    return None
                else:
                    return r  # type: ignore

        class SetVolume(AbstractEffect):
            displayName = "Set Volume"
            prefix = (0x03,)
            params = ["03xx", "x", "Volume [0-7F]"]
            help = "Set channel volume. Equivalent to 0107xx"

            @classmethod
            def actuate(
                cls, channel: Channel, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                try:
                    value = data[0]
                    r = [
                        Message(
                            "control_change",
                            channel=channel.channel,
                            control=7,
                            value=value,
                        )
                    ]
                except Exception:
                    return None
                else:
                    return r  # type: ignore


effectsList: dict[tuple[int, ...], type[AbstractEffect]] = dict()


def getEffectsList(parentClass: type):
    for childClass in parentClass.__dict__.values():
        if isinstance(childClass, type):
            if issubclass(childClass, AbstractEffect):
                effectsList[childClass.prefix] = childClass
            else:
                getEffectsList(childClass)


getEffectsList(Effects)


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
