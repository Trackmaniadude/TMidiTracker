CHANNEL_COUNT = 16

NOTES_PER_OCTAVE = 12

KEYBOARD_MAP: dict[str, int] = dict()
"""Map of keyboard keys to notes. (0 is C)"""
for i, k in enumerate("q2w3er5t6y7ui9o0p[=]"):
    KEYBOARD_MAP[k] = i
for i, k in enumerate("zsxdcvgbhnjm,l.;/"):
    KEYBOARD_MAP[k] = i - NOTES_PER_OCTAVE

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

if __name__ == "__main__":
    for name, value in dict(globals()).items():
        if not name.startswith("__"):
            print(f"{name}: {value}")
