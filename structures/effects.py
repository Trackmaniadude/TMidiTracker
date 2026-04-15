"""
Channel effects
"""

from __future__ import annotations

from mido import Message, MetaMessage

from utils.constants import CHANNEL_ORDER, CHANNEL_ORDER_INVERSE

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player

import logging

from structures import program
from utils.types_ import note, velocity

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
        cls, channel: Channel, player: Player, data: tuple[int, ...]
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


# TODO: figure out how to break this into multiple files
class Effects:
    class Control(EffectCategory):
        # 00-0F
        class RawMidi(AbstractEffect):
            displayName = "Raw MIDI Message"
            prefix = (0x00,)
            params = ["00..", "..", "An arbitrary series of hex bytes"]
            help = "Send an arbitrary midi message."

            # TODO: verify
            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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

        class SetInstrument(AbstractEffect):
            displayName = "Set Instrument"
            prefix = (0x02,)
            params = ["02xx", "x", "Instrument [0-7F]"]
            help = "Set channel instrument."

            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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

    class Timing(EffectCategory):
        # 10-1F
        class Delay(AbstractEffect):
            displayName = "Delay"
            prefix = (0x10,)
            params = ["10xx[yy]", "x", "Delay (in ticks)", "y", "Column"]
            help = "Delay playback of note(s) in this row (and channel). If no column is specified, applies to all notes."

            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
                cls, channel: Channel, player: Player, data: tuple[int, ...]
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
        # 20-2F
        class Vibrato:
            pass

        class Arpeggio:
            pass

    class Harmonization(EffectCategory):
        # 30-3F
        class EchoDouble(AbstractEffect):
            displayName = "Echo/Double"
            prefix = (0x30,)  # TODO:
            params = ["30[cc][dd][oo]", "cc", "Channel", "dd", "Delay", "oo", "Offset"]
            help = (
                "Copy notes from another channel and play them in this channel."
                " Notes can have an optional delay (for echo effects) and pitch offset (for harmonization/doubling)."
                " Offset is centered at 0x80, to allow for negative values."
                " Omitting the channel will turn off the effect."
                " Only one instance of the effect can be run per channel; adding another will override the first."
                "\n(Note: behavior of this effect when the source channel also has an Echo/Double effect is currently undefined.)"
            )

            storeName = "EchoDouble"

            class StoreValue(NamedTuple):
                targetChannel: int
                delay: int
                offset: int

            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                targetChannel = CHANNEL_ORDER[data[0]] if len(data) > 0 else None
                delay = data[1] if len(data) > 1 else 0
                offset = data[2] - 0x80 if len(data) > 2 else 0

                if targetChannel is None:
                    channel.playbackState.effectData.pop(cls.storeName, None)
                    return

                def loop(_: None):
                    data = channel.playbackState.effectData.get(cls.storeName, None)
                    if data is None:
                        return
                    if type(data) is not cls.StoreValue:
                        return  # Mostly for the type checker without using a static reference

                    targetChannel, delay, offset = data

                    source = program.p.currentSong.channels[targetChannel]
                    notes: dict[int, note] = {
                        col: (note + offset if type(note) is int else note)
                        for col, note in source.playbackState.queuedNotes.items()
                    }
                    vels = source.playbackState.queuedVelocities.copy()

                    if delay <= 0:
                        channel.playbackState.queuedNotes.update(notes)
                        channel.playbackState.queuedVelocities.update(vels)
                    else:
                        if len(notes) > 0 or len(vels) > 0:

                            def delayCallback(
                                data: tuple[dict[int, note], dict[int, velocity]]
                            ):
                                # Has to be defined in the loop body due to the schedule system indexing on the callback functions
                                # TODO: investigate the impact of doing this vs some other identifier
                                notes, vels = data
                                channel.playbackState.queuedNotes.update(notes)
                                channel.playbackState.queuedVelocities.update(vels)

                            channel.scheduleEffect(delay, delayCallback, (notes, vels))

                    channel.scheduleEffect(1, loop, None)

                start = cls.storeName not in channel.playbackState.effectData
                channel.playbackState.effectData[cls.storeName] = cls.StoreValue(
                    targetChannel, delay, offset
                )
                if start:
                    loop(None)

    class Flow(EffectCategory):
        # F0-FE
        class End(AbstractEffect):
            displayName = "End Song"
            prefix = (0xF0,)
            params = ["F0"]
            help = "Stops playback."

            @classmethod
            def actuate(
                cls, channel: Channel, player: program.Player, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                player.pause()

        class Loop(AbstractEffect):
            displayName = "Loop"
            prefix = (0xF4,)
            params = [
                "F4mm[pp][ll]",
                "mm",
                "Matrix Row",
                "[pp]",
                "Pattern Row",
                "[ll]",
                "Repeat Limit",
            ]
            help = (
                "Jump to another row, and optionally position in that row."
                "\nAlso has an optional repetition limit. Not specifying this will repeat "
                "indefinitely in live playback, or use the repeat amount for offline playback."
            )

            storeName = "LoopEffect{mat}{pat}"  # Was that the bite of '87??

            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                storeName = cls.storeName.format(
                    mat=player.currentMatrixRow, pat=player.currentPatternRow
                )

                matrixRow = data[0]
                patternRow = data[1] if len(data) > 1 else 0
                repeat = (
                    data[2]
                    if len(data) > 2
                    else (None if player.live else program.p.currentSong.loopCount)
                )

                if repeat is not None:
                    count: int = (
                        channel.playbackState.effectData.get(storeName, repeat) - 1
                    )
                    channel.playbackState.effectData[storeName] = count
                    if count <= 0:
                        del channel.playbackState.effectData[storeName]
                        return

                player.nextMatrixRow = matrixRow
                player.nextPatternRow = patternRow

        class Jump(AbstractEffect):
            displayName = "Jump"
            prefix = (0xF5,)
            params = [
                "F5mm[pp][cc]",
                "mm",
                "Matrix Row",
                "[pp]",
                "Pattern Row",
                "[cc]",
                "Countdown",
            ]
            help = (
                "Jump to another row, and optionally position in that row."
                "\nAlso has an optional countdown. Specifying this will ignore "
                "the jump until it has been passed n-1 times (so specifying 2 "
                "will jump the second time around)"
            )

            storeName = "JumpEffect{mat}{pat}"

            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                storeName = cls.storeName.format(
                    mat=player.currentMatrixRow, pat=player.currentPatternRow
                )

                matrixRow = data[0]
                patternRow = data[1] if len(data) > 1 else 0
                countdown = data[2] if len(data) > 2 else 1

                count: int = (
                    channel.playbackState.effectData.get(storeName, countdown) - 1
                )
                channel.playbackState.effectData[storeName] = count
                if count <= 0:
                    del channel.playbackState.effectData[storeName]
                    player.nextMatrixRow = matrixRow
                    player.nextPatternRow = patternRow

        class JumpRel(AbstractEffect):
            displayName = "Jump Relative"
            prefix = (0xF6,)
            params = [
                "F6mm[pp][cc]",
                "mm",
                "Matrix Row Offset",
                "[pp]",
                "Pattern Row Offset",
                "[cc]",
                "Countdown",
            ]
            help = (
                "Jump to another row, and optionally position in that row. "
                "Rows are specified as offsets. However, pattern offset only applies "
                "if row offset is 0, otherwise pattern is set absolute."
                "\nAlso has an optional countdown. Specifying this will ignore "
                "the jump until it has been passed n-1 times (so specifying 2 "
                "will jump the second time around)"
            )

            storeName = "JumpRelativeEffect{mat}{pat}"

            @classmethod
            def actuate(
                cls, channel: Channel, player: Player, data: tuple[int, ...]
            ) -> None | list[Message | MetaMessage]:
                storeName = cls.storeName.format(
                    mat=player.currentMatrixRow, pat=player.currentPatternRow
                )

                matrixRow = data[0]
                patternRow = data[1] if len(data) > 1 else 0
                countdown = data[2] if len(data) > 2 else 1

                count: int = (
                    channel.playbackState.effectData.get(storeName, countdown) - 1
                )
                channel.playbackState.effectData[storeName] = count
                if count <= 0:
                    del channel.playbackState.effectData[storeName]
                    player.nextMatrixRow = player.currentMatrixRow + matrixRow
                    if matrixRow == 0:
                        player.nextPatternRow = player.currentPatternRow + patternRow
                    else:
                        player.nextPatternRow = patternRow

    class Extended(EffectCategory):
        # FF00-FFFE
        pass


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
    channel: Channel, player: Player, data: tuple[int, ...]
) -> None | list[Message | MetaMessage]:
    """Get an effect, and call it's actuate if it exists with data - effect prefix."""
    effect = getEffect(data)
    if effect:
        return effect.actuate(channel, player, data[len(effect.prefix) :])


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
