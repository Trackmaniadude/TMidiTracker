from typing import TYPE_CHECKING

from mido import Message, MetaMessage

from structures.effectClasses import AbstractEffect, EffectCategory

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Control(EffectCategory):
    displayName = "Control"
    description = "Effects that control midi state outside of notes, or that control tracker state."


# 00-0F


class RawMidi(Control, AbstractEffect):
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


class RawControl(Control, AbstractEffect):
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


class SetInstrument(Control, AbstractEffect):
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


class SetVolume(Control, AbstractEffect):
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


class SetPan(Control, AbstractEffect):
    displayName = "Set Panning"
    prefix = (0x04,)
    params = ["04xx", "x", "Pan [0-7F]"]
    help = (
        "Set channel panning. Equivalent to 010Axx."
        "\nCenter is 0x40, lower is left, greater is right."
    )

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
                    control=10,
                    value=value,
                )
            ]
        except Exception:
            return None
        else:
            return r  # type: ignore


class SetGroove(Control, AbstractEffect):
    displayName = "Set Groove"
    prefix = (0x0F,)
    params = ["0F[tt...]", "t", "Row Time (Ticks)"]
    help = "Set groove pattern dynamically. Takes one or more values. No values returns to base groove."

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        if len(data) == 0:
            player.grooveOverride = None
        else:
            player.grooveOverride = data
