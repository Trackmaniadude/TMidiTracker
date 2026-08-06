from dataclasses import dataclass
from typing import TYPE_CHECKING

from mido import Message, MetaMessage

from structures.effectClasses import AbstractEffect, EffectCategory
from utils.types_ import note, velocity

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Timing(EffectCategory):
    displayName = "Timing"
    description = "Effects that adjust when notes are played."


# 10-1F


class Delay(Timing, AbstractEffect):
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


class Arpeggiate(Timing, AbstractEffect):
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

        callback((delay, orderedNotes[-1][0], [pair[1] for pair in orderedNotes]))


class Strum(Timing, AbstractEffect):
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


class Retrigger(Timing, AbstractEffect):
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
                channel.scheduleEffect(delay, callback, ({col: note}, count - 1))


class NoteCut(Timing, AbstractEffect):
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
            channel.scheduleEffect(delay, callback, {n: "stop" for n in notes.keys()})
        else:
            if note is not None:
                channel.scheduleEffect(delay, callback, {col: "stop"})


class Stutter(Timing, AbstractEffect):
    displayName = "Stutter"
    prefix = (0x15,)
    params = [
        "15[xy...]",
        "xy",
        "On/Off Delay",
    ]
    help = (
        "Repeat notes when played with a highly configurable pace.\n"
        "Note will be on for x ticks, then off for y ticks, repeating through all provided xy pairs.\n"
        "Calling with no arguments stops the effect.\n"
        "An xy pair of 00 will set a loop point rather than starting from the beginning of the pattern. "
        "If multiple points are specified, the last will be used."
    )

    storeName = "Stuttur"

    @dataclass
    class StoreValue:
        pattern: list[int]
        loop: int
        notes: dict[int, note]
        resetOnNewNotes: bool

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        if len(data) == 0:
            channel.playbackState.effectData.pop(cls.storeName, None)
            return

        def loop(loopData: tuple[int, int]):
            data = channel.playbackState.effectData.get(cls.storeName, None)
            if type(data) is not cls.StoreValue:
                return
            time, step = loopData

            # Precheck in case things get changed at the wrong time
            if step > len(data.pattern):
                step = data.loop
            wait = data.pattern[step]

            # Update playing notes
            newNotes = channel.playbackState.queuedNotes.copy()
            if len(newNotes) > 0:
                channel.playbackState.queuedNotes.clear()
                data.notes = newNotes
                if data.resetOnNewNotes:
                    time = 0
                    step = 0

            # Playback
            if time == 0:
                if step % 2 == 0:
                    channel.playbackState.queuedNotes.update(data.notes)
                else:
                    channel.playbackState.queuedNotes.update(
                        {c: "stop" for c in data.notes.keys()}
                    )

            # Timing
            time += 1
            if time >= wait:
                time = 0
                step += 1
                if step >= len(data.pattern):
                    step = data.loop

            # Loop
            channel.scheduleEffect(1, loop, (time, step))

        pattern: list[int] = list()
        loopPoint = 0
        count = 0
        for n in data:
            if n == 0:
                loopPoint = count
                continue
            pattern.append(n // 0x10)
            pattern.append(n % 0x10)
            count += 2

        running = cls.storeName in channel.playbackState.effectData
        channel.playbackState.effectData[cls.storeName] = cls.StoreValue(
            pattern, loopPoint, dict(), True
        )
        if not running:
            loop((0, 0))
