import argparse
import logging
import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import cast

from interface.program.patternList import PatternList
from interface.program.patternMatrix import PatternMatrix
from interface.program.patternViewFrame import PatternViewFrame
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
# root.bind_all(
#     "<Space>",
#     lambda *_: setattr(program, "allowEditingPattern", not program.allowEditingPattern),
# )


PatternViewFrame(root).pack(side="bottom", fill="both", expand=True)
PatternMatrix(root).pack(side="left", fill="both")
PatternList(root).pack(side="left", fill="both")


root.mainloop()
program.p.close()
