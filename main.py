import argparse
import logging
import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import cast

from interface.program.channelDebug import ChannelDebug
from interface.program.effectList import EffectList
from interface.program.instrumentList import InstrumentList
from interface.program.patternList import PatternList
from interface.program.patternMatrix import PatternMatrix
from interface.program.patternViewFrame import PatternViewFrame
from interface.program.songDataView import SongDataView
from structures import program

PROGRAM_NAME = "TMidiTracker"

parser = argparse.ArgumentParser(
    prog=PROGRAM_NAME,
    description="Midi tracker.",
)

# parser.add_argument("-f", "--file", help="File to open on start.")

loggerGroup = parser.add_mutually_exclusive_group()
loggerGroup.add_argument(
    "-d", "--debug", help="Print debug messages.", action="store_true"
)
loggerGroup.add_argument(
    "-q", "--quiet", help="Only print errors.", action="store_true"
)

args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
elif args.quiet:
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

_logger = logging.getLogger(__name__)


root = tk.Tk()
root.title(PROGRAM_NAME)
root.state("zoomed")
# root.geometry("800x600")
root.option_add("*tearOff", False)
root.unbind_all("<Tab>")
root.unbind_all("<<NextWindow>>")
root.unbind_all("<<PrevWindow>>")

from interface import theme

theme.generate()

menubar = tk.Menu(root)
root["menu"] = menubar

testMenu = tk.Menu(menubar)
menubar.add_cascade(menu=testMenu, label="Menu")
testMenu.add_command(label="Play", command=lambda: program.p.songPlayer.play())
testMenu.add_command(label="Pause", command=lambda: program.p.songPlayer.pause())


def focus(event):
    try:
        event.widget.focus_set()
    except AttributeError:
        pass


root.bind_all("<Button-1>", focus)
if args.debug:
    root.bind_all("<FocusIn>", lambda e: _logger.debug(f"FOCUS IN: {e.widget}"))
    root.bind_all("<FocusOut>", lambda e: _logger.debug(f"FOCUS OUT: {e.widget}"))
    root.bind_all(
        "<Button-2>",
        lambda e: _logger.debug(
            f"{e.widget}: {e.widget.winfo_class()}, {e.widget.winfo_name()}"
        ),
    )

if args.debug:
    ChannelDebug(root).pack(side="right", fill="both")
EffectList(root).pack(side="right", fill="both")
InstrumentList(root).pack(side="right", fill="both")
PatternViewFrame(root).pack(side="bottom", fill="both", expand=True)
PatternMatrix(root).pack(side="left", fill="both")
SongDataView(root).pack(side="left", fill="both")
PatternList(root).pack(side="left", fill="both", expand=True)


# Global Keyboard Shortcuts
# TODO: rebindable shortcuts
def makeKeybinds():
    # I wish I could make anonymous scopes.

    # Pause/Play
    root.bind_all("<space>", lambda *_: program.p.songPlayer.togglePlayback())

    # Jump to start of pattern
    def jumpToStartOfPattern():
        program.p.songPlayer.setPlaybackCursor(None, 0)

    root.bind_all("<Control-space>", lambda *_: jumpToStartOfPattern())

    # Jump to last playback position
    def jumpToLastPlaybackPosition():
        program.p.songPlayer.setPlaybackCursor(
            program.p.songPlayer.lastMatrixRow, program.p.songPlayer.lastPatternRow
        )

    root.bind_all("<Shift-space>", lambda *_: jumpToLastPlaybackPosition())

    # Jump to start of song
    def jumpToStartOfSong():
        program.p.songPlayer.setPlaybackCursor(0, 0)

    root.bind_all("<Control-Shift-space>", lambda *_: jumpToStartOfSong())


makeKeybinds()


root.mainloop()
program.p.close()
