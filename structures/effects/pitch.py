import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from mido import Message, MetaMessage

from structures.effectClasses import AbstractEffect, EffectCategory
from utils.misc import mapRange
from utils.types_ import note, velocity

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Pitch(EffectCategory):
    pass


# 20-2F


class Detune(Pitch, AbstractEffect):
    displayName = "Detune"
    prefix = (0x20,)
    params = [
        "20dd",
        "dd",
        "Detune",
    ]
    help = "Detune the channel.\n0  = -1\n80 =  0\nFF  =  1"

    bendName = "Detune"

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        bend = (data[0] - 0x80) / 0x7F
        if bend == 0:
            channel.playbackState.pitchBends.pop(cls.bendName, None)
        else:
            channel.playbackState.pitchBends[cls.bendName] = bend


class VibratoEffects(Pitch):
    settingsName = "VibratoSettings"


class Vibrato(VibratoEffects, AbstractEffect):
    displayName = "Vibrato"
    prefix = (0x21,)  # TODO:
    params = [
        "21pprr",
        "pp",
        "Period",
        "rr",
        "Range",
    ]
    help = (
        "Apply vibrato to the channel. Max range is up to 1 semitone (can be adjusted)"
        "\nCalling with no arguments will stop the effect."
        "\nCalling with both arguments set to 0 will use the arguments of the last call to the effect."
    )

    storeName = "Vibrato"
    bendName = "Vibrato"

    @dataclass
    class StoreValue:
        period: int
        range: float
        active: bool
        phase: int = 0

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        def loop(_: None):
            data = channel.playbackState.effectData.get(cls.storeName, None)
            if data is None:
                return
            if type(data) is not cls.StoreValue:
                return  # Mostly for the type checker without using a static reference
            if not data.active:
                return

            offset = math.sin((data.phase / data.period) * 2 * math.pi)
            channel.playbackState.pitchBends[cls.bendName] = offset * data.range
            data.phase = (data.phase + 1) % data.period

            channel.scheduleEffect(1, loop, None)

        # If no params, disable effect (but leave data object)
        if len(data) == 0:
            value = channel.playbackState.effectData.get(cls.storeName, None)
            if type(value) is cls.StoreValue:
                value.active = False
            channel.playbackState.pitchBends.pop(cls.bendName, None)
        else:
            value = channel.playbackState.effectData.get(cls.storeName, None)

            # If the effect has been disabled, we need to restart the loop
            doNew = value is None or value.active == False

            # Special case (0, 0) to reuse last data
            # Otherwise it does nothing
            if data == (0, 0):
                if type(value) is cls.StoreValue:
                    if value.active == False:
                        value.active = True
                        value.phase = 0
                else:
                    return
            else:
                period, range = data
                maxRange = 1  # TODO:
                rangeActual = (range / 0xFF) * maxRange

                # If an existing value is present, simply update it. If the effect is active, remap the phase to keep it continuous.
                # If it does not exist, make a new one.
                if type(value) is cls.StoreValue:
                    if value.active == True:
                        value.phase = int(
                            mapRange(0, value.period, 0, period, value.phase)
                        )
                    else:
                        value.phase = 0
                    value.period = period
                    value.range = rangeActual
                    value.active = True
                else:
                    value = cls.StoreValue(period, rangeActual, True)
                    channel.playbackState.effectData[cls.storeName] = value

            if doNew:
                loop(None)


class VibratoSetup(VibratoEffects, AbstractEffect):
    displayName = "Vibrato Setup"
    prefix = (0x22,)  # TODO:
    params = [
        "22TODO:",
    ]
    help = "Change less common vibrato settings."

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        pass


class Arpeggio:
    pass
