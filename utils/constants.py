"""Constants used by the program."""

import random

# Try to avoid importing things here. Except maybe data types.


# region PROGRAM INFORMATION


PROGRAM_NAME = "TMidiTracker"

PROJECT_FILE_EXTENSION = ".tmt"
PROJECT_FILE_TK_LIST = [("TMT Project", PROJECT_FILE_EXTENSION)]

MIDI_FILE_EXTENSION = ".mid"
MIDI_FILE_TK_LIST = [("MIDI File", MIDI_FILE_EXTENSION)]

RECENT_LIST_LENGTH = 10

AUTOPORT_ATTEMPTS = 10
"""Attempts to try and automatically connect to a port. Mostly to allow time for the internal Fluidsynth to boot up."""
AUTOPORT_TIME = 200  # milliseconds
"""Time between attempts to try and automatically connect to a port. Mostly to allow time for the internal Fluidsynth to boot up."""

INTERNAL_FLUIDSYNTH_IDENTIFIER = (
    f"TMidiTracker-Internal-Fluidsynth-{hex(random.randint(0x1000000, 0xFFFFFFFF))[2:]}"
)
"""Name of internal Fluidsynth port. Randomized as I don't know how to get this from Fluidsynth itself and therefor need a way to prevent collisions."""
INTERNAL_FLUIDSYNTH_SAVE_IDENTIFIER = "INTERNAL_FLUIDSYNTH_SAVE_IDENTIFIER"
"""Value used to indicate to persistence that the desired port is the internal Fluidsynth."""

PERSISTENCE_FILE_NAME = "PERSISTENCE"
SETTINGS_FILE_NAME = "SETTINGS"

# endregion


# region MIDI CONSTANTS

CHANNEL_COUNT = 16

DRUM_CHANNEL = 9
CHANNEL_ORDER = list(range(CHANNEL_COUNT))
"""Map from internal order (incremental) to display order (perc first)"""
del CHANNEL_ORDER[DRUM_CHANNEL]
CHANNEL_ORDER.insert(0, DRUM_CHANNEL)
CHANNEL_ORDER_INVERSE = list(range(1, CHANNEL_COUNT))
"""Map from display order (perc first) to internal order (incremental)"""
CHANNEL_ORDER_INVERSE.insert(DRUM_CHANNEL, 0)

NOTES_PER_OCTAVE = 12

# 16364, signed
PITCH_BEND_MIN = -8192
PITCH_BEND_MAX = 8191

DEFAULT_BEND_RANGE = 127  # Basically we want it at max
BEND_STEPS_PER_SEMITONE = 8192 // DEFAULT_BEND_RANGE
# Basically we want to set range to allow bending the entire range
# That's still 50 ish points per note, which is enough

# endregion


# region OTHERS

KEYBOARD_MAP: dict[str, int] = dict()
"""Map of keyboard keys to notes. (0 is C)"""
for i, k in enumerate("q2w3er5t6y7ui9o0p[=]"):
    KEYBOARD_MAP[k] = i
for i, k in enumerate("zsxdcvgbhnjm,l.;/"):
    KEYBOARD_MAP[k] = i - NOTES_PER_OCTAVE

HEX_KEYMAP = "0123456789abcdef"
"""Symbols used for hex numbers."""

NOTE_DELTAS = [1, NOTES_PER_OCTAVE, NOTES_PER_OCTAVE * 2]
"""Deltas for increment/decrement of notes."""
VALUE_DELTAS = [1, 4, 16]
"""Deltas for increment/decrement of values."""
PATTERN_DELTAS = [1, 4, 16, 64]
"""Deltas for increment/decrement of values."""

NOTE_NAMES_SHARP = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]

NOTE_NAMES_FLAT = [
    "C",
    "Db",
    "D",
    "Eb",
    "E",
    "F",
    "Gb",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
]

DRUM_NAMES = {
    35: "AKC",
    36: "KIC",
    37: "STK",
    38: "SN1",
    39: "CLP",
    40: "SN2",
    41: "TM1",
    42: "HTC",
    43: "TM2",
    44: "HTP",
    45: "TM3",
    46: "HTO",
    47: "TM4",
    48: "TM5",
    49: "CC1",
    50: "TM6",
    51: "RC1",
    52: "CHC",
    53: "RDB",
    54: "TMB",
    55: "SPC",
    56: "COW",
    57: "CC2",
    58: "VIB",
    59: "RC2",
    60: "BNH",
    61: "BNL",
    62: "CHM",
    63: "CHO",
    64: "CNL",
    65: "TMH",
    66: "TML",
    67: "AGH",
    68: "AGL",
    69: "CAB",
    70: "MRC",
    71: "WSH",
    72: "WLO",
    73: "GUS",
    74: "GUL",
    75: "CLV",
    76: "WDH",
    77: "WDL",
    78: "CUM",  # lol
    79: "CUO",
    80: "TRM",
    81: "TRO",
}

# endregion


if __name__ == "__main__":
    for name, value in dict(globals()).items():
        if not name.startswith("__"):
            print(f"{name}: {value}")
