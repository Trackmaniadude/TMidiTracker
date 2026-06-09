import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from mido import Message, MetaMessage

from structures.effectClasses import AbstractEffect, EffectCategory
from utils.misc import clamp, mapRange
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


class Bend(Pitch, AbstractEffect):
    displayName = "Pitch Bend"
    prefix = (0x2F,)
    params = [
        "2Faatt[rs]",
        "aa",
        "Amount",
        "tt",
        "Time",
        "[r]",
        "Reverse",
        "[c]",
        "Continue",
    ]
    help = (
        "Slide pitch up/down [aa] semitones over [tt] ticks. [aa] 00-7F is positive, 80-FF is negative (03 = +3, 83 = -3).\n"
        "Setting [r] to a non-zero value will start the bend at the far position rather than the current note.\n"
        "Bends will stop when a new note is played, unless [c] is set non-zero. In this case, "
        "any active bends on the channel can be stopped by using the effect with no arguments."
    )

    bendName = "Detune{}"
    stopName = "DetuneCancel"

    @dataclass
    class loopValue:
        bendName: str
        amount: int
        time: int
        reverse: bool
        cont: bool
        t: int = 0

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        if len(data) == 0:  # Stop
            # Add signal and then immediately remove it.
            # Anything active will have already scheduled, so this will end up last.
            channel.playbackState.effectData[cls.stopName] = None
            channel.scheduleEffect(
                0,
                lambda _: channel.playbackState.effectData.pop(cls.stopName, None),
                None,
            )
        elif len(data) == 2 or len(data) == 3:

            def loop(data: Bend.loopValue):
                stop = False

                # Stop when called for
                if cls.stopName in channel.playbackState.effectData:
                    stop = True
                # Stop when another note starts (unless disabled)
                if (
                    len(channel.playbackState.queuedNotes) > 0
                    and data.t > 0
                    and not data.cont
                ):
                    stop = True
                # Stop when a reversed slide ends
                if data.reverse and data.t >= data.time:
                    stop = True
                if stop:
                    channel.playbackState.pitchBends.pop(data.bendName, None)
                    return

                # Determine current bend
                t = clamp(data.t, 0, data.time)
                if data.reverse:
                    t = data.time - t
                bend: float = mapRange(0, data.time, 0, data.amount, t)

                channel.playbackState.pitchBends[data.bendName] = bend

                data.t += 1
                channel.scheduleEffect(1, loop, data)

            amount = data[0] if data[0] < 0x80 else 0x80 - data[0]
            time = data[1]
            reverse = bool((data[2] & 0xF0) >> 4) if len(data) == 3 else False
            cont = bool(data[2] & 0x0F) if len(data) == 3 else False

            name = cls.bendName.format(uuid4())
            v = cls.loopValue(name, amount, time, reverse, cont)

            channel.scheduleEffect(1, loop, v)
        else:
            raise Exception


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
